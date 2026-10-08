# LEARN: walkthrough, interview questions and live exercises

For Sara. Practise the walkthrough out loud twice before recording the video or an interview.

## 10-minute walkthrough script

| Time | Show | Say (in your own words) |
|---|---|---|
| 0:00–1:00 | README top | "A marketplace wants to know if sales grow, if customers return, and where late deliveries hurt reviews. I used the public Olist dataset: about 100,000 orders from Brazil." |
| 1:00–2:00 | `data/README.md`, run `python -m olist_analytics.pipeline` | "Each user downloads the data; it is never re-uploaded. One command rebuilds everything. It first checks that all 9 files and their columns are there." |
| 2:00–3:30 | `sql/stage_1_clean.sql`, `outputs/dq_log.csv` | "I load every column as text and cast explicitly, so bad values are counted, not hidden. The log shows each rule and how many rows it touched." Pick ONE problem: the `customer_id` trap. |
| 3:30–5:30 | `sql/questions/q02_repeat_customer_rate.sql`, `q07_cohort_retention.sql` | Walk through `ROW_NUMBER()` / `LEAD()` and `MIN() OVER (PARTITION BY customer)`. Show the repeat rate by `customer_id` (0%) next to the real one. |
| 5:30–6:30 | `sql/stage_2_model.sql`, `outputs/reconciliation.csv` | "Two fact tables at different grains. I aggregate items per order before joining, and I check the same revenue three ways." |
| 6:30–8:00 | Power BI pages 1–3 | Sales trend and categories → repeat rate and cohorts → the "review by days late" chart. |
| 8:00–9:15 | `outputs/MEMO_draft.md` → your `MEMO.md` | Three findings with numbers, three recommendations, each with a what-if and its assumption, then the risks. |
| 9:15–10:00 | README "Limitations" | "Correlation, not causation; no cost data; next I would test carriers in the worst states." Mention the optional AI draft and its number check. |

## 10 interview questions with short model answers

1. **Walk me through a query with a window function.**
   In `q07_cohort_retention.sql`, `MIN(purchase_month) OVER (PARTITION BY customer_unique_id)` puts each customer's first month on every one of their orders without a self-join. Then I count customers by cohort month and "months since first", and divide by the cohort size. `q01` uses `LAG()` to compare each month's revenue with the month before.

2. **How do late deliveries affect reviews in your data, and how sure are you?**
   Late orders have a much lower average review and far more 1–2 star reviews (quote the real numbers from `q05`). The 95% confidence interval for the gap shows it is not sampling noise, and the review falls step by step as delays grow (`q11`), which is consistent with a real effect. But it is a correlation: late orders may also differ by region, product or seller. To prove cause I would test, for example, a carrier change in one state against a similar state.

3. **What would you put on the CEO's one-page view?**
   Four numbers (revenue, delivered orders, late rate, repeat rate) with their trend, the one chart "review score by days late", and the three recommendations with their expected impact and assumptions. Nothing that needs explaining.

4. **One data-quality problem you found, and how you handled it.**
   `customer_id` is new for every order, so a naive repeat rate is 0%. I used `customer_unique_id` and show both numbers. (After the real run, add a second one from `dq_log.csv` with its real count, for example delivered orders without a delivery date: kept in revenue, left out of lateness.)

5. **Why load everything as text first?**
   Automatic type guessing can silently damage data: zip prefix `01310` becomes the number `1310`. Loading text and casting with `TRY_CAST` turns bad values into NULL, and the data-quality log counts them, so nothing disappears unnoticed.

6. **What is join fan-out, and how did you avoid it?**
   If you join orders to items and payments at the same time, each item is repeated for every payment line, and revenue is inflated. I aggregate items and payments to one row per order before joining, and `reconcile.py` checks that revenue by month, by category and from the export all match.

7. **Why two fact tables in Power BI?**
   They have different grains: one row per order (delivery, review) and one row per item (category, seller, price). Review score is an order fact; if it sat on the item table, an order with three items would count three times. Both facts share the same dimensions (date, state, customer), which is a star schema.

8. **Why `DECIMAL` for money instead of float?**
   Floating point cannot store most decimal amounts exactly, so sums drift by fractions of a cent. `DECIMAL(12,2)` adds exactly, which lets reconciliation require an exact match.

9. **How did you define "late", and why?**
   Delivered on a date after the estimated date. I compare dates, not timestamps, because the estimate is stored as midnight; a parcel delivered at 18:00 on the promised day is on time for the customer. Orders with a missing or impossible delivery date are left out of lateness but still count as sales.

10. **How did you use AI, and how did you stop it inventing numbers?**
    A coding agent wrote the first version from my brief and acceptance tests; I reviewed, ran and changed it (say what you changed). Inside the project, an optional script asks a model for a memo first draft using only the computed facts, and a checker lists any number in the draft that is not in the facts. I rewrote the final memo myself.

## 3 "change it live" exercises

Do each one, run `pytest`, and explain which tests changed and why.

1. **Change the definition of "late" to "more than 3 days late".**
   In `sql/stage_2_model.sql`, change `o.delay_days > 0` to `o.delay_days > 3` in `is_late`.
   Expected on the fixture: order `o02` (3 days late) becomes on time, so late orders go from
   2 to 1 and `test_late_rate_by_state` and the memo tests fail. Update the expected numbers
   by hand (late rate 1/8 = 12.5%), then discuss: is a grace period fairer to sellers, and
   would the review gap shrink or grow?

2. **Add a new question: revenue by weekday.**
   Create `sql/questions/q13_revenue_by_weekday.sql` starting with
   `-- Question: On which weekday do delivered orders bring the most revenue?`, using
   `fact_orders` joined to `dim_date` on `purchase_date = date`, grouped by `weekday_number`,
   `weekday_name`. Add a hand-worked test (on the fixture, Thursday 5 Jan 2017 is `o01`).
   Update the test that expects exactly 12 question files.

3. **Make "worst states" stricter.**
   In `src/olist_analytics/config.py`, change `min_state_orders` from 100 to 500 and re-run
   the real pipeline. Compare `worst_states` in `outputs/memo_facts.json` before and after.
   Explain the trade-off: higher thresholds give more reliable rates but can hide a small
   state with a real problem.
