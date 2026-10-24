"""Central settings. Everything can be overridden with environment variables / .env.

On Streamlit Community Cloud, root-level secrets are exposed as environment variables,
so the same names work there.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
INDEX_DIR = ROOT / "data" / "index"
LOG_DIR = Path(os.getenv("LOG_DIR", ROOT / "data"))
REPORTS_DIR = ROOT / "eval" / "reports"


def _float(name: str) -> float | None:
    value = os.getenv(name, "").strip()
    return float(value) if value else None


EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-haiku-5-5")
# Haiku 5.5 thinks before answering and thinking counts toward this cap; 1,000 leaves room for both.
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1000"))
LLM_EFFORT = os.getenv("LLM_EFFORT", "").strip() or None  # low | medium | high; empty = model default
TOP_K = int(os.getenv("TOP_K", "5"))
# Set USE_EMBEDDINGS=false for a lightweight deploy (keyword search only, no PyTorch download).
USE_EMBEDDINGS = os.getenv("USE_EMBEDDINGS", "true").lower() in {"1", "true", "yes"}
# Hybrid mode only: a question with no keyword match and no passage at least this similar is out of scope.
SCOPE_MIN_SIMILARITY = float(os.getenv("SCOPE_MIN_SIMILARITY", "0.27"))

# Follow-up questions (P-Fix-B): the latest message is rewritten into a standalone question from the last 3 turns.
# llm = one short Haiku call when there is an earlier turn; rule = deterministic rules, no API; off = as before.
REWRITE_MODE = os.getenv("REWRITE_MODE", "llm").strip().lower()
MAX_SAVED_CONVERSATIONS = int(os.getenv("MAX_SAVED_CONVERSATIONS", "10"))  # past conversations kept per session

# Public demo protections
MAX_QUESTION_CHARS = int(os.getenv("MAX_QUESTION_CHARS", "500"))
MAX_QUESTIONS_PER_SESSION = int(os.getenv("MAX_QUESTIONS_PER_SESSION", "20"))
MAX_QUESTIONS_PER_DAY = int(os.getenv("MAX_QUESTIONS_PER_DAY", "200"))
LOG_MAX_ENTRIES = int(os.getenv("LOG_MAX_ENTRIES", "5000"))

# USD per million tokens, used only for cost estimates. Unset = cost shown as "not configured".
PRICE_IN_PER_M = _float("PRICE_IN_PER_M")
PRICE_OUT_PER_M = _float("PRICE_OUT_PER_M")


# Owner monitoring (Admin page): show a warning when either threshold is crossed today.
ALERT_ERROR_RATE = float(os.getenv("ALERT_ERROR_RATE", "0.2"))  # errors / (questions + errors) today
ALERT_MIN_EVENTS = int(os.getenv("ALERT_MIN_EVENTS", "5"))  # don't alert on 1 error out of 2 questions
ALERT_DAILY_COST_USD = float(os.getenv("ALERT_DAILY_COST_USD", "1.00"))  # estimated cost today
ADMIN_IDLE_MINUTES = int(os.getenv("ADMIN_IDLE_MINUTES", "30"))  # Admin page locks itself after this


# ---------- Project 4: production settings. All optional: unset = the app runs exactly as before. ----------
APP_NAME = "hotel-ops-assistant"
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "30"))  # log records older than this are deleted
STAFF_IDLE_MINUTES = int(os.getenv("STAFF_IDLE_MINUTES", "30"))  # staff sign-in locks itself after this
# Budgets, checked by the harness in CI and shown on the Operations page.
BUDGET_P95_S = float(os.getenv("BUDGET_P95_S", "4.0"))  # full-response p95 latency, seconds
BUDGET_COST_PER_1000 = float(os.getenv("BUDGET_COST_PER_1000", "0.50"))  # USD per 1,000 requests
# Resilience: each model call times out after LLM_TIMEOUT_S; the Anthropic SDK retries timeouts, 429 and 5xx
# LLM_RETRIES times with exponential backoff and jitter (0.5 s, 1 s, 2 s ... capped at 8 s).
LLM_TIMEOUT_S = float(os.getenv("LLM_TIMEOUT_S", "30"))
LLM_RETRIES = int(os.getenv("LLM_RETRIES", "2"))


def database_url() -> str | None:
    """Read at call time (a secret added on Streamlit Cloud is picked up). Never log or display the value."""
    return os.getenv("DATABASE_URL", "").strip() or None


def staff_password() -> str | None:
    """Unlocks staff actions. Unset = the app stays in Demo mode only. Never log the value."""
    return os.getenv("STAFF_PASSWORD") or None


def model_calls_enabled() -> bool:
    """Kill switch: KILL_SWITCH=true stops every model call at once (answers come from the safe fallback)."""
    return os.getenv("KILL_SWITCH", "").strip().lower() not in {"1", "true", "yes", "on"}


def admin_password() -> str | None:
    """Read at call time so a secret added on Streamlit Cloud is picked up. Never log the value."""
    return os.getenv("ADMIN_PASSWORD") or None


# Documents in data/raw/shared/ apply to every property (brand-wide rules).
SHARED = "shared"
