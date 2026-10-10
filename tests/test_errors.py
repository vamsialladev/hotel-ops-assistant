import anthropic
import httpx2
import pytest

from src.errors import UNAVAILABLE, classify, private_detail

REQUEST = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


def status_error(cls, code, message="error"):
    return cls(message, response=httpx2.Response(code, request=REQUEST), body=None)


@pytest.mark.parametrize(
    "exc,code",
    [
        (status_error(anthropic.RateLimitError, 429), "rate_limit"),
        (status_error(anthropic.AuthenticationError, 401), "auth"),
        (status_error(anthropic.PermissionDeniedError, 403), "permission"),
        (status_error(anthropic.BadRequestError, 400, "Your credit balance is too low"), "credit_exhausted"),
        (status_error(anthropic.InternalServerError, 500), "server_error"),
        (status_error(anthropic.BadRequestError, 400, "invalid request"), "api_400"),
        (anthropic.APIConnectionError(request=REQUEST), "connection"),
        (TypeError("Could not resolve authentication method. Expected one of api_key"), "missing_key"),
        (RuntimeError("something else"), "unexpected"),
    ],
)
def test_errors_are_classified_for_the_private_log(exc, code):
    assert classify(exc) == code


def test_visitor_message_reveals_nothing():
    assert UNAVAILABLE == "The demo is temporarily unavailable. Please try again later."


def test_private_detail_is_short_and_masks_keys():
    detail = private_detail(RuntimeError("key sk-ant-abc123 " + "x" * 500))
    assert detail.startswith("RuntimeError: key sk-ant-***") and len(detail) == 300
