"""Document library: every source document with its status and the data-quality issues found."""

import re
from collections import Counter
from pathlib import Path

from src.config import RAW_DIR
from src.ingest import SUPPORTED, document_meta, document_name, load_pdf_pages, parse_front_matter

TYPES = {".md": "Policy document", ".txt": "Staff notes", ".pdf": "PDF"}
INDEXED, SUPERSEDED, NEEDS_OCR = "Indexed", "Superseded, excluded", "Scanned, needs OCR"
# Text addressed to an AI inside a document: a sign of pasted emails or tampering.
INSTRUCTION_LIKE = re.compile(r"\b(ignore (?:your|all|previous) (?:rules|instructions)|system notice)\b", re.I)


def inventory(chunks: list, raw_dir: Path = RAW_DIR) -> list[dict]:
    counts = Counter(c["source"] for c in chunks)
    docs = []
    for path in sorted(raw_dir.rglob("*")):
        if path.suffix.lower() not in SUPPORTED:
            continue
        rel = path.relative_to(raw_dir).as_posix()
        doc = {
            "property": rel.split("/", 1)[0],
            "file": rel,
            "type": TYPES[path.suffix.lower()],
            "title": "",
            "effective": None,
            "status": INDEXED,
            "chunks": counts.get(rel, 0),
            "issues": [],
        }
        if path.suffix.lower() == ".pdf":
            doc["title"] = document_name(rel, document_meta(path))
            pages = list(load_pdf_pages(path))
            empty = [n for n, text in pages if len(text.strip()) < 30]
            if pages and len(empty) == len(pages):
                doc["status"] = NEEDS_OCR
                doc["issues"].append("Scanned image with no text: not searchable until OCR is run.")
            elif empty:
                doc["issues"].append(f"{len(empty)} of {len(pages)} pages have no text (scanned).")
            text = "\n".join(t for _, t in pages)
            doc["issues"].append("No effective date.")
        else:
            raw = path.read_text(encoding="utf-8")
            meta, text = parse_front_matter(raw)
            doc["title"] = document_name(rel, meta)
            doc["effective"] = meta.get("effective")
            if meta.get("status", "").lower() == "superseded":
                doc["status"] = SUPERSEDED
                doc["issues"].append("Outdated version kept on the shared drive; excluded from search.")
            if not doc["effective"]:
                doc["issues"].append("No effective date.")
        if INSTRUCTION_LIKE.search(text):
            doc["issues"].append("Contains text written as instructions to an AI (treated as data, not commands).")
        docs.append(doc)
    return docs


def quality_summary(docs: list) -> dict:
    status = Counter(d["status"] for d in docs)
    return {
        "documents": len(docs),
        "indexed": status.get(INDEXED, 0),
        "superseded": status.get(SUPERSEDED, 0),
        "needs_ocr": status.get(NEEDS_OCR, 0),
        "chunks": sum(d["chunks"] for d in docs),
        "issues": [(d["title"], issue) for d in docs for issue in d["issues"]],
    }


def readable_name(source: str, raw_dir: Path = RAW_DIR) -> str:
    """Readable name for a document path (for manager notes and policy gaps). Unknown paths are returned
    as-is so nothing silently disappears."""
    path = raw_dir / source
    if not path.is_file():
        return source
    return document_name(source, document_meta(path))
