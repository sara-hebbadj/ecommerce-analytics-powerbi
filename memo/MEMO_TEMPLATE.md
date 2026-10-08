# Decision memo: delivery, repeat customers and freight

**Data:** $data_label · $period_start to $period_end · $delivered_orders delivered orders · BRL $revenue product revenue (item prices, excluding freight)

**To:** Head of Marketplace Operations (a fictional reader for this portfolio exercise) · **From:** Sara Hebbadj · **Draft generated:** $generated_on

Every number below is filled in by `python -m olist_analytics.pipeline` from `outputs/results/`. Nothing is typed by hand. Partial months flagged in the data: $partial_months.

## Three findings

_TODO (Sara): after checking the numbers, turn each bold heading into a one-line conclusion._

1. **Late deliveries and review scores.** $late_rate_pct of delivered orders arrived after the date promised at checkout. Late orders averaged **$avg_review_late** stars against **$avg_review_on_time** for on-time orders (a gap of $review_gap stars; 95% confidence interval $review_gap_ci_low to $review_gap_ci_high), and $low_review_pct_late of late orders got 1–2 stars against $low_review_pct_on_time of on-time orders. By days late: $review_by_delay_buckets. $late_answered_before_delivery_pct of the late orders' reviews were answered before the parcel arrived; the $late_answered_after_delivery late orders reviewed after delivery averaged $avg_review_late_answered_after_delivery stars. Highest late rates (states with enough orders): $worst_states.
2. **Repeat customers.** $repeat_rate_pct of $customers customers placed a second delivered order; $repeat_same_day_only of those $repeat_customers ($repeat_same_day_only_pct) placed all their orders on the same day (a split basket, not a return). Counting only customers who came back on a later day: $repeat_rate_later_day_pct, after a median of $median_days_to_later_order days. In the month after their first order, $month1_retention_pct of customers bought again (weighted over $month1_cohorts cohorts).
3. **Category concentration and freight.** The top 3 categories ($top3_categories) bring $top3_revenue_share_pct of revenue. Freight costs $freight_share_pct of the item value overall; the heaviest categories with enough orders are $high_freight_categories.

## Three recommendations

| # | Recommendation (Sara: rewrite in your own words) | Expected impact (what-if, computed) | Assumptions |
|---|---|---|---|
| 1 | **TODO (Sara):** e.g. review the delivery-date promise and carrier performance in $worst_state_codes first. | If the $what_if_state_count worst states had the national late rate: about **$late_orders_avoided fewer late orders** and **$low_reviews_avoided fewer 1–2 star reviews** over the period. | Treats the lateness–review link as if it were causal (it is only a correlation). Same order volume. |
| 2 | **TODO (Sara):** e.g. a second-order offer timed around day $median_days_to_later_order after the first purchase. | Each +1 point of repeat rate ≈ **$extra_repeat_customers_per_point more repeat customers** ≈ **BRL $revenue_per_repeat_point** extra revenue over the period. | Each extra repeat customer places one more order at today's average order value (BRL $avg_order_value). No campaign cost included. |
| 3 | **TODO (Sara):** e.g. test free-shipping thresholds or packaging changes in $high_freight_category_names. | If those categories had the overall freight share: **BRL $freight_reduction less freight** over the period. | Same sales volume and mix; freight savings would be shared between customers and sellers. |

## Risks and limits

- **Correlation, not causation.** Late orders may also differ in product, region or seller. A carrier test or A/B test is needed before promising review gains.
- **When the review was written.** Olist emails the review survey when the parcel arrives or when the promised date is due, so a late-order review can rate the wait itself: $late_answered_before_delivery_pct of late orders' reviews were answered before delivery. Customers who answered after delivery are a self-selected group, so their average ($avg_review_late_answered_after_delivery) is not a clean "effect of lateness" either.
- **Definition of "late".** Late compares the delivery DATE with the promised date. Comparing timestamps instead would put the late rate at $late_rate_pct_by_timestamp instead of $late_rate_pct.
- **Revenue is item prices only (BRL).** There is no cost data, so this memo says nothing about profit or margin.
- **Customer identity.** Repeat rates use `customer_unique_id`; counting by `customer_id` would show $repeat_rate_by_customer_id (every order gets a new `customer_id`). Including same-day orders, the median gap from first to second order is $median_days_to_second_order days.
- **Data quality.** $dq_summary See `outputs/dq_log.csv`.
- **Public historical data** from one Brazilian marketplace. The pattern needs checking before it is applied to any other shop.

---

## DRAFT recommendation wording by the coding agent (not Sara's: rewrite or delete)

_Written to fit any run of this pipeline, so it makes no claim about the direction or size of a result. The data-specific conclusions for the real run are in the README "Results" section._

1. Start with the states where late deliveries are most common ($worst_state_codes): compare carriers and check whether the promised dates there are realistic. Then run a controlled test (for example, a more cautious promised date for a random half of orders) to see whether reviews actually change, because the numbers above show an association, not a cause.
2. Test a second-order offer timed around day $median_days_to_later_order after the first purchase, with a random hold-out group, and measure the repeat rate on a later day (so same-day split orders do not count as returns).
3. Pilot free-shipping thresholds or packaging changes in one high-freight category ($high_freight_category_names) before any wider change, and track freight cost and conversion together.
