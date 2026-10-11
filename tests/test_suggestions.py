"""Curated suggestions: topics from the documents, examples that work, follow-ups, "Did you mean", popular."""

import pytest

from eval.run_suggestions_eval import cases, retrieves_topic
from src.display import section_name
from src.retrieve import Retriever
from src.suggestions import (
    available_topics,
    did_you_mean,
    follow_ups,
    hints,
    knows,
    load_catalog,
    norm,
    popular,
    recovery,
    topic_of,
)

CATALOG = load_catalog()
B, M = "beach-resort", "mountain-lodge"
INTROS = {"Hotel Group Brand Standards", "Hotel Group Guest Handbook"}  # a document's opening line, not a topic


@pytest.fixture(scope="module")
def retriever():
    return Retriever(use_embeddings=False)


def chunk(source, section):
    return {"source": source, "section": section, "property": source.split("/")[0]}


def test_catalog_has_three_good_examples_per_property_and_unique_topic_ids():
    assert {p: len(qs) for p, qs in CATALOG.good.items()} == {B: 3, M: 3}
    ids = [t.id for t in CATALOG.topics]
    assert len(ids) == len(set(ids)) and all(t.label and t.icon for t in CATALOG.topics)


def test_every_indexed_section_belongs_to_a_topic(retriever):
    """So "What this demo knows" is complete: a new document section needs a topic (and examples)."""
    missing = {
        (c["source"], section_name(c))
        for c in retriever.chunks
        if topic_of(c, CATALOG) is None and section_name(c) not in INTROS
    }
    assert missing == set()


def test_topics_come_from_the_documents_per_property(retriever):
    beach = {t.id for t in available_topics(retriever.chunks, B, CATALOG)}
    lodge = {t.id for t in available_topics(retriever.chunks, M, CATALOG)}
    assert "spa" in beach and "spa" not in lodge  # only Beach Resort has a spa menu
    assert "events" in lodge and "events" not in beach  # only Mountain Lodge has an events policy
    assert "safety" not in beach | lodge  # the only safety document is an unreadable scan
    assert knows(retriever.chunks, B, CATALOG)[:2] == ["Pets", "Check-in and check-out"]


def test_a_topic_without_indexed_passages_is_hidden():
    only_pets = [chunk("beach-resort/policies.md", "Beach Resort - Property Policies > Pets")]
    assert [t.id for t in available_topics(only_pets, B, CATALOG)] == ["pets"]


def test_every_curated_question_retrieves_a_passage_of_its_topic(retriever):
    failed = [q for p, t, q in cases(CATALOG, [B, M]) if not retrieves_topic(retriever, p, t, q, CATALOG)]
    assert failed == []


def test_follow_ups_come_from_the_cited_topic_and_never_repeat():
    pets = chunk("beach-resort/policies.md", "Beach Resort - Property Policies > Pets")
    out = follow_ups([pets], B, CATALOG, asked=["Can a guest bring their dog?"])
    assert out == ["Are dogs allowed at the pool?", "Is there a fee for service animals?"]


def test_follow_ups_top_up_a_small_topic_and_are_empty_without_citations():
    spa = chunk("beach-resort/spa_menu.md", "Spa - Beach Resort")
    asked = ["What are the spa hours?", "How much is a 60-minute Swedish massage?"]
    out = follow_ups([spa], B, CATALOG, asked=asked)
    assert out[0] == "Do Gold members get a spa discount?" and len(out) >= 2
    assert not set(map(norm, asked)) & set(map(norm, out))
    assert follow_ups([], B, CATALOG) == []


def test_did_you_mean_ranks_curated_questions_by_keyword_score():
    out = did_you_mean("Can you book me a room for next Friday?", B, CATALOG)
    assert out and all("room" in q.lower() for q in out[:2])
    assert did_you_mean("asdfgh", B, CATALOG) == [] and did_you_mean("", B, CATALOG) == []
    assert "What is the pet fee?" not in did_you_mean("What is the pet fee?", M, CATALOG)  # never the same question


def test_recovery_falls_back_to_popular_questions_and_always_offers_three():
    label, qs = recovery("tell me a joke", M, CATALOG)
    assert label == "popular" and qs == CATALOG.good[M]
    label, qs = recovery("Can you book me a room?", B, CATALOG)
    assert label == "did_you_mean" and len(qs) == 3 and len(set(qs)) == 3


def test_popular_skips_questions_already_asked():
    assert popular(B, CATALOG, asked=["can a guest bring their dog"])[0] != "Can a guest bring their dog?"


def test_input_hints_are_short_and_per_property():
    beach, lodge = hints(B, CATALOG), hints(M, CATALOG)
    assert beach and all(h.startswith("Try: ") and len(h) <= 45 for h in beach + lodge)
    assert "Try: What are the spa hours?" in beach and "Try: What are the spa hours?" not in lodge
