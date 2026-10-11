"""The owner's request log: what one usage record means, and the list and detail views on the Admin page.

Pure functions over the usage and feedback logs, so they're unit-tested without Streamlit. Records written by
older versions of the app are missing fields; every view shows those as "not recorded", never a blank or a crash.
"""

import hashlib
import json
from datetime import date

SCHEMA_VERSION = 2  # 1 (implicit): before 1.5.0, no answer, citations, follow-ups or outcome
NOT_RECORDED = "not recorded"
QUESTION_PREVIEW = 60

# outcome -> label shown in the Result column (the dot is the colored badge; dataframes can't style per cell
# in both themes, an emoji dot reads the same in light and dark)
RESULTS = {
    "answered": "🟢 Answered",
    "refused": "🟠 Refused",
    "off_topic": "🟡 Off-topic",
    "greeting": "🔵 Greeting",
    "error": "🔴 Error",
    "cap": "🟣 Cap",
}
REFUSAL_REASONS = {
    "not_in_documents": "Not in the documents: the model found no answer in the retrieved passages",
    "off_topic": "Off-topic: stopped by the scope check before the API (no API call)",
    "daily_cap": "Daily question cap reached (no API call)",
    "session_cap": "Session question limit reached (no API call)",
}
CAPS = ("daily_cap", "session_cap")


def outcome_of(record: dict) -> str:
    """answered | refused | off_topic | greeting | error | cap. Uses the stored outcome when there is one, and
    works it out for older records from kind, error, refused and pre_api."""
    if record.get("outcome") in RESULTS:
        return record["outcome"]
    error = record.get("error")
    if error in CAPS:
        return "cap"
    if error:
        return "error"
    kind = record.get("kind")
    if kind == "greeting":
        return "greeting"
    if kind == "scope" or (kind is None and record.get("pre_api") and record.get("refused")):
        return "off_topic"
    if kind == "refusal" or record.get("refused"):
        return "refused"
    return "answered"


def refusal_reason(record: dict) -> str | None:
    """Code for why there was no answer (a key of REFUSAL_REASONS), or None."""
    if record.get("refusal_reason"):
        return record["refusal_reason"]
    outcome = outcome_of(record)
    if outcome == "cap":
        return record.get("error")
    if outcome == "off_topic":
        return "off_topic"
    if outcome == "refused":
        return "not_in_documents"
    return None


def request_id(record: dict) -> str:
    """The record's ID. Records from before request IDs get a stable one made from their time and question."""
    rid = record.get("request_id") or record.get("turn_id")
    if rid:
        return str(rid)
    seed = f"{record.get('time')}|{record.get('property')}|{record.get('question')}"
    return "old-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]


def feedback_index(feedback_rows: list) -> dict:
    """request_id -> the latest feedback for it (older feedback records call it turn_id)."""
    out = {}
    for f in feedback_rows:
        rid = f.get("request_id") or f.get("turn_id")
        if rid:
            out[str(rid)] = f
    return out


def feedback_label(f: dict | None) -> str:
    if not f:
        return ""
    return "👍" if f.get("helpful") else "👎"


def short_time(value) -> str:
    return str(value or "")[:19].replace("T", " ") or NOT_RECORDED


def preview(text, limit: int = QUESTION_PREVIEW) -> str:
    text = " ".join(str(text or "").split())
    if not text:
        return NOT_RECORDED
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def fmt_seconds(record: dict, key: str) -> str:
    """ "1.73 s"; "–" when there was no API call to time; "not recorded" when an older record lacks it."""
    v = record.get(key)
    if v is not None:
        return f"{v:.2f} s"
    return "–" if record.get("pre_api") or outcome_of(record) in ("cap", "greeting", "off_topic") else NOT_RECORDED


def fmt_cost(record: dict) -> str:
    v = record.get("cost_usd")
    return NOT_RECORDED if v is None else f"${v:.5f}"


def list_rows(usage_rows: list, feedback_rows: list) -> list[dict]:
    """One row per request for the Admin table, newest first. Anything an older record lacks shows
    "not recorded"."""
    fb = feedback_index(feedback_rows)
    rows = []
    for r in reversed(usage_rows):
        rid = request_id(r)
        outcome = outcome_of(r)
        rows.append(
            {
                "id": rid,
                "time": short_time(r.get("time")),
                "property": r.get("property") or NOT_RECORDED,
                "result": RESULTS[outcome],
                "outcome": outcome,
                "question": preview(r.get("question")),
                "full_question": str(r.get("question") or ""),
                "total": fmt_seconds(r, "total_s"),
                "cost": fmt_cost(r),
                "feedback": feedback_label(fb.get(rid)),
            }
        )
    return rows


def day_of(row: dict) -> date | None:
    try:
        return date.fromisoformat(row["time"][:10])
    except (KeyError, TypeError, ValueError):
        return None


def filter_requests(
    rows: list,
    start: date | None = None,
    end: date | None = None,
    prop: str | None = None,
    outcomes: list | None = None,
    feedback: str = "any",
    errors_only: bool = False,
    text: str = "",
) -> list:
    """Filters for the Admin table. feedback: "any" | "up" | "down". text: case-insensitive, in the question."""
    out = []
    needle = " ".join(text.split()).lower()
    for r in rows:
        day = day_of(r)
        if (start or end) and day is None:
            continue
        if start and day < start or end and day > end:
            continue
        if prop and r["property"] != prop:
            continue
        if outcomes and r["outcome"] not in outcomes:
            continue
        if feedback == "up" and r["feedback"] != "👍" or feedback == "down" and r["feedback"] != "👎":
            continue
        if errors_only and r["outcome"] != "error":
            continue
        if needle and needle not in r["full_question"].lower():
            continue
        out.append(r)
    return out


def selected_id(shown: list, selection) -> str | None:
    """The request ID of the selected table row. `selection` is the dataframe's selection state
    ({"selection": {"rows": [i]}}) or None; an index outside the shown rows selects nothing."""
    try:
        rows = selection["selection"]["rows"]
    except (KeyError, TypeError):
        return None
    if not rows or not isinstance(rows[0], int) or not 0 <= rows[0] < len(shown):
        return None
    return shown[rows[0]]["id"]


def table_key(filters: tuple, limit: int) -> str:
    """Widget key for the Admin table. It changes with the filters and page size, so a new set of rows always
    starts with no row selected (a stale selection could otherwise point at a different request)."""
    return "requests_" + hashlib.sha1(repr((filters, limit)).encode("utf-8")).hexdigest()[:10]


def find(usage_rows: list, rid: str) -> dict | None:
    for r in reversed(usage_rows):
        if request_id(r) == rid:
            return r
    return None


def value(record: dict, key: str, fmt=None):
    """A field for display: "not recorded" when the record doesn't have it (older schema or not captured)."""
    if key not in record or record[key] is None:
        return NOT_RECORDED
    return fmt(record[key]) if fmt else record[key]


def details(record: dict, feedback_rows: list) -> dict:
    """Everything the Request details dialog shows, with "not recorded" for anything an older record lacks."""
    rid = request_id(record)
    outcome = outcome_of(record)
    reason = refusal_reason(record)
    f = feedback_index(feedback_rows).get(rid)
    has_answer = record.get("answer") is not None
    retrieved = record.get("retrieved")
    cited_ids = {(c.get("source"), c.get("section")) for c in record.get("citations") or []}
    passages = None
    if retrieved is not None:
        passages = [
            {
                "source": p.get("source") or NOT_RECORDED,
                "section": p.get("section") or NOT_RECORDED,
                "score": p.get("score"),
                "cited": (
                    p["cited"]
                    if "cited" in p
                    else ((p.get("source"), p.get("section")) in cited_ids if "citations" in record else None)
                ),
            }
            for p in retrieved
        ]
    return {
        "id": rid,
        "schema_version": record.get("schema_version", 1),
        "time": short_time(record.get("time")),
        "property": record.get("property") or NOT_RECORDED,
        "session_id": record.get("session_id") or NOT_RECORDED,
        "question": record.get("question") or NOT_RECORDED,
        "outcome": outcome,
        "result": RESULTS[outcome],
        "refusal_reason": REFUSAL_REASONS.get(reason, reason) if reason else None,
        "answer": record["answer"] if has_answer else None,
        "citations": record.get("citations"),  # None = not recorded; [] = none cited
        "follow_ups": record.get("follow_ups"),
        "passages": passages,
        "model": record.get("model") or ("none (no API call)" if record.get("pre_api") else NOT_RECORDED),
        "mode": value(record, "mode"),
        "ttft_s": record.get("ttft_s"),
        "total_s": record.get("total_s"),
        "tokens_in": record.get("tokens_in"),
        "tokens_out": record.get("tokens_out"),
        "cost_usd": record.get("cost_usd"),
        "grounding_flag": record.get("grounding_flag"),
        "ungrounded": record.get("ungrounded"),
        "escalations": record.get("escalations"),
        "error": record.get("error"),
        "error_message": record.get("error_message"),
        "feedback": f,
        "raw": record,
    }


def to_jsonl(rows: list) -> str:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)


def request_json(record: dict, feedback_rows: list) -> str:
    """One request as a downloadable JSON document: the log record plus its linked feedback."""
    f = feedback_index(feedback_rows).get(request_id(record))
    return json.dumps({"request": record, "feedback": f}, ensure_ascii=False, indent=2)


def log_since(usage_rows: list) -> str | None:
    times = [str(r.get("time")) for r in usage_rows if r.get("time")]
    return short_time(min(times)) if times else None
