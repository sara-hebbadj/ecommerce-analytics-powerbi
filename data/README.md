# Data: download the Olist dataset yourself (about 5 minutes)

This repository does **not** contain the Olist data and must never contain it. Each person
downloads it from Kaggle. `data/raw/` is listed in `.gitignore`, so git will not upload it
by accident.

## Source and licence (checked 8 October 2026)

- **Dataset:** "Brazilian E-Commerce Public Dataset by Olist"
- **Page:** https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
- **Owner:** Olist (Kaggle account `olistbr`). Kaggle version **2**, version note "Data Update 2021/10/01", last updated 2021-10-01T19:08:27.97Z.
- **Licence, exactly as Kaggle lists it:** **`CC BY-NC-SA 4.0`** (Kaggle's licence code for it: `CC-BY-NC-SA-4.0`). Full licence: https://creativecommons.org/licenses/by-nc-sa/4.0/
  - How this was checked: the Kaggle page is drawn by JavaScript, so a plain page fetch shows no licence line. The same page data comes from Kaggle's public API, which returned `"licenseName": "CC BY-NC-SA 4.0"` (https://www.kaggle.com/api/v1/datasets/view/olistbr/brazilian-ecommerce) and `"licenses": [{"name": "CC-BY-NC-SA-4.0"}]` (https://www.kaggle.com/api/v1/datasets/metadata/olistbr/brazilian-ecommerce) on 8 October 2026.
  - > TODO (Sara): open the Kaggle page while signed in, confirm the "License" line still says CC BY-NC-SA 4.0, and add the date you checked.
- **What the licence means for this project:**
  - **BY (attribution):** credit Olist and link to the dataset and the licence; say what was changed.
  - **NC (non-commercial):** use it only for non-commercial purposes, such as this learning portfolio; never in paid client work.
  - **SA (share-alike):** anything derived from the data that is shared (for example the aggregated result tables and charts in `outputs/`) is shared under the same licence, CC BY-NC-SA 4.0.
- **Attribution to use in the README, memo and dashboard footer:** *"Data: Brazilian E-Commerce Public Dataset by Olist (Kaggle, version 2), licensed CC BY-NC-SA 4.0. Aggregated and cleaned by Sara Hebbadj; see docs/cleaning_notes.md for the changes."*
- **About the data (from the publisher):** about 100,000 orders from 2016–2018 made at multiple Brazilian marketplaces; real commercial data, anonymised, with company and partner names in review text replaced by the names of Game of Thrones great houses.

## How the copy used for the 8 October 2026 run was downloaded

- **Tool:** `kagglehub` 1.0.2 (`pip install kagglehub`), **without** signing in:
  `python -c "import kagglehub; print(kagglehub.dataset_download('olistbr/brazilian-ecommerce'))"`.
  It downloaded version 2 (a 42.6 MB zip) from Kaggle's public download endpoint
  `https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce` and
  extracted the 9 CSV files, which were then copied into `data/raw/`. No mirror was used.
- **Check:** the 9 files add up to 126,186,995 bytes, the same total that Kaggle reports for
  version 2. Their SHA-256 checksums, so anyone can confirm they have the same files
  (`sha256sum data/raw/*.csv`, or `Get-FileHash` on Windows):

| File | Bytes | SHA-256 |
|---|---|---|
| `olist_customers_dataset.csv` | 9033957 | `983a422239e1712ded753b3bf9ecf47dc73f144d306029dcfa99e70a226883d2` |
| `olist_geolocation_dataset.csv` | 61273883 | `b514f6fc991b9566aeba02aa5d67e2c3630f034b60a0e05aa0d082a3b66d88d6` |
| `olist_order_items_dataset.csv` | 15438671 | `0bc4d068c4fe38cbb01bd90e8746e3c613fe7b4baef75fab7b0e329701c3e279` |
| `olist_order_payments_dataset.csv` | 5777138 | `4f713964f2815dbbaa40b9488268c55aac3627bfce5aa96cf58d1f3616de3cc0` |
| `olist_order_reviews_dataset.csv` | 14451670 | `012b61c7593e34f51fa614efdf802b9c7056ce6aae5307ddb93236e7cfc797d7` |
| `olist_orders_dataset.csv` | 17654914 | `8df58ef3d2d7e9944010f7beecd9b75367f5588ec6e3c91cec19ae3345ef9ecf` |
| `olist_products_dataset.csv` | 2379446 | `3e6569628a17fbc75fd206ee357b59e20364b9afa90f5b6cd5b4d624c58aa9cc` |
| `olist_sellers_dataset.csv` | 174703 | `1f643d2b950373b85735e7794b20986f528d7a000432e7c6f9bcbb44d0846a0e` |
| `product_category_name_translation.csv` | 2613 | `a81f0d1f27b27e7293f761bc79e3ce8f348ee39c4b3ed3e49bde38f478586278` |

Rows loaded from each file are in `outputs/load_summary.csv` (for example 99,441 orders and
99,224 reviews; the reviews file has more *lines* than rows because comments contain line breaks).

## Download steps (Windows, with your Kaggle account)

1. Sign in at https://www.kaggle.com with your account.
2. Open https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
3. Click the **Download** button (top right of the page). If Kaggle offers options, choose **Download dataset as zip**. The file is usually called `archive.zip`.
4. In File Explorer, right-click the zip → **Extract All…** → choose this folder as the destination:
   `...\ecommerce-analytics-powerbi\data\raw\`
5. Check that the CSV files sit directly in `data\raw\`, for example `data\raw\olist_orders_dataset.csv`. (If they ended up one folder deeper, for example `data\raw\archive\`, that also works. If you just put the zip file itself in `data\raw\`, the pipeline extracts the CSV files for you.)

Alternative without signing in: the `kagglehub` command above, then copy the 9 CSV files
from the folder it prints into `data\raw\`.

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
On the real files of 8 October 2026 the check passed with no changes to the loader: the real
column names match `src/olist_analytics/schema.py`.

## What the pipeline writes, and what may be committed

| Output | Contains | Commit to GitHub? |
|---|---|---|
| `outputs/olist.duckdb` | full database (row-level copy of the data) | **No** (git-ignored) |
| `outputs/powerbi/*.csv` | row-level tables for Power BI | **No** (git-ignored) |
| `outputs/results/*.csv` | answers to the 12 SQL questions (aggregates) | Yes, labelled CC BY-NC-SA 4.0 (see below), after Sara's check |
| `outputs/dq_log.csv`, `load_summary.csv`, `reconciliation.csv` | counts only | Yes, same label |
| `outputs/charts/*.png` | charts | Yes, same label |
| `outputs/MEMO_draft.md`, `memo_facts.json` | memo numbers | Yes, same label (Sara edits the draft into `MEMO.md`) |

**Licence check for the aggregated outputs (coding agent's reading, 8 October 2026; not
legal advice):** committing the aggregated tables and charts is compatible with
CC BY-NC-SA 4.0 if (1) they carry the attribution above and say they are licensed
CC BY-NC-SA 4.0 (ShareAlike), which `outputs/README.md` does, (2) they are used only
non-commercially, as in this portfolio, and (3) the raw rows are not re-published. They
contain counts, sums, averages and rates; the seller ranking (`q08`) lists Olist's
anonymised seller IDs with their totals. The repository's MIT licence covers the code only,
not these data-derived files. The row-level files (`olist.duckdb`, `powerbi/`, `data/raw/`)
stay git-ignored. Sara makes the final decision before the first push (see `AGENTS.md`).

Power BI: commit the `.pbit` template and a PDF export, **not** the `.pbix` file, because a
`.pbix` stores a full copy of the imported rows (see `docs/POWERBI_STEPS.md`).

## Privacy notes

- Olist anonymised customers and sellers before publishing (hashed IDs, zip prefixes only).
- Review comment text was written by real customers. The pipeline never copies it into any
  output; only the 1–5 score and the review dates are used.

## Test data

`tests/fixtures/olist_synthetic/` holds a tiny **synthetic** copy of the file layout, made
up by hand for the tests. It is not Olist data. `python -m olist_analytics.pipeline --demo`
runs on it so you can see every output before downloading anything.
