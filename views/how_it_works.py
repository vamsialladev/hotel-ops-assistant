"""Page 4: How it works, for recruiters, hiring managers and engineers.

Every number comes from a saved eval report or BUSINESS_CASE.md; nothing is hard-coded here.
"""

import streamlit as st

from src.config import LLM_MODEL, TOP_K
from src.display import esc, escape_dollars, model_name, table_html
from src.reports import business_case, latest, latest_visitor, paired
from views import components as ui

b, retriever = ui.brand(), ui.retriever()
mode = retriever.mode
MODE_LABEL = {"hybrid": "hybrid (keywords + meaning)", "keyword": "keyword-only"}
ui.header(
    "How it works",
    "A retrieval-augmented assistant built, measured and documented like a client delivery.",
)

st.markdown(
    "**The problem.** Front-desk staff answer policy questions all day (pets, late checkout, parking, fees), and the "
    "answers are spread across PDFs, menus, brand standards and staff notes that differ by hotel. Searching takes "
    "minutes while a guest waits, and a wrong answer turns into a refund or a bad review.\n\n"
    "**What it does.** Staff pick their property and ask in plain English. The assistant finds the relevant "
    "passages from that hotel's documents and the brand-wide standards, and Claude writes a short answer that cites "
    "every fact. When the documents don't say, it refuses and points to a manager."
)

report = latest(mode=mode, model=LLM_MODEL)
retrieval_report = latest(mode=mode, answers=None)
st.subheader("Key results")
if report:
    ui.tiles(
        [
            (
                f"{report['retrieval']['pct']}%",
                "Retrieval accuracy",
                f"Right passage in the top {TOP_K} ({MODE_LABEL[mode]})",
            ),
            (
                f"{report['answer_accuracy']['pct']}%",
                "Answer accuracy",
                f"{report.get('runs', 1)} runs, labeled questions",
            ),
            (
                ui.fmt_seconds(report["latency"]["p50"]),
                "Typical answer time",
                f"p95 {ui.fmt_seconds(report['latency']['p95'])}",
            ),
            (f"${report['cost_per_1000']:.2f}", "Cost per 1,000 questions", f"Measured, {model_name(report['model'])}"),
        ]
    )
else:
    ui.empty_state(
        "No answer eval for this setup yet",
        f"Run: python -m eval.run_eval --answers --runs 3{' --bm25-only' if mode == 'keyword' else ''}",
    )
if retrieval_report:
    r = retrieval_report["retrieval"]
    st.html(
        f'<div class="hoa-callout">This app is running <b>{esc(MODE_LABEL[mode])}</b> retrieval. Measured accuracy '
        f"in this mode: <b>{r['ok']}/{r['n']} ({r['pct']}%)</b> of answerable eval questions find the exact "
        "passage.</div>"
    )

cases = business_case()
if cases:
    low, base, high = cases["pessimistic"][0], cases["base"][0], cases["optimistic"][0]
    st.markdown(
        escape_dollars(
            f"**Projected business value:** {low} to {high} net per year for the two simulated properties "
            f"(base case {base}). This is a **projection from stated assumptions**, not a measured result; see the "
            "[business case](https://github.com/vamsialladev/hotel-ops-assistant/blob/main/docs/BUSINESS_CASE.md)."
        )
    )

st.divider()
st.subheader("Architecture")
# A static file from this repo (no dynamic text), so it is safe to render as HTML; st.html strips inline SVG.
svg = " ".join(
    (ui.HERE / "architecture.svg").read_text(encoding="utf-8").split()
)  # one line: Markdown ends HTML at blank lines
st.markdown(svg, unsafe_allow_html=True)
st.markdown(
    """
**What happens when staff ask a question**
1. **Check the input:** strip control characters, enforce the length limit, the per-session limit and the daily cap.
2. **Scope check:** a question that matches nothing in the hotel's documents is refused without calling the API.
3. **Search:** only the selected property's documents plus the brand-wide ones; ranked by keywords (and, in hybrid
   mode, by meaning), fused, top 5 passages kept.
4. **Generate:** Claude gets the rules, the numbered passages and the question, and streams a short answer that cites
   every fact, or refuses. Earlier turns are never sent, so each answer stands on the documents alone.
5. **Check:** every number must appear in a cited source (otherwise a visible warning); refund, safety and
   repeated-complaint questions get a "Check with a manager" note quoting the rule.
6. **Log:** tokens, timing, cost estimate, refusals and grounding flags go to a private log for the owner.
"""
)

st.subheader("How quality is measured")
metric_rows = [
    ["Retrieval (strict)", "The exact passage with the answer is in the top 5, not just the right document"],
    ["Answer accuracy", "Required facts present, forbidden claims absent, wrong facts in the question corrected"],
    ["Citation accuracy", "The answer cites the document that actually contains the answer"],
    ["Numeric grounding", "Every number in the answer appears in a cited source"],
    ["Correct refusals", "Questions the documents can't answer, and off-topic ones, are refused"],
    ["Scope check", "Off-topic questions blocked before the API; answerable questions never blocked"],
    ["Escalation rules", "The right 'Check with a manager' rule fires, and stays quiet when it shouldn't"],
    ["Speed and cost", "Time to first word and full answer (p50/p95), cost per 1,000 questions"],
]
st.html(table_html(["Metric", "What it checks"], metric_rows))
if report:
    st.caption(
        f"Latest eval for this setup: {report['retrieval']['n']} answerable questions plus must-refuse and off-topic "
        f"cases, {report.get('runs', 1)} runs, {model_name(report['model'])}. Citation accuracy "
        f"{report['citation']['pct']}%, numeric grounding {report['grounding']['pct']}%, correct refusals "
        f"{report['refusals']['pct']}%, time to first word p95 {ui.fmt_seconds(report.get('ttft', {}).get('p95'))}."
    )

st.subheader("Model choice: Claude Haiku 4.5 vs 5.5")
pair = paired(["claude-haiku-4-5-20251001", "claude-haiku-5-5"])
if pair:
    old, new = pair["claude-haiku-4-5-20251001"], pair["claude-haiku-5-5"]

    def cell(r, key, fmt):
        return fmt(r[key]) if key in r else "–"

    rows = [
        [label, cell(old, key, fmt), cell(new, key, fmt)]
        for label, key, fmt in [
            ("Answer accuracy", "answer_accuracy", lambda v: f"{v['pct']}%"),
            ("Citation accuracy", "citation", lambda v: f"{v['pct']}%"),
            ("Numeric grounding", "grounding", lambda v: f"{v['pct']}%"),
            ("Correct refusals", "refusals", lambda v: f"{v['pct']}%"),
            ("Full answer, p95", "latency", lambda v: f"{v['p95']:.2f}s"),
            ("Cost per 1,000 questions", "cost_per_1000", lambda v: f"${v:.2f}"),
        ]
    ]
    st.html(table_html(["", "Claude Haiku 4.5", "Claude Haiku 5.5 (shipped)"], rows))
    st.caption(
        f"Same {old['retrieval']['n']}-question eval and settings for both, hybrid retrieval, "
        f"{old.get('runs', 1)} runs each. Quality is equal or slightly better with 5.5 (a difference of about one "
        "question), at about a fifth of the cost and a little more latency."
    )

st.subheader("Helping users ask")
visitor, before = latest_visitor(mode), latest_visitor(mode, baseline=True)
if visitor:
    change = f", up from {before['first_question_success']:.0%} before this work" if before else ""
    st.html(
        f'<div class="hoa-callout"><b>First-question success: {visitor["first_question_success"]:.0%}</b>{change}. '
        f"Of {visitor['questions']} questions a visitor might type first, without seeing any examples "
        f"({MODE_LABEL[visitor['mode']]}, real answers, {esc(visitor['date'])}): in-scope questions answered with a "
        f"citation {visitor['in_scope_answered']:.0%}, out-of-scope questions refused "
        f"{visitor['out_of_scope_refused']:.0%}, greetings and off-topic input handled "
        f"{visitor['greetings_handled']:.0%} / {visitor['off_topic_handled']:.0%}.</div>"
    )
st.markdown(
    """
- **In-app guidance:** a three-step "How to use" strip, a "What this demo knows" panel generated from the indexed
  documents, good-question examples and topic chips, on first visit and after every New conversation.
- **Curated, always-answerable suggestions:** every example, follow-up and "Did you mean" question comes from a
  reviewed list, and a test checks each one retrieves its topic and gets a real answer.
- **Recovery instead of a dead end:** a refused question gets the closest curated questions ("Did you mean"), ranked
  by keyword retrieval; with nothing close, the most popular questions. Topic chips are always one tap away.
- **Greetings and off-topic input:** "hi", "thanks" or "what can you do?" get an instant reply with examples and
  don't use a question; gibberish or unrelated questions get a polite scope message, never a raw refusal.
- **Follow-ups at no extra cost:** two or three related questions, chosen by the topic of the cited document
  section. No extra AI call, and never a question already asked.
- **Why curated, not AI-generated:** a front-desk tool should only suggest questions it is known to answer
  correctly. Generated suggestions can't be tested in advance, can invent policies, and cost an API call each time.
"""
)

st.subheader("Safety and security")
st.markdown(
    """
- **Property isolation:** search is filtered to the selected hotel plus brand-wide documents (unit-tested).
- **Refuses rather than guesses:** a fixed refusal when the documents don't answer; off-topic questions are blocked.
- **Grounding check:** numbers not found in the cited sources are flagged on screen.
- **Prompt injection:** document text is treated as data; a planted "waive all fees" note is in the eval and ignored.
- **Wrong facts in questions:** if a question states a wrong fee or time, the answer corrects it from the sources.
- **Cost caps:** per-session and daily question limits; off-topic questions cost nothing.
- **Output escaping:** answers, documents and questions are shown as plain text, never as HTML.
- **Private logs and admin:** usage logs are git-ignored; the admin page is password-protected with a lockout.
"""
)

st.subheader("Known limitations")
st.markdown(
    """
- The embedding model is English-only, so a Spanish question isn't matched to the right passage (documented, not fixed).
- Scanned PDFs are flagged for OCR, not read. The beach resort's fire safety document is one of them.
- The public demo's password gate is demo protection, not real sign-in; roles and per-property access come in Project 4.
- The eval questions were written by the same person who wrote the documents, which flatters the scores.
"""
)
st.subheader("Learn more")
decisions = b.links.get("decisions")
st.html(
    f'<p class="hoa-links">{ui.link_row()} · '
    f'<a href="{esc(decisions)}" target="_blank" rel="noopener noreferrer">Decision log</a></p>'
)
st.caption(f"Answers are written by {model_name(LLM_MODEL)}.")
ui.footer()
