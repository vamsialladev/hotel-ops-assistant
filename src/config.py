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

# Public demo protections
MAX_QUESTION_CHARS = int(os.getenv("MAX_QUESTION_CHARS", "500"))
MAX_QUESTIONS_PER_SESSION = int(os.getenv("MAX_QUESTIONS_PER_SESSION", "20"))
MAX_QUESTIONS_PER_DAY = int(os.getenv("MAX_QUESTIONS_PER_DAY", "200"))
LOG_MAX_ENTRIES = int(os.getenv("LOG_MAX_ENTRIES", "5000"))

# USD per million tokens, used only for cost estimates. Unset = cost shown as "not configured".
PRICE_IN_PER_M = _float("PRICE_IN_PER_M")
PRICE_OUT_PER_M = _float("PRICE_OUT_PER_M")


def admin_password() -> str | None:
    """Read at call time so a secret added on Streamlit Cloud is picked up. Never log the value."""
    return os.getenv("ADMIN_PASSWORD") or None


# Documents in data/raw/shared/ apply to every property (brand-wide rules).
SHARED = "shared"
