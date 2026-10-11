"""First-question success: what happens to the questions visitors type first, without seeing any examples.

python -m eval.run_visitor_eval                      # routing + retrieval only (free), hybrid if installed
python -m eval.run_visitor_eval --bm25-only          # the live demo's keyword-only mode
python -m eval.run_visitor_eval --answers            # real answers (uses the API, about 40 calls)
python -m eval.run_visitor_eval --bm25-only --min-success 0.9 --no-report   # CI gate (free)
python -m eval.run_visitor_eval --baseline ...       # the pipeline before in-app guidance (1.3.3)

Each run saves a markdown report and a JSON summary in eval/reports/ (the app shows the latest
answered keyword-only result on the How it works and Admin pages).
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from eval.visitor_metrics import grade_visitor, summarize
from src import service
from src.config import LLM_MODEL, REPORTS_DIR, ROOT
from src.scope import SCOPE_MESSAGE

QUESTIONS = ROOT / "eval" / "visitor_questions.jsonl"


def load_items(path: Path = QUESTIONS) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def baseline_respond(retriever, question: str, prop: str, use_api: bool) -> dict:
    """The 1.3.3 pipeline: scope check, then Claude. No greetings, no suggestions."""
    prep = service.prepare(retriever, question, prop)
    if prep["blocked"]:
        return {"kind": "scope", "answer": SCOPE_MESSAGE, "citations": [], "hits": [], "suggestions": []}
    if not use_api:
        return {"kind": "pending", "answer": "", "citations": [], "hits": prep["hits"], "suggestions": []}
    from src.generate import answer

    result = answer(question, prop, prep["hits"])
    kind = "answer" if result["found"] else "refusal"
    return {**result, "kind": kind, "hits": prep["hits"], "suggestions": []}


def current_respond(retriever, question: str, prop: str, use_api: bool) -> dict:
    from src.assist import respond

    return respond(retriever, question, prop, use_api=use_api)


def pct(value) -> str:
    return "n/a" if value is None else f"{value:.0%}"


def report(items, outcomes, grades, summary, args, mode) -> str:
    lines = [
        f"# Visitor questions: first-question success ({mode}{', answers' if args.answers else ', routing only'})",
        "",
        f"{datetime.now():%Y-%m-%d %H:%M} · pipeline: {'baseline (1.3.3)' if args.baseline else 'current'}"
        + (f" · model: {LLM_MODEL}" if args.answers else ""),
        "",
        "| Metric | Result |",
        "|---|---|",
        f"| First-question success (all {len(items)}) | {pct(summary['first_question_success'])} |",
        f"| In-scope questions answered correctly with a citation | {pct(summary['in_scope_answered'])} |",
        f"| Out-of-scope questions refused | {pct(summary['out_of_scope_refused'])} |",
        f"| Refusals with 'Did you mean' suggestions | {pct(summary['refusals_with_suggestions'])} |",
        f"| Greetings and meta questions handled | {pct(summary['greetings_handled'])} |",
        f"| Off-topic and gibberish handled | {pct(summary['off_topic_handled'])} |",
        "",
        "| ID | Property | Question | Expected | Got | Suggestions | Result |",
        "|---|---|---|---|---|---|---|",
    ]
    for item, out, g in zip(items, outcomes, grades, strict=True):
        result = {True: "pass", False: "**FAIL**", None: "not graded"}[g["success"]]
        lines.append(
            f"| {item['id']} | {item['property']} | {item['question']} | {item['expect']} | {out['kind']} "
            f"| {g['suggestions']} | {result} |"
        )
    if args.answers:
        lines += ["", "## Answers", ""]
        for item, out in zip(items, outcomes, strict=True):
            text = " ".join((out.get("answer") or "").split())
            lines.append(f"- **{item['id']}** {item['question']} → {text[:300]}")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--answers", action="store_true", help="grade real answers (uses the API)")
    parser.add_argument("--bm25-only", action="store_true", help="keyword-only retrieval (the live demo)")
    parser.add_argument("--baseline", action="store_true", help="the pipeline before in-app guidance")
    parser.add_argument("--min-success", type=float, default=0.0, help="fail below this first-question success")
    parser.add_argument("--no-report", action="store_true")
    args = parser.parse_args(argv)

    from src.retrieve import Retriever

    retriever = Retriever(use_embeddings=not args.bm25_only)
    mode = retriever.mode
    respond = baseline_respond if args.baseline else current_respond
    items = load_items()
    outcomes = [respond(retriever, it["question"], it["property"], args.answers) for it in items]
    grades = [grade_visitor(it, out, args.answers) for it, out in zip(items, outcomes, strict=True)]
    summary = summarize(items, grades)

    print(f"Visitor questions ({mode}, {'answers' if args.answers else 'routing only'}): {len(items)}")
    for key in (
        "first_question_success",
        "in_scope_answered",
        "out_of_scope_refused",
        "refusals_with_suggestions",
        "greetings_handled",
        "off_topic_handled",
    ):
        print(f"  {key.replace('_', ' ')}: {pct(summary[key])}")
    failed = [it["id"] for it, g in zip(items, grades, strict=True) if g["success"] is False]
    print(f"  failed: {', '.join(failed) or 'none'}")

    if not args.no_report:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        stem = f"{datetime.now():%Y-%m-%d_%H%M}_visitor_{mode}{'_answers' if args.answers else ''}"
        stem += "_baseline" if args.baseline else ""
        (REPORTS_DIR / f"{stem}.md").write_text(report(items, outcomes, grades, summary, args, mode), encoding="utf-8")
        meta = {
            "mode": mode,
            "answers": args.answers,
            "pipeline": "baseline" if args.baseline else "current",
            "date": f"{datetime.now():%Y-%m-%d}",
            "model": LLM_MODEL if args.answers else None,
            "questions": len(items),
        }
        (REPORTS_DIR / f"{stem}.json").write_text(json.dumps({**meta, **summary}, indent=2), encoding="utf-8")
        print(f"  saved eval/reports/{stem}.md")

    score = summary["first_question_success"] or 0.0
    if score < args.min_success:
        print(f"FAIL: first-question success {score:.0%} is below the gate of {args.min_success:.0%}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
