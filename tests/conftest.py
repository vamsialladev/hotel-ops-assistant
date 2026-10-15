import pytest

from src.ingest import build_index


@pytest.fixture(scope="session", autouse=True)
def index():
    """Build a keyword-only index once so tests run fast and offline."""
    build_index(use_embeddings=False)


@pytest.fixture(autouse=True)
def no_live_settings(monkeypatch):
    """A developer's .env may hold the live DATABASE_URL (Neon) and passwords: tests never use them. Tests that need a
    database set their own (tests/test_store.py)."""
    from src import store

    for name in ("DATABASE_URL", "STAFF_PASSWORD", "KILL_SWITCH"):
        monkeypatch.delenv(name, raising=False)
    store.reset_connection()
    yield
    store.reset_connection()
