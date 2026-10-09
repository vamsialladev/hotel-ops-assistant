import pytest

from src.retrieve import Retriever, stem


@pytest.fixture(scope="module")
def retriever():
    return Retriever(use_embeddings=False)


@pytest.mark.parametrize("prop,other", [("beach-resort", "mountain-lodge"), ("mountain-lodge", "beach-resort")])
def test_never_returns_another_hotels_documents(retriever, prop, other):
    for q in ["pet fee", "parking", "airport shuttle", "pool hours", "late checkout"]:
        assert all(r["property"] != other for r in retriever.search(q, prop, k=10))


def test_shared_documents_are_visible_to_every_property(retriever):
    for prop in retriever.properties():
        results = retriever.search("cancellation policy 48 hours", prop)
        assert any(r["source"] == "shared/brand_standards.md" for r in results)


def test_properties_list_excludes_shared(retriever):
    assert "shared" not in retriever.properties()


@pytest.mark.parametrize(
    "a,b", [("cats", "cat"), ("RVs", "rv"), ("smoking", "smoke"), ("cribs", "crib"), ("policies", "policy")]
)
def test_word_forms_match(a, b):
    assert stem(a.lower()) == stem(b.lower())


def test_no_keyword_match_returns_nothing_in_keyword_mode(retriever):
    assert retriever.search("xyzzy qwerty", "beach-resort") == []
