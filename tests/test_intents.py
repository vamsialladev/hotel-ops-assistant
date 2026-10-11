import pytest

from src.intents import detect, reply


@pytest.mark.parametrize(
    "text,kind",
    [
        ("hi", "greeting"),
        ("Hello!", "greeting"),
        ("hey there", "greeting"),
        ("Good morning.", "greeting"),
        ("thanks", "thanks"),
        ("Thank you so much!", "thanks"),
        ("what can you do?", "meta"),
        ("HELP", "meta"),
        ("hi, what can you do?", "meta"),
        ("How does this work?", "meta"),
        ("hi, can a guest bring a dog?", None),  # a real question after the greeting
        ("Can a guest bring a dog?", None),
        ("history of the hotel", None),  # starts with "hi" but isn't a greeting
        ("", None),
        ("   ", None),
    ],
)
def test_detect(text, kind):
    assert detect(text) == kind


def test_replies_name_the_property_and_set_expectations():
    assert "Beach Resort" in reply("greeting", "Beach Resort")
    assert "can't make bookings" in reply("meta", "Mountain Lodge")
    assert reply("thanks", "Beach Resort").startswith("You're welcome")
