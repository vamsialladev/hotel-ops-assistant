"""Chat state and input handling. Pure Python: the app keeps a `ChatState` in st.session_state.

One conversation can span both properties: each turn records the property it was asked about. Follow-ups are
rewritten into a standalone question from the last 3 turns (src/rewrite.py), and only that question goes to
retrieval and Claude, never the raw history (docs/DECISIONS.md #21, #59). Past conversations are kept for the
browser session so the visitor can reopen one; "New conversation" saves the current one first.
"""

import re
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import datetime

FEEDBACK_REASONS = ("Wrong fact", "Missing information", "Wrong property", "Unclear", "Other")
# How a question was asked, logged with each question and rating (Insights: "How people ask").
SOURCES = {
    "typed": "Typed",
    "example": "Good-question example",
    "topic": "Topic example",
    "follow_up": "Follow-up",
    "did_you_mean": "Did you mean",
    "popular": "Popular question",
}

WHITESPACE = re.compile(r"\s+")


def clean_question(text: str | None) -> str:
    """Remove control and invisible formatting characters, collapse whitespace."""
    if not text:
        return ""
    chars = (" " if unicodedata.category(ch) in {"Cc", "Cf", "Zl", "Zp"} else ch for ch in text)
    return WHITESPACE.sub(" ", "".join(chars)).strip()


def validate_question(text: str | None, max_chars: int) -> tuple[str | None, str | None]:
    """Returns (clean question, None) or (None, friendly error). Enforced on the server, whatever the UI allows."""
    question = clean_question(text)
    if not question:
        return None, "Please type a question about a hotel policy."
    if len(question) > max_chars:
        return (
            None,
            f"Please keep questions under {max_chars} characters ({len(question)} now). Short questions work best.",
        )
    return question, None


@dataclass
class Turn:
    question: str
    property: str
    result: dict | None = None  # answer(), plus app extras such as "ungrounded" and "escalations"
    error: str | None = None  # friendly message shown instead of an answer
    feedback: str | None = None  # None, "up", "down_pending", "down"
    reason: str | None = None
    kind: str = "answer"  # answer | refusal | scope | greeting (set when the reply is ready)
    source: str = "typed"  # a key of SOURCES
    suggestions: list = field(default_factory=list)  # questions offered under the reply
    suggestion_label: str = ""  # follow_up | did_you_mean | popular | examples
    first: bool = False  # the session's first message
    rewritten: str | None = None  # the standalone question used for retrieval, when it differs from `question`
    rewrite_method: str = "none"  # none | rule | llm
    trace_id: str | None = None  # the shared ops trace (hotel-ai-platform): "Reference: 4f1c9a2e" on errors
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])


def new_id() -> str:
    return uuid.uuid4().hex[:12]


@dataclass
class Conversation:
    turns: list = field(default_factory=list)
    id: str = field(default_factory=new_id)
    started: str = field(default_factory=lambda: datetime.now().strftime("%H:%M"))

    def title(self, width: int = 48) -> str:
        """The first question asked, shortened: what the conversation list shows."""
        first = next((t.question for t in self.turns if t.kind != "greeting"), None) or (
            self.turns[0].question if self.turns else "Empty conversation"
        )
        return first if len(first) <= width else first[: width - 1].rstrip() + "…"

    def properties(self) -> list[str]:
        return list(dict.fromkeys(t.property for t in self.turns))


@dataclass
class ChatState:
    current: Conversation = field(default_factory=Conversation)
    past: list = field(default_factory=list)  # earlier conversations this session, newest first
    asked: int = 0  # questions this session, across conversations (greetings don't count)
    messages: int = 0  # everything sent this session, greetings included
    session_id: str = field(default_factory=new_id)
    max_saved: int = 10

    def history(self, prop: str | None = None) -> list:
        """The current conversation's turns (all properties). `prop` is accepted for older callers and ignored:
        a conversation now continues across a property switch."""
        return self.current.turns

    def add(self, turn: Turn, counted: bool = True) -> Turn:
        """Greetings and thanks pass counted=False: they don't use a question from the demo limits."""
        turn.first = self.messages == 0
        self.current.turns.append(turn)
        self.messages += 1
        self.asked += 1 if counted else 0
        return turn

    def questions(self, prop: str | None = None) -> list[str]:
        """Questions asked in this conversation, so suggestions never repeat one."""
        return [t.question for t in self.current.turns]

    def clear(self, prop: str | None = None) -> list[str]:
        """'New conversation': saves the current conversation to the list (if it has anything) and starts an empty
        one. Returns the ids of the turns that left the screen, so the page can drop their widgets. The question
        count is kept, so starting over can't be used to get around the per-session limit."""
        removed = [t.id for t in self.current.turns]
        self._save_current()
        self.current = Conversation()
        return removed

    def reopen(self, conversation_id: str) -> list[str]:
        """Make a past conversation the current one (the current one is saved first). Returns the ids of the turns
        that left the screen."""
        chosen = next((c for c in self.past if c.id == conversation_id), None)
        if chosen is None or chosen is self.current:
            return []
        removed = [t.id for t in self.current.turns]
        self.past.remove(chosen)
        self._save_current()
        self.current = chosen
        return removed

    def _save_current(self):
        if self.current.turns:
            self.past.insert(0, self.current)
            del self.past[self.max_saved :]

    def has_messages(self, prop: str | None = None) -> bool:
        """'New conversation' is enabled only when the conversation has something to clear."""
        return bool(self.current.turns)

    def find(self, turn_id: str) -> Turn | None:
        return next((t for c in [self.current, *self.past] for t in c.turns if t.id == turn_id), None)


def remaining(asked: int, limit: int) -> int:
    return max(0, limit - asked)
