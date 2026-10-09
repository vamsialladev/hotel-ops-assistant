"""Hybrid search: keyword (BM25) + meaning (embeddings), merged with Reciprocal Rank Fusion.
Results are always filtered to the selected property + brand-wide (shared) documents."""

import json
import re

import numpy as np
from rank_bm25 import BM25Okapi

from src.config import EMBED_MODEL, INDEX_DIR, SHARED, TOP_K
from src.ingest import contextual_text

STOPWORDS = set(
    "a an the is are am be can do does did i we our you your to of for in on at and or "
    "what how much many when where which who with it this that my me if".split()
)
# Domain stopwords: words that appear in almost every hotel document and add no signal.
# Found via eval: "guest" in "Can a guest bring their dog?" pulled loyalty docs to the top.
STOPWORDS |= {"guest", "guests", "hotel", "hotels"}


def stem(word: str) -> str:
    """Light stemmer so word forms match: cats->cat, RVs->rv, smoking/smoke->smok, cribs->crib."""
    if word.endswith("ies") and len(word) > 4:
        word = word[:-3] + "y"
    elif word.endswith("ing") and len(word) > 5:
        word = word[:-3]
    elif word.endswith("s") and not word.endswith("ss") and len(word) > 2:
        word = word[:-1]
    if word.endswith("e") and len(word) > 3:
        word = word[:-1]
    return word


def tokenize(text: str):
    return [stem(t) for t in re.findall(r"[a-z0-9$:]+", text.lower()) if t not in STOPWORDS]


class Retriever:
    def __init__(self, use_embeddings: bool = True):
        index_file = INDEX_DIR / "chunks.json"
        if not index_file.exists():
            raise FileNotFoundError("No index found. Run: python -m src.ingest")
        self.chunks = json.loads(index_file.read_text(encoding="utf-8"))
        self.bm25 = BM25Okapi([tokenize(contextual_text(c)) for c in self.chunks])

        self.model, self.vectors = None, None
        if use_embeddings and (INDEX_DIR / "vectors.npy").exists():
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:  # light install: fall back to keyword search
                return
            self.vectors = np.load(INDEX_DIR / "vectors.npy")
            self.model = SentenceTransformer(EMBED_MODEL)

    def properties(self):
        return sorted({c["property"] for c in self.chunks} - {SHARED})

    def search(self, query: str, prop: str, k: int = TOP_K):
        allowed = [i for i, c in enumerate(self.chunks) if c["property"] in (prop, SHARED)]

        bm25_scores = self.bm25.get_scores(tokenize(query))
        # Only passages that match at least one keyword; a zero score is not a match.
        matched = [i for i in allowed if bm25_scores[i] > 0]
        rankings = [sorted(matched, key=lambda i: -bm25_scores[i])]

        if self.model is not None:
            q = self.model.encode([query], normalize_embeddings=True)[0]
            sims = self.vectors @ q
            rankings.append(sorted(allowed, key=lambda i: -sims[i]))

        fused = {}
        for ranking in rankings:
            for rank, i in enumerate(ranking):
                fused[i] = fused.get(i, 0.0) + 1.0 / (60 + rank + 1)

        top = sorted(fused, key=lambda i: -fused[i])[:k]
        return [{**self.chunks[i], "score": round(fused[i], 4)} for i in top]
