"""Guards for .streamlit/config.toml (decisions 19 and 39)."""

import tomllib

from src.config import ROOT

CONFIG = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8"))


def test_file_watcher_stays_on_so_streamlit_cloud_reloads_each_push():
    # With the watcher off, Streamlit Cloud pulled pushes but kept serving the old code.
    assert CONFIG["server"]["fileWatcherType"] != "none"


def test_the_virtualenv_is_never_watched():
    # Watching .venv (PyTorch's thousands of files) hung startup for 5+ minutes on Windows.
    assert {".venv", "venv"} <= set(CONFIG["server"]["folderWatchBlacklist"])


def test_visitors_never_see_tracebacks_or_the_developer_toolbar():
    assert CONFIG["client"]["showErrorDetails"] == "none" and CONFIG["client"]["toolbarMode"] == "minimal"
