"""Shared guardrails, request tracing and the cross-app ops log (hotel-ai-platform), wired for this app.

    trace = ops.start(session_id)                  one trace per question; the reference shows on errors
    v = ops.check_question(question)               input guardrails, before the rewrite, retrieval and the model
    o = ops.check_answer(answer, hits, citations, question)   output guardrails, after the model
    ops.finish(trace, record)                      one ops_request_log row + the trace's spans, PII removed first

This sits next to the app's own request log (src/usage.py, src/store.py), which keeps its detailed record and
its Admin request list. The ops tables are the same in every hotel app, so one Admin view, one daily failure check
and one runbook work across all of them (hotel-ai-platform decision 1).
"""

import os
from functools import lru_cache
from pathlib import Path

from hotelplatform import guardrails, jsonlog, oplog, tracing, version

from src.config import (
    ALERT_DAILY_COST_USD,
    APP_NAME,
    BUDGET_P95_S,
    LLM_MODEL,
    MAX_QUESTION_CHARS,
    RETENTION_DAYS,
    database_url,
)
from src.generate import NOT_FOUND

ROOT = Path(__file__).resolve().parent.parent
APP_VERSION = "1.7.0"
MONTHLY_COST_CAP_USD = float(os.getenv("MONTHLY_COST_CAP_USD", "10.00"))

# The app's own tone for the guardrail messages (the defaults say "the hotel"; this app knows the property).
MESSAGES = {
    "sensitive_pii": "Please don't type card or ID numbers here. I only need your question about the hotel.",
    "data_exfiltration": "I can't share other guests' details or system information. Ask me about hotel policies.",
}
INPUT_POLICY = guardrails.InputPolicy(max_chars=MAX_QUESTION_CHARS, languages=("en", "es"), messages=MESSAGES)
# Answers cite passages; a refusal ("I can't answer that from this hotel's documents") needs no citation.
# Numbers are flagged, not blocked: src/grounding.py already shows ungrounded numbers to staff (Project 1).
OUTPUT_POLICY = guardrails.OutputPolicy(
    require_citation=True,
    numbers="flag",
    promises="block",
    pii_leak="redact",
    refusal_markers=(*guardrails.OutputPolicy().refusal_markers, NOT_FOUND.lower()[:40], "no puedo responder"),
)
# Statuses for the shared table, from this app's record outcome and error codes.
CAPS = {"session_cap", "daily_cap"}
TIMEOUTS = {"timeout"}


@lru_cache(maxsize=1)
def store() -> oplog.OpsStore:
    """One per process. Nothing connects until the first row is written (Neon stays asleep for bots)."""
    return oplog.OpsStore(APP_NAME, url=database_url() or "", log_dir=ROOT / "logs", retention_days=RETENTION_DAYS)


@lru_cache(maxsize=1)
def running_version() -> str:
    return version.version_string(APP_VERSION, ROOT)


def configure_logs() -> None:
    jsonlog.configure(APP_NAME, running_version())


def start(session_id: str | None):
    """`with ops.start(session_id) as trace:` around one question; guardrail verdicts and spans attach to it."""
    return tracing.new_trace(APP_NAME, session_id=session_id)


def check_question(question: str) -> guardrails.Verdict:
    return guardrails.check_input(question, INPUT_POLICY)


def passage_texts(hits: list) -> list[str]:
    return [h.get("text") or "" for h in hits or []]


def check_answer(answer: str, hits: list, citations: list, question: str) -> guardrails.Verdict:
    return guardrails.check_output(
        answer, OUTPUT_POLICY, sources=passage_texts(hits), citations=[c.get("source") for c in citations or []],
        input_text=question,
    )  # fmt: skip


def status_of(record: dict) -> str:
    """ok | refused | blocked | error | timeout | capped, from the app's usage record."""
    if record.get("guardrail"):
        return "blocked"
    error = record.get("error")
    if error in CAPS:
        return "capped"
    if error in TIMEOUTS:
        return "timeout"
    if error:
        return "error"
    if record.get("kind") in ("refusal", "scope"):
        return "refused"
    return "ok"


def safety_flags(trace) -> list[str]:
    """Every guardrail flag and block reason recorded on the trace, e.g. "pii_redacted:EMAIL_ADDRESS",
    "input:prompt_injection", "output:policy_promise"."""
    flags = set()
    for span in trace.spans if trace is not None else []:
        if span.name.startswith("guardrails."):
            stage = span.name.split(".", 1)[1]
            flags.update(span.attributes.get("flags") or [])
            flags.update(f"{stage}:{r}" for r in span.attributes.get("reasons") or [])
    return sorted(flags)


def finish(trace, record: dict, source: str = "user") -> bool:
    """Write the ops row for one request. Never raises, never blocks (the writer thread does the I/O)."""
    if trace is None:
        return False
    try:
        status = status_of(record)
        row = oplog.request_row(
            trace,
            request_type=record.get("kind") or "answer",
            status=status,
            latency_ms=round((record.get("total_s") or 0) * 1000, 1) or trace.elapsed_ms(),
            error_type=record.get("guardrail") or record.get("error"),
            error_message=record.get("error_message"),
            tokens_in=record.get("tokens_in") or 0,
            tokens_out=record.get("tokens_out") or 0,
            cost_usd=record.get("cost_usd") or 0.0,
            model=record.get("model"),
            tool_calls=[],
            sources=[f"{h.get('source')} › {h.get('section')}" for h in record.get("retrieved", [])],
            safety_flags=safety_flags(trace),
            source=source,
            version=running_version(),
            data={
                "property": record.get("property"),
                "question": record.get("question"),
                "rewritten": record.get("rewritten_question"),
                "answer": record.get("answer"),
                "escalations": record.get("escalations"),
                "request_id": record.get("request_id"),
            },  # fmt: skip
        )
        latency = row["latency_ms"] or 0
        if status == "ok" and latency > BUDGET_P95_S * 1000:
            jsonlog.slow_request(latency, BUDGET_P95_S * 1000, trace_id=trace.trace_id)
        if status == "capped":
            jsonlog.cap_hit(record.get("error"), trace_id=trace.trace_id)
        return store().submit(trace, row)
    except Exception:
        return False


def feedback(trace_id: str | None, helpful: bool, reason: str | None) -> None:
    if trace_id:
        store().feedback(trace_id, "up" if helpful else "down", reason or "")


def dependencies(retrieval_mode: str = "keyword") -> dict[str, str]:
    """For the Admin System health panel and the startup log. No network calls: what is configured."""
    return {
        "anthropic": "configured" if os.getenv("ANTHROPIC_API_KEY") else "missing key",
        "database": store().health()["status"],
        "embeddings": "loaded (hybrid search)" if retrieval_mode == "hybrid" else "not used (keyword search)",
        "model": LLM_MODEL,
    }


def caps() -> dict[str, float]:
    return {"cost_cap_day": ALERT_DAILY_COST_USD, "cost_cap_month": MONTHLY_COST_CAP_USD}
