from src.chat import FEEDBACK_REASONS, ChatState, Conversation, Turn, clean_question, remaining, validate_question


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


def test_one_conversation_continues_across_a_property_switch():
    state = ChatState()
    state.add(Turn("Dogs?", "beach-resort"))
    state.add(Turn("What about at Mountain Lodge?", "mountain-lodge"))
    assert [(t.question, t.property) for t in state.history()] == [
        ("Dogs?", "beach-resort"),
        ("What about at Mountain Lodge?", "mountain-lodge"),
    ]
    assert state.history("beach-resort") is state.history("mountain-lodge")  # the old argument is ignored
    assert state.current.properties() == ["beach-resort", "mountain-lodge"]


def test_new_conversation_saves_the_old_one_and_keeps_the_question_count():
    state = ChatState()
    turn = state.add(Turn("Dogs?", "beach-resort"))
    turn.feedback = "up"
    old = state.current
    assert state.clear() == [turn.id]
    assert state.history() == [] and state.past == [old]
    assert state.asked == 1 and state.find(turn.id) is turn and turn.feedback == "up"
    assert state.clear() == [] and state.past == [old]  # an empty conversation is not saved


def test_reopen_brings_back_a_past_conversation_and_saves_the_current_one():
    state = ChatState()
    first = state.add(Turn("Dogs?", "beach-resort"))
    state.clear()
    second = state.add(Turn("Parking?", "mountain-lodge"))
    old_id = state.past[0].id
    assert state.reopen(old_id) == [second.id]
    assert state.history() == [first] and [c.turns for c in state.past] == [[second]]
    assert state.reopen("missing") == []
    assert state.past[0].title() == "Parking?"


def test_only_the_newest_conversations_are_kept():
    state = ChatState(max_saved=2)
    for q in ("A?", "B?", "C?"):
        state.add(Turn(q, "beach-resort"))
        state.clear()
    assert [c.title() for c in state.past] == ["C?", "B?"]


def test_conversation_title_skips_greetings_and_is_shortened():
    c = Conversation([Turn("hi", "beach-resort", kind="greeting"), Turn("x" * 60, "beach-resort")])
    assert c.title(20) == "x" * 19 + "…"
    assert Conversation().title() == "Empty conversation"


def test_feedback_is_stored_on_the_turn_without_touching_others():
    state = ChatState()
    a, b = state.add(Turn("A?", "beach-resort")), state.add(Turn("B?", "beach-resort"))
    state.find(a.id).feedback, state.find(a.id).reason = "down", "Wrong fact"
    assert (a.feedback, a.reason, b.feedback) == ("down", "Wrong fact", None)


def test_session_limit_counter():
    assert remaining(0, 20) == 20 and remaining(20, 20) == 0 and remaining(25, 20) == 0


def test_feedback_reasons_are_the_agreed_list():
    assert FEEDBACK_REASONS == ("Wrong fact", "Missing information", "Wrong property", "Unclear", "Other")


def test_new_conversation_is_only_available_when_there_is_something_to_clear():
    state = ChatState()
    assert not state.has_messages()
    state.add(Turn("Dogs?", "beach-resort"))
    assert state.has_messages()
    state.clear()
    assert not state.has_messages()


def test_greetings_are_not_counted_and_the_first_message_is_marked():
    chat = ChatState()
    hi = chat.add(Turn("hi", "beach-resort"), counted=False)
    q = chat.add(Turn("Can a guest bring their dog?", "beach-resort"))
    assert hi.first and not q.first
    assert (chat.messages, chat.asked) == (2, 1)
    assert chat.questions("beach-resort") == ["hi", "Can a guest bring their dog?"]
