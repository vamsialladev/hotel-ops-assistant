"""One message end to end without the UI: greetings, scope, answers and refusals get the right suggestions."""

import pytest

import src.generate
from src.assist import respond, route, suggestions_after
from src.generate import NOT_FOUND
from src.retrieve import Retriever


@pytest.fixture(scope="module")
def retriever():
    return Retriever(use_embeddings=False)


def test_route(retriever):
    assert route(retriever, "hi", "beach-resort") == {"kind": "greeting", "intent": "greeting"}
    assert route(retriever, "asdfgh", "beach-resort")["kind"] == "scope"
    assert route(retriever, "Can a guest bring their dog?", "beach-resort")["kind"] == "ask"


def test_greeting_and_gibberish_get_three_questions_without_the_api(retriever):
    hi = respond(retriever, "hello", "mountain-lodge", use_api=False)
    junk = respond(retriever, "asdfgh", "beach-resort", use_api=False)
    assert hi["kind"] == "greeting" and len(hi["suggestions"]) == 3
    assert junk["kind"] == "scope" and len(junk["suggestions"]) == 3


def test_in_scope_questions_wait_for_the_model_without_the_api(retriever):
    out = respond(retriever, "Is there a gym?", "beach-resort", use_api=False)
    assert out["kind"] == "pending" and any(h["source"] == "beach-resort/guest_handbook.md" for h in out["hits"])


def fake_answer(text):
    def answer(question, prop, chunks):
        cited = [{**chunks[0], "n": 1}] if text != NOT_FOUND else []
        return {"answer": text, "found": text != NOT_FOUND, "citations": cited, "usage": {}}

    return answer


def test_an_answer_gets_follow_ups_and_a_refusal_gets_did_you_mean(retriever, monkeypatch):
    monkeypatch.setattr(src.generate, "answer", fake_answer("Dogs up to 40 lbs [1]."))
    ok = respond(retriever, "Can a guest bring their dog?", "beach-resort")
    assert ok["kind"] == "answer" and "Can a guest bring their dog?" not in ok["suggestions"]
    assert ok["suggestions"] and "dog" in " ".join(ok["suggestions"]).lower()

    monkeypatch.setattr(src.generate, "answer", fake_answer(NOT_FOUND))
    no = respond(retriever, "Can you book me a room for Friday?", "beach-resort")
    assert no["kind"] == "refusal" and len(no["suggestions"]) == 3


def test_suggestion_labels():
    assert suggestions_after("greeting", "hi", "beach-resort")[0] == "examples"
    assert suggestions_after("scope", "asdfgh", "beach-resort")[0] == "popular"
    assert suggestions_after("refusal", "book a room", "beach-resort")[0] == "did_you_mean"
    assert suggestions_after("answer", "x", "beach-resort", cited=[])[0] == "follow_up"
