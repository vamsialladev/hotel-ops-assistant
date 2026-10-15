"""Evaluation runner. Saves a markdown report (and, with --answers, every raw answer) to eval/reports/.

  python -m eval.run_eval                       # retrieval, scope and escalation checks (free, no API key)
  python -m eval.run_eval --answers             # also grades Claude's answers
  python -m eval.run_eval --answers --runs 3    # repeat to measure consistency
  python -m eval.run_eval --bm25-only           # keyword search only (what Streamlit Cloud runs)
  python -m eval.run_eval --min-hit 0.85        # fail if retrieval drops (used in CI)
  python -m eval.run_eval --answers --price-in 0.10 --price-out 0.50   # cost (USD per million tokens)

Answers go through the same path as the app: the scope check, then the streaming call with the
shipped model settings, so time to first word and cost match what users get.

Retrieval is strict: a hit means the expected phrase (e.g. "up to 40 lbs") is inside a
retrieved passage from the expected document, not just that the document appears somewhere.
"""

import argparse
import json
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from eval.metrics import grade
from src.activity import percentile
from src.config import LLM_EFFORT, LLM_MAX_TOKENS, LLM_MODEL, PRICE_IN_PER_M, PRICE_OUT_PER_M, TOP_K
from src.escalation import escalation_ids
from src.retrieve import Retriever
from src.service import blocked_result, prepare

HERE = Path(__file__).parent


def retrieval_hit(item: dict, results: list) -> bool:
    texts = item["expected_text"] if isinstance(item["expected_text"], list) else [item["expected_text"]]
    return all(any(r["source"] == item["expected_source"] and t in r["text"] for r in results) for t in texts)


def pct(ok: int, n: int) -> str:
    return f"{ok}/{n} = {ok / n:.0%}" if n else "n/a"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--answers", action="store_true", help="grade Claude's answers (uses the API)")
    parser.add_argument("--runs", type=int, default=1, help="repeat the answer eval N times")
    parser.add_argument("--bm25-only", action="store_true")
    parser.add_argument("--min-hit", type=float, default=0.0)
    parser.add_argument("--price-in", type=float, default=PRICE_IN_PER_M, help="USD per million input tokens")
    parser.add_argument("--price-out", type=float, default=PRICE_OUT_PER_M, help="USD per million output tokens")
    parser.add_argument("--no-report", action="store_true")
    args = parser.parse_args()

    lines = (HERE / "questions.jsonl").read_text(encoding="utf-8").splitlines()
    items = [json.loads(line) for line in lines if line.strip()]
    retriever = Retriever(use_embeddings=not args.bm25_only)
    setup = "hybrid" if retriever.model is not None else "bm25"
    if args.answers:
        from src.generate import AnswerStream

    # ---- Retrieval, scope check and escalation rules (deterministic, run once) ----
    rows, by_cat = [], defaultdict(lambda: [0, 0])
    prepared, hit_ok, hit_total = {}, 0, 0
    off_topic_blocked = off_topic_n = wrongly_blocked = esc_ok = 0
    for item in items:
        results = retriever.search(item["question"], item["property"], k=TOP_K)
        prepared[item["id"]] = prep = prepare(retriever, item["question"], item["property"])
        row = {"id": item["id"], "category": item["category"], "question": item["question"], "retrieval": "-"}
        if item.get("expected_source") and not item.get("unanswerable"):
            hit = retrieval_hit(item, results)
            hit_total += 1
            hit_ok += hit
            by_cat[item["category"]][1] += 1
            by_cat[item["category"]][0] += hit
            row["retrieval"] = "✅" if hit else "❌"
            wrongly_blocked += prep["blocked"]
        if item["category"] == "off_topic":
            off_topic_n += 1
            off_topic_blocked += prep["blocked"]
        expected_esc = item.get("escalate", [])
        got_esc = escalation_ids(item["question"], item["property"])
        esc_ok += got_esc == expected_esc
        row["note"] = "" if got_esc == expected_esc else f"[escalation: expected {expected_esc}, got {got_esc}]"
        row["scope"] = "blocked" if prep["blocked"] else "api"
        rows.append(row)
    hit_rate = hit_ok / hit_total

    # ---- Answers (optional, can repeat) ----
    run_scores, totals_s, ttfts, raw = [], [], [], []
    tokens_in = tokens_out = asked = 0
    totals = defaultdict(int)
    if args.answers:
        for run in range(args.runs):
            correct = 0
            for item, row in zip(items, rows, strict=True):
                prep = prepared[item["id"]]
                asked += 1
                if prep["blocked"]:
                    result = blocked_result(item["question"])
                else:
                    stream = AnswerStream(item["question"], item["property"], prep["hits"])
                    result = stream.run()
                    totals_s.append(stream.total_time)
                    ttfts.append(stream.time_to_first_token)
                tokens_in += result["usage"]["input_tokens"]
                tokens_out += result["usage"]["output_tokens"]
                g = grade(item, result)
                correct += g["correct"]
                raw.append(
                    {
                        "run": run + 1,
                        "id": item["id"],
                        "answer": result["answer"],
                        "cited": [c["source"] for c in result["citations"]],
                        "pre_api": prep["blocked"],
                        **g,
                    }
                )
                if item.get("unanswerable"):
                    totals["refuse_n"] += 1
                    totals["refuse_ok"] += g["correct"]
                else:
                    totals["ans_n"] += 1
                    totals["cite_ok"] += g["citation_ok"]
                    totals["ground_ok"] += g["grounded"]
                if run == 0:
                    row["answer"] = "✅" if g["correct"] else "❌"
                    if not g["correct"]:
                        row["note"] += " " + result["answer"][:110].replace("\n", " ").replace("|", "/")
                    if g["ungrounded"]:
                        row["note"] += f" [ungrounded numbers: {', '.join(g['ungrounded'])}]"
            run_scores.append(correct / len(items))
            print(f"run {run + 1}/{args.runs}: answer accuracy {correct}/{len(items)}")

    for row in rows:
        print(f"{row['id']} R:{row['retrieval']} A:{row.get('answer', '-')}  {row['question']}  {row['note'].strip()}")

    # ---- Summary ----
    head = f"Setup: {setup}, top_k={TOP_K}"
    if args.answers:
        head += f", model={LLM_MODEL}, max_tokens={LLM_MAX_TOKENS}, effort={LLM_EFFORT or 'default'}, runs={args.runs}"
    summary = [head, f"Retrieval (strict, right passage in top {TOP_K}): {pct(hit_ok, hit_total)}"]
    summary += [
        f"Off-topic questions refused before the API: {off_topic_blocked}/{off_topic_n}",
        f"Answerable questions wrongly blocked by the scope check: {wrongly_blocked}/{hit_total}",
        f"Escalation rules correct: {pct(esc_ok, len(items))}",
    ]
    if args.answers:
        mean = statistics.mean(run_scores)
        spread = f" (min {min(run_scores):.0%}, max {max(run_scores):.0%})" if args.runs > 1 else ""
        summary += [
            f"Answer accuracy: {mean:.0%}{spread}",
            f"Citation accuracy (cites the right document): {pct(totals['cite_ok'], totals['ans_n'])}",
            f"Numeric grounding (every number traceable to a source): {pct(totals['ground_ok'], totals['ans_n'])}",
            f"Correct refusals: {pct(totals['refuse_ok'], totals['refuse_n'])}",
            f"Time to first word: p50 {percentile(ttfts, 0.5):.2f}s, p95 {percentile(ttfts, 0.95):.2f}s",
            f"Latency per answer: p50 {percentile(totals_s, 0.5):.2f}s, p95 {percentile(totals_s, 0.95):.2f}s",
            f"Tokens per question: {tokens_in // asked} in / {tokens_out // asked} out",
        ]
        if args.price_in is not None and args.price_out is not None:
            cost = (tokens_in * args.price_in + tokens_out * args.price_out) / 1e6 / asked
            summary.append(
                f"Cost per question: ${cost:.4f} (${cost * 1000:.2f} per 1,000 questions; "
                f"prices ${args.price_in}/${args.price_out} per M tokens; off-topic questions blocked for free)"
            )
    print("\n" + "\n".join(summary))

    if not args.no_report:
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        report = HERE / "reports" / f"{stamp}_{setup}{f'_answers_{LLM_MODEL}' if args.answers else ''}.md"
        report.parent.mkdir(exist_ok=True)
        out = [f"# Eval report {stamp}", "", *[f"- {s}" for s in summary], "", "## Retrieval by category", ""]
        out += ["| Category | Hits |", "|---|---|"] + [f"| {c} | {ok}/{n} |" for c, (ok, n) in sorted(by_cat.items())]
        out += [
            "",
            "## All questions",
            "",
            "| ID | Category | Question | Retrieval | Scope | Answer | Note |",
            "|---|---|---|---|---|---|---|",
        ]
        for r in rows:
            cells = [r["id"], r["category"], r["question"], r["retrieval"], r["scope"], r.get("answer", "-"), r["note"]]
            out.append("| " + " | ".join(c.replace("|", "/") for c in cells) + " |")
        report.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
        print(f"Report saved: {report.relative_to(HERE.parent)}")
        if raw:
            dump = report.with_suffix(".jsonl")
            dump.write_text(
                "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in raw), encoding="utf-8", newline="\n"
            )
            print(f"Raw answers saved: {dump.relative_to(HERE.parent)}")

    if hit_rate < args.min_hit:
        sys.exit(f"FAIL: retrieval {hit_rate:.0%} is below the minimum {args.min_hit:.0%}")


if __name__ == "__main__":
    main()
