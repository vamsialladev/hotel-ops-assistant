from src.admin import LOCKOUT_SECONDS, MAX_ATTEMPTS, WRONG, GateState, attempt, password_matches


def test_correct_password_unlocks():
    state = GateState()
    assert attempt(state, "s3cret-pass", "s3cret-pass", now=0) == (True, None)
    assert state.unlocked


def test_wrong_password_gives_one_generic_message():
    state = GateState()
    # A near miss and a wild guess get exactly the same answer.
    assert attempt(state, "s3cret-pas", "s3cret-pass", now=0) == (False, WRONG)
    assert attempt(state, "zzz", "s3cret-pass", now=1) == (False, WRONG)
    assert not state.unlocked


def test_lockout_after_five_failures_even_with_the_right_password():
    state = GateState()
    for i in range(MAX_ATTEMPTS):
        ok, message = attempt(state, "wrong", "s3cret-pass", now=i)
    assert not ok and "Too many attempts" in message and "15 minutes" in message
    ok, message = attempt(state, "s3cret-pass", "s3cret-pass", now=MAX_ATTEMPTS + 60)
    assert not ok and "Too many attempts" in message


def test_lockout_expires_after_15_minutes():
    state = GateState()
    for _ in range(MAX_ATTEMPTS):
        attempt(state, "wrong", "s3cret-pass", now=0)
    assert attempt(state, "s3cret-pass", "s3cret-pass", now=LOCKOUT_SECONDS + 1) == (True, None)


def test_no_password_configured_means_no_admin():
    assert attempt(GateState(), "", None, now=0) == (False, "The admin page is not configured.")


def test_password_comparison_handles_unicode_and_empty_input():
    assert password_matches("pässwörd", "pässwörd") and not password_matches("", "x")
