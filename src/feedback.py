"""Staff feedback on answers, appended to a JSON Lines file (git-ignored) for weekly review."""

from pathlib import Path

from src.chat import FEEDBACK_REASONS
from src.config import LOG_DIR
from src.usage import append_jsonl, now_iso, read_jsonl

FEEDBACK_FILE = LOG_DIR / "feedback.jsonl"


def log_feedback(
    question: str, prop: str, result: dict, helpful: bool, path: Path = FEEDBACK_FILE, reason: str | None = None
) -> dict:
    record = {
        "time": now_iso(),
        "property": prop,
        "question": question,
        "answer": result["answer"],
        "found": result["found"],
        "sources": [c["source"] for c in result["citations"]],
        "helpful": helpful,
        "reason": reason if (not helpful and reason in FEEDBACK_REASONS) else None,
    }
    append_jsonl(path, record)
    return record


def summary(path: Path = FEEDBACK_FILE) -> dict:
    rows = read_jsonl(path)
    helpful = sum(bool(r.get("helpful")) for r in rows)
    return {"total": len(rows), "helpful": helpful, "rate": helpful / len(rows) if rows else None}
