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


def test_compound_words_have_one_spelling_in_questions_and_documents():
    from src.retrieve import tokenize

    assert tokenize("What time is checkout?")[-1] == tokenize("Late Check-out")[-1] == tokenize("check out")[-1]
    assert "checkin" in tokenize("Can I check in early?") and "wifi" in tokenize("Is there Wi-Fi?")


def test_visitor_words_are_expanded_to_document_words():
    from src.retrieve import expand_query

    assert "fitness" in expand_query("Is there a gym?")
    assert "lost found" in expand_query("I left something in my room")
    assert expand_query("Can a guest bring their dog?") == "Can a guest bring their dog?"  # nothing to add


def test_synonyms_find_passages_the_question_never_names(retriever):
    gym = retriever.search("Is there a gym?", "mountain-lodge")
    assert any(h["section"].endswith("Amenities") for h in gym)  # "partner fitness center"
    lost = retriever.search("I left something in my room. What happens to it?", "beach-resort")
    assert any("Lost and Found" in h["section"] for h in lost)
