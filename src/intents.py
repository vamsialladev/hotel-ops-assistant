"""Greetings, thanks and "what can you do?" are answered instantly, without an API call or using a question
from the demo limits. Only whole messages count: "hi, can a guest bring a dog?" is a policy question."""

import re

GREETINGS = {"hi", "hello", "hey", "hiya", "howdy", "yo", "good morning", "good afternoon", "good evening"}
THANKS = {
    "thanks",
    "thank you",
    "thx",
    "ty",
    "cheers",
    "thanks a lot",
    "thank you so much",
    "great thanks",
    "ok thanks",
}
META = {
    "help",
    "what can you do",
    "what can i ask",
    "what do you know",
    "what do you do",
    "how does this work",
    "how do i use this",
    "how do i use you",
    "who are you",
    "what are you",
    "what is this",
    "start",
    "menu",
    "options",
}
PUNCTUATION = re.compile(r"[^\w\s']")


def normalize(text: str) -> str:
    return " ".join(PUNCTUATION.sub(" ", text.lower()).split())


def detect(text: str) -> str | None:
    """'greeting', 'thanks', 'meta' or None (a real question)."""
    t = normalize(text)
    if not t:
        return None
    if t in THANKS:
        return "thanks"
    if t in META:
        return "meta"
    words = t.split()
    for n in (2, 1):  # "hi", "hello there", "hi what can you do"
        head, rest = " ".join(words[:n]), " ".join(words[n:])
        if head in GREETINGS:
            rest = rest.removeprefix("there").strip()
            if not rest:
                return "greeting"
            if rest in META:
                return "meta"
    return None


def reply(kind: str, property_name: str) -> str:
    if kind == "thanks":
        return "You're welcome! Ask another policy question any time."
    if kind == "meta":
        return (
            f"I answer front-desk policy questions for {property_name}, with the source for every fact. "
            "I can't make bookings or look up guests."
        )
    return f"Hi! I answer policy questions for {property_name} from its documents. Here's what I know:"
