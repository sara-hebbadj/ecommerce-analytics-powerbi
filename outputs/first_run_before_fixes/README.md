# First real run, before the fixes (8 October 2026): evidence only

These files come from the first run of the original code on the real Olist data, before the
changes listed in the main README, section 6. **Do not use these numbers**; the current
results are one folder up.

- `dq_log.csv`, `memo_facts.json`, `reconciliation.csv`, `q02_…csv`, `q05_…csv`: copied
  straight after the first run.
- `q01_monthly_orders_revenue.csv`: the first version of `q01` (growth computed for every
  month, partial or not), re-run on the same database after the first run, because the
  original file had already been overwritten. The `fact_orders` columns it reads were not
  changed by the fixes.

What they show: `products_category_without_english_name` = 2,058 in `dq_log.csv` (the real
number is 13), and `revenue_mom_pct` = 1,025,573.03 for January 2017 in `q01` (growth over a
December 2016 that had a single order).

Licence: derived from the Olist dataset, CC BY-NC-SA 4.0 (see `../README.md`).
