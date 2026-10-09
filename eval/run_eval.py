"""Evaluation runner. Saves a markdown report to eval/reports/ on every run.

  python -m eval.run_eval                       # retrieval only (free, no API key)
  python -m eval.run_eval --answers             # also grades Claude's answers
  python -m eval.run_eval --answers --runs 3    # repeat to measure consistency
  python -m eval.run_eval --bm25-only           # keyword search only, for comparison
  python -m eval.run_eval --min-hit 0.85        # fail if retrieval drops (used in CI)
  python -m eval.run_eval --answers --price-in 1 --price-out 5   # add cost (USD per million tokens)

Retrieval is strict: a hit means the expected phrase (e.g. "up to 40 lbs") is inside a
retrieved passage from the expected document, not just that the document appears somewhere.
"""

import argparse
import json
import statistics
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from eval.metrics import grade
from src.config import LLM_MODEL, TOP_K
from src.retrieve import Retriever

HERE = Path(__file__).parent


def retrieval_hit(item: dict, results: list) -> bool:
    texts = item["expected_text"] if isinstance(item["expected_text"], list) else [item["expected_text"]]
    return all(any(r["source"] == item["expected_source"] and t in r["text"] for r in results) for t in texts)


def pct(ok: int, n: int) -> str:
    return f"{ok}/{n} = {ok / n:.0%}" if n else "n/a"


def percentile(values: list, p: float) -> float:
    values = sorted(values)
    return values[min(len(values) - 1, int(round(p * (len(values) - 1))))] if values else 0.0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--answers", action="store_true", help="grade Claude's answers (uses the API)")
    parser.add_argument("--runs", type=int, default=1, help="repeat the answer eval N times")
    parser.add_argument("--bm25-only", action="store_true")
    parser.add_argument("--min-hit", type=float, default=0.0)
    parser.add_argument("--price-in", type=float, help="USD per million input tokens")
    parser.add_argument("--price-out", type=float, help="USD per million output tokens")
    parser.add_argument("--no-report", action="store_true")
    args = parser.parse_args()

    lines = (HERE / "questions.jsonl").read_text(encoding="utf-8").splitlines()
    items = [json.loads(line) for line in lines if line.strip()]
    retriever = Retriever(use_embeddings=not args.bm25_only)
    setup = "bm25" if retriever.model is None else "hybrid"
    if args.answers:
        from src.generate import answer

    # ---- Retrieval (deterministic, run once) ----
    rows, by_cat = [], defaultdict(lambda: [0, 0])
    results_by_id, hit_ok, hit_total = {}, 0, 0
    for item in items:
        results = retriever.search(item["question"], item["property"], k=TOP_K)
        results_by_id[item["id"]] = results
        row = {"id": item["id"], "category": item["category"], "question": item["question"], "retrieval": "-"}
        if item.get("expected_source"):
            hit = retrieval_hit(item, results)
            hit_total += 1
            hit_ok += hit
            by_cat[item["category"]][1] += 1
            by_cat[item["category"]][0] += hit
            row["retrieval"] = "✅" if hit else "❌"
        rows.append(row)
    hit_rate = hit_ok / hit_total

    # ---- Answers (optional, can repeat) ----
    run_scores, latencies, tokens_in, tokens_out = [], [], 0, 0
    totals = defaultdict(int)
    raw = []  # every answer from every run, saved next to the report so failures can be audited
    if args.answers:
        for run in range(args.runs):
            correct = 0
            for item, row in zip(items, rows, strict=True):
                start = time.time()
                result = answer(item["question"], item["property"], results_by_id[item["id"]])
                latencies.append(time.time() - start)
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
                    row["note"] = "" if g["correct"] else result["answer"][:110].replace("\n", " ").replace("|", "/")
                    if g["ungrounded"]:
                        row["note"] += f" [ungrounded numbers: {', '.join(g['ungrounded'])}]"
            run_scores.append(correct / len(items))
            print(f"run {run + 1}/{args.runs}: answer accuracy {correct}/{len(items)}")

    for row in rows:
        print(f"{row['id']} R:{row['retrieval']} A:{row.get('answer', '-')}  {row['question']}  {row.get('note', '')}")

    # ---- Summary ----
    summary = [f"Setup: {setup}, top_k={TOP_K}" + (f", model={LLM_MODEL}, runs={args.runs}" if args.answers else "")]
    summary.append(f"Retrieval (strict, right passage in top {TOP_K}): {pct(hit_ok, hit_total)}")
    if args.answers:
        mean = statistics.mean(run_scores)
        spread = f" (min {min(run_scores):.0%}, max {max(run_scores):.0%})" if args.runs > 1 else ""
        summary += [
            f"Answer accuracy: {mean:.0%}{spread}",
            f"Citation accuracy (cites the right document): {pct(totals['cite_ok'], totals['ans_n'])}",
            f"Numeric grounding (every number traceable to a source): {pct(totals['ground_ok'], totals['ans_n'])}",
            f"Correct refusals: {pct(totals['refuse_ok'], totals['refuse_n'])}",
            f"Latency per answer: p50 {percentile(latencies, 0.5):.2f}s, p95 {percentile(latencies, 0.95):.2f}s",
            f"Tokens per question: {tokens_in // len(latencies)} in / {tokens_out // len(latencies)} out",
        ]
        if args.price_in is not None and args.price_out is not None:
            cost = (tokens_in * args.price_in + tokens_out * args.price_out) / 1e6 / len(latencies)
            summary.append(f"Cost per question: ${cost:.4f} (${cost * 1000:.2f} per 1,000 questions)")
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
            "| ID | Category | Question | Retrieval | Answer | Note |",
            "|---|---|---|---|---|---|",
        ]
        for r in rows:
            cells = [r["id"], r["category"], r["question"], r["retrieval"], r.get("answer", "-"), r.get("note", "")]
            out.append("| " + " | ".join(cells) + " |")
        report.write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"Report saved: {report.relative_to(HERE.parent)}")
        if raw:
            dump = report.with_suffix(".jsonl")
            dump.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in raw), encoding="utf-8")
            print(f"Raw answers saved: {dump.relative_to(HERE.parent)}")

    if hit_rate < args.min_hit:
        sys.exit(f"FAIL: retrieval {hit_rate:.0%} is below the minimum {args.min_hit:.0%}")


if __name__ == "__main__":
    main()
