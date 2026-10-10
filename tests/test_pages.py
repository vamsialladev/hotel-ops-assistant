"""Every page runs for real (Streamlit AppTest, no browser, no API key, no PyTorch).

- each page renders without an exception
- an unexpected exception on any page shows the friendly message, never Streamlit's crash screen or a
  traceback, and is recorded for the owner
- "New conversation" is disabled when empty, enabled with a message, and clearing shows a toast
"""

import pytest
from streamlit.testing.v1 import AppTest

import src.errors as errors
import src.feedback as feedback
import src.usage as usage
from src.chat import ChatState, Turn
from src.config import ROOT
from src.errors import PAGE_ERROR
from src.retrieve import Retriever
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
