from src.grounding import numbers_in, ungrounded_numbers

POLICY = {"text": "Pet fee is $50 per night per room, capped at $200 per stay."}


def test_numbers_are_normalized():
    assert numbers_in("$1,200 and 2:00 PM [3]") == {"1200", "2"}


def test_numbers_from_cited_sources_and_the_question_are_allowed():
    assert ungrounded_numbers("No, $300 is over the $200 cap [1].", [POLICY], "Can I refund $300?") == []


def test_invented_numbers_are_reported():
    assert ungrounded_numbers("It's $50, or $75 per stay [1].", [POLICY]) == ["75"]
