# Data: download the Olist dataset yourself (about 5 minutes)

This repository does **not** contain the Olist data and must never contain it. Each person
downloads it from Kaggle with their own account. `data/raw/` is listed in `.gitignore`, so
git will not upload it by accident.

## Source

- **Dataset:** "Brazilian E-Commerce Public Dataset by Olist"
- **Page:** https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
- **Publisher:** Olist (a Brazilian marketplace). About 100,000 orders from 2016–2018, anonymised by the publisher.
- **Licence:** commonly listed as **CC BY-NC-SA 4.0 — TO VERIFY.** Sara: open the Kaggle page, read the "License" line, and replace this sentence with exactly what it says and the date you checked it.
  - If it is CC BY-NC-SA 4.0, that means: give credit to Olist (BY), non-commercial use only (NC: for example this learning portfolio; never in paid work), and anything derived from the data is shared under the same licence (SA).
  - Attribution to use in the README and dashboard footer: *"Data: Brazilian E-Commerce Public Dataset by Olist, Kaggle (licence: to verify)."*

## Download steps (Windows)

1. Sign in at https://www.kaggle.com with your account.
2. Open https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
3. Click the **Download** button (top right of the page). If Kaggle offers options, choose **Download dataset as zip**. The file is usually called `archive.zip`.
4. In File Explorer, right-click the zip → **Extract All…** → choose this folder as the destination:
   `...\ecommerce-analytics-powerbi\data\raw\`
5. Check that the CSV files sit directly in `data\raw\`, for example `data\raw\olist_orders_dataset.csv`. (If they ended up one folder deeper, for example `data\raw\archive\`, that also works. If you just put the zip file itself in `data\raw\`, the pipeline extracts the CSV files for you.)

You should have these 9 files:

```
olist_customers_dataset.csv          olist_order_reviews_dataset.csv
olist_geolocation_dataset.csv        olist_orders_dataset.csv
olist_order_items_dataset.csv        olist_products_dataset.csv
olist_order_payments_dataset.csv     olist_sellers_dataset.csv
product_category_name_translation.csv
```

## Run everything (one command)

From the repository folder, with the virtual environment active:

```
python -m olist_analytics.pipeline
```

Optional quick check first (only reads the file headers, takes a second):

```
python -m olist_analytics.pipeline --check-only
```

If a file or column is missing, the command stops and lists exactly what is wrong. The
schema check accepts the original Olist misspelling `product_name_lenght` and renames it.

## What the pipeline writes, and what may be committed

| Output | Contains | Commit to GitHub? |
|---|---|---|
| `outputs/olist.duckdb` | full database (row-level copy of the data) | **No** (git-ignored) |
| `outputs/powerbi/*.csv` | row-level tables for Power BI | **No** (git-ignored) |
| `outputs/results/*.csv` | answers to the 12 SQL questions (aggregates) | Yes, after the licence check |
| `outputs/dq_log.csv`, `load_summary.csv`, `reconciliation.csv` | counts only | Yes |
| `outputs/charts/*.png` | charts | Yes |
| `outputs/MEMO_draft.md`, `memo_facts.json` | memo numbers | Yes (Sara edits the draft into `MEMO.md`) |

Power BI: commit the `.pbit` template and a PDF export, **not** the `.pbix` file, because a
`.pbix` stores a full copy of the imported rows (see `docs/POWERBI_STEPS.md`).

## Privacy notes

- Olist anonymised customers and sellers before publishing (hashed IDs, zip prefixes only).
- Review comment text was written by real customers. The pipeline never copies it into any
  output; only the 1–5 score is used.

## Test data

`tests/fixtures/olist_synthetic/` holds a tiny **synthetic** copy of the file layout, made
up by hand for the tests. It is not Olist data. `python -m olist_analytics.pipeline --demo`
runs on it so you can see every output before downloading anything.
