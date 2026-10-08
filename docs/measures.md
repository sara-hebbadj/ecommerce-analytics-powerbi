# DAX measures

Create these in Power BI Desktop (see `docs/POWERBI_STEPS.md`, step 4). Each measure has the
same definition as the SQL question it mirrors, so the dashboard and `outputs/results/`
agree; the "Check" column says which number in `outputs/reconciliation.csv` it must match.

Conventions: flags are integers (`1` = yes); money is BRL; all measures live in one empty
table called `_Measures` so they are easy to find.

## Sales

```DAX
Orders Placed = COUNTROWS ( fact_orders )

Delivered Orders =
CALCULATE ( COUNTROWS ( fact_orders ), fact_orders[is_delivered] = 1 )

Revenue =
-- Item prices of delivered orders, excluding freight (same as q01 revenue_delivered)
CALCULATE ( SUM ( fact_orders[item_revenue] ), fact_orders[is_delivered] = 1 )

Average Order Value = DIVIDE ( [Revenue], [Delivered Orders] )

Revenue MoM % =
-- Needs dim_date marked as the date table and a month on the visual's axis
VAR CurrentRevenue = [Revenue]
VAR PreviousRevenue = CALCULATE ( [Revenue], DATEADD ( dim_date[date], -1, MONTH ) )
RETURN DIVIDE ( CurrentRevenue - PreviousRevenue, PreviousRevenue )

Item Revenue =
-- Same revenue, summed on the ITEM table: use it with category, product and seller fields
CALCULATE ( SUM ( fact_order_items[price] ), fact_order_items[is_delivered] = 1 )

Freight Share % =
DIVIDE (
    CALCULATE ( SUM ( fact_order_items[freight_value] ), fact_order_items[is_delivered] = 1 ),
    [Item Revenue]
)

Payment Value =
CALCULATE ( SUM ( fact_payments[payment_value] ), fact_payments[is_delivered] = 1 )
```

## Customers

```DAX
Customers =
-- Real customers (customer_unique_id) with at least one delivered order.
-- Lifetime number: based on dim_customer, so date slicers do not change it.
CALCULATE ( COUNTROWS ( dim_customer ), dim_customer[delivered_orders] >= 1 )

Repeat Customers =
CALCULATE ( COUNTROWS ( dim_customer ), dim_customer[is_repeat_customer] = 1 )

Repeat Rate % = DIVIDE ( [Repeat Customers], [Customers] )
```

Why `dim_customer` and not `DISTINCTCOUNT(fact_orders[customer_id])`? Olist gives every
order a new `customer_id`, so that count equals the number of orders and the repeat rate
would be 0%. `customer_unique_id` is the person.

## Delivery and experience

```DAX
Orders With Delivery Date =
-- Delivered orders whose dates can be used (q04 delivered_orders)
CALCULATE ( COUNTROWS ( fact_orders ), fact_orders[has_valid_delivery] = 1 )

Late Orders =
CALCULATE ( COUNTROWS ( fact_orders ), fact_orders[is_late] = 1 )

Late Rate % = DIVIDE ( [Late Orders], [Orders With Delivery Date] )

Avg Delivery Days =
CALCULATE ( AVERAGE ( fact_orders[delivery_days] ), fact_orders[has_valid_delivery] = 1 )

Avg Review Score =
-- AVERAGE ignores blank scores (orders without a review)
CALCULATE ( AVERAGE ( fact_orders[review_score] ), fact_orders[is_delivered] = 1 )

Low Review Share % =
-- Share of reviewed, delivered orders with 1 or 2 stars
DIVIDE (
    CALCULATE (
        COUNTROWS ( fact_orders ),
        fact_orders[review_score] <= 2,
        NOT ISBLANK ( fact_orders[review_score] ),
        fact_orders[is_delivered] = 1
    ),
    CALCULATE (
        COUNTROWS ( fact_orders ),
        NOT ISBLANK ( fact_orders[review_score] ),
        fact_orders[is_delivered] = 1
    )
)

Avg Review (orders in category) =
-- For category visuals: each ORDER counts once, even if it has 3 items in the category
-- (same rule as q03). SUMMARIZE makes one row per order before averaging.
AVERAGEX (
    SUMMARIZE (
        FILTER (
            fact_order_items,
            fact_order_items[is_delivered] = 1
                && NOT ISBLANK ( fact_order_items[review_score] )
        ),
        fact_order_items[order_id],
        fact_order_items[review_score]
    ),
    fact_order_items[review_score]
)
```

## Formats

| Measure | Format |
|---|---|
| Revenue, Item Revenue, Average Order Value, Payment Value | Decimal number, 0 decimals, thousands separator (prefix "BRL " in the visual title, not in the number) |
| Revenue MoM %, Freight Share %, Repeat Rate %, Late Rate %, Low Review Share % | Percentage, 1 decimal |
| Avg Review Score, Avg Review (orders in category) | Decimal number, 2 decimals |
| Avg Delivery Days | Decimal number, 1 decimal |
| Counts | Whole number, thousands separator |

## Check against the SQL (do this once after building)

With **no slicers selected**, these cards must equal `expected_in_powerbi` in
`outputs/reconciliation.csv`:

| Measure | Row in reconciliation.csv |
|---|---|
| Delivered Orders | Delivered orders |
| Revenue and Item Revenue | Revenue (BRL, item prices, delivered) |
| Late Orders | Late orders |
| Customers | Customers with a delivered order |
| Repeat Customers | Repeat customers |

If a number differs, the usual causes are: a relationship that should not exist (for
example `fact_orders` ↔ `fact_order_items`), a column imported with the wrong type, or a
slicer or page filter still applied.
