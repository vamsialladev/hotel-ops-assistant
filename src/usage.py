"""Private usage log: one JSON line per question in data/usage.jsonl (git-ignored), plus a short
line on stdout through Python logging, which the app owner can read in Streamlit Cloud's logs.

Never logged: the API key or any other secret. Every record is passed through `redact` before it's written,
so a secret value (or anything shaped like an Anthropic key) is masked even if a visitor pastes one into a
question. Question and answer text are stored in the JSON file only (for the owner's Insights and Admin pages),
not in stdout logs.
"""

import json
import logging
import re
import threading
from datetime import UTC, datetime
from pathlib import Path

from src import pii, store
from src.config import LOG_DIR, LOG_MAX_ENTRIES
from src.fileio import with_retries
from src.secrets_check import secret_values

USAGE_FILE = LOG_DIR / "usage.jsonl"
# Log file name -> database stream (Project 4). Files not listed here are never stored in the database.
STREAMS = {
    "usage.jsonl": "requests",
    "feedback.jsonl": "feedback",
    "errors.jsonl": "errors",
    "reports.jsonl": "reports",
}
logger = logging.getLogger("hotel_ops.usage")
_LOCK = threading.Lock()


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def estimate_cost(tokens_in: int, tokens_out: int, price_in: float | None, price_out: float | None) -> float | None:
    """USD estimate from prices per million tokens. None when prices aren't configured."""
    if price_in is None or price_out is None:
        return None
    return (tokens_in * price_in + tokens_out * price_out) / 1_000_000


REDACTED = "[redacted]"
KEY_PATTERN = re.compile(r"sk-ant-[A-Za-z0-9_\-]+")


def redact(value, secrets: list[str] | None = None):
    """Copy of a record with every secret value, and anything shaped like an Anthropic key, masked."""
    secrets = secret_values() if secrets is None else secrets
    if isinstance(value, str):
        for s in secrets:
            value = value.replace(s, REDACTED)
        return KEY_PATTERN.sub(REDACTED, value)
    if isinstance(value, dict):
        return {k: redact(v, secrets) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [redact(v, secrets) for v in value]
    return value


def append_jsonl(path: Path, record: dict, max_entries: int = LOG_MAX_ENTRIES) -> bool:
    """Append one record, then keep only the most recent `max_entries` lines (retention rule).

    Never raises: a log that can't be written (even after retries) is reported on stdout and skipped,
    because logging must not break the page that's being logged. Returns whether the write succeeded."""
    path = Path(path)
    record = pii.redact_record(redact(record))  # secrets, then personal data, before any storage
    stream = STREAMS.get(path.name)
    if stream and store.enabled() and store.save(stream, record):
        return True  # the database is the log; the file is only the fallback when it can't be written

    def write():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        lines = path.read_text(encoding="utf-8").splitlines()
        if len(lines) > max_entries:
            path.write_text("\n".join(lines[-max_entries:]) + "\n", encoding="utf-8")

    with _LOCK:
        try:
            with_retries(write)
            return True
        except OSError as exc:
            logger.warning("could not write %s: %s", path.name, type(exc).__name__)
            return False


def read_jsonl(path: Path) -> list[dict]:
    """A log's records, oldest first: from the database when one is configured (plus any records that fell back
    to the file), otherwise from the file as before."""
    path = Path(path)
    stream = STREAMS.get(path.name)
    if stream and store.enabled():
        rows = store.load(stream, LOG_MAX_ENTRIES)
        if rows is not None:
            extra = _read_file(path)
            return sorted(rows + extra, key=lambda r: str(r.get("time", ""))) if extra else rows
    return _read_file(path)


def _read_file(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        text = with_retries(lambda: path.read_text(encoding="utf-8"))
    except OSError:
        return []  # a locked file shows as empty for one refresh instead of breaking the page
    rows = []
    for line in text.splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue  # a damaged line never breaks the dashboards
    return rows


STDOUT_FIELDS = (
    "request_id",
    "outcome",
    "property",
    "model",
    "mode",
    "tokens_in",
    "tokens_out",
    "cost_usd",
    "ttft_s",
    "total_s",
    "refused",
    "pre_api",
    "grounding_flag",
    "error",
)


def log_usage(record: dict, path: Path | None = None) -> dict:
    """`path` defaults to USAGE_FILE read at call time, so tests (and LOG_DIR) can redirect it."""
    record = redact({"time": now_iso(), **record})
    append_jsonl(path or USAGE_FILE, record)
    logger.info("question %s", json.dumps({k: record.get(k) for k in STDOUT_FIELDS}))
    return record
