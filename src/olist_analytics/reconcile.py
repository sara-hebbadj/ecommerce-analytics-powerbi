"""Reconciliation: the same total, computed two independent ways, must match.

It catches the classic analytics bugs: a join that multiplies rows (fan-out), a filter
applied in one place but not another, or an export that lost rows.
The 'expected_in_powerbi' column is what Sara's Power BI cards should show.
"""

from pathlib import Path

import pandas as pd


def _total(df: pd.DataFrame, column: str) -> float:
    return float(pd.to_numeric(df[column]).sum())


def reconcile(results: dict[str, pd.DataFrame], powerbi_dir: Path) -> pd.DataFrame:
    """Compare SQL answers with sums over the exported Power BI files."""
    orders = pd.read_csv(powerbi_dir / "fact_orders.csv")
    items = pd.read_csv(powerbi_dir / "fact_order_items.csv")
    customers = pd.read_csv(powerbi_dir / "dim_customer.csv")
    delivered = orders[orders["is_delivered"] == 1]
    categories = results["q06_freight_share"]
    all_categories = categories[categories["category"] == "ALL CATEGORIES"].iloc[0]

    checks = [
        # (metric, value from SQL questions, source, value from exported files, source)
        (
            "Delivered orders",
            _total(results["q01_monthly_orders_revenue"], "orders_delivered"),
            "q01 sum of orders_delivered",
            float(len(delivered)),
            "fact_orders.csv rows with is_delivered = 1",
        ),
        (
            "Revenue (BRL, item prices, delivered)",
            _total(results["q01_monthly_orders_revenue"], "revenue_delivered"),
            "q01 sum of revenue_delivered",
            _total(delivered, "item_revenue"),
            "fact_orders.csv sum of item_revenue (delivered)",
        ),
        (
            "Revenue by category adds up to total",
            float(all_categories["revenue"]),
            "q06 ALL CATEGORIES revenue",
            _total(items[items["is_delivered"] == 1], "price"),
            "fact_order_items.csv sum of price (delivered)",
        ),
        (
            "Freight (BRL, delivered)",
            float(all_categories["freight"]),
            "q06 ALL CATEGORIES freight",
            _total(delivered, "freight_value"),
            "fact_orders.csv sum of freight_value (delivered)",
        ),
        (
            "Late orders",
            _total(results["q04_late_delivery_by_state"], "late_orders"),
            "q04 sum of late_orders",
            _total(orders, "is_late"),
            "fact_orders.csv sum of is_late",
        ),
        (
            "Customers with a delivered order",
            float(results["q02_repeat_customer_rate"]["customers"].iloc[0]),
            "q02 customers",
            float((customers["delivered_orders"] >= 1).sum()),
            "dim_customer.csv rows with delivered_orders >= 1",
        ),
        (
            "Repeat customers",
            float(results["q02_repeat_customer_rate"]["repeat_customers"].iloc[0]),
            "q02 repeat_customers",
            _total(customers, "is_repeat_customer"),
            "dim_customer.csv sum of is_repeat_customer",
        ),
    ]
    rows = []
    for metric, sql_value, sql_source, export_value, export_source in checks:
        rows.append(
            {
                "metric": metric,
                "sql_value": round(sql_value, 2),
                "sql_source": sql_source,
                "export_value": round(export_value, 2),
                "export_source": export_source,
                "matches": abs(sql_value - export_value) < 0.005,
                "expected_in_powerbi": round(sql_value, 2),
            }
        )
    return pd.DataFrame(rows)
