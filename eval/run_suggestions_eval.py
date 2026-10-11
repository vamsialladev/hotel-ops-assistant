"""Every curated question (welcome examples, topic examples, follow-ups, "Did you mean" and popular
questions all come from data/suggestions.toml) must work: retrieve a passage of its own topic, and with
--answers get a real cited answer, not a refusal.

python -m eval.run_suggestions_eval --bm25-only            # retrieval only (free); also a unit test
python -m eval.run_suggestions_eval --bm25-only --answers  # real answers (uses the API, ~80 calls)
"""

import argparse
import sys
from datetime import datetime

from src.config import REPORTS_DIR
from src.suggestions import Catalog, load_catalog, topic_of


def cases(catalog: Catalog, props: list[str]) -> list[tuple[str, str, str]]:
    """(property, topic id, question) for every topic example; good examples are topic examples too."""
    return [(p, t.id, q) for t in catalog.topics for p in props for q in t.examples.get(p, [])]


def retrieves_topic(retriever, prop: str, topic_id: str, question: str, catalog: Catalog) -> bool:
    hits = retriever.search(question, prop)
    return any((t := topic_of(h, catalog)) is not None and t.id == topic_id for h in hits)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--bm25-only", action="store_true")
    parser.add_argument("--answers", action="store_true")
    args = parser.parse_args(argv)

    from src import service
    from src.retrieve import Retriever

    retriever = Retriever(use_embeddings=not args.bm25_only)
    catalog = load_catalog()
    rows, failed = [], []
    for prop, topic_id, question in cases(catalog, retriever.properties()):
        ok_retrieval = retrieves_topic(retriever, prop, topic_id, question, catalog)
        answered = None
        if args.answers:
            from src.generate import answer

            prep = service.prepare(retriever, question, prop)
            answered = (not prep["blocked"]) and answer(question, prop, prep["hits"])["found"]
        ok = ok_retrieval and answered is not False
        rows.append((prop, topic_id, question, ok_retrieval, answered))
        if not ok:
            failed.append(f"{prop}: {question}")

    good = sum(1 for *_, r, a in rows if r and a is not False)
    print(f"Curated questions ({retriever.mode}{', answers' if args.answers else ''}): {good}/{len(rows)} work")
    for f in failed:
        print("  FAIL", f)
    if args.answers:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        name = f"{datetime.now():%Y-%m-%d_%H%M}_suggestions_{retriever.mode}_answers.md"
        lines = [f"# Curated questions ({retriever.mode}, real answers): {good}/{len(rows)} work", ""]
        lines += ["| Property | Topic | Question | Retrieves its topic | Answered |", "|---|---|---|---|---|"]
        lines += [f"| {p} | {t} | {q} | {'yes' if r else 'NO'} | {'yes' if a else 'NO'} |" for p, t, q, r, a in rows]
        (REPORTS_DIR / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"  saved eval/reports/{name}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
