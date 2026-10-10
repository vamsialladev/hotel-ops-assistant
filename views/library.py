"""Page 3: Document library, with status and data-quality issues."""

import streamlit as st

from src.display import badge_html, format_date, safe_markdown, table_html
from src.library import INDEXED, NEEDS_OCR, SUPERSEDED, inventory, quality_summary
from views import components as ui

b, retriever = ui.brand(), ui.retriever()
ui.header(
    "Document library",
    "Every document the assistant reads, what happened to it, and the data problems found along the way.",
    "For managers and engineers",
)

docs = inventory(retriever.chunks)
summary = quality_summary(docs)
ui.tiles(
    [
        (str(summary["documents"]), "Documents", "Across both properties and brand-wide"),
        (str(summary["indexed"]), "Indexed", "Searchable by the assistant"),
        (str(summary["superseded"]), "Superseded", "Outdated, excluded on purpose"),
        (str(summary["needs_ocr"]), "Need OCR", "Scanned images with no text"),
        (str(summary["chunks"]), "Searchable passages", "Split by section heading"),
    ]
)

TONE = {INDEXED: "ok", SUPERSEDED: "muted", NEEDS_OCR: "warn"}
rows = [
    [
        b.property_name(d["property"]),
        d["title"],
        d["type"],
        format_date(d["effective"]) or "–",
        badge_html(d["status"], TONE.get(d["status"], "muted")),
        str(d["chunks"]),
    ]
    for d in docs
]
st.html(table_html(["Property", "Document", "Type", "Effective", "Status", "Passages"], rows, raw_columns={4}))

st.subheader("Data quality issues found")
for name, issue in summary["issues"]:
    st.markdown(f"- **{safe_markdown(name)}**: {issue}")
st.caption("Documents are synthetic, written to mirror real hotel operations.")
ui.footer()
