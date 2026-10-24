"""Multi-turn eval: follow-up questions (pronouns, property switches, "and for Gold members?"), an injection hidden in
turn 1 or turn 2, a topic change, a follow-up after a refusal, a must-refuse follow-up and Spanish.

Every turn of every case runs through the same steps as the app (rewrite -> scope check and retrieval -> answer),
so earlier answers are real answers. Only the last turn is graded.

python -m eval.run_multiturn_eval --modes off,rule,llm --runs 3 --price-in 0.1 --price-out 0.5
python -m eval.run_multiturn_eval --split heldout --modes llm --runs 3 --price-in 0.1 --price-out 0.5
python -m eval.run_multiturn_eval --modes rule --no-answers      # retrieval only, free (CI)

Modes: off = each question as typed, for the picked property (the behaviour before this change);
rule = src/rewrite.rule_rewrite; llm = src/rewrite.llm_rewrite (one short Haiku call per follow-up).
Keyword-only search, like the live demo.
Saves eval/reports/multiturn-<date>-<split>-<mode>.md and .jsonl (raw turns, so a fixed metric can re-score them).
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from eval.metrics import grade
from eval.run_eval import retrieval_hit
from src import rewrite, service
from src.chat import Turn
from src.config import LLM_MODEL, REPORTS_DIR, ROOT
from src.escalation import is_safety
from src.retrieve import Retriever
from src.usage import estimate_cost

CASES = ROOT / "eval" / "multiturn_cases.jsonl"


def load_cases(path: Path = CASES, split: str = "dev") -> list[dict]:
    items = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [c for c in items if split == "all" or c["split"] == split]


def run_turn(retriever, question: str, picker: str, turns: list, mode: str, answers: bool, client=None) -> dict:
    """One message, the way views/assistant.py handles it. Returns what the eval needs to grade and cost it."""
    rw = rewrite.standalone(question, turns, picker, mode=mode, client=client)
    prep = service.prepare(retriever, rw.question, rw.property)
    if is_safety(question) and not prep.get("safety"):
        prep = {"blocked": True, "safety": True, "hits": []}
    seconds = rw.seconds
    if prep["blocked"]:
        result = service.blocked_result(question)
    elif not answers:
        result = None
    else:
        from src.generate import AnswerStream

        run = AnswerStream(rw.question, rw.property, prep["hits"], client=client)
        result = run.run()
        seconds += run.total_time or 0.0
    if result is not None:
        result = service.finalize(rw.question, rw.property, result)
    return {"rewrite": rw, "hits": prep["hits"], "result": result, "seconds": seconds, "pre_api": prep["blocked"]}


def grade_case(case: dict, final: dict) -> dict:
    rw, result = final["rewrite"], final["result"]
    item = {**case, "question": rw.question}
    out = {
        "property_ok": rw.property == case["expected_property"],
        "retrieval_ok": None if case.get("unanswerable") else retrieval_hit(item, final["hits"]),
    }
    if result is not None:
        out.update(grade(item, result))
    return out


def run_case(retriever, case: dict, mode: str, answers: bool, client=None) -> dict:
    turns, records = [], []
    for t in case["turns"]:
        step = run_turn(retriever, t["q"], t["property"], turns, mode, answers, client)
        rw, result = step["rewrite"], step["result"] or {"answer": "", "found": False, "citations": []}
        turn = Turn(t["q"], rw.property, result=result, kind="answer" if result.get("found") else "refusal")
        turn.rewritten = rw.question if rw.changed else None
        turns.append(turn)
        usage = (step["result"] or {}).get("usage", {"input_tokens": 0, "output_tokens": 0})
        records.append(
            {
                "question": t["q"],
                "picker": t["property"],
                "property": rw.property,
                "rewritten": rw.question,
                "method": rw.method,
                "answer": result.get("answer"),
                "found": result.get("found"),
                "cited": [c.get("source") for c in result.get("citations", [])],
                "retrieved": [{"source": h["source"], "section": h["section"]} for h in step["hits"]],
                "seconds": round(step["seconds"], 3),
                "tokens_in": usage["input_tokens"] + rw.usage["input_tokens"],
                "tokens_out": usage["output_tokens"] + rw.usage["output_tokens"],
                "rewrite_tokens_in": rw.usage["input_tokens"],
                "pre_api": step["pre_api"],
            }
        )
    return {"id": case["id"], "category": case["category"], "turns": records, "grade": grade_case(case, step)}


def percentile(values: list, q: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    k = (len(values) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (k - lo)


def rate(values: list) -> tuple[int, int]:
    vals = [v for v in values if v is not None]
    return sum(bool(v) for v in vals), len(vals)


def summarize(runs: list[list[dict]], price_in, price_out) -> dict:
    flat = [c for run in runs for c in run]
    metrics = {}
    for key in ("property_ok", "retrieval_ok", "correct", "citation_ok", "grounded"):
        metrics[key] = rate([c["grade"].get(key) for c in flat])
    per_run = [rate([c["grade"].get("correct") for c in run]) for run in runs]
    turns = [t for c in flat for t in c["turns"]]
    final_seconds = [c["turns"][-1]["seconds"] for c in flat if not c["turns"][-1]["pre_api"]]
    tokens_in, tokens_out = sum(t["tokens_in"] for t in turns), sum(t["tokens_out"] for t in turns)
    cost = estimate_cost(tokens_in, tokens_out, price_in, price_out)
    stable = {}
    for c in flat:
        stable.setdefault(c["id"], set()).add(bool(c["grade"].get("correct")))
    return {
        "metrics": metrics,
        "per_run_correct": per_run,
        "requests": len(turns),
        "rewrite_calls": sum(1 for t in turns if t["rewrite_tokens_in"]),
        "cost_per_1000": None if cost is None else cost / len(turns) * 1000,
        "p50": percentile(final_seconds, 0.5),
        "p95": percentile(final_seconds, 0.95),
        "consistent": sum(len(v) == 1 for v in stable.values()),
        "cases": len(stable),
        "failing": sorted({c["id"] for c in flat if c["grade"].get("correct") is False}),
    }


def pct(ok: int, n: int) -> str:
    return f"{ok / n:.0%} ({ok}/{n})" if n else "n/a"


def report(split: str, mode: str, runs: list, summary: dict, args) -> str:
    m = summary["metrics"]
    seconds = "n/a" if summary["p95"] is None else f"p50 {summary['p50']:.2f} s, p95 {summary['p95']:.2f} s"
    cost = "not configured" if summary["cost_per_1000"] is None else f"${summary['cost_per_1000']:.2f}"
    lines = [
        f"# Multi-turn eval: {split}, rewrite mode `{mode}`",
        "",
        f"- Date: {datetime.now():%Y-%m-%d %H:%M} · model {LLM_MODEL} · keyword-only search · {args.runs} run(s)",
        f"- Cases: {summary['cases']} · requests (every turn): {summary['requests']} · rewrite calls: "
        f"{summary['rewrite_calls']}",
        f"- Prices: ${args.price_in} / ${args.price_out} per million tokens (in / out)",
        "",
        "| Metric (last turn) | Result |",
        "|---|---|",
        f"| Right property | {pct(*m['property_ok'])} |",
        f"| Strict retrieval (expected passage retrieved) | {pct(*m['retrieval_ok'])} |",
    ]
    if args.answers:
        per_run = ", ".join(pct(*r) for r in summary["per_run_correct"])
        lines += [
            f"| Answer accuracy | {pct(*m['correct'])} (runs: {per_run}) |",
            f"| Citation accuracy | {pct(*m['citation_ok'])} |",
            f"| Numeric grounding | {pct(*m['grounded'])} |",
            f"| Same verdict in every run | {summary['consistent']}/{summary['cases']} cases |",
            f"| Latency, last turn (rewrite + answer) | {seconds} |",
            f"| Cost per 1,000 requests (every turn, rewrite included) | {cost} |",
        ]
        lines += ["", f"Failing cases: {', '.join(summary['failing']) or 'none'}"]
    lines += [
        "",
        "## Last turn of each case (run 1)",
        "",
        "| Case | Category | Typed | Understood as | Property | Pass |",
    ]
    lines += ["|---|---|---|---|---|---|"]
    for c in runs[0]:
        last = c["turns"][-1]
        ok = c["grade"].get("correct") if args.answers else c["grade"].get("retrieval_ok")
        mark = "–" if ok is None else ("yes" if ok else "**no**")
        typed = last["question"].replace("|", "\\|")
        understood = last["rewritten"].replace("|", "\\|")
        lines.append(f"| {c['id']} | {c['category']} | {typed} | {understood} | {last['property']} | {mark} |")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--modes", default="off,rule,llm")
    parser.add_argument("--split", default="dev", choices=["dev", "heldout", "all"])
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--no-answers", dest="answers", action="store_false", help="retrieval only, no API")
    parser.add_argument("--price-in", type=float, default=None, help="USD per million input tokens")
    parser.add_argument("--price-out", type=float, default=None, help="USD per million output tokens")
    parser.add_argument("--min-retrieval", type=float, default=0.0, help="fail below this strict retrieval rate")
    parser.add_argument("--no-report", action="store_true")
    args = parser.parse_args(argv)
    retriever = Retriever(use_embeddings=False)
    cases = load_cases(split=args.split)
    status = 0
    for mode in args.modes.split(","):
        if mode == "llm" and not args.answers:
            print("llm mode needs the API; skipped with --no-answers")
            continue
        runs = [[run_case(retriever, c, mode, args.answers) for c in cases] for _ in range(args.runs)]
        summary = summarize(runs, args.price_in, args.price_out)
        text = report(args.split, mode, runs, summary, args)
        print(text)
        ok, n = summary["metrics"]["retrieval_ok"]
        if n and ok / n < args.min_retrieval:
            print(f"FAIL: strict retrieval {ok}/{n} below {args.min_retrieval:.0%}")
            status = 1
        if not args.no_report:
            stem = REPORTS_DIR / f"multiturn-{datetime.now():%Y-%m-%d}-{args.split}-{mode}"
            stem.with_suffix(".md").write_text(text, encoding="utf-8")
            raw = {"summary": summary, "runs": runs}
            stem.with_suffix(".jsonl").write_text(json.dumps(raw, ensure_ascii=False) + "\n", encoding="utf-8")
    return status


if __name__ == "__main__":
    sys.exit(main())
