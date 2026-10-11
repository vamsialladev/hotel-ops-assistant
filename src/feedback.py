"""Staff feedback on answers, appended to a JSON Lines file (git-ignored) for weekly review."""

from pathlib import Path

from src.chat import FEEDBACK_REASONS
from src.config import LOG_DIR
from src.requestlog import SCHEMA_VERSION
from src.usage import append_jsonl, now_iso, read_jsonl

FEEDBACK_FILE = LOG_DIR / "feedback.jsonl"


def log_feedback(
    question: str,
    prop: str,
    result: dict,
    helpful: bool,
    path: Path | None = None,
    reason: str | None = None,
    turn_id: str | None = None,
    source: str = "typed",
) -> dict:
    record = {
        "schema_version": SCHEMA_VERSION,
        "time": now_iso(),
        "request_id": turn_id,  # links the rating to its request in the usage log
        "turn_id": turn_id,
        "property": prop,
        "source": source,
        "question": question,
        "answer": result["answer"],
        "found": result["found"],
        "sources": [c["source"] for c in result["citations"]],
        "helpful": helpful,
        "reason": reason if (not helpful and reason in FEEDBACK_REASONS) else None,
    }
    append_jsonl(path or FEEDBACK_FILE, record)  # FEEDBACK_FILE read at call time, so tests can redirect it
    return record


def summary(path: Path = FEEDBACK_FILE) -> dict:
    rows = read_jsonl(path)
    helpful = sum(bool(r.get("helpful")) for r in rows)
    return {"total": len(rows), "helpful": helpful, "rate": helpful / len(rows) if rows else None}
