"""One question, start to finish, without Streamlit: scope check and retrieval before the API,
then grounding, escalation and the usage record after it. The app page only wires these together.
"""

from src.config import LLM_MAX_TOKENS, LLM_MODEL, PRICE_IN_PER_M, PRICE_OUT_PER_M, SCOPE_MIN_SIMILARITY, TOP_K
from src.display import section_name
from src.escalation import escalations
from src.grounding import ungrounded_numbers
from src.scope import SCOPE_MESSAGE, in_scope
from src.usage import estimate_cost


def prepare(retriever, question: str, prop: str, k: int = TOP_K, min_similarity: float = SCOPE_MIN_SIMILARITY):
    """Retrieval plus the scope check. `blocked` means: answer without calling the API."""
    signals = retriever.signals(question, prop)
    if not in_scope(signals, min_similarity):
        return {"blocked": True, "hits": [], "signals": signals}
    hits = retriever.search(question, prop, k=k)
    return {"blocked": not hits, "hits": hits, "signals": signals}


def blocked_result() -> dict:
    return {
        "answer": SCOPE_MESSAGE,
        "found": False,
        "citations": [],
        "usage": {"input_tokens": 0, "output_tokens": 0},
        "scope_blocked": True,
    }


def finalize(question: str, prop: str, result: dict) -> dict:
    """Add the runtime checks the page displays: ungrounded numbers, manager notes and the topic."""
    refused = not result["found"]
    cited = result["citations"]
    return {
        **result,
        "ungrounded": [] if refused else ungrounded_numbers(result["answer"], cited, question),
        "escalations": [r.id for r in escalations(question, prop, refused=refused)],
        "topic": section_name(cited[0]) if cited else None,
    }


def usage_record(
    question: str,
    prop: str,
    mode: str,
    result: dict | None = None,
    hits: list | None = None,
    ttft: float | None = None,
    total: float | None = None,
    pre_api: bool = False,
    error: str | None = None,
    turn_id: str | None = None,
    source: str = "typed",
    kind: str | None = None,
    session_id: str | None = None,
    first: bool = False,
    topic_group: str | None = None,
    price_in: float | None = PRICE_IN_PER_M,
    price_out: float | None = PRICE_OUT_PER_M,
) -> dict:
    usage = (result or {}).get("usage", {"input_tokens": 0, "output_tokens": 0})
    tokens_in, tokens_out = usage["input_tokens"], usage["output_tokens"]
    return {
        "turn_id": turn_id,
        "session_id": session_id,
        "first": first,
        "source": source,
        "kind": kind or ("refusal" if result and not result["found"] else "answer" if result else None),
        "property": prop,
        "question": question,
        "model": None if pre_api else LLM_MODEL,
        "max_tokens": LLM_MAX_TOKENS,
        "mode": mode,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd": estimate_cost(tokens_in, tokens_out, price_in, price_out),
        "ttft_s": None if ttft is None else round(ttft, 3),
        "total_s": None if total is None else round(total, 3),
        "refused": bool(result) and not result["found"],
        "pre_api": pre_api,
        "grounding_flag": bool(result and result.get("ungrounded")),
        "ungrounded": (result or {}).get("ungrounded", []),
        "escalations": (result or {}).get("escalations", []),
        "topic": (result or {}).get("topic"),
        "topic_group": topic_group,
        "retrieved": [{"source": h["source"], "section": h["section"], "score": h.get("score")} for h in hits or []],
        "error": error,
    }
