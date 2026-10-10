"""Owner-only Admin page. Registered only when ADMIN_PASSWORD is set; hidden from the menu until unlocked.

The gate is simple demo protection, not real authentication (SECURITY.md).
"""

import time

import streamlit as st

from src.activity import admin_stats
from src.admin import FAILURE_DELAY_SECONDS, GateState, attempt
from src.config import MAX_QUESTIONS_PER_DAY, PRICE_IN_PER_M, PRICE_OUT_PER_M, admin_password
from src.display import table_html
from src.feedback import FEEDBACK_FILE
from src.limits import today_utc
from src.usage import USAGE_FILE, read_jsonl
from views import components as ui

gate = st.session_state.setdefault("admin_gate", GateState())

if not gate.unlocked:
    ui.header("Owner sign-in", "This page is for the app owner only.", "Admin")
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

ui.header("Admin", "Private usage, cost and quality signals. Never shown to visitors.", "Owner only")
if st.button("Lock admin page", icon=":material/lock:"):
    gate.unlocked = False
    st.rerun()

usage, feedback = read_jsonl(USAGE_FILE), read_jsonl(FEEDBACK_FILE)
s = admin_stats(usage, feedback, today=today_utc())
used_today = ui.daily_counter().used()


def money(value):
    return "not configured" if value is None else f"${value:,.4f}"


ui.tiles(
    [
        (str(s["questions_today"]), "Questions today (UTC)", f"{s['questions_total']} in the log"),
        (f"{used_today}/{MAX_QUESTIONS_PER_DAY}", "Daily cap used", "API calls counted today"),
        (money(s["cost_usd"]), "Estimated cost", "Whole log, from configured prices"),
        (f"{s['tokens_in']:,} / {s['tokens_out']:,}", "Tokens in / out", f"{s['api_calls']} API calls"),
    ]
)
ui.tiles(
    [
        (ui.fmt_seconds(s["avg_total_s"]), "Average answer time", f"p95 {ui.fmt_seconds(s['p95_total_s'])}"),
        (ui.fmt_seconds(s["p95_ttft_s"]), "Time to first word, p95", "Streaming"),
        (str(s["refused"]), "Refusals", f"{s['blocked_before_api']} blocked before the API"),
        (str(s["grounding_flags"]), "Grounding flags", "Numbers not in cited sources"),
    ]
)
st.caption(
    f"Cost is an estimate from PRICE_IN_PER_M={PRICE_IN_PER_M} and PRICE_OUT_PER_M={PRICE_OUT_PER_M} "
    "(USD per million tokens); the Anthropic Console is the source of truth for billing."
)

left, right = st.columns(2)
with left:
    st.subheader("👎 reasons")
    if s["reasons"]:
        st.html(table_html(["Reason", "Count"], [[r, str(n)] for r, n in s["reasons"]]))
    else:
        st.caption("None yet.")
with right:
    st.subheader("Errors")
    if s["errors"]:
        st.html(table_html(["Error", "Count"], [[e, str(n)] for e, n in s["errors"]]))
    else:
        st.caption("No API errors logged.")

st.subheader("Recent questions")
if not s["recent"]:
    st.caption("No questions logged yet.")
for r in s["recent"]:
    status = r.get("error") or ("refused" if r.get("refused") else "answered")
    title = f"{r.get('time', '')[:19].replace('T', ' ')} · {r.get('property', '')} · {status}"
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
        rows = [
            [p["source"], p["section"], f"{p['score']:.4f}" if p.get("score") is not None else "–"]
            for p in r.get("retrieved", [])
        ]
        if rows:
            st.html(table_html(["Retrieved passage", "Section", "Score"], rows))
