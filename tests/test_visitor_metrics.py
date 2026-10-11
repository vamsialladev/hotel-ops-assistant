from eval.run_visitor_eval import load_items
from eval.visitor_metrics import grade_visitor, summarize

ANSWER = {"expect": "answer", "expected_sources": ["shared/brand_standards.md"], "must_contain": ["3:00"]}
CITED = [{"source": "shared/brand_standards.md"}]


def outcome(kind, answer="", citations=(), hits=(), suggestions=0):
    return {
        "kind": kind,
        "answer": answer,
        "citations": list(citations),
        "hits": list(hits),
        "suggestions": ["q"] * suggestions,
    }


def test_in_scope_answer_needs_the_fact_and_a_citation_of_an_expected_document():
    assert grade_visitor(ANSWER, outcome("answer", "Check-in is 3:00 PM [1].", CITED), True)["success"]
    assert not grade_visitor(ANSWER, outcome("answer", "Check-in is 4:00 PM [1].", CITED), True)["success"]
    assert not grade_visitor(ANSWER, outcome("answer", "Check-in is 3:00 PM.", []), True)["success"]
    assert not grade_visitor(ANSWER, outcome("refusal"), True)["success"]


def test_routing_only_grading_uses_retrieval():
    assert grade_visitor(ANSWER, outcome("pending", hits=CITED), False)["success"]
    assert not grade_visitor(ANSWER, outcome("scope"), False)["success"]


def test_refusals_greetings_and_off_topic_need_questions_that_work():
    refuse, greet, off = {"expect": "refuse"}, {"expect": "greeting"}, {"expect": "offtopic"}
    assert grade_visitor(refuse, outcome("refusal", suggestions=2), True)["success"]
    assert not grade_visitor(refuse, outcome("refusal", suggestions=0), True)["success"]  # the old dead end
    assert grade_visitor(refuse, outcome("refusal"), True)["refused"]
    assert grade_visitor(greet, outcome("greeting", suggestions=3), True)["success"]
    assert not grade_visitor(greet, outcome("scope", suggestions=3), True)["success"]
    assert grade_visitor(off, outcome("scope", suggestions=3), True)["success"]
    assert not grade_visitor(off, outcome("answer", "Paris", suggestions=3), True)["refused"]
    assert grade_visitor(refuse, outcome("pending"), False)["success"] is None  # needs the model


def test_summary_rates_and_the_visitor_set():
    items = [ANSWER, {"expect": "greeting"}, {"expect": "offtopic"}, {"expect": "refuse"}]
    grades = [
        {"success": True, "refused": False},
        {"success": False, "refused": False},
        {"success": True, "refused": True},
        {"success": None, "refused": None},
    ]
    s = summarize(items, grades)
    assert s["first_question_success"] == 0.6667 and s["in_scope_answered"] == 1.0
    assert s["out_of_scope_refused"] == 1.0 and s["graded"] == 3
    visitor = load_items()
    assert len(visitor) >= 40 and {v["expect"] for v in visitor} == {"answer", "refuse", "greeting", "offtopic"}
    assert {v["property"] for v in visitor} == {"beach-resort", "mountain-lodge"}
