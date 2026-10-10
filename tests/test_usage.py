import json
import logging

from src.errors import mask_secrets
from src.usage import append_jsonl, estimate_cost, log_usage, read_jsonl


def test_cost_estimate_from_prices_per_million():
    assert estimate_cost(1_000_000, 0, 0.10, 0.50) == 0.10
    assert round(estimate_cost(899, 150, 0.10, 0.50), 8) == round((899 * 0.10 + 150 * 0.50) / 1e6, 8)


def test_cost_is_none_without_prices():
    assert estimate_cost(100, 10, None, 0.5) is None and estimate_cost(100, 10, 0.1, None) is None


def test_logs_are_trimmed_to_the_most_recent_entries(tmp_path):
    path = tmp_path / "usage.jsonl"
    for i in range(12):
        append_jsonl(path, {"i": i}, max_entries=5)
    assert [r["i"] for r in read_jsonl(path)] == [7, 8, 9, 10, 11]


def test_damaged_lines_are_skipped(tmp_path):
    path = tmp_path / "usage.jsonl"
    path.write_text('{"a": 1}\nnot json\n{"a": 2}\n', encoding="utf-8")
    assert read_jsonl(path) == [{"a": 1}, {"a": 2}]
    assert read_jsonl(tmp_path / "missing.jsonl") == []


def test_usage_goes_to_file_and_stdout_without_question_text(tmp_path, caplog):
    path = tmp_path / "usage.jsonl"
    with caplog.at_level(logging.INFO, logger="hotel_ops.usage"):
        record = log_usage({"property": "beach-resort", "question": "Dogs for Jane Doe?", "tokens_in": 9}, path=path)
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["question"] == "Dogs for Jane Doe?" and "time" in record
    assert "Jane Doe" not in caplog.text and '"property": "beach-resort"' in caplog.text


def test_api_keys_are_masked_in_error_details():
    assert mask_secrets("bad key sk-ant-not-a-real-key used") == "bad key sk-ant-*** used"
