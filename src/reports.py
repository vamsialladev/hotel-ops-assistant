"""Read real results from saved eval reports and BUSINESS_CASE.md, so the app never hard-codes a number."""

import re
from pathlib import Path

from src.config import REPORTS_DIR, ROOT

NAME = re.compile(r"^(?P<stamp>\d{4}-\d{2}-\d{2}_\d{4})_(?P<setup>bm25|hybrid)(?:_answers_(?P<model>.+))?\.md$")

FRACTION = r"(\d+)/(\d+) = (\d+)%"
PATTERNS = {
    "retrieval": re.compile(r"Retrieval \(strict[^)]*\): " + FRACTION),
    "answer_accuracy": re.compile(r"Answer accuracy: (\d+)%(?: \(min (\d+)%, max (\d+)%\))?"),
    "citation": re.compile(r"Citation accuracy[^:]*: " + FRACTION),
    "grounding": re.compile(r"Numeric grounding[^:]*: " + FRACTION),
    "refusals": re.compile(r"Correct refusals: " + FRACTION),
    "off_topic_blocked": re.compile(r"Off-topic questions refused before the API: (\d+)/(\d+)"),
    "wrongly_blocked": re.compile(r"Answerable questions wrongly blocked by the scope check: (\d+)/(\d+)"),
    "escalation": re.compile(r"Escalation rules correct: " + FRACTION),
    "ttft": re.compile(r"Time to first word: p50 ([\d.]+)s, p95 ([\d.]+)s"),
    "latency": re.compile(r"Latency per answer: p50 ([\d.]+)s, p95 ([\d.]+)s"),
    "tokens": re.compile(r"Tokens per question: (\d+) in / (\d+) out"),
    "cost_per_1000": re.compile(r"\(\$([\d.]+) per 1,000 questions"),
    "setup": re.compile(r"Setup: (bm25|hybrid), top_k=(\d+)(?:, model=([^,\s]+))?"),
    "runs": re.compile(r"runs=(\d+)"),
    "max_tokens": re.compile(r"max_tokens=(\d+)"),
    "effort": re.compile(r"effort=(\w+)"),
}


def _fraction(m) -> dict:
    return {"ok": int(m.group(1)), "n": int(m.group(2)), "pct": int(m.group(3))}


def parse_report(text: str) -> dict:
    out = {}
    for key, pattern in PATTERNS.items():
        m = pattern.search(text)
        if not m:
            continue
        if key in {"retrieval", "citation", "grounding", "refusals", "escalation"}:
            out[key] = _fraction(m)
        elif key == "answer_accuracy":
            out[key] = {
                "pct": int(m.group(1)),
                "min": int(m.group(2) or m.group(1)),
                "max": int(m.group(3) or m.group(1)),
            }
        elif key in {"off_topic_blocked", "wrongly_blocked"}:
            out[key] = {"ok": int(m.group(1)), "n": int(m.group(2))}
        elif key in {"ttft", "latency"}:
            out[key] = {"p50": float(m.group(1)), "p95": float(m.group(2))}
        elif key == "tokens":
            out[key] = {"in": int(m.group(1)), "out": int(m.group(2))}
        elif key == "cost_per_1000":
            out[key] = float(m.group(1))
        elif key == "setup":
            out["mode"] = "hybrid" if m.group(1) == "hybrid" else "keyword"
            out["top_k"] = int(m.group(2))
            if m.group(3):
                out["model"] = m.group(3)
        elif key in {"runs", "max_tokens"}:
            out[key] = int(m.group(1))
        else:
            out[key] = m.group(1)
    return out


def list_reports(reports_dir: Path = REPORTS_DIR) -> list[dict]:
    reports = []
    for path in Path(reports_dir).glob("*.md"):
        m = NAME.match(path.name)
        if m:
            info = {
                "path": path,
                "stamp": m["stamp"],
                "answers": bool(m["model"]),
                **parse_report(path.read_text("utf-8")),
            }
            info.setdefault("model", m["model"])
            reports.append(info)
    return sorted(reports, key=lambda r: r["stamp"])


def latest(reports_dir: Path = REPORTS_DIR, mode: str | None = None, model: str | None = None, answers=True):
    """Newest report matching the filters, or None."""
    for r in reversed(list_reports(reports_dir)):
        if answers is not None and r["answers"] != answers:
            continue
        if mode and r.get("mode") != mode:
            continue
        if model and r.get("model") != model:
            continue
        return r
    return None


def business_case(path: Path = ROOT / "docs" / "BUSINESS_CASE.md") -> dict:
    """Net value per year from the sensitivity table: {scenario: (2 properties, 100 properties)}."""
    out = {}
    row = re.compile(
        r"^\|\s*\**(Pessimistic|Base|Optimistic)\**\s*\|.*?\|\s*\**(\$[\d,]+)\**\s*\|\s*\**(\$[\d,]+)\**\s*\|$"
    )
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = row.match(line.strip())
        if m:
            out[m.group(1).lower()] = (m.group(2), m.group(3))
    return out


def paired(models: list[str], mode: str = "hybrid", reports_dir: Path = REPORTS_DIR) -> dict:
    """Latest answer report per model, from the largest question set that every model was run on,
    so a comparison is never between different evals. Returns {} if no common set exists."""
    by_size: dict = {}
    for r in list_reports(reports_dir):
        if r["answers"] and r.get("mode") == mode and r.get("model") in models and "retrieval" in r:
            by_size.setdefault(r["retrieval"]["n"], {})[r["model"]] = r  # later reports overwrite earlier
    for size in sorted(by_size, reverse=True):
        if all(m in by_size[size] for m in models):
            return {m: by_size[size][m] for m in models}
    return {}
