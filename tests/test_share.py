"""'Share this conversation' links (src/share.py): round trip, personal data replaced, damaged links rejected."""

import base64
import json
import zlib

from src import share
from src.chat import Turn


def turn(q, a="Dogs up to 40 lbs [1].", prop="beach-resort", kind="answer", rewritten=None):
    t = Turn(q, prop, result={"answer": a, "found": True, "citations": [{"source": "policies.md", "section": "Pets"}]})
    t.kind, t.rewritten = kind, rewritten
    return t


def test_round_trip_keeps_questions_answers_property_and_sources():
    turns = [
        turn("hi", "Hello!", kind="greeting"),
        turn("Dogs?"),
        turn(
            "What about at Mountain Lodge?",
            "Dogs of any size [1].",
            prop="mountain-lodge",
            rewritten="Can a guest bring a dog to Mountain Lodge?",
        ),
    ]
    token, found = share.make_token(turns)
    assert found == []
    shared = share.decode(token)
    assert [t["q"] for t in shared] == ["Dogs?", "What about at Mountain Lodge?"]  # greetings are left out
    assert shared[1]["u"] == "Can a guest bring a dog to Mountain Lodge?" and shared[1]["p"] == "mountain-lodge"
    assert shared[0]["s"] == ["policies.md › Pets"]


def test_personal_data_is_replaced_before_sharing():
    token, found = share.make_token([turn("Guest jane@mail.test, phone 555-201-3344, asked about dogs")])
    assert found == ["a phone number", "an email address"]
    text = share.decode(token)[0]["q"]
    assert "jane@mail.test" not in text and "[email]" in text and "[phone]" in text


def test_the_link_is_compressed_and_url_safe():
    token, _ = share.make_token([turn("Can a guest bring their dog? " * 5)])
    assert set(token) <= set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
    assert len(token) < len(("Can a guest bring their dog? " * 5) * 2)


def test_long_conversations_keep_the_newest_turns_that_fit(monkeypatch):
    monkeypatch.setattr(share, "MAX_TOKEN", 400)
    turns = [turn(f"Question {i} " + " ".join(f"w{i}x{j}" for j in range(40))) for i in range(8)]  # compresses poorly
    token, _ = share.make_token(turns)
    shared = share.decode(token)
    assert shared and shared[-1]["q"].startswith("Question 7") and len(shared) < 8


def test_nothing_to_share():
    assert share.make_token([turn("hi", kind="greeting")]) == (None, [])


def forged(payload) -> str:
    raw = json.dumps(payload).encode()
    return base64.urlsafe_b64encode(zlib.compress(raw)).decode().rstrip("=")


def test_damaged_or_foreign_links_are_rejected():
    assert share.decode("") is None
    assert share.decode("not-a-real-token") is None
    assert share.decode("x" * (share.MAX_TOKEN + 1)) is None
    assert share.decode(forged({"v": 99, "t": []})) is None
    assert share.decode(forged({"v": 1, "t": [{"q": 1, "a": "x"}]})) is None
    assert share.decode(forged({"v": 1, "t": []})) is None


def test_decoded_fields_are_capped():
    token = forged({"v": 1, "t": [{"q": "q" * 5000, "a": "a", "s": ["s"] * 20, "p": "beach-resort"}]})
    shared = share.decode(token)[0]
    assert len(shared["q"]) == share.MAX_TEXT and len(shared["s"]) == 6 and shared["k"] == "answer"


def test_share_url_keeps_only_the_share_parameter():
    assert share.share_url("https://app.test/?email=E01#top", "abc") == "https://app.test/?share=abc"
    assert share.share_url("", "abc") == "?share=abc"
