"""Scope check: refuse clearly off-topic questions before calling the API.

Works in both retrieval modes:
- keyword-only: no passage shares a single keyword with the question -> out of scope
- hybrid:       no keyword match AND no passage is at least `min_similarity` similar in meaning

The hybrid threshold was tuned on the eval so that no answerable question is blocked (the
"jacket" question has no keyword match but a similarity of 0.47). Anything that passes this
check still goes to Claude, whose prompt refuses questions outside the hotel's documents.
"""

SCOPE_MESSAGE = (
    "I can only help with this hotel's policies, fees, amenities and procedures, and I couldn't find "
    "anything about this in the hotel's documents. If it's a hotel question, please check with a manager."
)


def in_scope(signals: dict, min_similarity: float) -> bool:
    if signals["keyword_matches"] > 0:
        return True
    best = signals.get("best_similarity")
    return best is not None and best >= min_similarity
