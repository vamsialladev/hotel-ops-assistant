"""'Share this conversation': a read-only link with the conversation inside the URL. Nothing is stored on a server.

The turns (question, how it was understood, property, answer, source labels) are JSON, zlib-compressed and
base64url-encoded into `?share=...`. Personal data is checked first with the same redaction as the logs
(src/pii.py): anything it finds is replaced in the shared copy, and the visitor is told what was replaced.
Opening a link only decodes and displays it (escaped like any answer); it never calls the API.
"""

import base64
import binascii
import json
import zlib

from src.pii import scrub_text

VERSION = 1
MAX_TURNS = 12  # the last 12 turns are shared
MAX_TEXT = 1200  # characters per question or answer
MAX_TOKEN = 8000  # characters in the encoded link parameter (browsers and servers accept far longer URLs)
FINDINGS = {"[email]": "an email address", "[phone]": "a phone number", "[card]": "a card number", "[name]": "a name"}


def turn_payload(turn) -> dict:
    result = turn.result or {}
    sources = []
    for c in result.get("citations", []):
        label = c.get("section") or ""
        sources.append(f"{c.get('source', '')} › {label}" if label else c.get("source", ""))
    return {
        "q": turn.question[:MAX_TEXT],
        "u": (turn.rewritten or "")[:MAX_TEXT],
        "p": turn.property,
        "a": (result.get("answer") or turn.error or "")[:MAX_TEXT],
        "s": sources[:6],
        "k": turn.kind,
    }


def redact(turns: list[dict]) -> tuple[list[dict], list[str]]:
    """Returns the turns with personal data replaced, and what kinds were found (for the visitor)."""
    found, out = set(), []
    for t in turns:
        clean = dict(t)
        for key in ("q", "u", "a"):
            original = t.get(key) or ""
            scrubbed = scrub_text(original)
            found |= {label for marker, label in FINDINGS.items() if marker in scrubbed and marker not in original}
            clean[key] = scrubbed
        out.append(clean)
    return out, sorted(found)


def encode(payload: list[dict]) -> str:
    raw = json.dumps({"v": VERSION, "t": payload}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(zlib.compress(raw, 9)).decode("ascii").rstrip("=")


def make_token(turns: list) -> tuple[str | None, list[str]]:
    """(token, personal-data kinds replaced). None when there is nothing to share or the link would be too long
    even with fewer turns."""
    payload = [turn_payload(t) for t in turns if t.kind != "greeting"][-MAX_TURNS:]
    payload, found = redact(payload)
    while payload:
        token = encode(payload)
        if len(token) <= MAX_TOKEN:
            return token, found
        payload = payload[1:]  # drop the oldest turn until it fits
    return None, found


def decode(token: str) -> list[dict] | None:
    """The shared turns, or None for a damaged, foreign or oversized link. Every field is re-checked."""
    if not token or len(token) > MAX_TOKEN:
        return None
    try:
        raw = zlib.decompressobj().decompress(base64.urlsafe_b64decode(token + "=" * (-len(token) % 4)), 200_000)
        data = json.loads(raw.decode("utf-8"))
    except (ValueError, binascii.Error, zlib.error, UnicodeDecodeError):
        return None
    if not isinstance(data, dict) or data.get("v") != VERSION or not isinstance(data.get("t"), list):
        return None
    turns = []
    for t in data["t"][:MAX_TURNS]:
        if not isinstance(t, dict) or not isinstance(t.get("q"), str) or not isinstance(t.get("a"), str):
            return None
        turns.append(
            {
                "q": t["q"][:MAX_TEXT],
                "u": str(t.get("u") or "")[:MAX_TEXT],
                "p": str(t.get("p") or ""),
                "a": t["a"][:MAX_TEXT],
                "s": [str(s)[:200] for s in t.get("s", []) if isinstance(s, str)][:6],
                "k": str(t.get("k") or "answer"),
            }
        )
    return turns or None


def share_url(base_url: str, token: str) -> str:
    """The app's own address with only the share parameter."""
    base = (base_url or "").split("?", 1)[0].split("#", 1)[0]
    return f"{base}?share={token}"
