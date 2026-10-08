# Decision memo: delivery, repeat customers and freight

**Data:** Brazilian E-Commerce Public Dataset by Olist (Kaggle, version 2; licence CC BY-NC-SA 4.0) · Sep 2016 to Oct 2018 · 96,478 delivered orders · BRL 13,221,498 product revenue (item prices, excluding freight)

**To:** Head of Marketplace Operations (a fictional reader for this portfolio exercise) · **From:** Sara Hebbadj · **Draft generated:** 2026-10-08

Every number below is filled in by `python -m olist_analytics.pipeline` from `outputs/results/`. Nothing is typed by hand. Partial months flagged in the data: Sep 2016, Oct 2016, Dec 2016, Sep 2018, Oct 2018.

## Three findings

_TODO (Sara): after checking the numbers, turn each bold heading into a one-line conclusion._

1. **Late deliveries and review scores.** 6.8% of delivered orders arrived after the date promised at checkout. Late orders averaged **2.27** stars against **4.29** for on-time orders (a gap of 2.02 stars; 95% confidence interval 1.98 to 2.06), and 62.4% of late orders got 1–2 stars against 9.3% of on-time orders. By days late: On time or early 4.29 (n=89,443); 1-3 days late 3.29 (n=1,852); 4-7 days late 2.10 (n=1,748); 8-14 days late 1.67 (n=1,446); 15+ days late 1.72 (n=1,335). 70.1% of the late orders' reviews were answered before the parcel arrived; the 1,908 late orders reviewed after delivery averaged 3.72 stars. Highest late rates (states with enough orders): AL (21.4%), MA (17.4%), SE (15.2%).
2. **Repeat customers.** 3.0% of 93,358 customers placed a second delivered order; 786 of those 2,801 (28.1%) placed all their orders on the same day (a split basket, not a return). Counting only customers who came back on a later day: 2.2%, after a median of 74 days. In the month after their first order, 0.5% of customers bought again (weighted over 22 cohorts).
3. **Category concentration and freight.** The top 3 categories (health_beauty, watches_gifts, bed_bath_table) bring 25.9% of revenue. Freight costs 16.6% of the item value overall; the heaviest categories with enough orders are christmas_supplies (36.5%), signaling_and_security (30.4%), electronics (29.5%), food_drink (29.4%), furniture_living_room (26.3%).

## Three recommendations

| # | Recommendation (Sara: rewrite in your own words) | Expected impact (what-if, computed) | Assumptions |
|---|---|---|---|
| 1 | **TODO (Sara):** e.g. review the delivery-date promise and carrier performance in AL, MA, SE, PI, CE first. | If the 5 worst states had the national late rate: about **286 fewer late orders** and **152 fewer 1–2 star reviews** over the period. | Treats the lateness–review link as if it were causal (it is only a correlation). Same order volume. |
| 2 | **TODO (Sara):** e.g. a second-order offer timed around day 74 after the first purchase. | Each +1 point of repeat rate ≈ **934 more repeat customers** ≈ **BRL 127,939** extra revenue over the period. | Each extra repeat customer places one more order at today's average order value (BRL 137). No campaign cost included. |
| 3 | **TODO (Sara):** e.g. test free-shipping thresholds or packaging changes in christmas_supplies, signaling_and_security, electronics, food_drink, furniture_living_room. | If those categories had the overall freight share: **BRL 32,979 less freight** over the period. | Same sales volume and mix; freight savings would be shared between customers and sellers. |

## Risks and limits

- **Correlation, not causation.** Late orders may also differ in product, region or seller. A carrier test or A/B test is needed before promising review gains.
- **When the review was written.** Olist emails the review survey when the parcel arrives or when the promised date is due, so a late-order review can rate the wait itself: 70.1% of late orders' reviews were answered before delivery. Customers who answered after delivery are a self-selected group, so their average (3.72) is not a clean "effect of lateness" either.
- **Definition of "late".** Late compares the delivery DATE with the promised date. Comparing timestamps instead would put the late rate at 8.1% instead of 6.8%.
- **Revenue is item prices only (BRL).** There is no cost data, so this memo says nothing about profit or margin.
- **Customer identity.** Repeat rates use `customer_unique_id`; counting by `customer_id` would show 0.0% (every order gets a new `customer_id`). Including same-day orders, the median gap from first to second order is 29 days.
- **Data quality.** Delivered orders without a delivery date: 8; with a delivery date before the purchase date: 0 (both left out of lateness metrics). Products without a category: 610. See `outputs/dq_log.csv`.
- **Public historical data** from one Brazilian marketplace. The pattern needs checking before it is applied to any other shop.

---

## DRAFT recommendation wording by the coding agent (not Sara's: rewrite or delete)

_Written to fit any run of this pipeline, so it makes no claim about the direction or size of a result. The data-specific conclusions for the real run are in the README "Results" section._

1. Start with the states where late deliveries are most common (AL, MA, SE, PI, CE): compare carriers and check whether the promised dates there are realistic. Then run a controlled test (for example, a more cautious promised date for a random half of orders) to see whether reviews actually change, because the numbers above show an association, not a cause.
2. Test a second-order offer timed around day 74 after the first purchase, with a random hold-out group, and measure the repeat rate on a later day (so same-day split orders do not count as returns).
3. Pilot free-shipping thresholds or packaging changes in one high-freight category (christmas_supplies, signaling_and_security, electronics, food_drink, furniture_living_room) before any wider change, and track freight cost and conversion together.
