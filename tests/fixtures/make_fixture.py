"""Write the SYNTHETIC test fixture: 9 tiny CSV files shaped exactly like the Olist files.

Every row was hand-designed by the coding agent to exercise one rule, so the tests can
check exact answers worked out by hand (see olist_synthetic/README.md).
Nothing here comes from the real Olist dataset. Re-create the files with:

    python tests/fixtures/make_fixture.py
"""

import csv
from pathlib import Path

OUT = Path(__file__).parent / "olist_synthetic"


def write(name: str, header: list[str], rows: list[list], encoding: str = "utf-8") -> None:
    with open(OUT / name, "w", newline="", encoding=encoding) as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def customers() -> None:
    # customer_id is per ORDER (cNN = order oNN); customer_unique_id is the person (A..H).
    people = {
        "c01": ("uniq_A", "1310", "sao paulo", "SP"),  # zip lost its leading zero
        "c02": ("uniq_A", "01310", "sao paulo", "SP"),
        "c03": ("uniq_B", "20040", "rio de janeiro", "RJ"),
        "c04": ("uniq_C", "30130", "belo horizonte", "MG"),
        "c05": ("uniq_D", "01310", "sao paulo", "SP"),
        "c06": ("uniq_D", "01310", "sao paulo", "SP"),
        "c07": ("uniq_E", "80010", "curitiba", "PR"),
        "c08": ("uniq_E", "80010", "curitiba", "PR"),
        "c09": ("uniq_F", "40010", "salvador", "BA"),
        "c10": ("uniq_B", "20040", "rio de janeiro", "RJ"),
        "c11": ("uniq_C", "30130", "belo horizonte", "MG"),
        "c12": ("uniq_G", "69005", "manaus", "AM"),
        "c13": ("uniq_H", "01310", "sao paulo", "SP"),
    }
    write(
        "olist_customers_dataset.csv",
        [
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ],
        [[cid, *values] for cid, values in people.items()],
    )


def orders() -> None:
    header = [
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    o03 = [
        "o03",
        "c03",
        "delivered",
        "2017-01-12 08:00:00",
        "2017-01-12 09:00:00",
        "2017-01-14 10:00:00",
        "2017-01-29 12:00:00",
        "2017-01-30 00:00:00",
    ]
    rows = [
        # on time (5 days early)
        [
            "o01",
            "c01",
            "delivered",
            "2017-01-05 10:00:00",
            "2017-01-05 11:00:00",
            "2017-01-07 09:00:00",
            "2017-01-15 14:00:00",
            "2017-01-20 00:00:00",
        ],
        # 3 days late
        [
            "o02",
            "c02",
            "delivered",
            "2017-02-10 09:30:00",
            "2017-02-10 10:00:00",
            "2017-02-12 09:00:00",
            "2017-02-28 16:00:00",
            "2017-02-25 00:00:00",
        ],
        o03,
        o03,  # exact duplicate row
        # 10 days late
        [
            "o04",
            "c04",
            "delivered",
            "2017-01-20 20:00:00",
            "2017-01-21 08:00:00",
            "2017-01-23 09:00:00",
            "2017-02-15 10:00:00",
            "2017-02-05 00:00:00",
        ],
        # cancelled, but has a delivery date (status wins)
        [
            "o05",
            "c05",
            "canceled",
            "2017-02-03 12:00:00",
            "2017-02-03 13:00:00",
            "",
            "2017-02-15 10:00:00",
            "2017-02-20 00:00:00",
        ],
        [
            "o06",
            "c06",
            "delivered",
            "2017-03-01 10:00:00",
            "2017-03-01 11:00:00",
            "2017-03-03 09:00:00",
            "2017-03-10 10:00:00",
            "2017-03-15 00:00:00",
        ],
        # delivered at 18:00 ON the promised date -> on time
        [
            "o07",
            "c07",
            "delivered",
            "2017-03-05 15:00:00",
            "2017-03-05 16:00:00",
            "2017-03-07 09:00:00",
            "2017-03-20 18:00:00",
            "2017-03-20 00:00:00",
        ],
        [
            "o08",
            "c08",
            "delivered",
            "2017-04-02 11:00:00",
            "2017-04-02 12:00:00",
            "2017-04-04 09:00:00",
            "2017-04-10 10:00:00",
            "2017-04-20 00:00:00",
        ],
        # delivered status but NO delivery date
        [
            "o09",
            "c09",
            "delivered",
            "2017-02-14 13:00:00",
            "2017-02-14 14:00:00",
            "2017-02-16 09:00:00",
            "",
            "2017-03-01 00:00:00",
        ],
        # still in transit
        [
            "o10",
            "c10",
            "shipped",
            "2017-04-25 09:00:00",
            "2017-04-25 10:00:00",
            "2017-04-26 09:00:00",
            "",
            "2017-05-10 00:00:00",
        ],
        [
            "o11",
            "c11",
            "delivered",
            "2017-04-01 10:00:00",
            "2017-04-01 11:00:00",
            "2017-04-03 09:00:00",
            "2017-04-08 10:00:00",
            "2017-04-10 00:00:00",
        ],
        # delivered BEFORE it was purchased (impossible)
        [
            "o12",
            "c12",
            "delivered",
            "2017-03-10 10:00:00",
            "2017-03-10 11:00:00",
            "2017-03-11 09:00:00",
            "2017-03-05 10:00:00",
            "2017-03-25 00:00:00",
        ],
        ["o13", "c13", "unavailable", "2017-03-20 10:00:00", "", "", "", "2017-04-05 00:00:00"],
    ]
    write("olist_orders_dataset.csv", header, rows)


def order_items() -> None:
    header = [
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "shipping_limit_date",
        "price",
        "freight_value",
    ]
    limit = "2017-01-10 00:00:00"
    o03_item = ["o03", "1", "p06", "s01", limit, "50.00", "15.00"]
    rows = [
        ["o01", "1", "p01", "s01", limit, "100.00", "10.00"],
        ["o02", "1", "p02", "s01", limit, "200.00", "20.00"],
        o03_item,
        o03_item,  # exact duplicate row
        ["o04", "1", "p03", "s03", limit, "300.00", "60.00"],  # two sellers in one order
        ["o04", "2", "p01", "s01", limit, "100.00", "10.00"],
        ["o05", "1", "p01", "s01", limit, "100.00", "10.00"],
        ["o06", "1", "p01", "s02", limit, "80.00", "12.00"],  # 3 units of one product
        ["o06", "2", "p01", "s02", limit, "80.00", "12.00"],
        ["o06", "3", "p01", "s02", limit, "80.00", "12.00"],
        ["o07", "1", "p04", "s02", limit, "40.00", "8.00"],
        ["o08", "1", "p05", "s02", limit, "500.00", "25.00"],
        ["o09", "1", "p06", "s01", limit, "60.00", "9.00"],
        ["o10", "1", "p02", "s03", limit, "150.00", "20.00"],
        ["o11", "1", "p03", "s03", limit, "260.00", "50.00"],
        ["o12", "1", "p02", "s01", limit, "120.00", "15.00"],
        ["o99", "1", "p01", "s01", limit, "10.00", "1.00"],  # order o99 does not exist
    ]
    write("olist_order_items_dataset.csv", header, rows)


def payments() -> None:
    header = [
        "order_id",
        "payment_sequential",
        "payment_type",
        "payment_installments",
        "payment_value",
    ]
    rows = [
        ["o01", "1", "credit_card", "2", "110.00"],
        ["o02", "1", "credit_card", "3", "220.00"],
        ["o03", "1", "boleto", "1", "65.00"],
        ["o04", "1", "credit_card", "4", "400.00"],
        ["o04", "2", "voucher", "1", "70.00"],
        ["o05", "1", "not_defined", "1", "0.00"],
        ["o06", "1", "credit_card", "1", "276.00"],
        ["o07", "1", "debit_card", "1", "48.00"],
        ["o08", "1", "credit_card", "5", "525.00"],
        ["o09", "1", "boleto", "1", "69.00"],
        ["o10", "1", "credit_card", "2", "170.00"],
        ["o11", "1", "credit_card", "3", "310.00"],
        ["o12", "1", "voucher", "1", "100.00"],  # differs from items + freight (135.00)
    ]
    write("olist_order_payments_dataset.csv", header, rows)


def reviews() -> None:
    header = [
        "review_id",
        "order_id",
        "review_score",
        "review_comment_title",
        "review_comment_message",
        "review_creation_date",
        "review_answer_timestamp",
    ]

    def review(rid, oid, score, created, answered, message=""):
        return [rid, oid, score, "", message, created, answered]

    rows = [
        review("r01", "o01", "5", "2017-01-16 00:00:00", "2017-01-17 10:00:00"),
        review(
            "r02",
            "o02",
            "2",
            "2017-03-01 00:00:00",
            "2017-03-02 10:00:00",
            "chegou atrasado.\nnao gostei",
        ),  # synthetic text with a line break
        review("r03", "o03", "4", "2017-01-30 00:00:00", "2017-01-31 10:00:00"),
        review("r04", "o04", "1", "2017-02-16 00:00:00", "2017-02-17 10:00:00"),
        review("r05", "o05", "1", "2017-02-16 00:00:00", "2017-02-17 10:00:00"),
        review("r06", "o06", "5", "2017-03-11 00:00:00", "2017-03-12 10:00:00"),
        review("r06", "o13", "5", "2017-03-21 00:00:00", "2017-03-22 10:00:00"),  # reused id
        review("r07", "o07", "4", "2017-03-21 00:00:00", "2017-03-22 10:00:00"),
        review("r08a", "o08", "3", "2017-04-11 00:00:00", "2017-04-12 10:00:00"),
        review("r08b", "o08", "5", "2017-04-15 00:00:00", "2017-04-16 10:00:00"),  # latest
        review("r09", "o09", "3", "2017-03-02 00:00:00", "2017-03-03 10:00:00"),
        review("r10", "o10", "6", "2017-05-01 00:00:00", "2017-05-02 10:00:00"),  # bad score
        review("r11", "o11", "4", "2017-04-09 00:00:00", "2017-04-10 10:00:00"),
        # o12 has no review on purpose
    ]
    write("olist_order_reviews_dataset.csv", header, rows)


def products() -> None:
    # Header keeps the original Olist misspelling "lenght" to test the rename.
    header = [
        "product_id",
        "product_category_name",
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ]
    rows = [
        ["p01", "beleza_saude", "40", "300", "2", "500", "20", "10", "15"],
        ["p02", "informatica_acessorios", "45", "800", "3", "1200", "30", "10", "20"],
        ["p03", "moveis_decoracao", "50", "600", "4", "8000", "60", "40", "50"],
        ["p04", "", "", "", "", "300", "15", "10", "10"],  # missing category
        ["p05", "pc_gamer", "35", "500", "1", "2500", "40", "20", "30"],  # no translation
        ["p06", "beleza_saude", "30", "200", "1", "300", "15", "8", "10"],
    ]
    write("olist_products_dataset.csv", header, rows)


def sellers() -> None:
    write(
        "olist_sellers_dataset.csv",
        ["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"],
        [
            ["s01", "01001", "sao paulo", "SP"],
            ["s02", "80020", "curitiba", "PR"],
            ["s03", "30140", "belo horizonte", "MG"],
        ],
    )


def geolocation() -> None:
    header = [
        "geolocation_zip_code_prefix",
        "geolocation_lat",
        "geolocation_lng",
        "geolocation_city",
        "geolocation_state",
    ]
    sp = ["01310", "-23.56", "-46.65", "sao paulo", "SP"]
    rows = [
        sp,
        sp,  # exact duplicate
        ["20040", "-22.90", "-43.18", "rio de janeiro", "RJ"],
        ["30130", "-19.92", "-43.94", "belo horizonte", "MG"],
        ["80010", "-25.43", "-49.27", "curitiba", "PR"],
        ["40010", "-12.97", "-38.51", "salvador", "BA"],
        ["69005", "-3.13", "-60.02", "manaus", "AM"],
        ["01311", "38.70", "-9.14", "sao paulo", "SP"],  # point far outside Brazil
    ]
    write("olist_geolocation_dataset.csv", header, rows)


def category_translation() -> None:
    # Written with a byte-order mark (BOM) to test that the loader strips it.
    write(
        "product_category_name_translation.csv",
        ["product_category_name", "product_category_name_english"],
        [
            ["beleza_saude", "health_beauty"],
            ["informatica_acessorios", "computers_accessories"],
            ["moveis_decoracao", "furniture_decor"],
        ],
        encoding="utf-8-sig",
    )


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for make in (
        customers,
        orders,
        order_items,
        payments,
        reviews,
        products,
        sellers,
        geolocation,
        category_translation,
    ):
        make()
    print(f"Synthetic fixture written to {OUT}")
