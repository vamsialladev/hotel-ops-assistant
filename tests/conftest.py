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


@pytest.fixture(autouse=True)
def no_rewrite_api(monkeypatch):
    """The follow-up rewrite (src/rewrite.py) would call the API on any second question. Tests never do: the call
    fails here, so the page falls back to the question as typed. Tests of the rewrite replace call_model."""
    from src import rewrite

    def offline(*args, **kwargs):
        raise RuntimeError("no model calls in tests")

    monkeypatch.setattr(rewrite, "call_model", offline)


@pytest.fixture(autouse=True)
def fresh_gate_counters():
    """The Admin/staff lockout also counts per process (hotel-ai-platform admin_gate): reset it between tests."""
    from hotelplatform import admin_gate

    admin_gate.reset_process_counters()
    yield
    admin_gate.reset_process_counters()


@pytest.fixture(autouse=True)
def ops_log_in_tmp(tmp_path, monkeypatch):
    """The shared ops store writes JSONL under logs/ without DATABASE_URL; tests write to a temp folder instead."""
    from hotelplatform import oplog

    from src import ops

    store = oplog.OpsStore("hotel-ops-assistant", url="", log_dir=tmp_path / "ops")
    monkeypatch.setattr(ops, "store", lambda: store)
    yield store
