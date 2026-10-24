"""The multi-turn eval's plumbing (no API: retrieval-only runs and hand-made results)."""

from eval import run_multiturn_eval as mt
from src.retrieve import Retriever


def test_cases_have_dev_and_held_out_sets_and_the_required_categories():
    dev, held = mt.load_cases(split="dev"), mt.load_cases(split="heldout")
    assert len(dev) >= 12 and len(held) >= 4
    categories = {c["category"] for c in dev}
    for needed in ("pronoun_follow_up", "property_switch", "injection_turn_2", "topic_change", "after_refusal"):
        assert needed in categories
    assert all(len(c["turns"]) >= 2 for c in dev + held)
    assert len(mt.load_cases(split="all")) == len(dev) + len(held)


def test_rule_mode_finds_the_new_property_and_passage_without_the_api():
    retriever = Retriever(use_embeddings=False)
    case = next(c for c in mt.load_cases() if c["id"] == "m01")
    out = mt.run_case(retriever, case, "rule", answers=False)
    assert out["grade"] == {"property_ok": True, "retrieval_ok": True}
    assert out["turns"][-1]["property"] == "mountain-lodge" and out["turns"][-1]["rewritten"] != case["turns"][-1]["q"]
    before = mt.run_case(retriever, case, "off", answers=False)
    assert before["grade"]["property_ok"] is False  # as typed, the picker's property is used


def test_percentile_and_rate():
    assert mt.percentile([], 0.5) is None
    assert mt.percentile([1, 2, 3, 4], 0.5) == 2.5
    assert mt.percentile([1.0, 9.0], 0.95) == 8.6
    assert mt.rate([True, False, None, True]) == (2, 3)


def test_summarize_counts_every_turn_for_cost_and_the_last_turn_for_latency():
    def case(cid, correct, seconds):
        turns = [
            {"seconds": 1.0, "pre_api": False, "tokens_in": 1000, "tokens_out": 100, "rewrite_tokens_in": 0},
            {"seconds": seconds, "pre_api": False, "tokens_in": 1200, "tokens_out": 100, "rewrite_tokens_in": 200},
        ]
        return {"id": cid, "turns": turns, "grade": {"correct": correct, "property_ok": True}}

    runs = [[case("a", True, 2.0), case("b", False, 3.0)], [case("a", True, 2.0), case("b", True, 4.0)]]
    s = mt.summarize(runs, 0.1, 0.5)
    assert s["requests"] == 8 and s["rewrite_calls"] == 4
    assert s["metrics"]["correct"] == (3, 4) and s["per_run_correct"] == [(1, 2), (2, 2)]
    assert s["consistent"] == 1 and s["failing"] == ["b"]
    assert round(s["cost_per_1000"], 4) == round((4400 * 0.1 + 400 * 0.5) / 1e6 / 8 * 1000 * 2, 4)
    assert s["p50"] == 2.5
    assert mt.summarize(runs, None, None)["cost_per_1000"] is None


def test_report_lists_every_case(tmp_path):
    retriever = Retriever(use_embeddings=False)
    cases = mt.load_cases()[:2]
    runs = [[mt.run_case(retriever, c, "rule", answers=False) for c in cases]]
    args = type("A", (), {"runs": 1, "price_in": 0.1, "price_out": 0.5, "answers": False})()
    text = mt.report("dev", "rule", runs, mt.summarize(runs, 0.1, 0.5), args)
    assert "| m01 |" in text and "| m02 |" in text and "Strict retrieval" in text


def test_cli_retrieval_only_gate(tmp_path, monkeypatch, capsys):
    assert mt.main(["--modes", "rule", "--no-answers", "--no-report", "--min-retrieval", "0.5"]) == 0
    assert mt.main(["--modes", "off", "--no-answers", "--no-report", "--min-retrieval", "0.99"]) == 1
    assert mt.main(["--modes", "llm", "--no-answers", "--no-report"]) == 0
    assert "llm mode needs the API" in capsys.readouterr().out
