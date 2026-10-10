"""Chat state and input handling. Pure Python: the app keeps a `ChatState` in st.session_state.

Each question is answered on its own: earlier turns are shown on screen but never sent to
Claude (docs/DECISIONS.md #21), so every answer is grounded only in the documents.
"""

import re
import unicodedata
import uuid
from dataclasses import dataclass, field

FEEDBACK_REASONS = ("Wrong fact", "Missing information", "Wrong property", "Unclear", "Other")

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
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])


@dataclass
class ChatState:
    histories: dict = field(default_factory=dict)  # property -> list[Turn]
    asked: int = 0  # questions this session, across properties

    def history(self, prop: str) -> list:
        return self.histories.setdefault(prop, [])

    def add(self, turn: Turn) -> Turn:
        self.history(turn.property).append(turn)
        self.asked += 1
        return turn

    def clear(self, prop: str) -> list[str]:
        """'New conversation': clears this property's history and returns the removed turn ids (so the page
        can drop their feedback widgets). Other properties are untouched, and the question count is kept,
        so clearing can't be used to get around the per-session limit."""
        removed = [t.id for t in self.histories.get(prop, [])]
        self.histories[prop] = []
        return removed

    def has_messages(self, prop: str) -> bool:
        """'New conversation' is enabled only when this property's conversation has something to clear."""
        return bool(self.histories.get(prop))

    def find(self, turn_id: str) -> Turn | None:
        return next((t for turns in self.histories.values() for t in turns if t.id == turn_id), None)


def remaining(asked: int, limit: int) -> int:
    return max(0, limit - asked)
