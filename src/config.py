"""Central settings. Everything can be overridden with environment variables / .env."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
INDEX_DIR = ROOT / "data" / "index"

EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-haiku-4-5-20251001")
TOP_K = int(os.getenv("TOP_K", "5"))
# Set USE_EMBEDDINGS=false for a lightweight deploy (keyword search only, no PyTorch download).
USE_EMBEDDINGS = os.getenv("USE_EMBEDDINGS", "true").lower() in {"1", "true", "yes"}

# Documents in data/raw/shared/ apply to every property (brand-wide rules).
SHARED = "shared"
