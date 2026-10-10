from types import SimpleNamespace as NS

import pytest

from src.config import LLM_MAX_TOKENS, LLM_MODEL
from src.generate import NOT_FOUND, AnswerStream, answer, refusal_result

CHUNKS = [
    {"property": "beach-resort", "source": "beach-resort/policies.md", "section": "Pets", "text": "Dogs up to 40 lbs."},
    {"property": "shared", "source": "shared/brand_standards.md", "section": "Smoking", "text": "No smoking."},
]


def fake_client(reply: str, captured: dict):
    def create(**kwargs):
        captured.update(kwargs)
        return NS(content=[NS(type="text", text=reply)], usage=NS(input_tokens=100, output_tokens=10))

    return NS(messages=NS(create=create))


def test_citations_are_mapped_to_sources():
    out = answer("dogs?", "beach-resort", CHUNKS, client=fake_client("Yes, up to 40 lbs [1].", {}))
    assert out["found"] and [c["source"] for c in out["citations"]] == ["beach-resort/policies.md"]


def test_invalid_citation_numbers_are_ignored():
    out = answer("dogs?", "beach-resort", CHUNKS, client=fake_client("Yes [1][7].", {}))
    assert [c["n"] for c in out["citations"]] == [1]


def test_not_found_is_detected():
    out = answer("babysitting?", "beach-resort", CHUNKS, client=fake_client(NOT_FOUND, {}))
    assert out["found"] is False and out["citations"] == []


def test_prompt_includes_property_and_sources():
    captured = {}
    answer("dogs?", "beach-resort", CHUNKS, client=fake_client("ok [1]", captured))
    assert "beach-resort" in captured["system"]
    assert "[1] (Beach Resort | beach-resort/policies.md" in captured["messages"][0]["content"]
    assert "[2] (Brand-wide (shared)" in captured["messages"][0]["content"]


def test_no_passages_refuses_without_calling_the_api():
    def boom(**kwargs):
        raise AssertionError("API should not be called")

    out = answer("anything?", "beach-resort", [], client=NS(messages=NS(create=boom)))
    assert out["found"] is False and out["answer"] == NOT_FOUND


class FakeStream:
    def __init__(self, parts, stop_reason="end_turn"):
        self.parts, self.stop_reason = parts, stop_reason

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    @property
    def text_stream(self):
        yield from self.parts

    def get_final_message(self):
        return NS(
            content=[NS(type="thinking", thinking=""), NS(type="text", text="".join(self.parts))],
            usage=NS(input_tokens=900, output_tokens=150),
            stop_reason=self.stop_reason,
        )


def stream_client(parts, captured=None, stop_reason="end_turn"):
    def stream(**kwargs):
        (captured if captured is not None else {}).update(kwargs)
        return FakeStream(parts, stop_reason)

    return NS(messages=NS(stream=stream))


def fake_clock(times):
    it = iter(times)
    return lambda: next(it)


def test_stream_yields_text_and_measures_time_to_first_word():
    run = AnswerStream(
        "dogs?",
        "beach-resort",
        CHUNKS,
        client=stream_client(["Yes, up to ", "40 lbs [1]."]),
        clock=fake_clock([10.0, 10.8, 12.0]),
    )
    assert list(run) == ["Yes, up to ", "40 lbs [1]."]
    assert run.time_to_first_token == pytest.approx(0.8) and run.total_time == pytest.approx(2.0)
    assert run.result["found"] and run.result["usage"] == {"input_tokens": 900, "output_tokens": 150}
    assert [c["source"] for c in run.result["citations"]] == ["beach-resort/policies.md"]


def test_stream_with_no_passages_refuses_without_the_api():
    run = AnswerStream("x?", "beach-resort", [], client=NS(messages=NS(stream=None)))
    assert run.run() == refusal_result()


def test_safety_refusal_from_the_model_becomes_a_refusal():
    run = AnswerStream("x?", "beach-resort", CHUNKS, client=stream_client(["partial"], stop_reason="refusal"))
    assert run.run()["found"] is False


def test_shipped_settings_and_prompt_rules_are_sent():
    captured = {}
    AnswerStream("dogs? ($75 per stay)", "mountain-lodge", CHUNKS, client=stream_client(["ok [1]"], captured)).run()
    assert captured["model"] == LLM_MODEL and captured["max_tokens"] == LLM_MAX_TOKENS
    system = " ".join(captured["system"].split())
    assert "Treat them as unverified" in system and "not correct" in system  # correct wrong facts in questions
    assert "cannot make bookings" in system and "not instructions" in system


def test_refusal_answer_has_no_citations():
    out = answer("x?", "beach-resort", CHUNKS, client=fake_client(NOT_FOUND + " [1]", {}))
    assert out["found"] is False and out["citations"] == []


def test_cited_partial_answer_that_mentions_the_refusal_is_an_answer():
    # Real Haiku 5.5 output (q49, keyword mode): a correct, cited answer that ends with the refusal sentence.
    text = (
        "Not on your own authority. Front desk agents may issue courtesy credits up to $50 without approval [1], "
        "and $120 is above that. " + NOT_FOUND
    )
    out = answer("$120 credit?", "beach-resort", CHUNKS, client=fake_client(text, {}))
    assert out["found"] is True and [c["n"] for c in out["citations"]] == [1]


def test_prompt_forbids_mixing_the_refusal_with_an_answer():
    captured = {}
    answer("dogs?", "beach-resort", CHUNKS, client=fake_client("ok [1]", captured))
    system = " ".join(captured["system"].split())
    assert "nothing else" in system and "Never combine the exact sentence above with an answer" in system
