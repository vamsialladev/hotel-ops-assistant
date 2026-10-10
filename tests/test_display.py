from src.display import (
    badge_html,
    format_date,
    mask_personal_data,
    quote_markdown,
    safe_markdown,
    scope_label,
    section_name,
    source_chip_html,
    source_label,
    table_html,
)

CHUNK = {
    "property": "beach-resort",
    "source": "beach-resort/policies.md",
    "section": "Beach Resort - Property Policies > Pets",
    "title": "Beach Resort policies",
    "effective": "2026-03-01",
    "text": "Pet fee is $75 per stay.",
}


def test_dollar_amounts_are_not_turned_into_latex():
    # Bug: "$50 per night ... capped at $200" rendered as math because of the two '$' signs.
    assert safe_markdown("$50 per night, capped at $200") == "\\$50 per night, capped at \\$200"


def test_already_escaped_dollars_are_not_double_escaped():
    assert safe_markdown("costs \\$45") == "costs \\$45"


def test_html_in_answers_and_questions_is_shown_as_text():
    shown = safe_markdown('<script>alert("x")</script><b>bold</b>')
    assert "<script>" not in shown and "<b>" not in shown
    assert "&lt;script&gt;" in shown


def test_html_in_source_chips_is_escaped():
    evil = {**CHUNK, "title": "<img src=x onerror=alert(1)>", "section": "<script>x</script>"}
    chip = source_chip_html(evil, 1)
    assert "<img" not in chip and "<script>" not in chip
    assert "&lt;img" in chip


def test_table_cells_are_escaped_except_badge_columns():
    html = table_html(["Doc", "Status"], [["<b>x</b>", badge_html("Indexed", "ok")]], raw_columns={1})
    assert "&lt;b&gt;x&lt;/b&gt;" in html
    assert '<span class="hoa-badge hoa-badge-ok">Indexed</span>' in html


def test_badge_text_is_escaped_and_unknown_tones_are_muted():
    assert badge_html("<x>", "nope") == '<span class="hoa-badge hoa-badge-muted">&lt;x&gt;</span>'


def test_source_label_and_chip_details():
    assert source_label(CHUNK) == "Beach Resort policies › Pets"
    chip = source_chip_html(CHUNK, 2)
    assert "Property-specific · effective 1 Mar 2026" in chip and ">2<" in chip


def test_brand_wide_label_and_missing_date():
    shared = {**CHUNK, "property": "shared", "effective": None}
    assert scope_label(shared) == "Brand-wide"
    assert "effective" not in source_chip_html(shared, 1)


def test_dates_and_sections():
    assert format_date("2026-01-15") == "15 Jan 2026"
    assert format_date("not-a-date") is None and format_date(None) is None
    assert section_name({"section": "Page 3"}) == "Page 3"


def test_document_quotes_are_escaped_blockquotes():
    assert quote_markdown("Fee is $75.\n\n<b>x</b>") == "> Fee is \\$75.\n>\n> &lt;b&gt;x&lt;/b&gt;"


def test_personal_data_is_masked_for_public_pages():
    text = "Refund for jane.doe@example.com, call +1 305 555 0142, card 4111 1111 1111 1111"
    masked = mask_personal_data(text)
    assert "jane.doe" not in masked and "555" not in masked and "4111" not in masked
    assert "[email]" in masked and "[phone]" in masked and "[number]" in masked


def test_prices_and_times_are_not_masked():
    assert mask_personal_data("Is it $45 at 10:00 PM for room 214?") == "Is it $45 at 10:00 PM for room 214?"


def test_model_names_are_readable():
    from src.display import model_name

    assert model_name("claude-haiku-4-5-20251001") == "Claude Haiku 4.5"
    assert model_name("claude-haiku-5-5") == "Claude Haiku 5.5" and model_name(None) == "unknown"


def test_bar_list_scales_and_escapes():
    from src.display import bar_list_html

    html = bar_list_html([("Pets", 4), ("<b>x</b>", 1)])
    assert "width:100%" in html and "width:25%" in html and "&lt;b&gt;" in html
    assert bar_list_html([]) == ""
