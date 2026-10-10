import pytest

from src.retrieve import Retriever, tokenize
from src.scope import in_scope


@pytest.fixture(scope="module")
def keyword():
    return Retriever(use_embeddings=False)


def test_keyword_match_is_in_scope_in_both_modes():
    assert in_scope({"keyword_matches": 3, "best_similarity": None}, 0.27)
    assert in_scope({"keyword_matches": 1, "best_similarity": 0.05}, 0.27)


def test_keyword_only_mode_blocks_questions_with_no_match():
    assert not in_scope({"keyword_matches": 0, "best_similarity": None}, 0.27)


def test_hybrid_mode_uses_the_similarity_threshold():
    assert in_scope({"keyword_matches": 0, "best_similarity": 0.47}, 0.27)  # "jacket" -> lost and found
    assert not in_scope({"keyword_matches": 0, "best_similarity": 0.23}, 0.27)  # a poem request


def test_single_letters_are_not_keywords():
    # "What's" used to produce the token "s", which matched every "guest's" in the documents.
    assert tokenize("What's the capital of France?") == ["capital", "franc"]


@pytest.mark.parametrize("question", ["What's the capital of France?", "Can you write me a poem about the ocean?"])
def test_off_topic_questions_have_no_keyword_match(keyword, question):
    assert keyword.signals(question, "beach-resort") == {"keyword_matches": 0, "best_similarity": None}


def test_hotel_questions_match_keywords(keyword):
    assert keyword.signals("How much is valet parking?", "beach-resort")["keyword_matches"] > 0
    assert keyword.mode == "keyword"
