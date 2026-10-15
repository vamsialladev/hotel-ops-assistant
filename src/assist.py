"""What happens to one message before and after Claude, shared by the app and the visitor eval.

1. Greeting, thanks or "what can you do?"  -> instant friendly reply with questions that work (no API call)
2. Off-topic or gibberish (scope check)     -> polite scope message with "Did you mean" or popular questions
3. Otherwise Claude answers from the documents:
   - a cited answer gets 2-3 follow-up questions from the topic of the cited section
   - a refusal gets "Did you mean" questions (closest curated questions by retrieval score)
Every suggestion is a curated question the documents answer; none costs an extra API call.
"""

from src import intents, service
from src.suggestions import follow_ups, load_catalog, popular, recovery

GREETING_EXAMPLES = 3


def route(retriever, question: str, prop: str) -> dict:
    """Decide before any API call: {"kind": "greeting", "intent": ...} | {"kind": "scope", "prep": ...} |
    {"kind": "ask", "prep": ...}."""
    intent = intents.detect(question)
    if intent:
        return {"kind": "greeting", "intent": intent}
    prep = service.prepare(retriever, question, prop)
    if prep.get("safety"):
        return {"kind": "safety", "prep": prep}
    return {"kind": "scope" if prep["blocked"] else "ask", "prep": prep}


def suggestions_after(kind: str, question: str, prop: str, cited=(), asked=(), catalog=None) -> tuple[str, list]:
    """(label, questions) shown under a reply. label: follow_up | did_you_mean | popular | examples."""
    catalog = catalog or load_catalog()
    if kind == "greeting":
        return "examples", popular(prop, catalog, asked, GREETING_EXAMPLES)
    if kind == "answer":
        return "follow_up", follow_ups(list(cited), prop, catalog, asked)
    return recovery(question, prop, catalog, asked)  # refusal or scope


def respond(retriever, question: str, prop: str, use_api: bool = True, asked=()) -> dict:
    """The whole pipeline without the UI (used by the visitor eval)."""
    routed = route(retriever, question, prop)
    asked = list(asked) + [question]
    if routed["kind"] == "greeting":
        _, qs = suggestions_after("greeting", question, prop, asked=asked)
        return {
            "kind": "greeting",
            "answer": intents.reply(routed["intent"], prop),
            "citations": [],
            "hits": [],
            "suggestions": qs,
        }
    if routed["kind"] == "safety":  # emergency: fixed message and the manager note, no API call
        result = service.blocked_result(question)
        return {**result, "kind": "refusal", "hits": [], "suggestions": []}
    if routed["kind"] == "scope":
        _, qs = suggestions_after("scope", question, prop, asked=asked)
        return {"kind": "scope", "answer": "", "citations": [], "hits": [], "suggestions": qs}
    hits = routed["prep"]["hits"]
    if not use_api:
        return {"kind": "pending", "answer": "", "citations": [], "hits": hits, "suggestions": []}
    from src.generate import answer

    result = answer(question, prop, hits)
    kind = "answer" if result["found"] else "refusal"
    _, qs = suggestions_after(kind, question, prop, result["citations"], asked)
    return {**result, "kind": kind, "hits": hits, "suggestions": qs}
