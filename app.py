"""Staff-facing web app:  streamlit run app.py

Pages live in views/ and stay thin; the logic is in src/ and unit-tested.
"""

from pathlib import Path

import codeguard

updated = codeguard.refresh(Path(__file__).parent)  # after an in-place update, never mix old and new modules

import streamlit as st  # noqa: E402

if updated:
    st.cache_resource.clear()  # cached objects (the search index) were built by the old code

from src.config import admin_password  # noqa: E402
from views import components as ui  # noqa: E402

b = ui.brand()
st.set_page_config(page_title=b.name, page_icon=ui.asset(b.icon), layout="wide", initial_sidebar_state="auto")
ui.inject_css()
st.logo(ui.asset(b.logo), icon_image=ui.asset("assets/logo-icon.svg"), size="large")

pages = [
    st.Page("views/assistant.py", title="Assistant", icon=":material/support_agent:", default=True),
    st.Page("views/insights.py", title="Insights", icon=":material/insights:"),
    st.Page("views/library.py", title="Document library", icon=":material/folder_open:"),
    st.Page("views/how_it_works.py", title="How it works", icon=":material/schema:"),
    st.Page("views/about.py", title="Disclaimer and privacy", icon=":material/policy:", url_path="privacy"),
]
# Owner-only page: doesn't exist unless ADMIN_PASSWORD is set, and stays out of the menu until unlocked.
if admin_password():
    gate = st.session_state.get("admin_gate")
    unlocked = bool(gate and gate.unlocked)
    pages.append(
        st.Page(
            "views/admin.py",
            title="Admin",
            icon=":material/admin_panel_settings:",
            url_path="admin",
            visibility="visible" if unlocked else "hidden",
        )
    )

page = st.navigation(pages)
ui.app_started()  # remembered once per server start, for the Admin page's uptime
ui.startup_checks()  # logs any missing required secret by name, once per server start
with ui.error_boundary(page.title):  # no page ever shows Streamlit's crash screen or a traceback
    page.run()
