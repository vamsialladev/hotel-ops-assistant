from src.scope import SCOPE_MESSAGE
from src.service import blocked_result, finalize, prepare, usage_record

POLICY = {
    "property": "mountain-lodge",
    "source": "mountain-lodge/policies.md",
    "section": "Policies > Pets",
    "text": "Pet fee is $50 per night per room, capped at $200 per stay.",
}


class FakeRetriever:
    def __init__(self, signals, hits):
        self._signals, self._hits = signals, hits

    def signals(self, question, prop):
        return self._signals

    def search(self, question, prop, k=5):
        return self._hits


def test_off_topic_is_blocked_before_retrieval_and_the_api():
    out = prepare(FakeRetriever({"keyword_matches": 0, "best_similarity": None}, [POLICY]), "Poem?", "mountain-lodge")
    assert out["blocked"] and out["hits"] == []
    assert blocked_result()["answer"] == SCOPE_MESSAGE and blocked_result()["found"] is False


def test_in_scope_question_gets_passages():
    out = prepare(
        FakeRetriever({"keyword_matches": 2, "best_similarity": None}, [POLICY]), "Pet fee?", "mountain-lodge"
    )
    assert not out["blocked"] and out["hits"] == [POLICY]


def test_invented_number_is_flagged_at_runtime():
    result = {
        "answer": "It's $50 per night, or $300 a week [1].",
        "found": True,
        "citations": [{"n": 1, **POLICY}],
        "usage": {"input_tokens": 1, "output_tokens": 1},
    }
    out = finalize("What is the pet fee?", "mountain-lodge", result)
    assert out["ungrounded"] == ["300"] and out["topic"] == "Pets" and out["escalations"] == []


def test_refusal_gets_the_manager_note_and_no_grounding_flag():
    result = {"answer": "I couldn't find this.", "found": False, "citations": [], "usage": {}}
    out = finalize("Babysitting?", "mountain-lodge", result)
    assert out["ungrounded"] == [] and out["escalations"] == ["refused"] and out["topic"] is None


def test_usage_record_fields_and_cost():
    result = finalize(
        "Pet fee?",
        "mountain-lodge",
        {
            "answer": "$50 [1]",
            "found": True,
            "citations": [{"n": 1, **POLICY}],
            "usage": {"input_tokens": 1000, "output_tokens": 200},
        },
    )
    rec = usage_record(
        "Pet fee?",
        "mountain-lodge",
        "keyword",
        result,
        [{**POLICY, "score": 0.03}],
        0.8,
        1.5,
        price_in=0.10,
        price_out=0.50,
    )
    assert rec["cost_usd"] == (1000 * 0.10 + 200 * 0.50) / 1e6
    assert rec["refused"] is False and rec["grounding_flag"] is False and rec["pre_api"] is False
    assert rec["retrieved"] == [
        {"source": "mountain-lodge/policies.md", "section": "Policies > Pets", "score": 0.03, "cited": True}
    ]
    assert rec["citations"] == [{"n": 1, "source": "mountain-lodge/policies.md", "section": "Policies > Pets"}]
    assert (rec["outcome"], rec["answer"], rec["refusal_reason"]) == ("answered", "$50 [1]", None)
    assert "api_key" not in str(rec).lower()


def test_blocked_question_record_has_no_model_or_cost():
    rec = usage_record("Poem?", "beach-resort", "keyword", blocked_result(), pre_api=True, price_in=0.1, price_out=0.5)
    assert rec["model"] is None and rec["cost_usd"] == 0.0 and rec["refused"] and rec["pre_api"]
