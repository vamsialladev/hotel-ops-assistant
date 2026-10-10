from src.ingest import display_title, document_name, load_chunks
from src.library import INDEXED, NEEDS_OCR, SUPERSEDED, inventory, quality_summary, readable_name


def test_every_document_is_listed_with_the_right_status():
    docs = {d["file"]: d for d in inventory(load_chunks())}
    assert docs["beach-resort/policies.md"]["status"] == INDEXED
    assert docs["beach-resort/policies_2024_OLD.md"]["status"] == SUPERSEDED
    assert docs["beach-resort/fire_safety_scan.pdf"]["status"] == NEEDS_OCR
    assert docs["beach-resort/policies_2024_OLD.md"]["chunks"] == 0
    assert docs["beach-resort/policies.md"]["effective"] == "2026-03-01"
    assert docs["mountain-lodge/front_desk_notes.txt"]["type"] == "Staff notes"


def test_quality_issues_are_found():
    docs = inventory(load_chunks())
    summary = quality_summary(docs)
    assert summary["superseded"] == 1 and summary["needs_ocr"] == 1
    assert summary["chunks"] == len(load_chunks())
    issues = dict(summary["issues"])
    notes = " ".join(i for name, i in summary["issues"] if name == "Mountain Lodge front desk notes")
    assert "instructions to an AI" in notes
    assert "Beach Resort fire safety procedure" in issues
    assert all("/" not in name for name in issues)  # readable names, never file paths


def test_display_titles():
    assert display_title("beach-resort/policies.md", {"title": "Beach Resort - Property Policies"}) == (
        "Beach Resort policies"
    )
    assert display_title("mountain-lodge/front_desk_notes.txt", {}) == "Front desk notes"
    assert display_title("shared/x.md", {"title": "Housekeeping SOP"}) == "Housekeeping SOP"
    assert display_title("beach-resort/spa_menu.md", {"title": "Spa Menu - Beach Resort"}) == "Spa Menu"
    old = {"title": "Beach Resort - Property Policies (2024)"}
    assert display_title("beach-resort/policies_2024_OLD.md", old) == "Beach Resort policies (2024)"


def test_one_readable_name_per_document():
    assert document_name("mountain-lodge/front_desk_notes.txt", {}) == "Mountain Lodge front desk notes"
    assert document_name("beach-resort/spa_menu.md", {"title": "Spa Menu - Beach Resort"}) == "Beach Resort spa menu"
    assert document_name("shared/housekeeping_sop.md", {"title": "Housekeeping SOP"}) == "Housekeeping SOP"
    assert readable_name("beach-resort/fire_safety_scan.pdf") == "Beach Resort fire safety procedure"
    assert readable_name("missing/file.md") == "missing/file.md"
