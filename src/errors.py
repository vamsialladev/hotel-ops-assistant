"""Map API and runtime errors to one friendly message for visitors and a detailed, private log line.

Visitors never see raw exceptions, stack traces or which limit was hit on the API side.
"""

import logging
import re

import anthropic

UNAVAILABLE = "The demo is temporarily unavailable. Please try again later."


def classify(exc: Exception) -> str:
    """Short error code for the private log and the Admin page."""
    if isinstance(exc, anthropic.AuthenticationError):
        return "auth"
    if isinstance(exc, anthropic.PermissionDeniedError):
        return "permission"
    if isinstance(exc, anthropic.RateLimitError):
        return "rate_limit"
    if isinstance(exc, anthropic.APIStatusError):
        message = str(getattr(exc, "message", exc)).lower()
        if "credit balance" in message or "billing" in message:
            return "credit_exhausted"
        if exc.status_code >= 500:
            return "server_error"
        return f"api_{exc.status_code}"
    if isinstance(exc, anthropic.APIConnectionError):
        return "connection"
    message = str(exc).lower()
    if "api_key" in message or "api key" in message or "authentication" in message:
        return "missing_key"
    return "unexpected"


def private_detail(exc: Exception, limit: int = 300) -> str:
    """Error type and message for the owner's logs. Anthropic error messages don't contain the key;
    as a precaution anything that looks like one is masked."""
    text = f"{type(exc).__name__}: {exc}"
    return mask_secrets(text)[:limit]


def mask_secrets(text: str) -> str:
    return re.sub(r"sk-ant-[A-Za-z0-9_\-]+", "sk-ant-***", text)


# ---------- Error log for the owner's Admin page ----------
PAGE_ERROR = "Something went wrong on this page. Please try again; the error was logged for the app owner."
ERRORS_FILE = None  # resolved at call time (tests point it elsewhere): LOG_DIR / "errors.jsonl"
MESSAGE_CHARS = 160


def errors_file():
    from src.config import LOG_DIR

    return ERRORS_FILE or LOG_DIR / "errors.jsonl"


def error_record(page: str, exc: BaseException) -> dict:
    """What gets stored: the page, a short error type and a short, masked message. Never the question text
    or a traceback (those stay in the owner-only stdout logs)."""
    from src.usage import now_iso

    message = " ".join(mask_secrets(str(exc)).split())[:MESSAGE_CHARS]
    return {"time": now_iso(), "page": page, "type": classify(exc), "error": type(exc).__name__, "message": message}


def record_error(page: str, exc: BaseException, path=None) -> dict:
    """Append to the bounded, git-ignored error log and to stdout. Never raises."""
    from src.usage import append_jsonl

    record = error_record(page, exc)
    append_jsonl(path or errors_file(), record)
    logging.getLogger("hotel_ops.errors").error("error %s", record)
    return record


def is_control_flow(exc: BaseException) -> bool:
    """Streamlit's st.rerun / st.stop / page switches raise these; an error boundary must let them through."""
    return type(exc).__name__ in {"RerunException", "StopException", "ScriptControlException"} or not isinstance(
        exc, Exception
    )
