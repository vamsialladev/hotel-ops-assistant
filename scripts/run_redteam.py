"""Red-team suite for this app: the shared corpus (hotel-ai-platform) plus this app's own cases (redteam/cases.jsonl),
run through this app's real defences before the API: input guardrails, the scope check and emergency rule
(service.prepare), passage quarantine, and the output guardrails. No API calls; runs in CI.

    python scripts/run_redteam.py                 print the summary, exit 1 below the gate
    python scripts/run_redteam.py --report        also rewrite docs/redteam-report.md

The app's cases were written after the shared patterns were frozen (v0.1.0) and are reported as they came out.
"""

import argparse
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hotelplatform import jsonlog, redteam  # noqa: E402

from src import ops, service  # noqa: E402

CASES = ROOT / "redteam" / "cases.jsonl"
REPORT = ROOT / "docs" / "redteam-report.md"
PROPERTY = "beach-resort"


def handlers(retriever):
    def input_layer(case):
        v = ops.check_question(case.text)
        if not v.allowed:
            return redteam.Outcome("block", v.reason)
        prep = service.prepare(retriever, v.text, PROPERTY)
        if prep.get("safety"):
            return redteam.Outcome("allow", None, "emergency: fixed safety message")
        if prep["blocked"]:
            return redteam.Outcome("block", "off_topic", "scope check")
        if any(f.startswith("injection_removed") for f in v.flags):
            return redteam.Outcome("quarantine", None, v.text[:100])
        if any(f.startswith("pii_redacted") for f in v.flags):
            return redteam.Outcome("redact")
        return redteam.Outcome("allow")

    def output_layer(case):
        ctx = case.context
        hits = [{"text": s} for s in ctx.get("sources", [])]
        cites = [{"source": c} for c in ctx.get("citations", [])]
        v = ops.check_answer(case.text, hits, cites, ctx.get("input", ""))
        if not v.allowed:
            return redteam.Outcome("block", v.reason)
        return redteam.Outcome("redact" if v.text != case.text else "allow", None, ", ".join(v.flags))

    def retrieved_layer(case):
        (passage,), changed = service.quarantine_passages([{"text": case.text}])
        return redteam.Outcome("quarantine" if changed else "allow", None, passage["text"][:100])

    return {"input": input_layer, "output": output_layer, "retrieved": retrieved_layer}


def run(retriever=None):
    from src.retrieve import Retriever

    jsonlog.configure("redteam", "ci", stream=io.StringIO())
    retriever = retriever or Retriever(use_embeddings=False)
    h = handlers(retriever)
    shared = redteam.run(redteam.shared_cases(), h)
    own = redteam.run(redteam.load_cases(CASES), h)
    return shared, own


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args(argv)
    shared, own = run()
    for name, results in (("shared corpus", shared), ("this app's cases", own)):
        s = redteam.score(results)
        print(f"{name}: {s['passed']}/{s['cases']} passed; attacks stopped {s['attacks_stopped']}/{s['attacks']}; "
              f"false alarms {s['false_alarms']}/{s['controls']}")  # fmt: skip
        for r in results:
            if not r.passed:
                print(f"  FAIL {r.case.id} [{r.case.category}] expected {r.case.expect}, got {r.outcome.verdict}")
    if args.report:
        REPORT.write_text(
            redteam.report_markdown(shared, "Red-team report: shared corpus through this app")
            + "\n"
            + redteam.report_markdown(own, "Red-team report: this app's own cases (held out)"),
            encoding="utf-8",
            newline="\n",
        )
    # The gate: the shared corpus passes in full, and no case of this app's fails unless it's a listed known gap.
    new_failures = [r.case.id for r in shared + own if not r.passed and r.case.id not in known_gaps()]
    if new_failures:
        print("GATE FAILED: new red-team failures:", ", ".join(new_failures))
    return 1 if new_failures else 0


def known_gaps() -> set[str]:
    lines = (ROOT / "redteam" / "known_gaps.txt").read_text(encoding="utf-8").splitlines()
    return {ln.split()[0] for ln in lines if ln.strip() and not ln.startswith("#")}


if __name__ == "__main__":
    sys.exit(main())
