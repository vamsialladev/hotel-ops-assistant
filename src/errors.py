"""Map API and runtime errors to one friendly message for visitors and a detailed, private log line.

Visitors never see raw exceptions, stack traces or which limit was hit on the API side.
"""

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
