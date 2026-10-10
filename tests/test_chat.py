from src.chat import FEEDBACK_REASONS, ChatState, Turn, clean_question, remaining, validate_question


def test_empty_and_whitespace_questions_are_rejected():
    for text in [None, "", "   ", "\n\t"]:
        question, error = validate_question(text, 500)
        assert question is None and "type a question" in error


def test_long_questions_are_rejected_on_the_server():
    question, error = validate_question("a" * 501, 500)
    assert question is None and "under 500 characters" in error
    assert validate_question("a" * 500, 500) == ("a" * 500, None)


def test_control_and_invisible_characters_are_stripped():
    assert clean_question("Pet\x00 fee?\x1b[31m​ ok\r\n") == "Pet fee? [31m ok"


def test_html_is_kept_as_text_for_display_escaping():
    # Validation doesn't mangle input; display escaping makes it safe (see test_display).
    assert validate_question("<script>alert(1)</script>", 500) == ("<script>alert(1)</script>", None)


def test_histories_are_separate_per_property():
    state = ChatState()
    state.add(Turn("Dogs?", "beach-resort"))
    state.add(Turn("Parking?", "mountain-lodge"))
    assert [t.question for t in state.history("beach-resort")] == ["Dogs?"]
    assert [t.question for t in state.history("mountain-lodge")] == ["Parking?"]


def test_new_conversation_clears_one_property_but_keeps_the_question_count():
    state = ChatState()
    turn = state.add(Turn("Dogs?", "beach-resort"))
    state.add(Turn("Parking?", "mountain-lodge"))
    other = state.history("mountain-lodge")[0]
    other.feedback = "up"
    assert state.clear("beach-resort") == [turn.id]
    assert state.history("beach-resort") == [] and state.history("mountain-lodge") == [other]
    assert other.feedback == "up"  # the other property's feedback state is untouched
    assert state.asked == 2 and state.find(turn.id) is None
    assert state.clear("beach-resort") == []  # clearing an empty conversation is harmless


def test_feedback_is_stored_on_the_turn_without_touching_others():
    state = ChatState()
    a, b = state.add(Turn("A?", "beach-resort")), state.add(Turn("B?", "beach-resort"))
    state.find(a.id).feedback, state.find(a.id).reason = "down", "Wrong fact"
    assert (a.feedback, a.reason, b.feedback) == ("down", "Wrong fact", None)


def test_session_limit_counter():
    assert remaining(0, 20) == 20 and remaining(20, 20) == 0 and remaining(25, 20) == 0


def test_feedback_reasons_are_the_agreed_list():
    assert FEEDBACK_REASONS == ("Wrong fact", "Missing information", "Wrong property", "Unclear", "Other")
