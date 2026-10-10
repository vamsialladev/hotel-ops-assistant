from src.reports import business_case, latest, list_reports, paired, parse_report

REPORT = """# Eval report 2026-10-09_1200

- Setup: hybrid, top_k=5, model=claude-haiku-5-5, max_tokens=1000, effort=default, runs=3
- Retrieval (strict, right passage in top 5): 44/45 = 98%
- Answer accuracy: 96% (min 94%, max 98%)
- Citation accuracy (cites the right document): 130/135 = 96%
- Numeric grounding (every number traceable to a source): 129/135 = 96%
- Correct refusals: 27/27 = 100%
- Off-topic questions refused before the API: 1/5
- Answerable questions wrongly blocked by the scope check: 0/45
- Escalation rules correct: 54/54 = 100%
- Time to first word: p50 0.95s, p95 1.60s
- Latency per answer: p50 1.30s, p95 2.20s
- Tokens per question: 950 in / 150 out
- Cost per question: $0.0002 ($0.17 per 1,000 questions)
"""


def test_report_summary_is_parsed():
    r = parse_report(REPORT)
    assert r["mode"] == "hybrid" and r["model"] == "claude-haiku-5-5" and r["runs"] == 3 and r["max_tokens"] == 1000
    assert r["retrieval"] == {"ok": 44, "n": 45, "pct": 98}
    assert r["answer_accuracy"] == {"pct": 96, "min": 94, "max": 98}
    assert r["refusals"]["pct"] == 100 and r["escalation"]["ok"] == 54
    assert r["off_topic_blocked"] == {"ok": 1, "n": 5} and r["wrongly_blocked"] == {"ok": 0, "n": 45}
    assert r["ttft"] == {"p50": 0.95, "p95": 1.6} and r["latency"]["p95"] == 2.2
    assert r["tokens"] == {"in": 950, "out": 150} and r["cost_per_1000"] == 0.17


def test_old_reports_without_new_metrics_still_parse():
    r = parse_report("- Setup: bm25, top_k=5\n- Retrieval (strict, right passage in top 5): 32/34 = 94%\n")
    assert r == {"mode": "keyword", "top_k": 5, "retrieval": {"ok": 32, "n": 34, "pct": 94}}


def test_latest_report_is_selected_by_mode_and_model(tmp_path):
    (tmp_path / "2026-10-08_2146_bm25.md").write_text("- Setup: bm25, top_k=5\n", encoding="utf-8")
    (tmp_path / "2026-10-09_1200_hybrid_answers_claude-haiku-5-5.md").write_text(REPORT, encoding="utf-8")
    (tmp_path / "2026-10-09_1300_hybrid_answers_claude-haiku-4-5.md").write_text(
        REPORT.replace("claude-haiku-5-5", "claude-haiku-4-5"), encoding="utf-8"
    )
    (tmp_path / "notes.md").write_text("ignored", encoding="utf-8")
    assert len(list_reports(tmp_path)) == 3
    assert latest(tmp_path, mode="hybrid")["stamp"] == "2026-10-09_1300"
    assert latest(tmp_path, model="claude-haiku-5-5")["stamp"] == "2026-10-09_1200"
    assert latest(tmp_path, mode="keyword", answers=False)["stamp"] == "2026-10-08_2146"
    assert latest(tmp_path, mode="keyword") is None


def test_business_case_range_is_read_from_the_document():
    cases = business_case()
    assert set(cases) == {"pessimistic", "base", "optimistic"}
    assert all(two.startswith("$") and hundred.startswith("$") for two, hundred in cases.values())


def test_model_comparison_uses_the_same_question_set(tmp_path):
    old = REPORT.replace("44/45", "33/34")
    (tmp_path / "2026-10-08_2216_hybrid_answers_claude-haiku-4-5.md").write_text(
        old.replace("claude-haiku-5-5", "claude-haiku-4-5"), encoding="utf-8"
    )
    (tmp_path / "2026-10-08_2220_hybrid_answers_claude-haiku-5-5.md").write_text(old, encoding="utf-8")
    (tmp_path / "2026-10-09_1200_hybrid_answers_claude-haiku-5-5.md").write_text(REPORT, encoding="utf-8")
    pair = paired(["claude-haiku-4-5", "claude-haiku-5-5"], reports_dir=tmp_path)
    assert {m: r["stamp"] for m, r in pair.items()} == {
        "claude-haiku-4-5": "2026-10-08_2216",
        "claude-haiku-5-5": "2026-10-08_2220",
    }
    assert paired(["claude-haiku-4-5", "claude-opus-5-5"], reports_dir=tmp_path) == {}


def test_new_cost_line_format_is_parsed():
    line = "- Cost per question: $0.0002 ($0.18 per 1,000 questions; prices $0.1/$0.5 per M tokens)"
    assert parse_report(line)["cost_per_1000"] == 0.18
