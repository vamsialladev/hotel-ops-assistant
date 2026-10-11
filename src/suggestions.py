"""Curated questions that always work: welcome-screen examples, topic chips, follow-ups, "Did you mean" and
the popular-question fallback. Pure functions over data/suggestions.toml and the index; no API calls.

Topics come from the documents: a topic is shown for a property only when the index has a passage for
it (by section heading or whole document) in that property's or the shared documents.
"""

import functools
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from rank_bm25 import BM25Okapi

from src.config import ROOT, SHARED
from src.display import section_name
from src.retrieve import expand_query, tokenize

CATALOG = ROOT / "data" / "suggestions.toml"


@dataclass(frozen=True)
class Topic:
    id: str
    label: str
    icon: str
    sections: tuple = ()
    sources: tuple = ()
    examples: dict = field(default_factory=dict, hash=False, compare=False)

    def covers(self, chunk: dict) -> bool:
        return chunk["source"] in self.sources or section_name(chunk) in self.sections


@dataclass(frozen=True)
class Catalog:
    topics: tuple
    good: dict = field(hash=False, compare=False)


def parse_catalog(data: dict) -> Catalog:
    topics = tuple(
        Topic(
            id=t["id"],
            label=t["label"],
            icon=t.get("icon", ""),
            sections=tuple(t.get("sections", ())),
            sources=tuple(t.get("sources", ())),
            examples={p: list(qs) for p, qs in t.get("examples", {}).items()},
        )
        for t in data["topics"]
    )
    return Catalog(topics=topics, good={p: list(qs) for p, qs in data["good"].items()})


def load_catalog(path: Path = CATALOG) -> Catalog:
    """Re-read when the file changes (a push to a running app updates it in place)."""
    return _load_catalog(str(path), Path(path).stat().st_mtime_ns)


@functools.cache
def _load_catalog(path: str, mtime_ns: int) -> Catalog:
    return parse_catalog(tomllib.loads(Path(path).read_text(encoding="utf-8")))


def norm(question: str) -> str:
    return " ".join(question.lower().split()).rstrip("?.! ")


def topic_of(chunk: dict, catalog: Catalog) -> Topic | None:
    return next((t for t in catalog.topics if t.covers(chunk)), None)


def property_chunks(chunks: list, prop: str) -> list:
    return [c for c in chunks if c["property"] in (prop, SHARED)]


def available_topics(chunks: list, prop: str, catalog: Catalog) -> list[Topic]:
    """Topics with at least one indexed passage for this property and at least one example."""
    mine = property_chunks(chunks, prop)
    return [t for t in catalog.topics if t.examples.get(prop) and any(t.covers(c) for c in mine)]


def knows(chunks: list, prop: str, catalog: Catalog) -> list[str]:
    """ "What this demo knows": topic labels generated from the indexed documents, in catalog order."""
    return [t.label for t in available_topics(chunks, prop, catalog)]


def all_examples(prop: str, catalog: Catalog) -> list[str]:
    """Every curated question for a property, good examples first, without duplicates."""
    seen, out = set(), []
    for q in catalog.good.get(prop, []) + [q for t in catalog.topics for q in t.examples.get(prop, [])]:
        if norm(q) not in seen:
            seen.add(norm(q))
            out.append(q)
    return out


def popular(prop: str, catalog: Catalog, asked=(), n: int = 3) -> list[str]:
    """The good examples (they're also the most-clicked); topped up from the rest if some were asked."""
    done = {norm(q) for q in asked}
    return [q for q in all_examples(prop, catalog) if norm(q) not in done][:n]


def follow_ups(cited: list, prop: str, catalog: Catalog, asked=(), n: int = 3) -> list[str]:
    """2-3 related questions, chosen by the topics of the cited passages (first citation first), never one
    already asked in this conversation. Empty when nothing was cited."""
    done = {norm(q) for q in asked}
    out = []
    for chunk in cited:
        topic = topic_of(chunk, catalog)
        for q in topic.examples.get(prop, []) if topic else []:
            if norm(q) not in done and q not in out:
                out.append(q)
    if cited and len(out) < 2:  # a small topic: top up with popular questions
        out += [q for q in popular(prop, catalog, list(asked) + out, n) if q not in out]
    return out[:n]


@functools.cache
def _example_index(prop: str, catalog: Catalog):
    examples = all_examples(prop, catalog)
    return examples, BM25Okapi([tokenize(expand_query(q)) for q in examples])


def did_you_mean(question: str, prop: str, catalog: Catalog, asked=(), n: int = 3) -> list[str]:
    """The curated questions closest to a refused question, by keyword retrieval score (no API call).
    Empty when none shares a keyword."""
    tokens = tokenize(expand_query(question))
    if not tokens:
        return []
    examples, index = _example_index(prop, catalog)
    scores = index.get_scores(tokens)
    done = {norm(q) for q in asked} | {norm(question)}
    ranked = sorted((i for i, s in enumerate(scores) if s > 0), key=lambda i: -scores[i])
    return [examples[i] for i in ranked if norm(examples[i]) not in done][:n]


def recovery(question: str, prop: str, catalog: Catalog, asked=(), n: int = 3) -> tuple[str, list[str]]:
    """After a refusal or off-topic input: ("did_you_mean", closest) topped up to n with popular questions,
    or ("popular", the most popular) when nothing is close. Always n questions that work."""
    close = did_you_mean(question, prop, catalog, asked, n)
    if not close:
        return "popular", popular(prop, catalog, asked, n)
    extra = [q for q in popular(prop, catalog, list(asked) + close, n) if q not in close]
    return "did_you_mean", (close + extra)[:n]


def hints(prop: str, catalog: Catalog) -> list[str]:
    """Short chat-input hints ("Try: What time is breakfast served?"), shortest questions first."""
    return [f"Try: {q}" for q in sorted(all_examples(prop, catalog), key=len) if len(q) <= 40]
