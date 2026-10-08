"""The nine Olist CSV files and the columns the pipeline needs from each.

Source: "Brazilian E-Commerce Public Dataset by Olist" on Kaggle (olistbr/brazilian-ecommerce).
The check runs BEFORE anything is loaded, so a wrong or partial download fails fast with a
clear message instead of a confusing SQL error later.
"""

import csv
from pathlib import Path

# DuckDB table suffix -> (file name, required columns). Extra columns are allowed.
EXPECTED_FILES: dict[str, tuple[str, list[str]]] = {
    "customers": (
        "olist_customers_dataset.csv",
        [
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ],
    ),
    "geolocation": (
        "olist_geolocation_dataset.csv",
        [
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng",
            "geolocation_city",
            "geolocation_state",
        ],
    ),
    "order_items": (
        "olist_order_items_dataset.csv",
        [
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "shipping_limit_date",
            "price",
            "freight_value",
        ],
    ),
    "payments": (
        "olist_order_payments_dataset.csv",
        [
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_installments",
            "payment_value",
        ],
    ),
    "reviews": (
        "olist_order_reviews_dataset.csv",
        [
            "review_id",
            "order_id",
            "review_score",
            "review_comment_title",
            "review_comment_message",
            "review_creation_date",
            "review_answer_timestamp",
        ],
    ),
    "orders": (
        "olist_orders_dataset.csv",
        [
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    ),
    "products": (
        "olist_products_dataset.csv",
        [
            "product_id",
            "product_category_name",
            "product_name_length",
            "product_description_length",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ],
    ),
    "sellers": (
        "olist_sellers_dataset.csv",
        ["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"],
    ),
    "category_translation": (
        "product_category_name_translation.csv",
        ["product_category_name", "product_category_name_english"],
    ),
}

# The original products file spells "length" as "lenght". We accept both spellings
# and always use the correct one after loading.
COLUMN_RENAMES = {
    "product_name_lenght": "product_name_length",
    "product_description_lenght": "product_description_length",
}


class SchemaError(Exception):
    """Raised when the raw files are missing or do not have the expected columns."""


def normalise_column(name: str) -> str:
    """Strip a byte-order mark and spaces, lower-case, and fix known misspellings."""
    clean = name.replace("﻿", "").strip().strip('"').lower()
    return COLUMN_RENAMES.get(clean, clean)


def read_header(path: Path) -> list[str]:
    """Return the normalised column names from the first line of a CSV file."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        header = next(csv.reader(f), [])
    return [normalise_column(col) for col in header]


def check_raw_files(raw_dir: Path) -> list[str]:
    """List every problem with the raw folder. An empty list means the schema is OK."""
    problems = []
    for file_name, columns in EXPECTED_FILES.values():
        path = raw_dir / file_name
        if not path.exists():
            problems.append(f"Missing file: {file_name}")
            continue
        found = read_header(path)
        missing = [col for col in columns if col not in found]
        if missing:
            problems.append(f"{file_name}: missing columns {missing} (found {found})")
    return problems
