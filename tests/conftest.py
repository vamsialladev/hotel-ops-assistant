import pytest

from src.ingest import build_index


@pytest.fixture(scope="session", autouse=True)
def index():
    """Build a keyword-only index once so tests run fast and offline."""
    build_index(use_embeddings=False)
