# Outputs

Everything here is written by `python -m olist_analytics.pipeline`. Nothing is typed by hand.

> Status (8 October 2026): the pipeline has not yet been run on the real Olist data, so
> this folder has no real results yet. Sara downloads the data (see `data/README.md`) and
> runs the pipeline; the files below then appear.

| Path | Contents | In git? |
|---|---|---|
| `results/q01…q12_*.csv` | Answer to each SQL question; `results/_index.csv` lists the questions | Yes |
| `dq_log.csv` | Data-quality checks: rows affected, table size, action | Yes |
| `load_summary.csv` | Rows loaded from each raw file | Yes |
| `reconciliation.csv` | Same totals computed two ways; `expected_in_powerbi` for the dashboard check | Yes |
| `charts/*.png` | Five charts | Yes |
| `memo_facts.json`, `MEMO_draft.md` | Memo numbers and the filled template | Yes |
| `olist.duckdb` | The full database | No (row-level data) |
| `powerbi/*.csv` | Tables for Power BI | No (row-level data) |
| `synthetic_demo/` | Output of `--demo` on the synthetic fixture | No (not real results) |
