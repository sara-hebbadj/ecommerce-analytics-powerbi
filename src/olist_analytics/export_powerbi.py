"""Export tidy CSV tables for Power BI (outputs/powerbi/).

These files are row-level copies of the Olist data, so they are git-ignored and stay on
your computer. Power BI Desktop imports them with Get Data -> Text/CSV
(see docs/POWERBI_STEPS.md).
"""

from pathlib import Path

import duckdb
import pandas as pd

# Model tables built in sql/stage_2_model.sql, exported as-is.
MODEL_TABLES = [
    "fact_orders",
    "fact_order_items",
    "fact_payments",
    "dim_customer",
    "dim_product",
    "dim_seller",
    "dim_state",
    "dim_date",
]

# Small pre-aggregated tables that are easier in SQL than in DAX.
AGGREGATE_TABLES = {
    "agg_cohort_retention": "q07_cohort_retention",
    "agg_worst_routes": "q12_worst_routes",
}


def export_powerbi_tables(
    con: duckdb.DuckDBPyConnection, results: dict[str, pd.DataFrame], powerbi_dir: Path
) -> list[Path]:
    """Write every model table and aggregate table as a CSV file; return the file paths."""
    powerbi_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for table in MODEL_TABLES:
        path = powerbi_dir / f"{table}.csv"
        safe_path = str(path).replace("'", "''")
        con.execute(f"COPY {table} TO '{safe_path}' (HEADER, DELIMITER ',')")
        written.append(path)
    for table, result_name in AGGREGATE_TABLES.items():
        path = powerbi_dir / f"{table}.csv"
        results[result_name].to_csv(path, index=False)
        written.append(path)
    return written
