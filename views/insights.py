"""Page 2: Insights for hotel managers, from the question and feedback logs."""

import streamlit as st

from src.activity import insights
from src.display import bar_list_html, esc, table_html
from src.feedback import FEEDBACK_FILE
from src.gaps import KNOWN_GAPS
from src.library import readable_name
from src.usage import USAGE_FILE, read_jsonl
from views import components as ui

b = ui.brand()
ui.header("Insights", "What staff ask, how useful the answers are, and where the policies have gaps.", "For managers")

data = insights(read_jsonl(USAGE_FILE), read_jsonl(FEEDBACK_FILE))

if data["questions"] == 0 and data["feedback"] == 0:
    ui.empty_state(
        "No questions yet",
        "As staff use the assistant, this page fills in: how many questions were asked, the helpful rate from "
        "👍 / 👎 feedback, the most common topics, and every question the documents couldn't answer, which "
        "usually points to a missing or unclear policy.",
    )
else:
    ui.tiles(
        [
            (str(data["questions"]), "Questions asked", "Answered or refused"),
            (ui.fmt_pct(data["helpful_rate"]), "Helpful rate", f"From {data['feedback']} feedback ratings"),
            (str(data["refused"]), "Not in the documents", "Possible policy gaps"),
            (str(sum(n for _, n in data["reasons"])), "Reasons given for 👎", "See the chart below"),
        ]
    )
    left, right = st.columns(2)
    with left:
        st.subheader("Most common topics")
        if data["topics"]:
            st.html(bar_list_html(data["topics"]))
            st.caption("Topic = the document section of the first cited source.")
        else:
            st.caption("No answered questions yet.")
    with right:
        st.subheader("Why answers weren't helpful")
        if data["reasons"]:
            st.html(bar_list_html(data["reasons"]))
        else:
            st.caption("No 👎 reasons given yet.")

    st.subheader("Possible policy gaps")
    st.caption("Questions the documents couldn't answer, newest first. Emails and phone numbers are masked.")
    if data["gaps"]:
        rows = [[g["time"][:16].replace("T", " "), b.property_name(g["property"]), g["question"]] for g in data["gaps"]]
        st.html(table_html(["When (UTC)", "Property", "Question"], rows))
    else:
        st.caption("None yet: every question so far was answered from the documents.")

st.subheader("Known policy gaps")
st.caption("Found while building and testing the assistant. Each one is worth raising with the hotel group.")
for gap in KNOWN_GAPS:
    st.html(
        f'<div class="hoa-card"><h3>{esc(gap.title)}</h3><p>{esc(gap.detail)}</p>'
        f'<p class="hoa-tile-help">Suggested fix: {esc(gap.suggestion)} · '
        f"Source: {esc(readable_name(gap.source))}</p></div>"
    )

st.caption(
    "On the public demo the log resets whenever the app restarts, so this page shows recent activity only. "
    "Questions are stored as typed by visitors; see the privacy note."
)
ui.footer()
