"""The request log: one complete record per request type, older records, feedback links, secrets, filters and
row selection. Pure functions, no Streamlit."""

import json
from datetime import date

import pytest

from src import service
from src.feedback import log_feedback
from src.requestlog import (
    NOT_RECORDED,
    REFUSAL_REASONS,
    SCHEMA_VERSION,
    details,
    feedback_index,
    filter_requests,
    find,
    list_rows,
    log_since,
    outcome_of,
    request_id,
    request_json,
    selected_id,
    table_key,
    to_jsonl,
)
from src.usage import REDACTED, log_usage, read_jsonl, redact

HITS = [
    {"id": "beach-resort/policies.md#3", "source": "beach-resort/policies.md", "section": "Pets", "score": 0.031},
    {"id": "shared/brand.md#1", "source": "shared/brand.md", "section": "Loyalty", "score": 0.018},
]
ANSWER = {
    "answer": "Dogs up to 40 lbs are welcome [1].",
    "found": True,
    "citations": [{**HITS[0], "n": 1, "text": "Dogs up to 40 lbs..."}],
    "usage": {"input_tokens": 1000, "output_tokens": 40},
    "ungrounded": [],
    "escalations": [],
}
REFUSAL = {**ANSWER, "answer": "I couldn't find that.", "found": False, "citations": []}
GREETING = {"answer": "Hi! Ask me about a policy.", "found": False, "citations": []}


def record(**kwargs):
    base = {"question": "Can a guest bring their dog?", "prop": "beach-resort", "mode": "keyword", "turn_id": "r1"}
    return service.usage_record(**{**base, **kwargs}, price_in=0.10, price_out=0.50)


# ---------- one complete record per request type ----------
def test_answered_record_has_answer_citations_follow_ups_and_cited_passages():
    r = record(
        result=ANSWER, hits=HITS, ttft=0.51, total=1.2, kind="answer", session_id="s1",
        follow_ups=["Are dogs allowed at the pool?"], follow_up_label="follow_up",
    )  # fmt: skip
    assert r["schema_version"] == SCHEMA_VERSION and r["request_id"] == "r1" and r["outcome"] == "answered"
    assert r["answer"] == ANSWER["answer"] and r["refusal_reason"] is None
    assert r["citations"] == [{"n": 1, "source": "beach-resort/policies.md", "section": "Pets"}]
    assert [p["cited"] for p in r["retrieved"]] == [True, False]
    assert r["follow_ups"] == ["Are dogs allowed at the pool?"] and r["follow_up_label"] == "follow_up"
    assert (r["ttft_s"], r["total_s"], r["tokens_in"], r["tokens_out"]) == (0.51, 1.2, 1000, 40)
    assert r["cost_usd"] == pytest.approx(0.00012)
    assert r["model"] and r["mode"] == "keyword" and r["session_id"] == "s1"


@pytest.mark.parametrize(
    "kwargs,outcome,reason",
    [
        ({"result": REFUSAL, "hits": HITS, "kind": "refusal"}, "refused", "not_in_documents"),
        ({"result": GREETING, "kind": "greeting", "pre_api": True}, "greeting", None),
        ({"result": service.blocked_result(), "kind": "scope", "pre_api": True}, "off_topic", "off_topic"),
        ({"hits": HITS, "kind": "answer", "error": "rate_limit", "error_message": "RateLimitError: slow down"},
         "error", None),
        ({"kind": "answer", "pre_api": True, "error": "daily_cap", "error_message": "Daily limit."}, "cap",
         "daily_cap"),
        ({"kind": "answer", "pre_api": True, "error": "session_cap", "error_message": "Session limit."}, "cap",
         "session_cap"),
    ],
)  # fmt: skip
def test_every_request_type_gets_an_outcome_and_reason(kwargs, outcome, reason):
    r = record(**kwargs)
    assert (r["outcome"], r["refusal_reason"]) == (outcome, reason)
    assert r["schema_version"] == SCHEMA_VERSION and r["request_id"] == "r1"
    if outcome in ("error", "cap"):
        assert r["answer"] is None and r["error_message"]
    if kwargs.get("pre_api"):
        assert r["model"] is None and r["tokens_in"] == 0


# ---------- older records ----------
OLD = {  # 1.3.x: no request_id, kind, outcome, answer, citations or follow-ups
    "time": "2026-10-10T01:54:10+00:00",
    "property": "mountain-lodge",
    "question": "Can a guest bring their dog?",
    "model": "claude-haiku-5-5",
    "mode": "keyword",
    "tokens_in": 980,
    "tokens_out": 60,
    "cost_usd": 0.000128,
    "ttft_s": 0.9,
    "total_s": 1.4,
    "refused": False,
    "pre_api": False,
    "retrieved": [{"source": "mountain-lodge/policies.md", "section": "Pets", "score": 0.02}],
    "error": None,
}


def test_old_records_get_an_outcome_and_a_stable_id():
    assert outcome_of(OLD) == "answered"
    assert outcome_of({**OLD, "refused": True, "pre_api": True}) == "off_topic"
    assert outcome_of({**OLD, "refused": True}) == "refused"
    assert outcome_of({**OLD, "error": "daily_cap"}) == "cap"
    assert request_id(OLD) == request_id(dict(OLD)) and request_id(OLD).startswith("old-")
    assert request_id({**OLD, "turn_id": "abc"}) == "abc"


def test_old_records_show_not_recorded_never_blank():
    d = details(OLD, [])
    assert d["schema_version"] == 1 and d["answer"] is None and d["citations"] is None
    assert d["follow_ups"] is None and d["session_id"] == NOT_RECORDED
    assert d["passages"][0]["cited"] is None  # unknown: citations weren't recorded
    row = list_rows([OLD], [])[0]
    assert row["question"].startswith("Can a guest") and row["total"] == "1.40 s"


@pytest.mark.parametrize("broken", [{}, {"time": None}, {"question": None, "retrieved": None}, {"retrieved": [{}]}])
def test_records_missing_fields_never_crash(broken):
    row = list_rows([broken], [])[0]
    d = details(broken, [])
    assert row["question"] == NOT_RECORDED and row["time"] == NOT_RECORDED and row["cost"] == NOT_RECORDED
    assert d["question"] == NOT_RECORDED and d["property"] == NOT_RECORDED
    assert filter_requests([row], start=date(2026, 10, 10)) == []  # no date: not in a date range
    assert filter_requests([row]) == [row]


def test_greeting_and_cap_rows_show_a_dash_for_time_not_not_recorded():
    rows = list_rows([record(result=GREETING, kind="greeting", pre_api=True)], [])
    assert rows[0]["total"] == "–" and rows[0]["result"] == "🔵 Greeting"


# ---------- feedback linked by request_id ----------
def test_feedback_links_to_its_request_by_request_id(tmp_path):
    usage_rows = [record(result=ANSWER, hits=HITS, turn_id=t) for t in ("a1", "b2")]
    f = log_feedback("q", "beach-resort", ANSWER, helpful=False, reason="Unclear", turn_id="b2", path=tmp_path / "f")
    assert f["request_id"] == "b2"
    rows = list_rows(usage_rows, [f])
    assert [r["feedback"] for r in rows] == ["👎", ""]  # newest first
    d = details(usage_rows[1], [f])
    assert d["feedback"]["reason"] == "Unclear" and details(usage_rows[0], [f])["feedback"] is None
    assert json.loads(request_json(usage_rows[1], [f]))["feedback"]["helpful"] is False


def test_older_feedback_links_by_turn_id_and_the_latest_wins():
    index = feedback_index([{"turn_id": "x", "helpful": True}, {"turn_id": "x", "helpful": False}])
    assert index["x"]["helpful"] is False


# ---------- secrets ----------
def test_no_secret_reaches_any_record(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-FAKEKEY_123")
    monkeypatch.setenv("ADMIN_PASSWORD", "correct-horse-battery")
    monkeypatch.setenv("SOME_SERVICE_TOKEN", "tok_abcdefghijkl")
    leaky = record(
        question="my password is correct-horse-battery, key sk-ant-test-FAKEKEY_123",
        result={**ANSWER, "answer": "Echo: tok_abcdefghijkl"},
        hits=HITS,
        error="auth",
        error_message="AuthenticationError: bad key sk-ant-xyz987",
    )
    path = tmp_path / "usage.jsonl"
    log_usage(leaky, path=path)
    log_feedback("correct-horse-battery?", "beach-resort", ANSWER, True, path=tmp_path / "feedback.jsonl")
    text = path.read_text(encoding="utf-8") + (tmp_path / "feedback.jsonl").read_text(encoding="utf-8")
    for secret in ("FAKEKEY_123", "correct-horse-battery", "tok_abcdefghijkl", "xyz987"):
        assert secret not in text
    assert REDACTED in read_jsonl(path)[0]["question"]


def test_redact_leaves_short_or_unset_values_alone(monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", "")
    monkeypatch.setenv("PRICE_KEY", "0.10")  # too short to be a secret: never masks ordinary text
    assert redact({"a": ["costs 0.10"], "n": 3}) == {"a": ["costs 0.10"], "n": 3}


# ---------- filters, paging and selection ----------
def make_rows():
    usage_rows = [
        {**record(result=ANSWER, hits=HITS, turn_id="a"), "time": "2026-10-09T10:00:00+00:00"},
        {**record(result=REFUSAL, kind="refusal", turn_id="b", prop="mountain-lodge"), "time": "2026-10-10T10:00:00"},
        {**record(kind="answer", error="auth", turn_id="c", question="Pool hours?"), "time": "2026-10-11T09:00:00"},
        {**record(kind="answer", pre_api=True, error="daily_cap", turn_id="d"), "time": "2026-10-11T10:00:00"},
    ]
    feedback = [{"request_id": "a", "helpful": True}, {"request_id": "b", "helpful": False}]
    return usage_rows, list_rows(usage_rows, feedback)


def test_list_is_newest_first_with_badges_and_feedback():
    _, rows = make_rows()
    assert [r["id"] for r in rows] == ["d", "c", "b", "a"]
    assert [r["result"] for r in rows] == ["🟣 Cap", "🔴 Error", "🟠 Refused", "🟢 Answered"]
    assert [r["feedback"] for r in rows] == ["", "", "👎", "👍"]


def test_filters():
    _, rows = make_rows()
    ids = lambda **kw: [r["id"] for r in filter_requests(rows, **kw)]  # noqa: E731
    assert ids(start=date(2026, 10, 10), end=date(2026, 10, 10)) == ["b"]
    assert ids(start=date(2026, 10, 11)) == ["d", "c"]  # one date picked = that day
    assert ids(start=date(2026, 10, 10), end=date(2026, 10, 11)) == ["d", "c", "b"]
    assert ids(prop="mountain-lodge") == ["b"]
    assert ids(outcomes=["answered", "cap"]) == ["d", "a"]
    assert ids(feedback="up") == ["a"] and ids(feedback="down") == ["b"]
    assert ids(errors_only=True) == ["c"]  # caps are not errors
    assert ids(text="  POOL ") == ["c"] and ids(text="nothing like this") == []


def test_selected_row_opens_the_right_record():
    usage_rows, rows = make_rows()
    shown = filter_requests(rows, start=date(2026, 10, 11))
    rid = selected_id(shown, {"selection": {"rows": [1], "columns": []}})
    assert rid == "c" and find(usage_rows, rid)["question"] == "Pool hours?"
    for nothing in (None, {}, {"selection": {"rows": []}}, {"selection": {"rows": [7]}}):
        assert selected_id(shown, nothing) is None


def test_table_key_changes_with_filters_and_page_size():
    assert table_key(("a",), 50) == table_key(("a",), 50) != table_key(("b",), 50) != table_key(("a",), 100)


def test_downloads_and_log_since():
    usage_rows, _ = make_rows()
    lines = to_jsonl(usage_rows).splitlines()
    assert len(lines) == 4 and json.loads(lines[0])["request_id"] == "a"
    assert log_since(usage_rows) == "2026-10-09 10:00:00" and log_since([]) is None


def test_refusal_reasons_are_explained():
    assert set(REFUSAL_REASONS) == {"not_in_documents", "off_topic", "daily_cap", "session_cap", "guardrail"}
