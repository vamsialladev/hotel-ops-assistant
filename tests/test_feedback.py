import json

from src.feedback import log_feedback, summary

RESULT = {"answer": "Yes, up to 40 lbs [1].", "found": True, "citations": [{"source": "beach-resort/policies.md"}]}


def test_feedback_is_appended_and_summarized(tmp_path):
    path = tmp_path / "feedback.jsonl"
    log_feedback("Dogs?", "beach-resort", RESULT, helpful=True, path=path)
    log_feedback("Dogs?", "beach-resort", RESULT, helpful=False, path=path)
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert [r["helpful"] for r in rows] == [True, False]
    assert rows[0]["sources"] == ["beach-resort/policies.md"]
    assert summary(path) == {"total": 2, "helpful": 1, "rate": 0.5}


def test_summary_with_no_feedback(tmp_path):
    assert summary(tmp_path / "none.jsonl")["total"] == 0


def test_thumbs_down_reason_is_saved_and_unknown_reasons_dropped(tmp_path):
    path = tmp_path / "feedback.jsonl"
    log_feedback("Dogs?", "beach-resort", RESULT, helpful=False, path=path, reason="Wrong property")
    log_feedback("Dogs?", "beach-resort", RESULT, helpful=False, path=path, reason="<script>")
    log_feedback("Dogs?", "beach-resort", RESULT, helpful=True, path=path, reason="Wrong fact")
    assert [json.loads(line)["reason"] for line in path.read_text().splitlines()] == ["Wrong property", None, None]
