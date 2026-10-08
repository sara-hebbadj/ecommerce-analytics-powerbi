# Outputs

Everything here is written by `python -m olist_analytics.pipeline`. Nothing is typed by hand.

> Status: the pipeline was run on the real Olist data (Kaggle version 2) on 8 October 2026
> by the coding agent (see `data/README.md` for the download and checksums). Sara has not
> yet reviewed these outputs.

## Licence of the files in this folder

The files below are **derived from the Brazilian E-Commerce Public Dataset by Olist**
(https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce, version 2), which is licensed
**CC BY-NC-SA 4.0** (https://creativecommons.org/licenses/by-nc-sa/4.0/). They are
aggregated (counts, sums, averages, rates) and cleaned as described in
`docs/cleaning_notes.md`, and they are shared under the **same licence, CC BY-NC-SA 4.0**:
non-commercial use only, with credit to Olist. The repository's MIT licence covers the code,
not these files.

| Path | Contents | In git? |
|---|---|---|
| `results/q01…q12_*.csv` | Answer to each SQL question; `results/_index.csv` lists the questions | Yes (CC BY-NC-SA 4.0) |
| `dq_log.csv` | Data-quality checks: rows affected, table size, action | Yes (CC BY-NC-SA 4.0) |
| `load_summary.csv` | Rows loaded from each raw file | Yes (CC BY-NC-SA 4.0) |
| `reconciliation.csv` | Same totals computed two ways; `expected_in_powerbi` for the dashboard check | Yes (CC BY-NC-SA 4.0) |
| `charts/*.png` | Five charts | Yes (CC BY-NC-SA 4.0) |
| `memo_facts.json`, `MEMO_draft.md` | Memo numbers and the filled template | Yes (CC BY-NC-SA 4.0) |
| `first_run_before_fixes/` | DQ log, memo facts and two results from the FIRST real run, before the fixes listed in the README section 6. Kept as evidence for those fixes; do not use these numbers. | Yes (CC BY-NC-SA 4.0) |
| `olist.duckdb` | The full database | No (row-level data) |
| `powerbi/*.csv` | Tables for Power BI | No (row-level data) |
| `synthetic_demo/` | Output of `--demo` on the synthetic fixture | No (not real results) |
