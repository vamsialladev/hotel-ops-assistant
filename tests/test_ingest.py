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
