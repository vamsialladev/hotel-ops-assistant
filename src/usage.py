"""Private usage log: one JSON line per question in data/usage.jsonl (git-ignored), plus a short
line on stdout through Python logging, which the app owner can read in Streamlit Cloud's logs.

Never logged: the API key or any other secret. Question text is stored in the JSON file only
(for the owner's Insights and Admin pages), not in stdout logs.
"""

import json
import logging
import threading
from datetime import UTC, datetime
from pathlib import Path

from src.config import LOG_DIR, LOG_MAX_ENTRIES

USAGE_FILE = LOG_DIR / "usage.jsonl"
logger = logging.getLogger("hotel_ops.usage")
_LOCK = threading.Lock()


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def estimate_cost(tokens_in: int, tokens_out: int, price_in: float | None, price_out: float | None) -> float | None:
    """USD estimate from prices per million tokens. None when prices aren't configured."""
    if price_in is None or price_out is None:
        return None
    return (tokens_in * price_in + tokens_out * price_out) / 1_000_000


def append_jsonl(path: Path, record: dict, max_entries: int = LOG_MAX_ENTRIES) -> None:
    """Append one record, then keep only the most recent `max_entries` lines (retention rule)."""
    path = Path(path)
    with _LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        lines = path.read_text(encoding="utf-8").splitlines()
        if len(lines) > max_entries:
            path.write_text("\n".join(lines[-max_entries:]) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue  # a damaged line never breaks the dashboards
    return rows


STDOUT_FIELDS = (
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


def log_usage(record: dict, path: Path = USAGE_FILE) -> dict:
    record = {"time": now_iso(), **record}
    append_jsonl(path, record)
    logger.info("question %s", json.dumps({k: record.get(k) for k in STDOUT_FIELDS}))
    return record
