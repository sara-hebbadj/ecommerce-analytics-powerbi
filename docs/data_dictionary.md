# Data dictionary

All tables are built by `sql/stage_1_clean.sql` (clean_*) and `sql/stage_2_model.sql`
(fact_* and dim_*). The model tables are exported to `outputs/powerbi/` for Power BI.
Money is in **BRL** (Brazilian reais). Flags are integers: `1` = yes, `0` = no, empty = unknown.

## Grain and keys

| Table | One row per | Key | Joins to |
|---|---|---|---|
| `fact_orders` | order | `order_id` | `dim_customer` (customer_unique_id), `dim_state` (customer_state), `dim_date` (purchase_date) |
| `fact_order_items` | item inside an order | `order_id` + `order_item_id` | `dim_product`, `dim_seller`, `dim_customer`, `dim_state`, `dim_date` |
| `fact_payments` | payment line of an order | `order_id` + `payment_sequential` | `dim_state`, `dim_date` |
| `dim_customer` | real customer (person) | `customer_unique_id` | |
| `dim_product` | product | `product_id` | |
| `dim_seller` | seller | `seller_id` | |
| `dim_state` | Brazilian state (27) | `state_code` | |
| `dim_date` | calendar day (whole years) | `date` | |
| `agg_cohort_retention` | cohort month × months since first order | `cohort_month` + `months_since_first` | (stand-alone) |
| `agg_worst_routes` | seller state → customer state route (top 15) | `route` | (stand-alone) |

## fact_orders

| Column | Type | Meaning |
|---|---|---|
| order_id | text | Olist order ID |
| customer_id | text | **Per-order** customer ID from Olist. Do not use it to count customers. |
| customer_unique_id | text | The real customer (one person can have many `customer_id`s) |
| customer_state, customer_city | text | Customer location for this order (state code such as `SP`) |
| order_status | text | e.g. `delivered`, `shipped`, `canceled`, `unavailable`, `invoiced`, `processing` (check the full list with `SELECT DISTINCT order_status`) |
| purchase_date | date | Day the order was placed |
| purchase_month | date | First day of the purchase month (used for monthly results and cohorts) |
| estimated_date | date | Delivery date promised at checkout |
| delivered_date | date | Day the customer received the order (empty if not delivered) |
| is_delivered | 0/1 | Status is `delivered` |
| is_cancelled | 0/1 | Status is `canceled` or `unavailable` |
| has_valid_delivery | 0/1 | Delivered, with purchase, delivery and estimated dates, and delivery not before purchase |
| is_late | 0/1/empty | `delivered_date > estimated_date` (compared as dates). Empty when `has_valid_delivery = 0` |
| delivery_days | integer | Days from purchase to delivery |
| delay_days | integer | Days after the promised date (negative = early, 0 = on the day) |
| delay_bucket, delay_bucket_order | text, integer | `On time or early`, `1-3 days late`, `4-7`, `8-14`, `15+`; the order column is for sorting |
| items_count | integer | Number of items (units) in the order |
| distinct_products | integer | Number of different products |
| sellers_count | integer | Number of different sellers |
| item_revenue | money | Sum of item prices. **This is "revenue" everywhere in this project.** Excludes freight. |
| freight_value | money | Sum of freight charged on the items |
| payment_value | money | Sum of payments (can differ from items + freight: vouchers, instalment interest) |
| main_payment_type | text | Payment type that paid the largest share of the order |
| review_score | 1–5/empty | Latest review for the order; empty if none or invalid |
| review_answered_before_delivery | 0/1/empty | 1 if the customer answered the review survey BEFORE the parcel arrived (Olist sends the survey when the parcel arrives or when the promised date is due). Empty when there is no review or `has_valid_delivery = 0` |

## fact_order_items

| Column | Type | Meaning |
|---|---|---|
| order_id, order_item_id | text, integer | Order and item number inside the order (1, 2, 3 …) |
| product_id, seller_id | text | Product and seller |
| category | text | English category name (Portuguese if no translation; `unknown` if missing) |
| seller_state | text | Seller's state |
| customer_unique_id, customer_state, purchase_date, purchase_month | | Copied from the order, so item-level visuals can be sliced the same way |
| is_delivered, has_valid_delivery, is_late, review_score | | Copied from the order (order-level facts repeated on each item) |
| price | money | Item price |
| freight_value | money | Freight charged for this item |

## fact_payments

`order_id`, `payment_sequential` (1, 2 …), `payment_type` (`credit_card`, `boleto`,
`voucher`, `debit_card`, `not_defined`), `payment_installments`, `payment_value` (money),
plus `purchase_date`, `purchase_month`, `is_delivered`, `customer_state` from the order.

## dim_customer

| Column | Meaning |
|---|---|
| customer_unique_id | The real customer |
| customer_state, customer_city | Location at the customer's first order |
| first_order_date | First order of any status |
| cohort_month | Month of the first **delivered** order (empty if never delivered) |
| orders_placed | Orders of any status |
| delivered_orders | Delivered orders |
| is_repeat_customer | 1 if `delivered_orders >= 2` |

## dim_product, dim_seller, dim_state, dim_date

- **dim_product:** `product_id`, `category`, `category_pt`, `weight_g`, `photos_qty`, `length_cm`, `height_cm`, `width_cm`. (`clean_products` also has `has_english_name`, used only by the data-quality log: some category names are the same in Portuguese and English, e.g. `pet_shop`.)
- **dim_seller:** `seller_id`, `seller_zip_code_prefix` (5 digits, leading zeros kept), `seller_city`, `seller_state`.
- **dim_state:** `state_code`, `state_name`, `region` (North, Northeast, Central-West, Southeast, South), `map_location` (e.g. "São Paulo, Brazil", for the Power BI map), `latitude`, `longitude` (median of the geolocation points in that state).
- **dim_date:** `date`, `year`, `quarter`, `month_number`, `month_name`, `year_month`, `month_start`, `weekday_number` (1 = Monday), `weekday_name`.

## Raw files (as downloaded)

| File | Rows describe | Notes |
|---|---|---|
| olist_orders_dataset.csv | orders and their status/dates | timestamps as text `YYYY-MM-DD HH:MM:SS` |
| olist_order_items_dataset.csv | items in each order | freight is per item |
| olist_order_payments_dataset.csv | payment lines | one order can have several |
| olist_order_reviews_dataset.csv | customer reviews | comment text has line breaks; not used |
| olist_customers_dataset.csv | customer per order | `customer_id` vs `customer_unique_id` |
| olist_products_dataset.csv | products | columns spelt `..._lenght` in the original |
| olist_sellers_dataset.csv | sellers | |
| olist_geolocation_dataset.csv | zip prefix → lat/lng | many repeated points |
| product_category_name_translation.csv | Portuguese → English category | the DQ log counts categories without a translation |
