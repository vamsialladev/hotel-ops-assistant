"""Page 1: the front-desk assistant (chat). Logic lives in src/; this page wires it to the UI."""

import logging

import streamlit as st

from src import service
from src.chat import FEEDBACK_REASONS, Turn, remaining, validate_question
from src.config import MAX_QUESTION_CHARS, MAX_QUESTIONS_PER_SESSION
from src.display import esc, quote_markdown, safe_markdown, scope_label, source_chip_html, source_label
from src.errors import UNAVAILABLE, classify, private_detail
from src.escalation import RULES_BY_ID
from src.feedback import log_feedback
from src.generate import AnswerStream
from src.library import readable_name
from src.usage import log_usage
from views import components as ui

log = logging.getLogger("hotel_ops.app")
b, retriever, chat = ui.brand(), ui.retriever(), ui.chat_state()

PLACEHOLDER = "Ask about a hotel policy. Don't enter guest names or personal details."
SESSION_LIMIT = (
    f"You've reached this demo's limit of {MAX_QUESTIONS_PER_SESSION} questions per session. Thanks for trying it! "
    "The How it works page shows the measured results."
)
DAILY_LIMIT = "The demo has reached its daily question limit. Please come back tomorrow."
USER_AVATAR, BOT_AVATAR = ":material/person:", ui.asset("assets/favicon.png")


# ---------- callbacks (run before the rerun, so history is never lost and nothing is re-asked) ----------
def ask_later(question: str):
    st.session_state.pending = question


def new_conversation(prop: str):
    """Clear only this property's chat, drop the cleared turns' feedback widgets, and scroll to the top.
    The question limits are not reset."""
    for turn_id in chat.clear(prop):
        for prefix in ("reason_", "send_", "skip_", "up_", "down_"):
            st.session_state.pop(f"{prefix}{turn_id}", None)
    st.session_state.pop("pending", None)
    st.session_state.scroll_top = True


def feedback(turn_id: str, helpful: bool, reason: str | None = None):
    turn = chat.find(turn_id)
    if turn and turn.result and turn.feedback in (None, "down_pending"):
        log_feedback(turn.question, turn.property, turn.result, helpful=helpful, reason=reason)
        turn.feedback, turn.reason = ("up" if helpful else "down"), reason


def ask_reason(turn_id: str):
    turn = chat.find(turn_id)
    if turn and turn.feedback is None:
        turn.feedback = "down_pending"


# ---------- rendering ----------
def manager_note(rule) -> str:
    quote = f"<q>{esc(rule.quote)}</q>" if rule.quote else ""
    return (
        f'<div class="hoa-note" role="note"><b>{esc(rule.title)}</b>{esc(rule.message)}{quote}'
        f"<small>Source: {esc(rule.source_label or readable_name(rule.source))}</small></div>"
    )


def render_feedback(turn: Turn):
    if turn.feedback in ("up", "down"):
        st.caption("Thanks, your feedback was saved.")
        return
    if turn.feedback == "down_pending":
        reason = st.pills("What was wrong? (optional)", FEEDBACK_REASONS, key=f"reason_{turn.id}")
        c1 = c2 = st.container(horizontal=True, gap="small")
        c1.button("Send feedback", key=f"send_{turn.id}", on_click=feedback, args=(turn.id, False, reason))
        c2.button("Skip", key=f"skip_{turn.id}", type="tertiary", on_click=feedback, args=(turn.id, False, None))
        return
    row = st.container(horizontal=True, gap="small", vertical_alignment="center")  # stays one row on phones
    with row.popover("Copy", icon=":material/content_copy:", type="tertiary", help="Copy answer"):
        st.caption("Use the copy icon in the box.")
        st.code(turn.result["answer"], language=None, wrap_lines=True)
    row.button("👍", key=f"up_{turn.id}", help="Helpful", type="tertiary", on_click=feedback, args=(turn.id, True))
    row.button("👎", key=f"down_{turn.id}", help="Not helpful", type="tertiary", on_click=ask_reason, args=(turn.id,))


def render_answer(turn: Turn, text_shown: bool = False):
    if turn.error:
        if turn.error == UNAVAILABLE:
            st.error(turn.error, icon=":material/cloud_off:")
        else:
            st.info(turn.error, icon=":material/hourglass_bottom:")
        return
    result = turn.result
    rules = [RULES_BY_ID[r] for r in result.get("escalations", []) if r in RULES_BY_ID]
    if not text_shown:
        st.markdown(safe_markdown(result["answer"]))
    if result["found"] and not rules:
        st.html('<span class="hoa-status hoa-status-ok">Answered from the documents</span>')
    else:
        st.html('<span class="hoa-status hoa-status-warn">Check with a manager</span>')
    if result.get("ungrounded"):
        numbers = ", ".join(result["ungrounded"])
        st.html(f'<p class="hoa-check">Check before quoting: {esc(numbers)} does not appear in the cited sources.</p>')
    for rule in rules:
        st.html(manager_note(rule))
    cited = result["citations"]
    if cited:
        st.html('<div class="hoa-chips">' + "".join(source_chip_html(c, c["n"]) for c in cited) + "</div>")
        with st.expander("Sources", icon=":material/format_quote:"):
            for c in cited:
                st.markdown(f"**[{c['n']}] {safe_markdown(source_label(c))}** · {scope_label(c)}")
                st.markdown(quote_markdown(c["text"]))
    render_feedback(turn)


def render_turn(turn: Turn):
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(safe_markdown(turn.question))
    with st.chat_message("assistant", avatar=BOT_AVATAR):
        render_answer(turn)


def stream_text(run: AnswerStream, waiting):
    first = True
    for chunk in run:
        if first:
            waiting.empty()
            first = False
        yield safe_markdown(chunk)


# ---------- one question ----------
def handle(raw: str, prop: str):
    question, error = validate_question(raw, MAX_QUESTION_CHARS)
    if error:
        st.warning(error, icon=":material/edit_note:")
        return
    if chat.asked >= MAX_QUESTIONS_PER_SESSION:
        st.info(SESSION_LIMIT, icon=":material/hourglass_bottom:")
        return
    turn = Turn(question, prop)
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(safe_markdown(question))
    with st.chat_message("assistant", avatar=BOT_AVATAR):
        prep = service.prepare(retriever, question, prop)
        if prep["blocked"]:  # off-topic or nothing found: answered without an API call
            turn.result = service.finalize(question, prop, service.blocked_result())
            log_usage(service.usage_record(question, prop, retriever.mode, turn.result, pre_api=True))
        elif not ui.daily_counter().try_consume():
            turn.error = DAILY_LIMIT
            log_usage(service.usage_record(question, prop, retriever.mode, pre_api=True, error="daily_cap"))
        else:
            waiting = st.empty()
            waiting.caption("Checking the hotel's documents...")
            run = AnswerStream(question, prop, prep["hits"])
            try:
                shown = st.write_stream(stream_text(run, waiting))
            except Exception as exc:  # never show raw errors to visitors
                waiting.empty()
                code = classify(exc)
                log.error("answer failed: %s %s", code, private_detail(exc))
                turn.error = UNAVAILABLE
                log_usage(service.usage_record(question, prop, retriever.mode, hits=prep["hits"], error=code))
                chat.add(turn)
                render_answer(turn)
                return
            turn.result = service.finalize(question, prop, run.result)
            log_usage(
                service.usage_record(
                    question, prop, retriever.mode, turn.result, prep["hits"], run.time_to_first_token, run.total_time
                )
            )
            chat.add(turn)
            text_shown = isinstance(shown, str) and shown.strip() == safe_markdown(turn.result["answer"]).strip()
            render_answer(turn, text_shown=text_shown)
            return
        chat.add(turn)
        render_answer(turn)


# ---------- page ----------
props = retriever.properties()
st.session_state.setdefault("property", props[0])

ui.header(b.name, b.tagline)
# In the page (not the sidebar) so it's visible on phones, where the sidebar starts collapsed.
prop = st.segmented_control("Your property", props, format_func=b.property_name, key="property", required=True)
st.html(f'<div class="hoa-property"><b>{esc(b.property_name(prop))}</b><span>{esc(b.highlights(prop))}</span></div>')

with st.sidebar:
    st.button(
        "New conversation",
        key="new_conversation",
        icon=":material/add_comment:",
        on_click=new_conversation,
        args=(prop,),
        width="stretch",
    )
    questions_left = st.empty()  # filled in at the end, after this run's question is counted

if st.session_state.pop("scroll_top", False):
    ui.scroll_to_top()

typed = st.chat_input(PLACEHOLDER, max_chars=2000)
incoming = typed or st.session_state.pop("pending", None)

history = chat.history(prop)
if not history and not incoming:
    name = esc(b.property_name(prop))
    st.html(
        '<div class="hoa-card hoa-accent">'
        "<h3>Ask about a hotel policy</h3>"
        "<p>Front-desk staff lose minutes searching PDFs, menus and notes for rules that differ by hotel, "
        "while a guest waits.</p>"
        f"<p>This assistant answers in seconds from {name}'s documents and the brand-wide standards, "
        "and shows the source for every fact. When the documents don't say, it tells you to check with a manager.</p>"
        '<div class="hoa-cols"><div><h4>Can help with</h4><ul><li>Hotel policies and fees</li>'
        "<li>Amenities and opening hours</li><li>Loyalty benefits and procedures</li></ul></div>"
        "<div><h4>Can't help with</h4><ul><li>Bookings or reservation changes</li>"
        "<li>Guest records or personal details</li><li>Anything outside the hotel's documents</li></ul></div></div>"
        "</div>"
    )
    st.markdown("**Try one of these**")
    cols = st.columns(2)
    for i, sample in enumerate(b.samples(prop)):
        cols[i % 2].button(
            sample,
            key=f"main_{prop}_{i}",
            icon=":material/chat:",
            width="stretch",
            wrap=True,  # long sample questions wrap instead of being cut off
            on_click=ask_later,
            args=(sample,),
        )

for turn in history:
    render_turn(turn)

if incoming:
    handle(incoming, prop)

ui.footer()
questions_left.caption(
    f"{remaining(chat.asked, MAX_QUESTIONS_PER_SESSION)} of {MAX_QUESTIONS_PER_SESSION} demo questions left "
    "in this session."
)
