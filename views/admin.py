"""Owner-only Admin page. Registered only when ADMIN_PASSWORD is set; hidden from the menu until unlocked.

The gate is simple demo protection, not real authentication (SECURITY.md). Logic lives in src/admin.py,
src/activity.py and src/monitoring.py.
"""

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
from src.display import model_name, table_html
from src.errors import errors_file
from src.feedback import FEEDBACK_FILE
from src.limits import today_utc
from src.monitoring import ACTIVITY_COLUMNS, ERROR_COLUMNS, activity, alerts, filter_rows, health, recent_errors, to_csv
from src.usage import USAGE_FILE, read_jsonl
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
warnings = alerts(h, ALERT_ERROR_RATE, ALERT_MIN_EVENTS, ALERT_DAILY_COST_USD)


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
st.markdown(f"**Most recent errors** ({h['errors_today']} today, {len(errors)} in the log)")
recent = recent_errors(errors, 20)
if recent:
    rows = [
        [r.get("time", "")[:19].replace("T", " "), r.get("page", ""), r.get("type", ""), r.get("message", "")]
        for r in recent
    ]
    st.html(table_html(["Time (UTC)", "Page", "Error type", "Message"], rows))
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

# ---------- Recent activity ----------
st.subheader("Recent activity")
props = sorted({r.get("property") for r in usage if r.get("property")})
c1, c2, c3 = st.columns([1.2, 1.2, 1])
pick_day = c1.date_input("Date (UTC)", value=None, max_value=date.today(), help="Leave empty for all dates")
pick_prop = c2.selectbox("Property", ["All properties", *props])
errors_only = c3.checkbox("Errors only")
table = filter_rows(
    activity(usage, feedback),
    day=pick_day.isoformat() if pick_day else None,
    prop=None if pick_prop == "All properties" else pick_prop,
    errors_only=errors_only,
)
shown = [{**r, "time": str(r.get("time", ""))[:19].replace("T", " ")} for r in table[:200]]
st.dataframe(
    shown,
    column_order=ACTIVITY_COLUMNS,
    hide_index=True,
    width="stretch",
    column_config={
        "time": "Time (UTC)",
        "property": "Property",
        "model": "Model",
        "tokens_in": "Tokens in",
        "tokens_out": "Tokens out",
        "cost_usd": st.column_config.NumberColumn("Cost (USD)", format="%.5f"),
        "total_s": st.column_config.NumberColumn("Answer time (s)", format="%.2f"),
        "refused": "Refused",
        "grounding_flag": "Grounding flag",
        "error": "Error",
        "feedback": "👍 / 👎",
        "reason": "Reason",
    },
)
st.caption(f"Showing {min(len(table), 200)} of {len(table)} matching entries, newest first. No question text here.")

d1, d2, d3 = st.columns(3)
d1.download_button("Download usage CSV", to_csv(usage), f"usage-{today}.csv", "text/csv", icon=":material/download:")
d2.download_button(
    "Download feedback CSV", to_csv(feedback), f"feedback-{today}.csv", "text/csv", icon=":material/download:"
)
d3.download_button(
    "Download errors CSV", to_csv(errors, ERROR_COLUMNS), f"errors-{today}.csv", "text/csv", icon=":material/download:"
)
st.caption("The usage and feedback files include questions as typed by visitors. Keep them private.")

# ---------- Recent questions (detail) ----------
st.subheader("Recent questions")
if not s["recent"]:
    st.caption("No questions logged yet.")
for r in s["recent"]:
    state = r.get("error") or ("refused" if r.get("refused") else "answered")
    title = f"{r.get('time', '')[:19].replace('T', ' ')} · {r.get('property', '')} · {state}"
    with st.expander(title):
        st.text(r.get("question", ""))
        st.caption(
            f"Model {r.get('model') or 'none (blocked before the API)'} · mode {r.get('mode')} · "
            f"first word {ui.fmt_seconds(r.get('ttft_s'))} · total {ui.fmt_seconds(r.get('total_s'))} · "
            f"tokens {r.get('tokens_in', 0)}/{r.get('tokens_out', 0)} · cost {money(r.get('cost_usd'))}"
        )
        if r.get("ungrounded"):
            st.caption(f"Ungrounded numbers: {', '.join(r['ungrounded'])}")
        if r.get("escalations"):
            st.caption(f"Manager notes: {', '.join(r['escalations'])}")
        passages = [
            [p["source"], p["section"], f"{p['score']:.4f}" if p.get("score") is not None else "–"]
            for p in r.get("retrieved", [])
        ]
        if passages:
            st.html(table_html(["Retrieved passage", "Section", "Score"], passages))
