"""Page 1: the front-desk assistant (chat). Logic lives in src/; this page wires it to the UI."""

import logging

import streamlit as st

from src import assist, intents, service
from src.chat import FEEDBACK_REASONS, Turn, remaining, validate_question
from src.config import MAX_QUESTION_CHARS, MAX_QUESTIONS_PER_SESSION
from src.display import esc, quote_markdown, safe_markdown, scope_label, source_chip_html, source_label
from src.errors import UNAVAILABLE, category, classify, private_detail, record_error, safe_message
from src.escalation import RULES_BY_ID
from src.feedback import log_feedback
from src.generate import NOT_FOUND, AnswerStream
from src.library import readable_name
from src.suggestions import available_topics, hints, knows, load_catalog, topic_of
from src.usage import log_usage
from views import components as ui

log = logging.getLogger("hotel_ops.app")
b, retriever, chat, catalog = ui.brand(), ui.retriever(), ui.chat_state(), load_catalog()

PRIVACY = "Don't enter guest names or personal details."
TIP = "Ask one policy question at a time, in plain English."
REFUSAL_HEAD = "I can't answer that from this hotel's documents."
SUGGESTION_LABELS = {
    "follow_up": "Related questions",
    "did_you_mean": "Did you mean:",
    "popular": "Try one of these popular questions:",
    "examples": "Try one of these:",
}
SUGGESTION_SOURCES = {  # suggestion list -> question source logged when one is clicked
    "follow_up": "follow_up",
    "did_you_mean": "did_you_mean",
    "popular": "popular",
    "examples": "example",
}
SESSION_LIMIT = (
    f"You've reached this demo's limit of {MAX_QUESTIONS_PER_SESSION} questions per session. Thanks for trying it! "
    "The How it works page shows the measured results."
)
DAILY_LIMIT = "The demo has reached its daily question limit. Please come back tomorrow."
PAGE_ERROR_SHORT = "That didn't work. Please try again; the error was logged for the app owner."
USER_AVATAR, BOT_AVATAR = ":material/person:", ui.asset("assets/favicon.png")
HOW_TO = (
    '<ol class="hoa-howto" aria-label="How to use">'
    "<li><span>1</span>Pick your property</li>"
    "<li><span>2</span>Tap a topic or type your question</li>"
    "<li><span>3</span>Check the sources, and ask a manager when the answer says so</li>"
    "</ol>"
)

NEW_CHAT_TOAST = "Started a new conversation"
NEW_CHAT_EMPTY_HELP = "This conversation is already empty"
guard = ui.safe_callback("Assistant")
TURN_WIDGETS = ("reason_", "send_", "skip_", "up_", "down_", "topics_")


# ---------- callbacks (run before the rerun, so history is never lost and nothing is re-asked) ----------
@guard
def ask_later(question: str, source: str = "typed"):
    """A suggestion click: asked on the next run exactly like a typed question, and counted the same way."""
    st.session_state.pending = {"question": question, "source": source}


@guard
def new_conversation(prop: str):
    """Clear only this property's chat, drop the cleared turns' widgets, scroll to the top, confirm with a toast,
    and put the cursor back in the chat input. The question limits are not reset."""
    if not chat.has_messages(prop):
        return
    for turn_id in chat.clear(prop):
        for prefix in TURN_WIDGETS:
            st.session_state.pop(f"{prefix}{turn_id}", None)
    st.session_state.pop("pending", None)
    st.session_state.pop(f"topics_welcome_{prop}", None)
    st.session_state.scroll_top = True
    st.session_state.toast = NEW_CHAT_TOAST
    st.session_state.focus = "new_chat"


@guard
def feedback(turn_id: str, helpful: bool, reason: str | None = None):
    turn = chat.find(turn_id)
    if turn and turn.result and turn.feedback in (None, "down_pending"):
        log_feedback(
            turn.question,
            turn.property,
            turn.result,
            helpful=helpful,
            reason=reason,
            turn_id=turn.id,
            source=turn.source,
        )
        turn.feedback, turn.reason = ("up" if helpful else "down"), reason


@guard
def ask_reason(turn_id: str):
    turn = chat.find(turn_id)
    if turn and turn.feedback is None:
        turn.feedback = "down_pending"


# ---------- guidance ----------
def knows_html(prop: str, chips_below: bool = False) -> str:
    """'What this demo knows': topics generated from the indexed documents, what it can't do, and a link.
    On the welcome screen the topics are the clickable chips under this line (chips_below)."""
    labels = knows(retriever.chunks, prop, catalog)
    name = esc(b.property_name(prop))
    library = '<a href="library" target="_self">Document library</a>'
    topics = "tap a topic for example questions" if chips_below else esc(", ".join(labels))
    return (
        '<div class="hoa-knows" role="note">'
        f'<p class="hoa-knows-full"><b>What this demo knows at {name}:</b> {len(labels)} topics, {topics}.</p>'
        f'<p class="hoa-knows-short"><b>Knows:</b> {len(labels)} topics at {name} · {library}</p>'
        "</div>"
    )


CANT = (
    '<p class="hoa-knows-cant">It can&rsquo;t make bookings, look up guests or answer anything outside these '
    'documents · <a href="library" target="_self">Document library</a></p>'
)


def suggestion_buttons(questions: list, source: str, key: str, label: str | None = None):
    """Clickable questions. Each is a real button labelled with the question it asks."""
    if not questions:
        return
    if label:
        st.markdown(f"**{label}**")
    row = st.container(horizontal=True, gap="small")
    for i, q in enumerate(questions):
        row.button(q, key=f"{key}_{i}", icon=":material/chat:", on_click=ask_later, args=(q, source))


def topic_browser(prop: str, key: str, label: str = "Or browse by topic", show_label: bool = True):
    """Topic chips; picking one shows 3-4 example questions to click."""
    topics = {t.id: t for t in available_topics(retriever.chunks, prop, catalog)}
    choice = st.pills(
        label,
        list(topics),
        format_func=lambda i: f"{topics[i].icon} {topics[i].label}",
        key=key,
        label_visibility="visible" if show_label else "collapsed",
    )
    if choice in topics:
        suggestion_buttons(topics[choice].examples[prop][:4], "topic", f"{key}_{choice}")


def welcome(prop: str):
    """How to use, what the demo knows (its topics are the chips), and good questions: one laptop screen."""
    st.html(HOW_TO)
    with st.container(key=f"knows_{prop}"):  # styled as one panel
        st.html(knows_html(prop, chips_below=True))
        topic_browser(prop, key=f"topics_welcome_{prop}", label="Topics", show_label=False)
        st.html(CANT)
    st.html(f'<p class="hoa-label"><b>Good questions look like…</b><span class="hoa-tip">{TIP}</span></p>')
    good = catalog.good.get(prop, [])
    for col, (i, q) in zip(st.columns(len(good) or 1, gap="small"), enumerate(good), strict=False):  # one row
        col.button(q, key=f"good_{prop}_{i}", width="stretch", on_click=ask_later, args=(q, "example"))


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


def render_suggestions(turn: Turn):
    """Follow-ups under an answer; after a refusal, greeting or off-topic reply, recovery questions plus topics."""
    source = SUGGESTION_SOURCES.get(turn.suggestion_label, "example")
    label = SUGGESTION_LABELS.get(turn.suggestion_label)
    suggestion_buttons(turn.suggestions, source, f"sugg_{turn.id}", label)
    if turn.kind != "answer":
        topic_browser(turn.property, key=f"topics_{turn.id}")


def render_answer(turn: Turn, text_shown: bool = False):
    if turn.error:
        if turn.error == UNAVAILABLE:
            st.error(turn.error, icon=":material/cloud_off:")
        else:
            st.info(turn.error, icon=":material/hourglass_bottom:")
        return
    result = turn.result
    if turn.kind == "greeting":
        st.markdown(safe_markdown(result["answer"]))
        st.html(knows_html(turn.property))
        render_suggestions(turn)
        return
    if turn.kind == "scope":
        name = b.property_name(turn.property)
        st.markdown(
            safe_markdown(f"{REFUSAL_HEAD} I answer questions about {name}'s policies, fees, amenities and procedures.")
        )
        render_suggestions(turn)
        render_feedback(turn)
        return
    rules = [RULES_BY_ID[r] for r in result.get("escalations", []) if r in RULES_BY_ID]
    if turn.kind == "refusal" and result["answer"].strip() == NOT_FOUND:
        st.markdown(f"{REFUSAL_HEAD} If it's a real guest question, please check with a manager.")
    elif not text_shown:
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
    render_suggestions(turn)
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


# ---------- one message ----------
def finish(turn: Turn, kind: str, counted: bool = True, **log_fields):
    """Attach the right suggestions (no API call), log the request with everything the visitor sees, then add
    the turn to the conversation."""
    turn.kind = kind
    asked = chat.questions(turn.property) + [turn.question]
    cited = (turn.result or {}).get("citations", [])
    turn.suggestion_label, turn.suggestions = assist.suggestions_after(
        kind, turn.question, turn.property, cited, asked, catalog
    )
    log_turn(turn, kind, **log_fields)
    chat.add(turn, counted=counted)


def log_turn(turn: Turn, kind: str, **fields):
    """One usage record per request (answered, refused, greeting, off-topic, error or cap), with how it was
    asked, whether it was the session's first, and the follow-ups shown under it."""
    cited = (turn.result or {}).get("citations", [])
    topic = topic_of(cited[0], catalog) if cited else None
    log_usage(
        service.usage_record(
            turn.question,
            turn.property,
            retriever.mode,
            turn.result,
            turn_id=turn.id,
            source=turn.source,
            kind=kind,
            session_id=chat.session_id,
            first=chat.messages == 0,
            topic_group=topic.label if topic else None,
            follow_ups=turn.suggestions,
            follow_up_label=turn.suggestion_label,
            **fields,
        )
    )


def handle(raw: str, prop: str, source: str = "typed"):
    question, error = validate_question(raw, MAX_QUESTION_CHARS)
    if error:
        st.warning(error, icon=":material/edit_note:")
        return
    turn = Turn(question, prop, source=source)
    intent = intents.detect(question)
    if intent:  # hi / thanks / what can you do: instant, free, not counted toward the limits
        turn.result = {"answer": intents.reply(intent, b.property_name(prop)), "found": False, "citations": []}
        finish(turn, "greeting", counted=False, pre_api=True)
        render_turn(turn)
        return
    if chat.asked >= MAX_QUESTIONS_PER_SESSION:
        st.info(SESSION_LIMIT, icon=":material/hourglass_bottom:")
        log_turn(turn, "answer", pre_api=True, error="session_cap", error_message=SESSION_LIMIT)
        return
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(safe_markdown(question))
    with st.chat_message("assistant", avatar=BOT_AVATAR):
        prep = service.prepare(retriever, question, prop)
        if prep["blocked"]:  # off-topic or gibberish: answered without an API call
            turn.result = service.finalize(question, prop, service.blocked_result())
            finish(turn, "scope", pre_api=True)
        elif not ui.daily_counter().try_consume():
            turn.error = DAILY_LIMIT
            log_turn(turn, "answer", pre_api=True, error="daily_cap", error_message=DAILY_LIMIT)
            chat.add(turn)
        else:
            waiting = st.empty()
            waiting.caption("Checking the hotel's documents...")
            run = AnswerStream(question, prop, prep["hits"])
            streamed = st.empty()  # cleared for a refusal, which gets the recovery message instead
            try:
                with streamed:
                    shown = st.write_stream(stream_text(run, waiting))
            except Exception as exc:  # never show raw errors to visitors
                waiting.empty()
                code = classify(exc)
                log.error("answer failed: %s (%s) %s", code, category(code), private_detail(exc))
                record_error("Assistant", exc)
                turn.error = UNAVAILABLE
                log_turn(turn, "answer", hits=prep["hits"], error=code, error_message=safe_message(exc))
                chat.add(turn)
                render_answer(turn)
                return
            turn.result = service.finalize(question, prop, run.result)
            kind = "answer" if turn.result["found"] else "refusal"
            finish(turn, kind, hits=prep["hits"], ttft=run.time_to_first_token, total=run.total_time)
            text_shown = isinstance(shown, str) and shown.strip() == safe_markdown(turn.result["answer"]).strip()
            if kind == "refusal":
                streamed.empty()
            render_answer(turn, text_shown=text_shown and kind == "answer")
            return
        render_answer(turn)


# ---------- page ----------
props = retriever.properties()
st.session_state.setdefault("property", props[0])

ui.header(b.name, b.tagline)
# In the page (not the sidebar) so it's visible on phones, where the sidebar starts collapsed.
prop = st.segmented_control(
    "Your property", props, format_func=b.property_name, key="property", required=True, label_visibility="collapsed"
)

with st.sidebar:
    # Both filled in at the end of the page, after this run's question is counted, so the button is
    # enabled as soon as the first answer appears.
    new_chat_slot = st.empty()
    questions_left = st.empty()

if st.session_state.pop("scroll_top", False):
    ui.scroll_to_top()
if message := st.session_state.pop("toast", None):
    st.toast(message, icon=":material/check_circle:")
if st.session_state.pop("callback_error", False):
    st.warning(PAGE_ERROR_SHORT, icon=":material/error:")

tips = hints(prop, catalog)
with st.bottom:  # pinned to the bottom of the page, under the chat input
    typed = st.chat_input(tips[chat.messages % len(tips)] if tips else "Ask about a hotel policy", key="chat_input")
    st.html(
        '<p class="hoa-input-note">Answers are written live by AI using only the documents in the '
        f'<a href="library" target="_self">Document library</a>. {PRIVACY}</p>'
    )
pending = st.session_state.pop("pending", None)
if isinstance(pending, str):  # older sessions stored the question only
    pending = {"question": pending, "source": "typed"}
incoming = {"question": typed, "source": "typed"} if typed else pending

history = chat.history(prop)
if not history and not incoming:
    with st.container(key="welcome"):  # tighter spacing so it fits one laptop screen
        welcome(prop)
else:  # in a conversation there's room for the property's highlights
    st.html(
        f'<div class="hoa-property"><b>{esc(b.property_name(prop))}</b><span>{esc(b.highlights(prop))}</span></div>'
    )

for turn in history:
    render_turn(turn)

if incoming:
    handle(incoming["question"], prop, incoming.get("source", "typed"))
    ui.focus_chat_input()  # ready for the next question (left alone on phones, so the keyboard stays down)
elif st.session_state.pop("focus", None) == "new_chat":
    ui.focus_chat_input(close_sidebar=True)  # on phones the sidebar covered the input after New conversation

ui.footer()
has_messages = chat.has_messages(prop)
new_chat_slot.button(
    "New conversation",
    key="new_conversation",
    icon=":material/add_comment:",
    on_click=new_conversation,
    args=(prop,),
    width="stretch",
    disabled=not has_messages,
    help=None if has_messages else NEW_CHAT_EMPTY_HELP,
)
questions_left.caption(
    f"{remaining(chat.asked, MAX_QUESTIONS_PER_SESSION)} of {MAX_QUESTIONS_PER_SESSION} demo questions left "
    "in this session."
)
