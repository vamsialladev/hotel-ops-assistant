"""Shared Streamlit building blocks: cached resources, header, banner, footer, tiles.

Only static markup or `esc()`-escaped values go into HTML here.
"""

import logging
from pathlib import Path

import streamlit as st

from src.branding import DEMO_LABEL, load_branding
from src.chat import ChatState
from src.config import INDEX_DIR, LOG_DIR, MAX_QUESTIONS_PER_DAY, ROOT, USE_EMBEDDINGS
from src.display import esc
from src.limits import DailyCounter

HERE = Path(__file__).parent
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@st.cache_resource(show_spinner=False)
def brand():
    return load_branding()


@st.cache_resource(show_spinner="Starting up the assistant. The first load can take up to a minute.")
def retriever():
    from src.ingest import build_index
    from src.retrieve import Retriever

    # The index isn't committed to git, so it's built on first start (e.g. on Streamlit Cloud).
    if not (INDEX_DIR / "chunks.json").exists():
        build_index(use_embeddings=USE_EMBEDDINGS)
    return Retriever(use_embeddings=USE_EMBEDDINGS)


@st.cache_resource(show_spinner=False)
def daily_counter():
    return DailyCounter(LOG_DIR / "daily_count.json", MAX_QUESTIONS_PER_DAY)


def asset(path: str) -> str:
    """Branding asset path, resolved against the project root so it works from any working directory."""
    return str(ROOT / path)


def chat_state() -> ChatState:
    if "chat" not in st.session_state:
        st.session_state.chat = ChatState()
    return st.session_state.chat


def scroll_to_top():
    """Scroll the page back to the top (Streamlit keeps chat pages scrolled to the bottom)."""
    from streamlit.components.v1 import html

    html(
        "<script>const d = window.parent.document; d.querySelectorAll('*').forEach("
        "el => { if (el.scrollTop > 0) el.scrollTop = 0; }); window.parent.scrollTo(0, 0);</script>",
        height=0,
    )


def inject_css():
    st.html(f"<style>{(HERE / 'style.css').read_text(encoding='utf-8')}</style>")


def banner():
    st.html(f'<div class="hoa-banner" role="note">{esc(DEMO_LABEL)}</div>')


def header(title: str, subtitle: str = "", eyebrow: str = ""):
    banner()
    parts = [f'<p class="hoa-eyebrow">{esc(eyebrow)}</p>' if eyebrow else ""]
    parts.append(f'<h1 class="hoa-title">{esc(title)}</h1>')
    if subtitle:
        parts.append(f'<p class="hoa-subtitle">{esc(subtitle)}</p>')
    st.html("".join(parts))


def tiles(items: list[tuple[str, str, str]]):
    """Metric tiles: (value, label, help text)."""
    cells = "".join(
        f'<div class="hoa-tile"><div class="hoa-tile-value">{esc(v)}</div>'
        f'<div class="hoa-tile-label">{esc(label)}</div>'
        + (f'<div class="hoa-tile-help">{esc(help_text)}</div>' if help_text else "")
        + "</div>"
        for v, label, help_text in items
    )
    st.html(f'<div class="hoa-tiles">{cells}</div>')


def empty_state(title: str, body: str):
    st.html(f'<div class="hoa-empty"><b>{esc(title)}</b>{esc(body)}</div>')


def link_row() -> str:
    """Case study, GitHub and LinkedIn links, opening in a new tab."""
    links = brand().links
    items = [("case_study", "Case study"), ("github", "GitHub"), ("linkedin", "LinkedIn")]
    return " · ".join(
        f'<a href="{esc(links[key])}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>'
        for key, label in items
        if links.get(key)
    )


def footer():
    author = brand().links.get("author", "Vamsi Alla")
    st.html(
        '<footer class="hoa-footer">'
        f"<p>Built by {esc(author)} · Simulated client engagement with synthetic hotel documents</p>"
        f"<p>{link_row()}</p>"
        "</footer>"
    )
    st.page_link("views/about.py", label="Disclaimer and privacy", icon=":material/policy:")


def fmt_pct(value) -> str:
    return "–" if value is None else f"{value:.0%}"


def fmt_seconds(value) -> str:
    return "–" if value is None else f"{value:.1f}s"
