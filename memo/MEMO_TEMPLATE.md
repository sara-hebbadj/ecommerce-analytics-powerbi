# Decision memo: delivery, repeat customers and freight

**Data:** $data_label · $period_start to $period_end · $delivered_orders delivered orders · BRL $revenue product revenue (item prices, excluding freight)

**To:** Head of Marketplace Operations (a fictional reader for this portfolio exercise) · **From:** Sara Hebbadj · **Draft generated:** $generated_on

Every number below is filled in by `python -m olist_analytics.pipeline` from `outputs/results/`. Nothing is typed by hand. Partial months flagged in the data: $partial_months.

## Three findings

_TODO (Sara): after checking the numbers, turn each bold heading into a one-line conclusion._

1. **Late deliveries and review scores.** $late_rate_pct of delivered orders arrived after the date promised at checkout. Late orders averaged **$avg_review_late** stars against **$avg_review_on_time** for on-time orders (a gap of $review_gap stars; 95% confidence interval $review_gap_ci_low to $review_gap_ci_high), and $low_review_pct_late of late orders got 1–2 stars against $low_review_pct_on_time of on-time orders. Highest late rates (states with enough orders): $worst_states.
2. **Repeat customers.** $repeat_rate_pct of $customers customers placed a second delivered order. A typical returning customer came back after $median_days_to_second_order days (median). In the month after their first order, $month1_retention_pct of customers bought again (weighted over $month1_cohorts cohorts).
3. **Category concentration and freight.** The top 3 categories ($top3_categories) bring $top3_revenue_share_pct of revenue. Freight costs $freight_share_pct of the item value overall; the heaviest categories with enough orders are $high_freight_categories.

## Three recommendations

| # | Recommendation (Sara: rewrite in your own words) | Expected impact (what-if, computed) | Assumptions |
|---|---|---|---|
| 1 | **TODO (Sara):** e.g. review the delivery-date promise and carrier performance in $worst_state_codes first. | If the $what_if_state_count worst states had the national late rate: about **$late_orders_avoided fewer late orders** and **$low_reviews_avoided fewer 1–2 star reviews** over the period. | Treats the lateness–review link as if it were causal (it is only a correlation). Same order volume. |
| 2 | **TODO (Sara):** e.g. a second-order offer timed around day $median_days_to_second_order after the first delivery. | Each +1 point of repeat rate ≈ **$extra_repeat_customers_per_point more repeat customers** ≈ **BRL $revenue_per_repeat_point** extra revenue over the period. | Each extra repeat customer places one more order at today's average order value (BRL $avg_order_value). No campaign cost included. |
| 3 | **TODO (Sara):** e.g. test free-shipping thresholds or packaging changes in $high_freight_category_names. | If those categories had the overall freight share: **BRL $freight_reduction less freight** over the period. | Same sales volume and mix; freight savings would be shared between customers and sellers. |

## Risks and limits

- **Correlation, not causation.** Late orders may also differ in product, region or seller. A carrier test or A/B test is needed before promising review gains.
- **Revenue is item prices only (BRL).** There is no cost data, so this memo says nothing about profit or margin.
- **Customer identity.** Repeat rates use `customer_unique_id`; counting by `customer_id` would show $repeat_rate_by_customer_id (every order gets a new `customer_id`).
- **Data quality.** $dq_summary See `outputs/dq_log.csv`.
- **Public historical data** from one Brazilian marketplace. The pattern needs checking before it is applied to any other shop.
