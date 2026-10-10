"""Turn answers, sources and visitor text into safe display strings. Pure functions, no Streamlit.

Two rules:
- Text shown with st.markdown goes through `safe_markdown`: '$' is escaped (Streamlit treats
  text between two '$' as LaTeX, which turned "$50 ... $200" into code-formatted math) and HTML
  is escaped so a question or answer containing <script> is shown as plain text.
- Text placed inside our own HTML (chips, badges, tables) goes through `html.escape`.
"""

import html
import re
from datetime import date

from src.config import SHARED

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(?<!\d)(?:\+?\d[\s().-]?){9,15}\d(?!\d)")
CARD = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
DOC_ICON = (
    '<svg class="hoa-chip-icon" viewBox="0 0 24 24" width="14" height="14" aria-hidden="true">'
    '<path fill="currentColor" d="M6 2h8l6 6v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zm7 1.5V9h5.5'
    'L13 3.5zM8 13h8v1.5H8V13zm0 3.5h8V18H8v-1.5z"/></svg>'
)


def escape_dollars(text: str) -> str:
    return text.replace("\\$", "$").replace("$", "\\$")


def safe_markdown(text: str) -> str:
    """Escape HTML and '$' so model output, document text and visitor input render as plain text."""
    return escape_dollars(html.escape(text, quote=False))


def esc(text) -> str:
    """For text inside our own HTML snippets."""
    return html.escape(str(text), quote=True)


def mask_personal_data(text: str) -> str:
    """Best-effort masking of emails, card numbers and phone numbers before showing visitor
    questions on a public page. Not a full redaction system (planned for Project 4)."""
    text = EMAIL.sub("[email]", text)
    text = CARD.sub("[number]", text)
    return PHONE.sub("[phone]", text)


def property_name(prop: str, names: dict | None = None) -> str:
    """'beach-resort' -> 'Beach Resort' unless branding provides a name."""
    if names and prop in names:
        return names[prop]
    if prop == SHARED:
        return "Brand-wide"
    return prop.replace("-", " ").title()


def scope_label(chunk: dict) -> str:
    return "Brand-wide" if chunk["property"] == SHARED else "Property-specific"


def format_date(iso: str | None) -> str | None:
    """'2026-03-01' -> '1 Mar 2026'. Returns None for missing or malformed dates."""
    if not iso:
        return None
    try:
        d = date.fromisoformat(iso)
    except ValueError:
        return None
    return f"{d.day} {d.strftime('%b %Y')}"


def section_name(chunk: dict) -> str:
    """Last part of the heading path: 'Beach Resort - Property Policies > Pets' -> 'Pets'."""
    return chunk.get("section", "").split(">")[-1].strip() or "Document"


def source_label(chunk: dict) -> str:
    """'Beach Resort policies › Pets' style label for a source chip."""
    title = chunk.get("title") or chunk["source"].rsplit("/", 1)[-1]
    return f"{title} › {section_name(chunk)}"


def source_chip_html(chunk: dict, number: int) -> str:
    effective = format_date(chunk.get("effective"))
    meta = scope_label(chunk) + (f" · effective {effective}" if effective else "")
    return (
        '<span class="hoa-chip">'
        f"{DOC_ICON}"
        f'<span class="hoa-chip-n">{number}</span>'
        f'<span class="hoa-chip-label">{esc(source_label(chunk))}</span>'
        f'<span class="hoa-chip-meta">{esc(meta)}</span>'
        "</span>"
    )


def quote_markdown(text: str) -> str:
    """Document text as a Markdown blockquote, escaped."""
    return "\n".join("> " + safe_markdown(line) if line.strip() else ">" for line in text.splitlines())


def badge_html(text: str, tone: str) -> str:
    tone = tone if tone in {"ok", "warn", "error", "muted"} else "muted"
    return f'<span class="hoa-badge hoa-badge-{tone}">{esc(text)}</span>'


def table_html(columns: list[str], rows: list[list[str]], raw_columns: set[int] = frozenset()) -> str:
    """Simple HTML table. Cells are escaped unless their column index is in `raw_columns`
    (used only for cells we built ourselves with `badge_html`)."""
    head = "".join(f"<th>{esc(c)}</th>" for c in columns)
    body = "".join(
        "<tr>" + "".join(f"<td>{cell if i in raw_columns else esc(cell)}</td>" for i, cell in enumerate(row)) + "</tr>"
        for row in rows
    )
    table = f'<table class="hoa-table"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'
    return f'<div class="hoa-table-wrap">{table}</div>'


def model_name(model_id: str | None) -> str:
    """'claude-haiku-4-5-20251001' -> 'Claude Haiku 4.5'."""
    m = re.match(r"claude-([a-z]+)-(\d+)-(\d+)", model_id or "")
    return f"Claude {m.group(1).title()} {m.group(2)}.{m.group(3)}" if m else (model_id or "unknown")


def bar_list_html(items: list[tuple[str, int]]) -> str:
    """Horizontal bars as plain HTML: labels wrap instead of being cut off, and colors follow the theme."""
    if not items:
        return ""
    top = max(n for _, n in items) or 1
    rows = "".join(
        f'<div class="hoa-bar"><div class="hoa-bar-label">{esc(label)}</div><div class="hoa-bar-track">'
        f'<div class="hoa-bar-fill" style="width:{max(4, round(100 * n / top))}%"></div></div>'
        f'<div class="hoa-bar-n">{int(n)}</div></div>'
        for label, n in items
    )
    return f'<div class="hoa-bars">{rows}</div>'
