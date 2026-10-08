# Cleaning notes and decisions

Every rule below is in `sql/stage_1_clean.sql` or `sql/stage_2_model.sql`, and the rows it
touches are counted in `outputs/dq_log.csv` (check name, rows affected, table size, action).
A count of 0 is a valid result: it means "we looked and found none".

> TODO (Sara): after the first real run, add the real counts from `outputs/dq_log.csv` here
> and write one sentence on the data-quality problem you found most interesting.

## 1. Types and dates

| Decision | Why |
|---|---|
| Load every column as text, then `TRY_CAST` | A bad value becomes NULL and is counted, instead of the load crashing or a type being guessed wrongly. |
| Zip prefixes stay text and are left-padded to 5 digits | Read as numbers, `01310` becomes `1310` and no longer matches the geolocation file. |
| Money is `DECIMAL(12, 2)` | Floating point adds tiny errors (0.1 + 0.2 ≠ 0.3); decimals add up to the cent, so reconciliation can be exact. |
| "Late" compares **dates**, not timestamps | The promised date is stored as midnight. A parcel delivered at 18:00 on the promised day is on time for the customer. |
| Orders are counted in their **purchase** month | That is when the customer decided to buy; delivery month would move revenue between months. |

## 2. Duplicates and missing values

| Rule | Action |
|---|---|
| Duplicate `order_id` | Keep one row (`QUALIFY ROW_NUMBER() ... = 1`). |
| Exact duplicate item rows | Removed with `SELECT DISTINCT`. |
| Several reviews for one order | Keep the latest answered review. |
| Same `review_id` on several orders | Information only: reviews are matched by `order_id`. |
| Review score not 1–5 | Set to missing. |
| Product without category | Category `unknown` (left out of category conclusions in the memo). |
| Category without an English name | Keep the Portuguese name. |
| Item whose order does not exist | Dropped by the inner join in `fact_order_items`. |
| Geolocation duplicates and points outside Brazil | Harmless / ignored: only one median point per state is used for the map. |

## 3. Delivered vs cancelled orders

| Status group | Revenue | Repeat customers & cohorts | Delivery & lateness | Reviews |
|---|---|---|---|---|
| `delivered` with valid dates | yes | yes | yes | yes |
| `delivered`, missing or impossible delivery date | yes | yes | **no** | no (lateness unknown) |
| `canceled`, `unavailable` | no | no | no | no |
| still in progress (`shipped`, `invoiced`, …) | no | no | no | no |

A cancelled order that still has a delivery date is treated as **not delivered** (the status wins).

## 4. Customer identity (the most important trap)

Olist creates a new `customer_id` for every order. Counting repeat customers by
`customer_id` therefore gives 0%. The person is `customer_unique_id`. Query
`q02_repeat_customer_rate.sql` prints both numbers side by side so the difference is visible.

## 5. Revenue definition

Revenue = sum of **item prices** of **delivered** orders, in BRL, **excluding freight**.
Payments are not used for revenue because one order can be paid with several methods,
vouchers and instalment interest make payments differ from prices. There is no cost data,
so nothing in this project is about profit or margin.

## 6. Avoiding double counting (join fan-out)

Items and payments are aggregated to one row per order **before** they are joined to orders.
Joining the raw tables directly would repeat each item once per payment line and inflate
revenue. `reconcile.py` checks that revenue is the same whether it is summed by month,
by category, or from the exported Power BI files.

## 7. Thresholds (judgement calls)

Groups smaller than these sizes are not ranked or called "worst", because their rates are
noisy. They live in `src/olist_analytics/config.py` (`Params`) and the `params` table.

| Parameter | Default | Used in |
|---|---|---|
| `min_category_orders` | 100 | q03 review rank, q06 freight, memo |
| `min_state_orders` | 100 | q04 "enough_orders", memo worst states |
| `min_route_orders` | 50 | q12 |
| `min_seller_orders` | 30 | q08 |
| `min_cohort_size` | 100 | retention chart |
