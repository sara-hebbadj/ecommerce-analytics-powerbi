"""Optional AI memo draft: the number checker and the offline dry run. No network calls."""

import json

import pytest

from olist_analytics import llm_client
from olist_analytics.ai_draft import extract_numbers, find_unsupported_numbers, run

FACTS = {"late_rate_pct": "25.0%", "revenue": "1,970", "avg_review_late": "1.50"}


def test_numbers_are_extracted_without_thousand_separators():
    assert extract_numbers("BRL 1,970 and 25.0% in 2017") == ["1970", "25.0", "2017"]


def test_rounded_and_reformatted_numbers_are_accepted():
    draft = "Revenue was BRL 1970; 25% of orders were late, averaging 1.5 stars."
    assert find_unsupported_numbers(draft, FACTS) == []


def test_invented_number_is_flagged():
    draft = "25.0% were late, and fixing this would raise revenue by 12%."
    assert find_unsupported_numbers(draft, FACTS) == ["12"]


def test_dry_run_end_to_end(tmp_path, pipeline_outputs):
    facts_path = pipeline_outputs["out_dir"] / "memo_facts.json"
    record = run(facts_path, "cheap", dry_run=True, evals_dir=tmp_path)
    assert record["passed"] is True
    assert record["model"].startswith("fake-client")
    assert (tmp_path / "dry_run" / record["draft_file"]).exists()
    trace = json.loads((tmp_path / "dry_run" / "traces.jsonl").read_text().splitlines()[0])
    assert trace["cost_usd"] == 0.0


def test_real_client_needs_a_key(monkeypatch, tmp_path):
    monkeypatch.setattr(llm_client, "ENV_FILES", [tmp_path / "missing.env"])
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="--dry-run"):
        llm_client.OpenRouterClient("cheap")
