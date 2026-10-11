from src.activity import admin_stats, insights, percentile

USAGE = [
    {
        "time": "2026-10-08T10:00:00+00:00",
        "property": "beach-resort",
        "question": "Dogs?",
        "topic": "Pets",
        "refused": False,
        "pre_api": False,
        "tokens_in": 900,
        "tokens_out": 150,
        "cost_usd": 0.0002,
        "ttft_s": 0.9,
        "total_s": 1.4,
        "grounding_flag": False,
    },
    {
        "time": "2026-10-09T10:00:00+00:00",
        "property": "beach-resort",
        "question": "Babysitting? mail me at a@b.co",
        "topic": None,
        "refused": True,
        "pre_api": False,
        "tokens_in": 800,
        "tokens_out": 40,
        "cost_usd": 0.0001,
        "ttft_s": 0.8,
        "total_s": 1.0,
        "grounding_flag": False,
    },
    {
        "time": "2026-10-09T11:00:00+00:00",
        "property": "beach-resort",
        "question": "babysitting? mail me at a@b.co",
        "topic": None,
        "refused": True,
        "pre_api": True,
        "tokens_in": 0,
        "tokens_out": 0,
        "cost_usd": 0.0,
        "ttft_s": None,
        "total_s": None,
        "grounding_flag": False,
    },
    {
        "time": "2026-10-09T12:00:00+00:00",
        "property": "mountain-lodge",
        "question": "Pet fee?",
        "topic": "Pets",
        "refused": False,
        "pre_api": False,
        "tokens_in": 900,
        "tokens_out": 160,
        "cost_usd": 0.0002,
        "ttft_s": 1.1,
        "total_s": 2.0,
        "grounding_flag": True,
    },
    {"time": "2026-10-09T13:00:00+00:00", "property": "mountain-lodge", "question": "x", "error": "rate_limit"},
]
FEEDBACK = [
    {"helpful": True},
    {"helpful": False, "reason": "Wrong fact"},
    {"helpful": False, "reason": "Wrong fact"},
    {"helpful": False, "reason": None},
]


def test_insights_counts_topics_feedback_and_policy_gaps():
    out = insights(USAGE, FEEDBACK)
    assert out["questions"] == 4 and out["refused"] == 2
    assert out["topics"] == [("Pets", 2)]
    assert out["helpful_rate"] == 0.25 and out["reasons"] == [("Wrong fact", 2)]
    # Policy gaps: typed questions Claude said the documents don't cover, with personal data masked. The
    # off-topic row stopped by the scope check (pre_api) is not a policy gap.
    assert [g["question"] for g in out["gaps"]] == ["Babysitting? mail me at [email]"]


def test_insights_empty_state():
    out = insights([], [])
    assert out["questions"] == 0 and out["helpful_rate"] is None and out["gaps"] == [] and out["topics"] == []


def test_admin_stats():
    s = admin_stats(USAGE, FEEDBACK, today="2026-10-09")
    assert s["questions_today"] == 3 and s["questions_total"] == 4
    assert s["api_calls"] == 3 and s["blocked_before_api"] == 1
    assert (s["tokens_in"], s["tokens_out"]) == (2600, 350)
    assert round(s["cost_usd"], 4) == 0.0005
    assert s["grounding_flags"] == 1 and s["errors"] == [("rate_limit", 1)]
    assert s["p95_total_s"] == 2.0 and round(s["avg_total_s"], 2) == 1.47


def test_percentile_ignores_missing_values():
    assert percentile([None, 1.0, 3.0, 2.0], 0.5) == 2.0 and percentile([None], 0.95) is None


def test_insights_how_people_ask_and_disliked_suggestions():
    usage = [
        {"question": "hi", "kind": "greeting", "source": "typed"},
        {"question": "Dogs?", "kind": "answer", "source": "typed", "topic": "Pets", "topic_group": "Pets"},
        {"question": "Pool hours?", "kind": "answer", "source": "topic", "topic": "Pool and Beach"},
        {"question": "Spa?", "kind": "answer", "source": "follow_up", "topic_group": "Spa"},
        {"question": "Typed gap", "kind": "refusal", "refused": True, "pre_api": False, "source": "typed"},
        {"question": "Suggested gap", "kind": "refusal", "refused": True, "pre_api": False, "source": "did_you_mean"},
        {"question": "asdfgh", "kind": "scope", "refused": True, "pre_api": True, "source": "typed"},
    ]
    feedback = [
        {"question": "Spa?", "helpful": False, "reason": "Unclear", "source": "follow_up"},
        {"question": "Dogs?", "helpful": False, "reason": "Wrong fact", "source": "typed"},
    ]
    out = insights(usage, feedback)
    assert out["questions"] == 6  # the greeting isn't a question
    assert dict(out["how_asked"]) == {"Typed": 3, "Suggestion": 3}
    assert ("Follow-up", 1) in out["by_source"] and ("Topic example", 1) in out["by_source"]
    assert dict(out["topics"]) == {"Pets": 1, "Pool and Beach": 1, "Spa": 1}
    assert [g["question"] for g in out["gaps"]] == ["Typed gap"]
    assert [(s["question"], s["source"]) for s in out["disliked_suggestions"]] == [("Spa?", "Follow-up")]
