"""Answer grading. Pure functions, so they're unit-tested without calling the API.

Checks for each answer:
- correct:      required facts present, forbidden phrases absent (or a correct refusal)
- citation_ok:  the expected source document is among the cited sources
- grounded:     every number in the answer (prices, times, limits) appears in a cited source
                or in the question; a cheap, deterministic faithfulness check
"""

import re

CITATION = re.compile(r"\[\d+\]")
NUMBER = re.compile(r"\d[\d,]*(?::\d{2})?")


def numbers_in(text: str) -> set[str]:
    """Numbers normalized so '$1,200' -> '1200' and '2:00' -> '2' (matches '2 PM')."""
    text = CITATION.sub(" ", text)
    out = set()
    for raw in NUMBER.findall(text):
        n = raw.replace(",", "")
        if n.endswith(":00"):
            n = n[:-3]
        out.add(n)
    return out


def grade(item: dict, result: dict) -> dict:
    answer = result["answer"]
    refused = not result["found"]

    if item.get("unanswerable"):
        return {"correct": refused, "citation_ok": None, "grounded": None, "ungrounded": []}

    lower = answer.lower()
    has_required = all(s.lower() in lower for s in item.get("must_contain", []))
    has_forbidden = any(s.lower() in lower for s in item.get("must_not_contain", []))
    correct = (not refused) and has_required and not has_forbidden

    cited = result["citations"]
    citation_ok = item.get("expected_source") in {c["source"] for c in cited}

    allowed = numbers_in(" ".join(c["text"] for c in cited)) | numbers_in(item["question"])
    ungrounded = sorted(numbers_in(answer) - allowed)
    grounded = (not refused) and bool(cited) and not ungrounded

    return {"correct": correct, "citation_ok": citation_ok, "grounded": grounded, "ungrounded": ungrounded}
