"""Every page runs for real (Streamlit AppTest, no browser, no API key, no PyTorch).

- each page renders without an exception
- an unexpected exception on any page shows the friendly message, never Streamlit's crash screen or a
  traceback, and is recorded for the owner
- "New conversation" is disabled when empty, enabled with a message, and clearing shows a toast
- the note under the chat input links to the Document library; Admin shows missing secrets by name only
"""

import time

import pytest
from streamlit.testing.v1 import AppTest

import codeguard
import src.errors as errors
import src.feedback as feedback
import src.generate
import src.usage as usage
from src.admin import GateState
from src.chat import ChatState, Turn
from src.config import ROOT
from src.errors import PAGE_ERROR
from src.generate import NOT_FOUND
from src.retrieve import Retriever
from src.suggestions import load_catalog
from src.usage import read_jsonl
from views import components

PAGES = {
    "views/assistant.py": "Assistant",
    "views/insights.py": "Insights",
    "views/library.py": "Document library",
    "views/how_it_works.py": "How it works",
    "views/about.py": "Disclaimer and privacy",
    "views/admin.py": "Admin",
}


@pytest.fixture
def app(tmp_path, monkeypatch):
    """The real app.py with logs in a temp folder, keyword-only search and an admin password set."""
    monkeypatch.setenv("ADMIN_PASSWORD", "test-only-password")
    # The code hasn't changed during the test run: tell app.py's reload guard, so it keeps the (patched) modules.
    monkeypatch.setenv(codeguard.STAMP_KEY, codeguard.code_stamp(ROOT))
    monkeypatch.setattr(usage, "USAGE_FILE", tmp_path / "usage.jsonl")
    monkeypatch.setattr(feedback, "FEEDBACK_FILE", tmp_path / "feedback.jsonl")
    monkeypatch.setattr(errors, "ERRORS_FILE", tmp_path / "errors.jsonl")
    keyword = Retriever(use_embeddings=False)
    monkeypatch.setattr(components, "retriever", lambda: keyword)
    return AppTest.from_file(str(ROOT / "app.py"), default_timeout=60), tmp_path


def open_page(at, path):
    at.run()
    if path != "views/assistant.py":
        at.switch_page(path).run()
    return at


@pytest.mark.parametrize("path", PAGES)
def test_every_page_renders_without_errors(app, path):
    at, logs = app
    open_page(at, path)
    assert not at.exception and not [e for e in at.error if e.value == PAGE_ERROR]
    assert not (logs / "errors.jsonl").exists()


@pytest.mark.parametrize("path,title", PAGES.items())
def test_an_exception_on_any_page_shows_the_friendly_message(app, monkeypatch, path, title):
    at, logs = app

    def broken(*args, **kwargs):
        raise RuntimeError("simulated failure with key sk-ant-not-a-real-key")

    monkeypatch.setattr(components, "header", broken)  # every page calls ui.header near the top
    open_page(at, path)
    assert not at.exception  # no crash screen, no traceback
    assert [e.value for e in at.error] == [PAGE_ERROR]
    record = read_jsonl(logs / "errors.jsonl")[-1]
    assert record["page"] == title and record["error"] == "RuntimeError"
    assert "not-a-real-key" not in record["message"]


def test_new_conversation_button_state_and_toast(app):
    at, _ = app
    at.run()
    button = at.sidebar.button(key="new_conversation")
    assert button.disabled and button.help == "This conversation is already empty"

    chat = ChatState()
    chat.add(Turn("Dogs?", "beach-resort", result={"answer": "Yes [1].", "found": True, "citations": [], "usage": {}}))
    at.session_state["chat"] = chat
    at.run()
    button = at.sidebar.button(key="new_conversation")
    assert not button.disabled

    button.click().run()
    assert [t.value for t in at.toast] == ["Started a new conversation"]
    assert at.sidebar.button(key="new_conversation").disabled
    assert not at.session_state["chat"].has_messages("beach-resort")


def html_text(at) -> str:
    return " ".join(str(e.proto.body) for e in at.get("html"))


def test_note_under_the_chat_input_links_to_the_document_library(app):
    at, _ = app
    at.run()
    text = html_text(at)
    assert "Answers are written live by AI using only the documents in the" in text
    assert '<a href="library" target="_self">Document library</a>' in text


def test_admin_health_shows_missing_secrets_by_name_only(app, monkeypatch):
    at, _ = app
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("PRICE_IN_PER_M", "0.10")
    at.run()
    at.session_state["admin_gate"] = GateState(unlocked=True, last_active=time.time())
    at.switch_page("views/admin.py").run()
    assert not at.exception
    text = html_text(at)
    assert "ANTHROPIC_API_KEY: missing" in text and "ADMIN_PASSWORD: set" in text
    assert any("Required secret ANTHROPIC_API_KEY is missing" in w.value for w in at.warning)
    assert "test-only-password" not in text + " ".join(w.value for w in at.warning)


# ---------- welcome screen, guidance and suggestions (no API: Claude's stream is replaced) ----------
class FakeStream:
    """Stands in for AnswerStream: answers from the first retrieved passage, or refuses."""

    text = "Dogs up to 40 lbs are welcome [1]."

    def __init__(self, question, prop, chunks, *args, **kwargs):
        self.chunks, self.result, self.time_to_first_token, self.total_time = chunks, None, 0.1, 0.2

    def __iter__(self):
        yield self.text
        found = self.text != NOT_FOUND
        self.result = {
            "answer": self.text,
            "found": found,
            "citations": [{**self.chunks[0], "n": 1}] if found else [],
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }


@pytest.fixture
def chat_app(app, monkeypatch):
    from src.limits import DailyCounter

    at, logs = app
    monkeypatch.setattr(components, "daily_counter", lambda: DailyCounter(logs / "daily.json", 200))
    monkeypatch.setattr(src.generate, "AnswerStream", FakeStream)
    return at, logs


def welcome_text(at) -> str:
    return html_text(at) + " ".join(e.value for e in at.markdown)


def focus_scripts(at) -> list[str]:
    return [str(e.proto.srcdoc) for e in at.sidebar.get("iframe") if "stChatInputTextArea" in str(e.proto.srcdoc)]


@pytest.mark.parametrize("prop", ["beach-resort", "mountain-lodge"])
def test_welcome_screen_guides_a_first_time_visitor(app, prop):
    at, _ = app
    at.run()
    at.session_state["property"] = prop
    at.run()
    text = welcome_text(at)
    assert "Pick your property" in text and "Tap a topic or type your question" in text
    assert "What this demo knows at" in text and "can&rsquo;t make bookings" in text
    assert "Good questions look like" in text and "one policy question at a time" in text
    assert [at.button(key=f"good_{prop}_{i}").label for i in range(3)] == load_catalog().good[prop]
    assert at.get("button_group")  # topic chips
    assert at.chat_input(key="chat_input").placeholder.startswith("Try: ")
    assert "Don't enter guest names or personal details" in html_text(at)


def test_typing_bug_regression_new_conversation_shows_welcome_and_frees_the_input(chat_app):
    """Found on the live app: on a phone, the sidebar stayed open over the chat input after "New conversation",
    so taps never reached it. Now the page closes an overlaying sidebar and focuses the input."""
    at, _ = chat_app
    at.run()
    at.button(key="good_beach-resort_0").click().run()
    assert at.sidebar.button(key="new_conversation").disabled is False
    at.sidebar.button(key="new_conversation").click().run()
    assert "Good questions look like" in welcome_text(at) and not at.chat_message
    script = focus_scripts(at)[-1]
    assert 'stSidebarCollapseButton"] button' in script and "if (true && overlay" in script
    assert not at.chat_input(key="chat_input").proto.disabled
    at.chat_input(key="chat_input").set_value("Can a guest bring their dog?").run()  # typing works again
    assert at.chat_message[0].markdown[0].value == "Can a guest bring their dog?"


def test_example_click_is_asked_as_the_users_question_counted_and_logged_with_its_source(chat_app):
    at, logs = chat_app
    at.run()
    at.button(key="good_beach-resort_0").click().run()
    assert at.chat_message[0].markdown[0].value == "Can a guest bring their dog?"
    assert "19 of 20" in at.sidebar.caption[0].value
    record = read_jsonl(logs / "usage.jsonl")[-1]
    assert (record["source"], record["kind"], record["first"]) == ("example", "answer", True)
    assert focus_scripts(at)  # the input is focused after the answer


def test_answer_shows_follow_ups_that_ask_with_their_source(chat_app):
    at, logs = chat_app
    at.run()
    at.chat_input(key="chat_input").set_value("Can a guest bring their dog?").run()
    assert "Related questions" in [m.value for m in at.markdown] or any(
        "Related questions" in m.value for m in at.markdown
    )
    follow = [b for b in at.button if b.key and b.key.startswith("sugg_")]
    assert 2 <= len(follow) <= 3 and all(b.label != "Can a guest bring their dog?" for b in follow)
    follow[0].click().run()
    assert read_jsonl(logs / "usage.jsonl")[-1]["source"] == "follow_up"


def test_greeting_is_instant_free_and_offers_questions(chat_app):
    at, logs = chat_app
    at.run()
    at.chat_input(key="chat_input").set_value("hi").run()
    reply = at.chat_message[1]
    assert "Hi!" in reply.markdown[0].value and "20 of 20" in at.sidebar.caption[0].value  # not counted
    assert len([b for b in reply.button if b.key.startswith("sugg_")]) == 3
    assert read_jsonl(logs / "usage.jsonl")[-1]["kind"] == "greeting"


def test_gibberish_gets_a_polite_scope_message_popular_questions_and_topics(chat_app):
    at, _ = chat_app
    at.run()
    at.chat_input(key="chat_input").set_value("asdfgh").run()
    reply = at.chat_message[1]
    text = " ".join(m.value for m in reply.markdown)
    assert "can't answer that from this hotel's documents" in text and "popular questions" in text
    assert len([b for b in reply.button if b.key.startswith("sugg_")]) == 3 and reply.get("button_group")


def test_refusal_shows_did_you_mean_and_topics_never_follow_ups(chat_app, monkeypatch):
    at, logs = chat_app
    monkeypatch.setattr(FakeStream, "text", NOT_FOUND)
    at.run()
    at.chat_input(key="chat_input").set_value("Can you book me a room for Friday?").run()
    reply = at.chat_message[1]
    text = " ".join(m.value for m in reply.markdown)
    assert "can't answer that from this hotel's documents" in text and "Did you mean:" in text
    assert "Related questions" not in text and reply.get("button_group")
    assert read_jsonl(logs / "usage.jsonl")[-1]["kind"] == "refusal"
