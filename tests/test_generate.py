from types import SimpleNamespace as NS

from src.generate import NOT_FOUND, answer

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
    assert "[1] (beach-resort" in captured["messages"][0]["content"]


def test_no_passages_refuses_without_calling_the_api():
    def boom(**kwargs):
        raise AssertionError("API should not be called")

    out = answer("anything?", "beach-resort", [], client=NS(messages=NS(create=boom)))
    assert out["found"] is False and out["answer"] == NOT_FOUND
