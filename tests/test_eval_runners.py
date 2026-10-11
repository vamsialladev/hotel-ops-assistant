"""The visitor and curated-question eval runners, end to end on the free keyword index (the model is faked)."""

import json

import pytest

import eval.run_suggestions_eval as suggestions_eval
import eval.run_visitor_eval as visitor_eval
import src.generate
from src.generate import NOT_FOUND


def fake_answer(question, prop, chunks):
    """Cites the first passage and repeats it, or refuses when nothing was retrieved."""
    if not chunks:
        return {"answer": NOT_FOUND, "found": False, "citations": [], "usage": {}}
    return {"answer": chunks[0]["text"] + " [1]", "found": True, "citations": [{**chunks[0], "n": 1}], "usage": {}}


@pytest.fixture
def reports(tmp_path, monkeypatch):
    monkeypatch.setattr(visitor_eval, "REPORTS_DIR", tmp_path)
    monkeypatch.setattr(suggestions_eval, "REPORTS_DIR", tmp_path)
    monkeypatch.setattr(src.generate, "answer", fake_answer)
    return tmp_path


def test_visitor_eval_routing_only_passes_the_ci_gate(reports, capsys):
    assert visitor_eval.main(["--bm25-only", "--no-report", "--min-success", "0.9"]) == 0
    assert "first question success: 100%" in capsys.readouterr().out
    assert list(reports.iterdir()) == []  # --no-report


def test_visitor_eval_gate_fails_below_the_threshold(reports, capsys):
    assert visitor_eval.main(["--bm25-only", "--no-report", "--baseline", "--min-success", "0.9"]) == 1
    assert "FAIL: first-question success" in capsys.readouterr().out


def test_visitor_eval_with_answers_saves_a_report_and_summary(reports):
    assert visitor_eval.main(["--bm25-only", "--answers"]) == 0
    summary = json.loads(next(reports.glob("*_visitor_keyword_answers.json")).read_text("utf-8"))
    report = next(reports.glob("*_visitor_keyword_answers.md")).read_text("utf-8")
    assert summary["mode"] == "keyword" and summary["pipeline"] == "current" and summary["questions"] >= 40
    # The fake model answers whatever it's given, so only routing-decided results are certain here.
    assert summary["greetings_handled"] == 1.0 and summary["off_topic_handled"] == 1.0
    assert "| v01 | beach-resort | Is there Wi-Fi? |" in report and "## Answers" in report


def test_baseline_pipeline_has_no_greetings_or_suggestions(reports):
    visitor_eval.main(["--bm25-only", "--answers", "--baseline"])
    summary = json.loads(next(reports.glob("*_answers_baseline.json")).read_text("utf-8"))
    assert summary["pipeline"] == "baseline" and summary["greetings_handled"] == 0.0
    assert summary["refusals_with_suggestions"] == 0.0


def test_suggestions_eval_every_curated_question_works(reports, capsys):
    assert suggestions_eval.main(["--bm25-only"]) == 0
    assert suggestions_eval.main(["--bm25-only", "--answers"]) == 0
    assert "work" in capsys.readouterr().out
    assert "| beach-resort | pets | Can a guest bring their dog? | yes | yes |" in next(
        reports.glob("*_suggestions_keyword_answers.md")
    ).read_text("utf-8")
