from eval.metrics import grade, numbers_in

POLICY = {"source": "mountain-lodge/policies.md", "text": "Pet fee is $50 per night, capped at $200 per stay."}
NOTES = {"source": "mountain-lodge/front_desk_notes.txt", "text": "early check in before 12pm = $25 fee"}
ITEM = {
    "question": "What is the pet fee?",
    "expected_source": "mountain-lodge/policies.md",
    "must_contain": ["50"],
    "must_not_contain": ["waived"],
}


def result(answer, citations, found=True):
    return {"answer": answer, "found": found, "citations": citations}


def test_numbers_are_normalized():
    assert numbers_in("$1,200 and 2:00 PM [3]") == {"1200", "2"}


def test_correct_cited_and_grounded_answer():
    g = grade(ITEM, result("It's $50 per night, up to $200 per stay [1].", [POLICY]))
    assert g == {"correct": True, "citation_ok": True, "grounded": True, "ungrounded": []}


def test_invented_number_is_caught():
    g = grade(ITEM, result("It's $50 per night, or $300 for a week [1].", [POLICY]))
    assert g["grounded"] is False and g["ungrounded"] == ["300"]


def test_wrong_source_cited():
    g = grade(ITEM, result("It's $50 [1].", [NOTES]))
    assert g["citation_ok"] is False and g["grounded"] is False


def test_forbidden_phrase_fails_answer():
    g = grade(ITEM, result("The $50 fee is waived for this guest [1].", [POLICY]))
    assert g["correct"] is False


def test_numbers_from_the_question_are_allowed():
    item = {**ITEM, "question": "Can I refund $300 myself?", "must_contain": []}
    rule = {"source": "x", "text": "Refunds over $200 need the Manager on Duty."}
    assert grade(item, result("No, $300 is over the $200 limit [1].", [rule]))["grounded"] is True


def test_refusal_is_correct_only_for_unanswerable_questions():
    refusal = result("I couldn't find this.", [], found=False)
    assert grade({"question": "Babysitting?", "unanswerable": True}, refusal)["correct"] is True
    assert grade(ITEM, refusal)["correct"] is False
