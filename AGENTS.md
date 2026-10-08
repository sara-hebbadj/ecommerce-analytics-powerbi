# Notes for coding agents (this repo)

Read the shared rules in `Portfolio Projects/AGENTS.md` first if you have that folder.
This file covers what is specific to this project.

## What this is

Analytics on the public Olist dataset: DuckDB SQL → star schema → 12 SQL answers, Power BI
CSV export, reconciliation, charts and a one-page memo. Sara must be able to explain every
line, so keep SQL readable, functions short, and comment any non-obvious decision.

## Hard rules

- **Never commit Olist data.** `data/raw/`, `outputs/olist.duckdb`, `outputs/powerbi/` and
  `*.pbix` are git-ignored on purpose (row-level data). Aggregated `outputs/results/*.csv`,
  charts and the DQ log may be committed only after Sara has checked the licence.
- **Never invent numbers.** Every number in the README, memo or RESULTS.md must come from a
  saved output file, with its denominator and run date. Memo numbers come only from
  `memo.py` (`build_facts`); the template must not contain hard-coded figures.
- **Synthetic fixture stays synthetic** and clearly labelled. If you change it, change
  `tests/fixtures/make_fixture.py`, re-run it, and update the hand-worked answers in
  `tests/fixtures/olist_synthetic/README.md` and the tests (work them out by hand first).
- No network in tests. LLM calls only through `src/olist_analytics/llm_client.py`.

## Where things are defined (single source of truth)

| Definition | Place |
|---|---|
| Revenue, delivered, cancelled, valid delivery, late, delay buckets | `sql/stage_1_clean.sql`, `sql/stage_2_model.sql` |
| Thresholds (min orders per category/state/route/seller) | `src/olist_analytics/config.py` → `params` table |
| Expected raw files and columns | `src/olist_analytics/schema.py` |
| Data-quality checks | `src/olist_analytics/quality.py` |
| Memo numbers and what-if formulas | `src/olist_analytics/memo.py` |
| DAX measures | `docs/measures.md` (must mirror the SQL definitions) |

If you change a definition in SQL, update `docs/measures.md`, `docs/data_dictionary.md`
and `docs/cleaning_notes.md` in the same change.

## Adding a SQL question

1. Create `sql/questions/qNN_short_name.sql`. The first line must be `-- Question: ...?`
   (tests enforce it). Query only model tables (`fact_*`, `dim_*`, `params`), never `raw_*`.
2. Add a test with a hand-worked answer on the fixture in `tests/test_metrics.py`.
3. The pipeline picks it up automatically and writes `outputs/results/qNN_short_name.csv`.

## Commands

```
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run python -m olist_analytics.pipeline --demo      # synthetic, writes outputs/synthetic_demo/
uv run python -m olist_analytics.pipeline --check-only
```

## Known facts about the real Olist files (handled in code)

- `customer_id` is per order; use `customer_unique_id` for people.
- Products columns are spelt `product_name_lenght` / `product_description_lenght`.
- Review comments contain quoted line breaks.
- Some orders have several reviews and some review IDs repeat across orders.
