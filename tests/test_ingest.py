from src.ingest import load_chunks, normalize_line, split_by_headings


def test_superseded_docs_are_never_indexed():
    sources = {c["source"] for c in load_chunks()}
    assert "beach-resort/policies_2024_OLD.md" not in sources


def test_every_chunk_has_a_property():
    for c in load_chunks():
        assert c["property"] in {"shared", "beach-resort", "mountain-lodge"}


def test_tables_are_never_split():
    body = "# Menu\n| Item | Price |\n|---|---|\n" + "".join(f"| Dish {i} | ${i} |\n" for i in range(200))
    pieces = split_by_headings(body)
    tables = [text for _, text in pieces if "| Dish 0 |" in text]
    assert len(tables) == 1 and "| Dish 199 |" in tables[0]


def test_heading_path_is_kept():
    pieces = split_by_headings("# Policies\n## Pets\nDogs welcome.")
    assert pieces[0][0] == "Policies > Pets"


def test_pdf_headers_and_page_footers_are_removed():
    menu = [c for c in load_chunks() if c["source"] == "beach-resort/restaurant_menu.pdf"]
    assert menu, "restaurant menu PDF should be indexed"
    for c in menu:
        assert "CONFIDENTIAL" not in c["text"]
        assert "Page " not in c["text"]


def test_scanned_pdf_is_skipped_not_indexed_as_garbage():
    sources = {c["source"] for c in load_chunks()}
    assert "beach-resort/fire_safety_scan.pdf" not in sources


def test_footer_normalization():
    assert normalize_line("Page 1 of 3") == normalize_line("Page 2 of 3")


def test_index_fingerprint_changes_with_documents_and_mode(tmp_path):
    from src.ingest import docs_fingerprint, index_is_current

    raw = tmp_path / "raw"
    (raw / "shared").mkdir(parents=True)
    doc = raw / "shared" / "a.md"
    doc.write_text("# A\nOne", encoding="utf-8")
    first = docs_fingerprint(False, raw)
    assert first == docs_fingerprint(False, raw) and first != docs_fingerprint(True, raw)
    doc.write_text("# A\nTwo", encoding="utf-8")
    assert docs_fingerprint(False, raw) != first

    index = tmp_path / "index"
    index.mkdir()
    assert not index_is_current(False, index, raw)  # nothing built yet
    (index / "chunks.json").write_text("[]", encoding="utf-8")
    (index / "fingerprint.txt").write_text(docs_fingerprint(False, raw), encoding="utf-8")
    assert index_is_current(False, index, raw) and not index_is_current(True, index, raw)
    (raw / "shared" / "b.md").write_text("# B\nNew", encoding="utf-8")
    assert not index_is_current(False, index, raw)  # a pushed document triggers a rebuild


def test_the_built_index_is_current_and_drops_stale_vectors():
    from src.config import INDEX_DIR
    from src.ingest import index_is_current

    assert index_is_current(False)  # conftest built a keyword-only index
    assert not (INDEX_DIR / "vectors.npy").exists()
