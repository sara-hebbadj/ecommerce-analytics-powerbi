# Build the Power BI dashboard, step by step

Time: about 90 minutes the first time. Power BI Desktop is free (Windows only): install it
from the Microsoft Store or https://powerbi.microsoft.com/desktop.

Sara builds this herself: doing it is the interview practice. Menu names below are from
recent Power BI Desktop versions; if a button has moved, search for it in the ribbon's
search box.

## 0. Before you start

1. Run the pipeline on the real data: `python -m olist_analytics.pipeline`.
2. Check the last lines of the output say `Reconciliation: 7 of 7 checks match`.
3. Open `outputs/reconciliation.csv` and keep it open: the `expected_in_powerbi` column is
   what your cards must show at the end (step 8).
4. The files you will import are in `outputs/powerbi/` (10 CSV files).

## 1. Settings for this file

1. Open Power BI Desktop → **Blank report**.
2. **File → Options and settings → Options**:
   - *Current file → Data Load*: untick **Auto date/time** (we bring our own calendar).
   - *Current file → Regional settings*: set **Locale for import** to *English (United States)*
     so `2017-01-05` and `12.50` are read correctly whatever your Windows language is.
   - *Global → Security*: tick **Use Map and Filled Map visuals** (needed for page 1).
3. Save now as `powerbi/olist_dashboard.pbix` (this file is git-ignored; see step 9).

## 2. Import the 10 CSV files

For each file in `outputs/powerbi/`:

1. **Home → Get data → Text/CSV** → pick the file → **Transform Data** (not Load).
2. In Power Query, check the type icon on each column header and fix it if needed:
   - IDs and codes are **Text** (`order_id`, `customer_unique_id`, `product_id`,
     `seller_id`, `customer_state`, `seller_state`, `state_code`, `route`).
   - **`seller_zip_code_prefix` must be Text.** Power Query will guess "Whole number"
     and turn `01001` into `1001`. Click the `123` icon → Text → *Replace current*.
   - Dates are **Date** (`purchase_date`, `purchase_month`, `estimated_date`,
     `delivered_date`, `date`, `month_start`, `first_order_date`, `cohort_month`).
   - Money is **Fixed decimal number** (`item_revenue`, `freight_value`, `payment_value`, `price`).
   - Flags and counts are **Whole number** (`is_delivered`, `is_late`, `items_count`, …).
     Empty cells stay empty (null); that is correct.
3. **Close & Apply**.

Files: `fact_orders`, `fact_order_items`, `fact_payments`, `dim_customer`, `dim_product`,
`dim_seller`, `dim_state`, `dim_date`, `agg_cohort_retention`, `agg_worst_routes`.

Tip: you can import the first file, then use **Home → New Source → Text/CSV** inside Power
Query for the others, and do one **Close & Apply** at the end.

## 3. Model view: relationships, date table, sorting

Open the **Model view** (third icon on the left).

1. **Delete any relationship Power BI created by itself** between `fact_orders` and
   `fact_order_items` (or any other two fact tables). Fact tables only connect through
   dimensions; a direct link creates ambiguous filter paths.
2. Create these relationships by dragging the dimension column onto the fact column.
   All are **one-to-many (1:*)**, **single** cross-filter direction (dimension filters fact):

   | From (one side) | To (many side) |
   |---|---|
   | `dim_date[date]` | `fact_orders[purchase_date]` |
   | `dim_date[date]` | `fact_order_items[purchase_date]` |
   | `dim_date[date]` | `fact_payments[purchase_date]` |
   | `dim_state[state_code]` | `fact_orders[customer_state]` |
   | `dim_state[state_code]` | `fact_order_items[customer_state]` |
   | `dim_state[state_code]` | `fact_payments[customer_state]` |
   | `dim_customer[customer_unique_id]` | `fact_orders[customer_unique_id]` |
   | `dim_customer[customer_unique_id]` | `fact_order_items[customer_unique_id]` |
   | `dim_product[product_id]` | `fact_order_items[product_id]` |
   | `dim_seller[seller_id]` | `fact_order_items[seller_id]` |

   `agg_cohort_retention` and `agg_worst_routes` stay unconnected (they are ready-made
   summaries from SQL).
3. **Mark the date table:** select `dim_date` → **Table tools → Mark as date table** →
   choose the `date` column.
4. **Sort columns** (Data view → select the column → **Column tools → Sort by column**):
   - `dim_date[month_name]` by `month_number`;
   - `fact_orders[delay_bucket]` by `delay_bucket_order`.
5. **Map fields** (select the column → **Column tools → Data category**):
   `dim_state[map_location]` = *Place*, `dim_state[latitude]` = *Latitude*,
   `dim_state[longitude]` = *Longitude*.
6. Hide technical columns from report view (right-click → *Hide in report view*):
   `customer_id`, `delay_bucket_order`, `month_number`.

Interview angle: "Why two fact tables?" Orders and items have different grains (one row per
order vs one row per item). Putting order-level facts like review score on the item table
would count an order with 3 items three times, so each measure uses the table at the right
grain.

## 4. Measures

1. **Home → Enter data** → name the table `_Measures` → **Load** (an empty helper table).
2. Select `_Measures` → **New measure** → paste each measure from `docs/measures.md` (one at
   a time) → set its format as listed there.
3. Once there are measures in it, you can delete the empty `Column1` from `_Measures`.

## 5. Page 1: Sales

Rename the page **Sales**. Add:

| Visual | Fields | Settings |
|---|---|---|
| 4 × **Card** | `Revenue`, `Delivered Orders`, `Average Order Value`, `Freight Share %` | One card each, in a row at the top |
| **Line chart** "Monthly revenue" | X: `dim_date[month_start]`; Y: `Revenue` | X-axis type *Categorical* if dates look crowded. Note in the subtitle that the first and last months are partial (see `is_partial_month` in `outputs/results/q01_monthly_orders_revenue.csv`; on the real data the full months are Jan 2017 to Aug 2018, so filter the visual to those months). |
| **Clustered bar chart** "Top 10 categories" | Y: `fact_order_items[category]`; X: `Item Revenue` | Filters pane → category → *Top N* = 10 by `Item Revenue` |
| **Filled map** (or **Map**) "Revenue by state" | Location: `dim_state[map_location]` (or Latitude/Longitude); Color saturation / Bubble size: `Revenue` | Tooltips: `Delivered Orders` |
| **Donut** or **bar** "How customers pay" | Legend/axis: `fact_payments[payment_type]`; Values: `Payment Value` | |
| **Slicers** | `dim_date[year]`, `dim_state[region]` | Put them in one row under the title |

## 6. Page 2: Customers

| Visual | Fields | Settings |
|---|---|---|
| 3 × **Card** | `Customers`, `Repeat Customers`, `Repeat Rate %` | Subtitle: "lifetime, not affected by date slicers" |
| **Matrix** "Cohort retention (%)" | Rows: `agg_cohort_retention[cohort_month]`; Columns: `months_since_first`; Values: `retention_pct` (set to **Sum**, there is one value per cell) | Filters: `months_since_first` between 1 and 6; `cohort_size` ≥ 100. Values → **Conditional formatting → Background color** (gradient, light to dark blue). |
| **Column chart** "Delivered orders per customer" | X: `dim_customer[delivered_orders]`; Y: Count of `customer_unique_id` | Shows how many people bought once, twice, … |
| **Slicer** | `dim_customer[customer_state]` | |

## 7. Page 3: Delivery and experience

| Visual | Fields | Settings |
|---|---|---|
| 3 × **Card** | `Late Rate %`, `Avg Delivery Days`, `Avg Review Score` | |
| **Column chart** "Review score by days late" (the key chart) | X: `fact_orders[delay_bucket]`; Y: `Avg Review Score` | Filter: `delay_bucket` *is not blank*. Data labels on. Add a text box: "Correlation, not proof of cause." |
| **Clustered bar chart** "Late rate by state" | Y: `dim_state[state_code]`; X: `Late Rate %` | Sort by `Late Rate %` descending. Visual filter: `Orders With Delivery Date` *is greater than or equal to* 100. Tooltip: `Orders With Delivery Date`. |
| **Table** "Worst routes (seller state → customer state)" | `agg_worst_routes[route]`, `orders`, `late_orders`, `late_rate_pct` | Sort by `late_rate_pct` descending |
| **Line chart** (optional) "Low reviews by days late" | X: `fact_orders[delay_bucket]`; Y: `Low Review Share %` | Same blank filter |
| **Line on the key chart** (secondary axis) "Answered before delivery" | Add `Answered Before Delivery %` as the line value of the "Review score by days late" chart (Line and clustered column chart) | Shows that, for very late orders, most reviews were written before the parcel arrived (see `q11`). |
| **Slicers** | `dim_date[year]`, `dim_state[region]` | |

Add the footer text box on every page: *"Data: Brazilian E-Commerce Public Dataset by Olist
(Kaggle, version 2), licensed CC BY-NC-SA 4.0. Revenue = item prices of delivered orders, BRL."*

## 8. Check the totals

Clear all slicers, then compare the cards with `outputs/reconciliation.csv`
(`expected_in_powerbi`), as listed at the end of `docs/measures.md`. Write the result in
the README "Results" table (for example "Power BI cards match SQL: 5 of 5, checked on <date>").

## 9. Save, export and screenshot

1. **Save** `powerbi/olist_dashboard.pbix`. Do **not** commit it: a `.pbix` contains a full
   copy of every imported row, which would re-publish the Olist data. (It is git-ignored.)
2. **File → Export → Power BI template** → `powerbi/olist_dashboard.pbit`. A template keeps
   the model, measures and pages but no data. Anyone can open it and point it at their own
   download. Note: the template stores the CSV file paths, which include your Windows user
   name. Optional fix: **Home → Transform data → Manage parameters → New** parameter
   `DataFolder`, and use it in each query's `Source` step instead of the full path.
3. **File → Export → Export to PDF** → `powerbi/olist_dashboard.pdf`.
4. Screenshot each page (Windows: `Win + Shift + S`) and save them as
   `docs/screenshots/page1_sales.png`, `page2_customers.png`, `page3_delivery.png`.
5. Record the 2-minute walkthrough video (one minute per finding, 30 seconds on data quality).
