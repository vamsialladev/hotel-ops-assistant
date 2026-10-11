"""Shared Streamlit building blocks: cached resources, header, banner, footer, tiles.

Only static markup or `esc()`-escaped values go into HTML here.
"""

import functools
import logging
import time
from contextlib import contextmanager
from pathlib import Path

import streamlit as st

from src.branding import DEMO_LABEL, load_branding
from src.chat import ChatState
from src.config import LOG_DIR, MAX_QUESTIONS_PER_DAY, ROOT, USE_EMBEDDINGS
from src.display import esc
from src.errors import PAGE_ERROR, is_control_flow, record_error
from src.limits import DailyCounter
from src.secrets_check import log_missing

HERE = Path(__file__).parent
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def brand():
    """Re-read when branding.toml changes: a push updates the file in place on Streamlit Cloud."""
    from src.branding import BRANDING_FILE

    return _brand(BRANDING_FILE.stat().st_mtime_ns if BRANDING_FILE.exists() else 0)


@st.cache_resource(show_spinner=False)
def _brand(mtime_ns: int):
    return load_branding()


def retriever():
    """The search index for the current documents. Keyed by their fingerprint, so a push that changes a
    document rebuilds the index without a reboot (Streamlit Cloud keeps the old one on disk)."""
    from src.ingest import docs_fingerprint

    return _retriever(docs_fingerprint(USE_EMBEDDINGS))


@st.cache_resource(show_spinner="Starting up the assistant. The first load can take up to a minute.")
def _retriever(fingerprint: str):
    from src.ingest import build_index, index_is_current
    from src.retrieve import Retriever

    # The index isn't committed to git, so it's built on first start and whenever the documents change.
    if not index_is_current(USE_EMBEDDINGS):
        build_index(use_embeddings=USE_EMBEDDINGS)
    return Retriever(use_embeddings=USE_EMBEDDINGS)


@st.cache_resource(show_spinner=False)
def daily_counter():
    return DailyCounter(LOG_DIR / "daily_count.json", MAX_QUESTIONS_PER_DAY)


@st.cache_resource(show_spinner=False)
def app_started() -> float:
    """Time of the first page view since the server started (cached for the life of the process)."""
    return time.time()


@st.cache_resource(show_spinner=False)
def startup_checks() -> list[str]:
    """Once per server start: log each missing required secret by name (never a value)."""
    return log_missing()


@contextmanager
def error_boundary(page: str):
    """Top-level guard for every page: an unexpected exception shows a friendly message, is recorded for the
    owner (Admin page + stdout), and never reaches Streamlit's crash screen. st.rerun / st.stop pass through."""
    try:
        yield
    except BaseException as exc:
        if is_control_flow(exc):
            raise
        logging.getLogger("hotel_ops.app").exception("page error on %s", page)
        record_error(page, exc)
        st.error(PAGE_ERROR, icon=":material/error:")


def safe_callback(page: str):
    """Same guard for button callbacks, which Streamlit runs before the page script."""

    def wrap(fn):
        @functools.wraps(fn)
        def guarded(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                logging.getLogger("hotel_ops.app").exception("callback error on %s", page)
                record_error(page, exc)
                st.session_state.callback_error = True

        return guarded

    return wrap


def asset(path: str) -> str:
    """Branding asset path, resolved against the project root so it works from any working directory."""
    return str(ROOT / path)


def chat_state() -> ChatState:
    if "chat" not in st.session_state:
        st.session_state.chat = ChatState()
    return st.session_state.chat


def scroll_to_top():
    """Scroll the page back to the top (Streamlit keeps chat pages scrolled to the bottom)."""
    # A fixed script, never user input (st.iframe runs it with access to the app page).
    st.iframe(
        "<script>const d = window.parent.document; d.querySelectorAll('*').forEach("
        "el => { if (el.scrollTop > 0) el.scrollTop = 0; }); window.parent.scrollTo(0, 0);</script>",
        height=1,
    )


FOCUS_SCRIPT = """<script>/* {nonce} */
const d = window.parent.document, w = window.parent;
const sidebar = d.querySelector('[data-testid="stSidebar"]');
const overlay = w.matchMedia("(max-width: 767px)").matches;  // phones: the sidebar covers the page
if ({close} && overlay && sidebar && sidebar.getAttribute("aria-expanded") === "true") {{
  // The button itself: clicking its wrapper div does nothing.
  const b = d.querySelector('[data-testid="stSidebarCollapseButton"] button')
    || d.querySelector('[data-testid="stSidebarCollapseButton"]');
  if (b) b.click();
}}
const touch = w.matchMedia("(pointer: coarse)").matches;
if (!touch || {close}) setTimeout(() => {{
  const box = d.querySelector('[data-testid="stChatInputTextArea"]');
  if (box && !box.disabled) box.focus({{preventScroll: true}});
}}, 300);
</script>"""


def focus_chat_input(close_sidebar: bool = False):
    """Put the cursor in the chat input. With close_sidebar (after "New conversation"), first close the
    sidebar when it covers the page on a phone: it stayed open over the input, so taps never reached it.
    After an answer, phones are left alone so the keyboard doesn't cover the answer."""
    nonce = st.session_state["focus_nonce"] = st.session_state.get("focus_nonce", 0) + 1  # re-runs the script
    with st.sidebar:  # a fixed script, never user input
        st.iframe(FOCUS_SCRIPT.format(nonce=nonce, close="true" if close_sidebar else "false"), height=1)


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
