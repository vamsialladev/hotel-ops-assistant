"""Staff feedback on answers, appended to a JSON Lines file for weekly review."""

import json
from datetime import UTC, datetime
from pathlib import Path

from src.config import ROOT

FEEDBACK_FILE = ROOT / "data" / "feedback.jsonl"


def log_feedback(question: str, prop: str, result: dict, helpful: bool, path: Path = FEEDBACK_FILE) -> dict:
    record = {
        "time": datetime.now(UTC).isoformat(timespec="seconds"),
        "property": prop,
        "question": question,
        "answer": result["answer"],
        "found": result["found"],
        "sources": [c["source"] for c in result["citations"]],
        "helpful": helpful,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def summary(path: Path = FEEDBACK_FILE) -> dict:
    if not path.exists():
        return {"total": 0, "helpful": 0, "rate": None}
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    helpful = sum(r["helpful"] for r in rows)
    return {"total": len(rows), "helpful": helpful, "rate": helpful / len(rows) if rows else None}
