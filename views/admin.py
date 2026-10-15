"""Owner-only Admin page. Registered only when ADMIN_PASSWORD is set; hidden from the menu until unlocked.

The gate is simple demo protection, not real authentication (SECURITY.md). Logic lives in src/admin.py,
src/activity.py and src/monitoring.py.
"""

import json
import time
from datetime import date

import streamlit as st

from src.activity import admin_stats
from src.admin import FAILURE_DELAY_SECONDS, GateState, attempt, sign_out, still_signed_in
from src.config import (
    ADMIN_IDLE_MINUTES,
    ALERT_DAILY_COST_USD,
    ALERT_ERROR_RATE,
    ALERT_MIN_EVENTS,
    LLM_MODEL,
    MAX_QUESTIONS_PER_DAY,
    PRICE_IN_PER_M,
    PRICE_OUT_PER_M,
    admin_password,
)
from src.display import esc, model_name, safe_markdown, table_html
from src.errors import category, errors_file
from src.feedback import FEEDBACK_FILE
from src.library import readable_name
from src.limits import today_utc
from src.monitoring import (
    ERROR_COLUMNS,
    alerts,
    first_question_success,
    health,
    recent_errors,
    to_csv,
)
from src.reports import latest_visitor
from src.requestlog import (
    NOT_RECORDED,
    RESULTS,
    details,
    filter_requests,
    find,
    list_rows,
    log_since,
    request_json,
    selected_id,
    short_time,
    table_key,
    to_jsonl,
)
from src.secrets_check import REQUIRED, secret_status
from src.usage import USAGE_FILE, read_jsonl, redact
from views import components as ui

IDLE_SECONDS = ADMIN_IDLE_MINUTES * 60
gate = st.session_state.setdefault("admin_gate", GateState())
timed_out = gate.unlocked and not still_signed_in(gate, time.time(), IDLE_SECONDS)

if not gate.unlocked:
    ui.header("Owner sign-in", "This page is for the app owner only.", "Admin")
    if timed_out:
        st.info(f"Signed out after {ADMIN_IDLE_MINUTES} minutes of inactivity.", icon=":material/lock_clock:")
    with st.form("admin_login", clear_on_submit=True):
        given = st.text_input("Password", type="password", autocomplete="current-password")
        submitted = st.form_submit_button("Unlock", icon=":material/lock_open:")
    if submitted:
        ok, message = attempt(gate, given, admin_password(), now=time.time())
        if ok:
            st.rerun()  # shows the Admin page in the menu
        time.sleep(FAILURE_DELAY_SECONDS)  # slows down guessing
        st.error(message, icon=":material/lock:")
    st.stop()


@st.fragment(run_every="60s")
def idle_watch():
    """Locks the page even if it's just left open: checks once a minute without counting as activity."""
    if time.time() - gate.last_active > IDLE_SECONDS:
        sign_out(gate)
        st.rerun()


idle_watch()

ui.header("Admin", "Private health, usage, cost and quality signals. Never shown to visitors.", "Owner only")
if st.button("Sign out", icon=":material/logout:"):
    sign_out(gate)
    st.rerun()
st.caption(f"Signs out automatically after {ADMIN_IDLE_MINUTES} minutes without activity.")

usage, feedback, errors = read_jsonl(USAGE_FILE), read_jsonl(FEEDBACK_FILE), read_jsonl(errors_file())
today = today_utc()
retriever = ui.retriever()
h = health(usage, errors, today, time.time(), ui.app_started(), ui.daily_counter().used(), MAX_QUESTIONS_PER_DAY)
secrets = secret_status()  # "set" or "missing" only, never a value
warnings = [
    f"Required secret {name} is missing. Add it under Secrets on Streamlit Cloud (or .streamlit/secrets.toml "
    "locally), then reboot the app."
    for name in REQUIRED
    if secrets[name] == "missing"
] + alerts(h, ALERT_ERROR_RATE, ALERT_MIN_EVENTS, ALERT_DAILY_COST_USD)


def money(value, digits=4):
    return "not configured" if value is None else f"${value:,.{digits}f}"


# ---------- Health and errors ----------
st.subheader("Health and errors")
for w in warnings:
    st.warning(w, icon=":material/warning:")
status = "Needs attention" if warnings else "Running normally"
ui.tiles(
    [
        (status, "App status", f"Up for {h['uptime']} since the last restart"),
        (model_name(LLM_MODEL), "Model", f"Retrieval: {'hybrid' if retriever.mode == 'hybrid' else 'keyword-only'}"),
        (
            f"{h['daily_used']}/{h['daily_cap']}",
            "Questions today vs daily cap",
            f"{h['questions_today']} answered (UTC)",
        ),
        (money(h["cost_today"], 4), "Estimated cost today", f"Warns at ${ALERT_DAILY_COST_USD:.2f}"),
    ]
)
fq, visitor = first_question_success(usage), latest_visitor(retriever.mode)
ui.tiles(
    [
        (
            ui.fmt_pct(fq["rate"]),
            "First-question success (live)",
            f"{fq['ok']} of {fq['sessions']} sessions got a cited answer or a greeting reply to their first message",
        ),
        (
            ui.fmt_pct(visitor["first_question_success"] if visitor else None),
            "First-question success (eval)",
            f"{visitor['questions']} visitor questions, {visitor['date']}" if visitor else "No visitor eval report yet",
        ),
    ]
)
st.html(
    '<p class="hoa-secrets"><b>Secrets</b> '
    + " ".join(
        f'<span class="hoa-status hoa-status-{"ok" if state == "set" else "error"}">{name}: {state}</span>'
        for name, state in secrets.items()
    )
    + "</p>"
)
st.markdown(f"**Most recent errors** ({h['errors_today']} today, {len(errors)} in the log)")
recent = recent_errors(errors, 20)
if recent:
    rows = [
        [
            r.get("time", "")[:19].replace("T", " "),
            r.get("page", ""),
            r.get("category") or category(r.get("type", "")),
            r.get("message", ""),
        ]
        for r in recent
    ]
    st.html(table_html(["Time (UTC)", "Page", "Likely cause", "Message"], rows))
else:
    st.caption("No errors recorded since the last restart.")
st.caption(
    f"Cost is an estimate from PRICE_IN_PER_M={PRICE_IN_PER_M} and PRICE_OUT_PER_M={PRICE_OUT_PER_M} "
    "(USD per million tokens); the Anthropic Console is the source of truth for billing. Warnings appear when "
    f"the error rate today reaches {ALERT_ERROR_RATE:.0%} (after {ALERT_MIN_EVENTS} events) or the estimated "
    f"cost reaches ${ALERT_DAILY_COST_USD:.2f}."
)

# ---------- Usage summary ----------
s = admin_stats(usage, feedback, today=today)
st.subheader("Usage")
since = log_since(usage)
st.caption(f"Log since {since + ' UTC' if since else 'no entries yet'} · {ui.log_storage_note()}")
k1, k2 = st.columns(2)
k1.download_button(
    "Download usage log (JSONL)",
    to_jsonl(usage),
    f"usage-{today}.jsonl",
    "application/jsonl",
    icon=":material/download:",
    on_click="ignore",
)
k2.download_button(
    "Download feedback log (JSONL)",
    to_jsonl(feedback),
    f"feedback-{today}.jsonl",
    "application/jsonl",
    icon=":material/download:",
    on_click="ignore",
)
ui.tiles(
    [
        (str(s["questions_total"]), "Questions in the log", f"{s['blocked_before_api']} answered without the API"),
        (money(s["cost_usd"]), "Estimated cost, whole log", f"{s['api_calls']} API calls"),
        (f"{s['tokens_in']:,} / {s['tokens_out']:,}", "Tokens in / out", "Whole log"),
        (ui.fmt_seconds(s["p95_total_s"]), "Full answer, p95", f"First word p95 {ui.fmt_seconds(s['p95_ttft_s'])}"),
    ]
)
ui.tiles(
    [
        (str(s["refused"]), "Refusals", "Not in the documents, or off-topic"),
        (str(s["grounding_flags"]), "Grounding flags", "Numbers not in cited sources"),
        (str(sum(n for _, n in s["reasons"])), "👎 with a reason", ", ".join(r for r, _ in s["reasons"][:3]) or "None"),
    ]
)


# ---------- Requests: list, filters, details ----------
def nr(value, fmt=None) -> str:
    """A value for display, or "not recorded" when the record doesn't have it."""
    return NOT_RECORDED if value is None else (fmt(value) if fmt else str(value))


def citation_badges(citations: list) -> str:
    chips = "".join(
        '<span class="hoa-chip">'
        f'<span class="hoa-chip-n">{esc(c.get("n") or "")}</span>'
        f'<span class="hoa-chip-label">{esc(readable_name(c.get("source") or "") or NOT_RECORDED)}</span>'
        f'<span class="hoa-chip-meta">{esc(c.get("section") or "")}</span>'
        "</span>"
        for c in citations
    )
    return f'<div class="hoa-chips">{chips}</div>'


def fields_table(pairs: list) -> str:
    return table_html(["Field", "Value"], [[k, v] for k, v in pairs])


@st.dialog("Request details", width="large")
def request_dialog(record: dict, feedback_rows: list):
    d = details(record, feedback_rows)
    tabs = st.tabs(["Summary", "Answer", "Sources", "Performance", "Checks", "Feedback", "Raw"])
    with tabs[0]:
        st.markdown("**Question**")
        st.text(d["question"])
        st.html(
            fields_table(
                [
                    ("Result", d["result"]),
                    ("Property", d["property"]),
                    ("Time (UTC)", d["time"]),
                    ("Session", d["session_id"]),
                    ("Log schema", f"v{d['schema_version']}"),
                ]
            )
        )
        st.caption("Request ID (copy icon on the right)")
        st.code(d["id"], language=None)
    with tabs[1]:
        if d["answer"] is None:
            missing = NOT_RECORDED if d["schema_version"] < 2 else "no answer (see Checks)"
            st.caption(f"Answer: {d['error_message'] or missing}")
        else:
            st.markdown(safe_markdown(d["answer"]))
        if d["citations"] is None:
            st.caption(f"Citations: {NOT_RECORDED}")
        elif d["citations"]:
            st.html(citation_badges(d["citations"]))
        else:
            st.caption("No citations.")
    with tabs[2]:
        if d["passages"] is None:
            st.caption(f"Retrieved passages: {NOT_RECORDED}")
        elif not d["passages"]:
            st.caption("No passages retrieved (the reply was made without searching or before the API).")
        else:
            st.html(
                table_html(
                    ["Source", "Section", "Score", "Cited"],
                    [
                        [
                            readable_name(p["source"]) if p["source"] != NOT_RECORDED else NOT_RECORDED,
                            p["section"],
                            nr(p["score"], lambda v: f"{v:.4f}"),
                            {True: "✓", False: "", None: NOT_RECORDED}[p["cited"]],
                        ]
                        for p in d["passages"]
                    ],
                )
            )
    with tabs[3]:
        st.html(
            fields_table(
                [
                    ("Model", d["model"]),
                    ("Search mode", d["mode"]),
                    ("First word", nr(d["ttft_s"], lambda v: f"{v:.2f} s")),
                    ("Total time", nr(d["total_s"], lambda v: f"{v:.2f} s")),
                    ("Tokens in / out", f"{nr(d['tokens_in'])} / {nr(d['tokens_out'])}"),
                    ("Estimated cost", nr(d["cost_usd"], lambda v: f"${v:.6f}")),
                ]
            )
        )
        st.caption("Replies made without an API call have no timing. Cost is an estimate.")
    with tabs[4]:
        follow = d["follow_ups"]
        st.html(
            fields_table(
                [
                    ("Refusal reason", d["refusal_reason"] or "None"),
                    ("Grounding flag", nr(d["grounding_flag"], lambda v: "Yes" if v else "No")),
                    ("Numbers not in sources", nr(d["ungrounded"], lambda v: ", ".join(v) or "None")),
                    ("Manager notes", nr(d["escalations"], lambda v: ", ".join(v) or "None")),
                    ("Error", d["error"] or "None"),
                    ("Error message", d["error_message"] or ("None" if not d["error"] else NOT_RECORDED)),
                    ("Follow-ups shown", NOT_RECORDED if follow is None else (" · ".join(follow) or "None")),
                ]
            )
        )
    with tabs[5]:
        f = d["feedback"]
        if not f:
            st.caption("No feedback")
        else:
            st.html(
                fields_table(
                    [
                        ("Rating", "👍 Helpful" if f.get("helpful") else "👎 Not helpful"),
                        ("Reason", f.get("reason") or "None given"),
                        ("Time (UTC)", short_time(f.get("time"))),
                    ]
                )
            )
    with tabs[6]:
        st.code(json.dumps(redact(d["raw"]), ensure_ascii=False, indent=2), language="json", wrap_lines=True)
    b1, b2 = st.columns(2)
    b1.download_button(
        "Download this request (JSON)",
        redact(request_json(record, feedback_rows)),
        f"request-{d['id']}.json",
        "application/json",
        icon=":material/download:",
        on_click="ignore",
        width="stretch",
    )
    if b2.button("Close", icon=":material/close:", width="stretch"):
        st.rerun()


PAGE_SIZE = 50
st.subheader("Requests")
st.caption("Every request: answered, refused, off-topic, greeting, error or cap. Select a row to see all its details.")
all_rows = list_rows(usage, feedback)
props = sorted({r["property"] for r in all_rows if r["property"] != NOT_RECORDED})
f1, f2, f3 = st.columns(3)
picked = f1.date_input("Date range (UTC)", value=(), max_value=date.today(), help="Pick a start and an end date")
pick_prop = f2.selectbox("Property", ["All properties", *props])
pick_results = f3.multiselect("Result", list(RESULTS), format_func=RESULTS.get, placeholder="All results")
g1, g2, g3 = st.columns([1, 1, 2], vertical_alignment="bottom")
pick_feedback = g1.selectbox(
    "Feedback", ["any", "up", "down"], format_func={"any": "Any", "up": "👍", "down": "👎"}.get
)
errors_only = g2.checkbox("Errors only")
search = g3.text_input("Search questions", placeholder="Words in the question")
dates = list(picked) if isinstance(picked, list | tuple) else [picked]
start = dates[0] if dates else None
end = dates[1] if len(dates) > 1 else start
filters = (start, end, pick_prop, tuple(pick_results), pick_feedback, errors_only, search.strip().lower())
matching = filter_requests(
    all_rows,
    start=start,
    end=end,
    prop=None if pick_prop == "All properties" else pick_prop,
    outcomes=pick_results,
    feedback=pick_feedback,
    errors_only=errors_only,
    text=search,
)
if st.session_state.get("requests_filters") != filters:  # new filters: back to the first page
    st.session_state.requests_filters, st.session_state.requests_limit = filters, PAGE_SIZE
limit = st.session_state.setdefault("requests_limit", PAGE_SIZE)
shown = matching[:limit]
in_log = f" ({len(all_rows)} in the log)" if len(matching) != len(all_rows) else ""
st.caption(f"Showing {len(shown)} of {len(matching)} requests{in_log}, newest first.")
event = st.dataframe(
    shown,
    column_order=("time", "property", "result", "question", "total", "cost", "feedback"),
    column_config={
        "time": "Time (UTC)",
        "property": "Property",
        "result": "Result",
        "question": st.column_config.TextColumn("Question", width="large"),
        "total": "Total time",
        "cost": "Cost",
        "feedback": "Feedback",
    },
    hide_index=True,
    width="stretch",
    on_select="rerun",
    selection_mode="single-row",
    key=table_key(filters, limit),
)
if len(matching) > limit:
    if st.button(f"Load {min(PAGE_SIZE, len(matching) - limit)} more", icon=":material/expand_more:"):
        st.session_state.requests_limit = limit + PAGE_SIZE
        st.rerun()

rid = selected_id(shown, event)
if rid is None:
    st.session_state.pop("requests_open", None)
elif st.session_state.get("requests_open") != rid:  # opens once per selection; Close doesn't reopen it
    st.session_state.requests_open = rid
    record = find(usage, rid)
    if record is not None:
        request_dialog(record, feedback)

d1, d2, d3 = st.columns(3)
d1.download_button(
    "Download usage CSV", to_csv(usage), f"usage-{today}.csv", "text/csv", icon=":material/download:", on_click="ignore"
)
d2.download_button(
    "Download feedback CSV",
    to_csv(feedback),
    f"feedback-{today}.csv",
    "text/csv",
    icon=":material/download:",
    on_click="ignore",
)
d3.download_button(
    "Download errors CSV",
    to_csv(errors, ERROR_COLUMNS),
    f"errors-{today}.csv",
    "text/csv",
    icon=":material/download:",
    on_click="ignore",
)
st.caption("The logs include questions and answers as typed and shown. Keep downloads private.")
