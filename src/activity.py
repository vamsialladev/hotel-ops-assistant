"""Aggregate the usage and feedback logs for the Insights (managers) and Admin (owner) pages."""

import statistics
from collections import Counter

from src.chat import SOURCES
from src.display import mask_personal_data


def percentile(values: list, p: float) -> float | None:
    values = sorted(v for v in values if v is not None)
    if not values:
        return None
    return values[min(len(values) - 1, int(round(p * (len(values) - 1))))]


def answered(rows: list) -> list:
    """Questions that got an answer or a refusal (errors, blocked-by-limit rows and greetings excluded)."""
    return [r for r in rows if not r.get("error") and r.get("kind") != "greeting"]


def source_label(row: dict) -> str:
    return SOURCES.get(row.get("source") or "typed", "Typed")


def insights(usage_rows: list, feedback_rows: list, top: int = 8, gap_limit: int = 25) -> dict:
    rows = answered(usage_rows)
    topics = Counter(r.get("topic_group") or r["topic"] for r in rows if r.get("topic_group") or r.get("topic"))
    how_asked = Counter("Typed" if (r.get("source") or "typed") == "typed" else "Suggestion" for r in rows)
    by_source = Counter(source_label(r) for r in rows)
    disliked = [
        {
            "time": f.get("time", ""),
            "property": f.get("property", ""),
            "question": mask_personal_data(f.get("question", ""))[:160],
            "source": source_label(f),
            "reason": f.get("reason") or "",
        }
        for f in reversed(feedback_rows)
        if not f.get("helpful") and (f.get("source") or "typed") != "typed"
    ]
    reasons = Counter(r["reason"] for r in feedback_rows if not r.get("helpful") and r.get("reason"))
    helpful = sum(bool(r.get("helpful")) for r in feedback_rows)

    gaps, seen = [], set()
    for r in reversed(rows):  # most recent first
        # A policy gap: a typed question Claude said the documents don't answer. Off-topic input stopped by the
        # scope check (pre_api) and refused suggestions are not policy gaps.
        if not r.get("refused") or r.get("pre_api") or (r.get("source") or "typed") != "typed":
            continue
        text = mask_personal_data(r.get("question", ""))[:160]
        key = (r.get("property"), text.lower())
        if text and key not in seen:
            seen.add(key)
            gaps.append({"time": r.get("time", ""), "property": r.get("property", ""), "question": text})
    return {
        "questions": len(rows),
        "refused": sum(bool(r.get("refused")) for r in rows),
        "feedback": len(feedback_rows),
        "helpful": helpful,
        "helpful_rate": helpful / len(feedback_rows) if feedback_rows else None,
        "reasons": reasons.most_common(),
        "topics": topics.most_common(top),
        "by_property": Counter(r.get("property") for r in rows).most_common(),
        "gaps": gaps[:gap_limit],
        "how_asked": how_asked.most_common(),
        "by_source": by_source.most_common(),
        "disliked_suggestions": disliked[:gap_limit],
    }


def admin_stats(usage_rows: list, feedback_rows: list, today: str) -> dict:
    rows = answered(usage_rows)
    api_rows = [r for r in rows if not r.get("pre_api")]
    totals = [r.get("total_s") for r in api_rows]
    ttfts = [r.get("ttft_s") for r in api_rows]
    costs = [r["cost_usd"] for r in rows if r.get("cost_usd") is not None]
    return {
        "questions_today": sum(1 for r in rows if str(r.get("time", "")).startswith(today)),
        "questions_total": len(rows),
        "api_calls": len(api_rows),
        "blocked_before_api": len(rows) - len(api_rows),
        "tokens_in": sum(r.get("tokens_in") or 0 for r in rows),
        "tokens_out": sum(r.get("tokens_out") or 0 for r in rows),
        "cost_usd": sum(costs) if costs else None,
        "avg_total_s": statistics.mean(measured) if (measured := [t for t in totals if t is not None]) else None,
        "p95_total_s": percentile(totals, 0.95),
        "p95_ttft_s": percentile(ttfts, 0.95),
        "refused": sum(bool(r.get("refused")) for r in rows),
        "grounding_flags": sum(bool(r.get("grounding_flag")) for r in rows),
        "errors": Counter(r["error"] for r in usage_rows if r.get("error")).most_common(),
        "reasons": Counter(
            r["reason"] for r in feedback_rows if not r.get("helpful") and r.get("reason")
        ).most_common(),
    }
