# Cleaning notes and decisions

Every rule below is in `sql/stage_1_clean.sql` or `sql/stage_2_model.sql`, and the rows it
touches are counted in `outputs/dq_log.csv` (check name, rows affected, table size, action).
A count of 0 is a valid result: it means "we looked and found none".

> TODO (Sara): after the first real run, add the real counts from `outputs/dq_log.csv` here
> and write one sentence on the data-quality problem you found most interesting.

**Real counts, first full run on the Olist data (8 October 2026, coding agent).** Copied from
`outputs/dq_log.csv`; the "Table rows" column is the denominator. The sentence above is still
Sara's to write.

| Check | Rows affected | Table rows |
|---|---|---|
| orders_cancelled_or_unavailable | 1,234 | 99,441 orders |
| orders_still_in_progress | 1,729 | 99,441 orders |
| orders_delivered_but_no_delivery_date | 8 | 99,441 orders |
| orders_on_time_by_date_but_late_by_timestamp | 1,292 | 99,441 orders |
| orders_not_delivered_but_have_delivery_date | 6 | 99,441 orders |
| products_missing_category | 610 | 32,951 products |
| products_category_without_english_name | 13 | 32,951 products |
| reviews_review_id_reused | 814 | 99,224 reviews |
| reviews_extra_reviews_for_same_order | 551 | 99,224 reviews |
| delivered_orders_without_review | 646 | 99,441 orders |
| payments_type_not_defined | 3 | 103,886 payment lines |
| payments_zero_value | 9 | 103,886 payment lines |
| delivered_orders_payment_differs_from_items_plus_freight | 247 | 99,441 orders |
| geolocation_exact_duplicate_rows | 261,831 | 1,000,163 points |
| geolocation_points_outside_brazil | 31 | 1,000,163 points |

The other 12 checks found 0 rows (for example no duplicate `order_id`, no orphan items, no
delivery before purchase, no review score outside 1–5, no zip prefix that lost its leading zero).

## 1. Types and dates

| Decision | Why |
|---|---|
| Load every column as text, then `TRY_CAST` | A bad value becomes NULL and is counted, instead of the load crashing or a type being guessed wrongly. |
| Zip prefixes stay text and are left-padded to 5 digits | Read as numbers, `01310` becomes `1310` and no longer matches the geolocation file. |
| Money is `DECIMAL(12, 2)` | Floating point adds tiny errors (0.1 + 0.2 ≠ 0.3); decimals add up to the cent, so reconciliation can be exact. |
| "Late" compares **dates**, not timestamps | The promised date is stored as midnight. A parcel delivered at 18:00 on the promised day is on time for the customer. On the real data this moves 1,292 orders from "late" to "on time" (check `orders_on_time_by_date_but_late_by_timestamp`); the memo reports both late rates. |
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
| Category without an English name | Keep the Portuguese name. Counted with an explicit `has_english_name` flag: some names are the same in both languages (`pet_shop`, `cool_stuff`), so "English name = Portuguese name" does not mean "no translation". |
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

Two more traps found on the real data (8 October 2026):

- **Same-day "repeat" customers.** 786 of the 2,801 customers with two or more delivered
  orders placed all of them on the same day: a basket split into several orders, not a
  return. `q02` keeps the original repeat rate and adds the rate and timing for customers
  who came back on a **later** day.
- **Reviews answered before the parcel arrived.** Olist emails the survey when the parcel
  arrives or when the promised date is due, so for late orders the customer often answers
  while still waiting. `fact_orders.review_answered_before_delivery` compares the review
  answer timestamp with the delivery timestamp (not `review_creation_date`, which behaves
  like the date the survey was sent: almost always midnight, never after the answer); `q05` and
  `q11` report the share.

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

## 7. Partial months

`q01` flags a month as partial when it has fewer than 10% of the median month's orders. On
the real data that is Sep, Oct and Dec 2016 and Sep and Oct 2018 (November 2016 has no
orders at all). Month-on-month growth is left empty next to a partial month, the revenue
chart leaves partial months out, and the cohort chart treats months after the last full
month (August 2018) as "not observable yet" instead of 0%.

## 8. Thresholds (judgement calls)

Groups smaller than these sizes are not ranked or called "worst", because their rates are
noisy. They live in `src/olist_analytics/config.py` (`Params`) and the `params` table.

| Parameter | Default | Used in |
|---|---|---|
| `min_category_orders` | 100 | q03 review rank, q06 freight, memo |
| `min_state_orders` | 100 | q04 "enough_orders", memo worst states |
| `min_route_orders` | 50 | q12 |
| `min_seller_orders` | 30 | q08 |
| `min_cohort_size` | 100 | retention chart |
