"""Optional AI touch: a model writes a FIRST DRAFT of the memo from the computed facts only.

A deterministic checker then lists every number in the draft that does not appear in the
facts (an "invented number"). Sara rewrites the draft herself; the README says so.

    python -m olist_analytics.ai_draft --dry-run                 # offline, fake client
    python -m olist_analytics.ai_draft --model cheap             # real call, needs a key

Input: outputs/memo_facts.json (written by the pipeline). Real runs write to evals/ai_draft/,
dry runs to evals/dry_run/ so they can never be mistaken for real results.
"""

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from olist_analytics.config import DEFAULT_OUT_DIR, REPO_ROOT
from olist_analytics.llm_client import FakeClient, OpenRouterClient

EVALS_DIR = REPO_ROOT / "evals"
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
SMALL_NUMBERS_ALLOWED = {str(n) for n in range(11)}  # list numbering, "1-2 stars", "3 findings"

SYSTEM_PROMPT = (
    "You are a junior data analyst writing a one-page business memo for a marketplace "
    "operations manager. Use ONLY the numbers given in FACTS, written exactly as given. "
    "Do not calculate, round or estimate any new number. If a number you want is not in "
    "FACTS, write the sentence without a number."
)


def build_user_prompt(facts: dict[str, str]) -> str:
    return (
        "FACTS (JSON):\n"
        + json.dumps(facts, indent=2)
        + "\n\nWrite at most 300 words in Markdown with these sections: "
        "'Three findings', 'Three recommendations' (each with its expected impact and the "
        "assumption behind it), 'Risks'. Say clearly that lateness and reviews are correlated, "
        "not proven cause and effect."
    )


def _variants(number_text: str) -> set[str]:
    """Spellings of the same number: '4.50' -> {'4.5', '4.50', '5', ...}."""
    value = float(number_text.replace(",", ""))
    return {f"{value:g}", str(round(value)), f"{value:.1f}", f"{value:.2f}"}


def extract_numbers(text: str) -> list[str]:
    """All numbers written in a text, with thousands separators removed."""
    return [match.replace(",", "") for match in NUMBER.findall(text)]


def allowed_numbers(facts: dict[str, str]) -> set[str]:
    allowed = set(SMALL_NUMBERS_ALLOWED)
    for value in facts.values():
        for number in extract_numbers(str(value)):
            allowed |= _variants(number)
    return allowed


def find_unsupported_numbers(draft: str, facts: dict[str, str]) -> list[str]:
    """Numbers in the draft that cannot be found in the facts (in any rounding)."""
    allowed = allowed_numbers(facts)
    return [n for n in extract_numbers(draft) if not (_variants(n) & allowed)]


def fake_draft(facts: dict[str, str]) -> str:
    """A fixed, rule-based 'draft' used by --dry-run. It only proves the plumbing works."""
    return (
        "## Three findings\n"
        f"1. {facts['late_rate_pct']} of delivered orders were late; late orders averaged "
        f"{facts['avg_review_late']} stars vs {facts['avg_review_on_time']} on time.\n"
        f"2. {facts['repeat_rate_pct']} of {facts['customers']} customers ordered again.\n"
        f"3. The top 3 categories bring {facts['top3_revenue_share_pct']} of revenue.\n"
        "## Three recommendations\n"
        "1. Fix delivery promises in the worst states.\n"
        "2. Test a second-order offer.\n"
        "3. Review freight in heavy categories.\n"
        "## Risks\nCorrelation, not causation.\n"
    )


def run(facts_path: Path, model_key: str, dry_run: bool, evals_dir: Path = EVALS_DIR) -> dict:
    if not facts_path.exists():
        raise FileNotFoundError(
            f"{facts_path} not found. Run the pipeline first "
            "(python -m olist_analytics.pipeline, or --demo for the synthetic fixture)."
        )
    facts = json.loads(facts_path.read_text(encoding="utf-8"))
    client = FakeClient(fake_draft(facts)) if dry_run else OpenRouterClient(model_key)
    reply = client.complete(SYSTEM_PROMPT, build_user_prompt(facts))
    unsupported = find_unsupported_numbers(reply.text, facts)

    out_dir = evals_dir / ("dry_run" if dry_run else "ai_draft")
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    draft_path = out_dir / f"memo_draft_{stamp}.md"
    banner = "DRY RUN - fake client, NOT a model output" if dry_run else "FIRST DRAFT by a model"
    draft_path.write_text(
        f"<!-- {banner}; model: {reply.model}; facts: {facts_path.name}; "
        f"data: {facts.get('data_label', '?')}. Sara rewrites this. -->\n\n{reply.text}\n",
        encoding="utf-8",
    )
    record = {
        "timestamp_utc": stamp,
        "model": reply.model,
        "data_label": facts.get("data_label", ""),
        "draft_file": draft_path.name,
        "numbers_in_draft": len(extract_numbers(reply.text)),
        "unsupported_numbers": " ".join(unsupported),
        "passed": not unsupported,
        "prompt_tokens": reply.prompt_tokens,
        "completion_tokens": reply.completion_tokens,
        "cost_usd": reply.cost_usd,
        "latency_s": reply.latency_s,
    }
    results_csv = out_dir / "number_check.csv"
    pd.DataFrame([record]).to_csv(
        results_csv, mode="a", header=not results_csv.exists(), index=False
    )
    with open(out_dir / "traces.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AI first draft of the memo + number check")
    parser.add_argument("--facts", type=Path, default=DEFAULT_OUT_DIR / "memo_facts.json")
    parser.add_argument("--model", choices=["cheap", "main"], default="cheap")
    parser.add_argument("--dry-run", action="store_true", help="use the offline fake client")
    args = parser.parse_args(argv)
    try:
        record = run(args.facts, args.model, args.dry_run)
    except (FileNotFoundError, RuntimeError) as err:
        print(err, file=sys.stderr)
        return 1
    status = "PASSED" if record["passed"] else f"FAILED: {record['unsupported_numbers']}"
    print(f"Draft: evals/{'dry_run' if args.dry_run else 'ai_draft'}/{record['draft_file']}")
    print(f"Number check ({record['numbers_in_draft']} numbers): {status}")
    print(f"Model: {record['model']}; cost USD: {record['cost_usd']}")
    return 0 if record["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
