import pytest

from src.config import RAW_DIR
from src.escalation import RULES, amounts, escalation_ids, escalations
from src.gaps import KNOWN_GAPS


@pytest.mark.parametrize("rule", [r for r in RULES if r.quote], ids=lambda r: r.id)
def test_rule_quotes_appear_word_for_word_in_the_documents(rule):
    assert rule.quote in (RAW_DIR / rule.source).read_text(encoding="utf-8")


@pytest.mark.parametrize("gap", [g for g in KNOWN_GAPS if g.evidence], ids=lambda g: g.title)
def test_policy_gap_evidence_appears_in_the_documents(gap):
    assert gap.evidence in (RAW_DIR / gap.source).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "question,prop,expected",
    [
        ("Can I give a guest a $300 refund myself?", "beach-resort", ["refund_over_limit"]),
        ("A guest wants a $120 credit. Can I give it?", "beach-resort", ["refund_over_limit"]),
        ("Can I give a $25 courtesy credit?", "beach-resort", []),
        ("Can I refund 75 dollars?", "mountain-lodge", ["refund_over_limit"]),
        ("Guest on a non-refundable rate wants money back", "mountain-lodge", ["nonrefundable_exception"]),
        ("Where is the fire assembly point?", "beach-resort", ["safety"]),
        ("The smoke alarm is going off in room 210", "beach-resort", ["safety"]),
        ("A guest is injured by the pool", "beach-resort", ["safety"]),
        ("Can a guest smoke on the balcony?", "mountain-lodge", []),
        ("What time do the fire pit evenings start?", "mountain-lodge", []),
        ("A guest got a third noise complaint", "mountain-lodge", ["noise_removal"]),
        ("A guest got a third noise complaint", "beach-resort", []),
        ("What are the pool hours?", "beach-resort", []),
        ("How much is valet parking? It's $45, right?", "beach-resort", []),
    ],
)
def test_rules_fire_only_when_they_should(question, prop, expected):
    assert escalation_ids(question, prop) == expected


def test_refused_answers_get_the_generic_manager_note_only_when_no_rule_applies():
    assert [r.id for r in escalations("Do we offer babysitting?", "beach-resort", refused=True)] == ["refused"]
    assert [r.id for r in escalations("Where is the fire exit?", "beach-resort", refused=True)] == ["safety"]
    assert escalations("Do we offer babysitting?", "beach-resort", refused=False) == []


def test_amounts_are_parsed():
    assert amounts("$1,200 or 75 dollars or $49.50") == [1200.0, 75.0, 49.5]
