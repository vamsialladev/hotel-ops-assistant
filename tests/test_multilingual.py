"""Project 4: Spanish questions reach the model and get a Spanish answer; emergencies in other words and in Spanish
get the safety note; nothing else does. The held-out cases these fix (a06, a07, a12, a13) failed before the change
(eval-harness reports/p1-harness-2026-10-14.md)."""

import json
import re
import tomllib

import pytest

from src import escalation
from src.config import ROOT
from src.escalation import escalation_ids, is_safety
from src.generate import build_request, question_text
from src.language import detect_language, fold
from src.retrieve import SPANISH, SYNONYMS, Retriever, expand_query
from src.scope import SCOPE_MESSAGE, SCOPE_MESSAGE_ES, scope_message
from src.service import blocked_result, finalize, prepare


@pytest.fixture(scope="module")
def retriever():
    return Retriever(use_embeddings=False)


@pytest.mark.parametrize(
    "text",
    [
        "¿Cuánto cuesta el estacionamiento?",
        "¿Se permiten gatos en el hotel?",
        "¿A qué hora es el check-out?",
        "Hay un incendio en la cocina, ¿qué hacemos?",
        "cuanto cuesta el desayuno",  # no accents, no question marks
    ],
)
def test_spanish_questions_are_detected(text):
    assert detect_language(text) == "es"


@pytest.mark.parametrize(
    "text",
    [
        "How much is valet parking?",
        "Is the plaza open late?",  # Spanish loan word
        "Can a guest bring their dog?",
        "What time is check-out?",
        "",
        "wifi",
    ],
)
def test_english_questions_stay_english(text):
    assert detect_language(text) == "en"


def test_fold_removes_accents():
    assert fold("Habitación ÑANDÚ") == "habitacion nandu"


@pytest.mark.parametrize(
    "question, prop, source, section",
    [
        ("¿Cuánto cuesta el estacionamiento?", "beach-resort", "beach-resort/policies.md", "Parking"),  # a06
        ("¿Se permiten gatos en el hotel?", "mountain-lodge", "mountain-lodge/policies.md", "Pets"),  # a07
        ("¿Hay piscina?", "beach-resort", "beach-resort/policies.md", "Pool"),
        ("¿Cuál es la contraseña del wifi?", "mountain-lodge", None, "Wi-Fi"),
    ],
)
def test_spanish_questions_pass_the_scope_check_and_find_the_passage(retriever, question, prop, source, section):
    prep = prepare(retriever, question, prop)
    assert not prep["blocked"]
    top = prep["hits"][:3]
    assert any(section in h["section"] and (source is None or h["source"] == source) for h in top)


def test_off_topic_spanish_is_still_refused_before_the_api_in_spanish(retriever):
    q = "¿Cuál es la capital de Francia?"
    assert prepare(retriever, q, "beach-resort")["blocked"]
    assert blocked_result(q)["answer"] == SCOPE_MESSAGE_ES
    assert blocked_result("What's the capital of France?")["answer"] == SCOPE_MESSAGE
    assert scope_message("es") != scope_message("en")


def test_spanish_glossary_keys_are_not_english_words_or_existing_synonyms():
    """An English question must never be expanded by the Spanish table ("auto", "cargo" and "resort" were removed
    for this reason)."""
    english = {"auto", "cargo", "resort", "animal", "internet", "hotel", "plaza", "fee", "pet"}
    assert not (set(SPANISH) & english)
    assert not (set(SPANISH) & set(SYNONYMS))
    assert all(k == fold(k) and k.isalpha() for k in SPANISH)
    assert expand_query("Is the plaza open late?") == "Is the plaza open late?"


def test_spanish_question_asks_for_a_spanish_answer_and_english_stays_unchanged():
    assert question_text("How much is parking?") == "How much is parking?"
    es = question_text("¿Cuánto cuesta el estacionamiento?")
    assert es.startswith("¿Cuánto cuesta") and "answer in Spanish" in es
    request = build_request("¿Cuánto cuesta el estacionamiento?", "beach-resort", [])
    assert "answer in Spanish" in request["messages"][0]["content"]
    assert "language of the question" in request["system"]


def test_finalize_records_the_language():
    result = {"answer": "x", "found": False, "citations": [], "usage": {"input_tokens": 0, "output_tokens": 0}}
    assert finalize("¿Se permiten gatos en el hotel?", "mountain-lodge", result)["language"] == "es"
    assert finalize("Are cats allowed?", "mountain-lodge", result)["language"] == "en"


EMERGENCIES = [
    "There's smoke coming from under a guest room door. What should I do?",  # a12
    "Hay un incendio en la cocina, ¿qué hacemos?",  # a13
    "Hay un incendio en la cocina, que hacemos",  # no accents
    "I smell gas in the second-floor hallway. What do I do?",
    "A guest collapsed in the lobby and isn’t responding.",
    "A guest collapsed in the lobby and isn't responding.",
    "Un huésped se desmayó en el vestíbulo.",
    "Un huésped se cayó junto a la piscina y está sangrando.",
    "Someone is stuck in the elevator",
    "Il y a un incendie au deuxième étage",
]


@pytest.mark.parametrize("question", EMERGENCIES)
def test_emergencies_in_other_words_and_spanish_get_the_safety_note(question):
    assert is_safety(question)
    assert "safety" in escalation_ids(question, "beach-resort")


@pytest.mark.parametrize(
    "question",
    [
        "Can guests smoke on the balcony?",
        "¿Se puede fumar en el balcón?",
        "Is the fire pit open tonight?",
        "¿Me llamas un taxi?",  # "llamas" = you call
        "¿Hay un armario en la habitación?",  # "armario" contains "arma"
        "Is the hotel smoke-free?",
    ],
)
def test_lookalike_questions_do_not_get_the_safety_note(question):
    assert not is_safety(question)


def every_non_safety_question() -> list[str]:
    """Every question in the dev eval, the visitor eval and the curated suggestions that is not about safety."""
    rows = [json.loads(line) for line in (ROOT / "eval" / "questions.jsonl").read_text(encoding="utf-8").splitlines()]
    rows += [
        json.loads(line)
        for line in (ROOT / "eval" / "visitor_questions.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    out = [r["question"] for r in rows if "safety" not in (r.get("escalate") or [])]
    data = tomllib.loads((ROOT / "data" / "suggestions.toml").read_text(encoding="utf-8"))

    def walk(node):
        if isinstance(node, str):
            yield node
        elif isinstance(node, list):
            for x in node:
                yield from walk(x)
        elif isinstance(node, dict):
            for x in node.values():
                yield from walk(x)

    out += [s for s in walk(data) if s.endswith("?")]
    return out


def false_alarms(detector) -> list[str]:
    return [q for q in every_non_safety_question() if detector(q)]


def test_false_alarm_rate_is_zero_on_every_non_safety_question():
    questions = every_non_safety_question()
    assert len(questions) > 150  # dev + visitor + suggestions
    assert false_alarms(is_safety) == []


def test_the_false_alarm_check_can_fail():
    """A naive detector ("smoke" or "fire" anywhere) is caught by the same check."""
    naive = re.compile(r"\b(smok\w*|fire\w*)\b", re.I)
    assert false_alarms(lambda q: bool(naive.search(q)))


def test_old_safety_terms_alone_missed_the_held_out_emergencies():
    """Before Project 4 only SAFETY_TERMS existed: it misses a12 and a13 (so the new cases really test the fix)."""
    assert not escalation.SAFETY_TERMS.search(EMERGENCIES[0])
    assert not escalation.SAFETY_TERMS.search(EMERGENCIES[1])
