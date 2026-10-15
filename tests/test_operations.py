"""Project 4: Operations numbers and budgets, Demo mode / Staff role, kill switch, timeouts, and the Operations page."""

import time
from datetime import date

import anthropic
import pytest
from streamlit.testing.v1 import AppTest

import codeguard
import src.errors as errors
import src.feedback as feedback
import src.usage as usage
from src import generate, roles
from src.admin import GateState
from src.config import ROOT
from src.errors import PAUSED, UNAVAILABLE, classify, friendly
from src.operations import budget_label, summary
from src.retrieve import Retriever
from views import components

TODAY = date(2026, 10, 15)


def rec(outcome, total=1.0, cost=0.0002, day="2026-10-15", **kw):
    return {"time": f"{day}T10:00:00+00:00", "outcome": outcome, "total_s": total, "cost_usd": cost, **kw}


ROWS = [
    rec("answered", 1.0),
    rec("answered", 2.0, escalations=["safety"]),
    rec("refused", 3.0),
    rec("off_topic", None, None, pre_api=True),
    rec("greeting", None, None, pre_api=True),
    rec("error", None, None, error="server_error"),
    rec("answered", 9.0, day="2026-09-01"),  # outside a 7-day window
]


def test_summary_counts_latency_cost_and_budgets():
    s = summary(ROWS, [{"time": "2026-10-15T10:00:00+00:00"}], days=7, p95_budget=4.0, cost_budget=0.5, today=TODAY)
    assert s["requests"] == 5 and s["errors"] == 1 and s["error_rate"] == 0.2  # greeting not counted
    assert s["p50_s"] == 2.0 and s["p95_s"] == 3.0
    assert s["cost_per_1000"] == 0.2 and s["refusals"] == 2 and s["escalations"] == 1 and s["app_errors"] == 1
    assert s["budgets"]["p95_s"]["ok"] is True and s["budgets"]["cost_per_1000"]["ok"] is True
    assert s["per_day"] == [{"day": "2026-10-15", "requests": 5, "errors": 1, "cost_usd": 0.0006, "p95_s": 3.0}]


def test_budgets_can_fail():
    s = summary(ROWS, [], days=7, p95_budget=2.5, cost_budget=0.1, today=TODAY)
    assert s["budgets"]["p95_s"]["ok"] is False and s["budgets"]["cost_per_1000"]["ok"] is False
    assert budget_label(s["budgets"]["p95_s"], "{:.2f} s") == "Over budget: 3.00 s (budget 2.50 s)"
    empty = summary([], [], days=1, p95_budget=4.0, cost_budget=0.5, today=TODAY)
    assert empty["budgets"]["p95_s"]["ok"] is None and empty["error_rate"] is None
    assert budget_label(empty["budgets"]["p95_s"], "{:.2f} s").startswith("No data yet")


def test_staff_role_uses_the_admin_gate_rules():
    gate = GateState()
    assert roles.role(gate, 0, 60) == roles.DEMO
    assert roles.staff_attempt(gate, "x", None, 0) == (False, "Staff sign-in is not configured.")
    assert roles.staff_attempt(gate, "wrong", "right", 0)[0] is False
    assert roles.staff_attempt(gate, "right", "right", 1) == (True, None)
    assert roles.role(gate, 30, 60) == roles.STAFF
    assert roles.role(gate, 200, 60) == roles.DEMO  # idle sign-out


def test_staff_lockout_after_five_wrong_passwords():
    gate = GateState()
    for i in range(5):
        roles.staff_attempt(gate, "nope", "right", i)
    ok, message = roles.staff_attempt(gate, "right", "right", 10)
    assert not ok and "Too many attempts" in message


def test_report_record_is_bounded_and_labelled():
    r = roles.report_record("r1", "q" * 900, "Not a reason", " note ", "2026-10-15T10:00:00+00:00")
    assert r["reason"] == "Other" and len(r["question"]) == 500 and r["note"] == "note" and r["role"] == "staff"


def test_kill_switch_stops_model_calls_with_a_clear_message(monkeypatch):
    monkeypatch.setenv("KILL_SWITCH", "true")
    with pytest.raises(generate.ModelCallsPaused) as caught:
        generate.make_client()
    assert classify(caught.value) == "paused" and friendly("paused") == PAUSED
    stream = generate.AnswerStream("Is there parking?", "beach-resort", [{"text": "x", "source": "s", "section": "x"}])
    with pytest.raises(generate.ModelCallsPaused):
        stream.run()
    monkeypatch.setenv("KILL_SWITCH", "off")
    assert isinstance(generate.make_client(), anthropic.Anthropic)


def test_client_has_a_timeout_and_retries(monkeypatch):
    monkeypatch.delenv("KILL_SWITCH", raising=False)
    client = generate.make_client()
    assert client.timeout == 30 and client.max_retries == 2


def test_timeouts_and_outages_get_the_generic_message():
    request = __import__("httpx").Request("POST", "https://api.anthropic.com/v1/messages")
    assert classify(anthropic.APITimeoutError(request=request)) == "timeout"
    assert friendly("timeout") == UNAVAILABLE and friendly("server_error") == UNAVAILABLE


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", "test-only-password")
    monkeypatch.setenv("STAFF_PASSWORD", "test-only-staff")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv(codeguard.STAMP_KEY, codeguard.code_stamp(ROOT))
    monkeypatch.setattr(usage, "USAGE_FILE", tmp_path / "usage.jsonl")
    monkeypatch.setattr(feedback, "FEEDBACK_FILE", tmp_path / "feedback.jsonl")
    monkeypatch.setattr(errors, "ERRORS_FILE", tmp_path / "errors.jsonl")
    monkeypatch.setattr(components, "LOG_DIR", tmp_path)
    keyword = Retriever(use_embeddings=False)
    monkeypatch.setattr(components, "retriever", lambda: keyword)
    return AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)


def test_operations_page_needs_the_admin_sign_in(app):
    app.run()
    app.switch_page("views/operations.py").run()
    assert not app.exception
    assert "Sign in on the Admin page first." in " ".join(str(h.proto) for h in app.get("html"))
    assert not app.dataframe  # no numbers before sign-in


def test_operations_page_shows_numbers_budgets_and_storage(app):
    usage.append_jsonl(usage.USAGE_FILE, rec("answered", 1.2, time=None) | {"time": usage.now_iso()})
    app.run()
    app.session_state["admin_gate"] = GateState(unlocked=True, last_active=time.time())
    app.switch_page("views/operations.py").run()
    assert not app.exception and not app.error
    text = " ".join(str(x.value) for x in [*app.markdown, *app.caption])
    assert "Within budget: 1.20 s (budget 4.00 s)" in text
    assert "Not configured: temporary files" in str([d.value for d in app.dataframe])


def test_demo_mode_label_and_staff_sign_in(app):
    app.run()
    assert "Demo mode" in " ".join(c.value for c in app.sidebar.caption)
    assert app.sidebar.expander  # Staff sign-in offered because STAFF_PASSWORD is set
    form_input = app.sidebar.text_input[0]
    form_input.input("test-only-staff")
    next(b for b in app.button if b.label == "Sign in").click().run()
    assert not app.exception
    assert "Signed in as staff" in " ".join(c.value for c in app.sidebar.caption)


def test_without_staff_password_there_is_no_sign_in(app, monkeypatch):
    monkeypatch.delenv("STAFF_PASSWORD")
    app.run()
    assert "Demo mode" in " ".join(c.value for c in app.sidebar.caption)
    assert not [t for t in app.sidebar.text_input if t.label == "Staff password"]
