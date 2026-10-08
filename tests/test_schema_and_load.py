"""Schema checks and loading: a wrong download must fail fast with a clear message."""

import shutil
import zipfile

import duckdb
import pytest

from olist_analytics.config import FIXTURE_DIR
from olist_analytics.load import load_raw_tables, locate_csv_folder
from olist_analytics.pipeline import check_schema
from olist_analytics.schema import EXPECTED_FILES, SchemaError, check_raw_files, read_header


@pytest.fixture
def raw_copy(tmp_path):
    """A writable copy of the synthetic fixture."""
    target = tmp_path / "raw"
    shutil.copytree(FIXTURE_DIR, target, ignore=shutil.ignore_patterns("*.md"))
    return target


def test_fixture_has_exactly_the_olist_files_and_passes():
    assert check_raw_files(FIXTURE_DIR) == []
    names = {file_name for file_name, _ in EXPECTED_FILES.values()}
    assert names == {p.name for p in FIXTURE_DIR.glob("*.csv")}


def test_missing_file_is_reported(raw_copy):
    (raw_copy / "olist_orders_dataset.csv").unlink()
    problems = check_raw_files(raw_copy)
    assert problems == ["Missing file: olist_orders_dataset.csv"]


def test_missing_column_is_reported(raw_copy):
    path = raw_copy / "olist_sellers_dataset.csv"
    lines = path.read_text().splitlines()
    lines[0] = lines[0].replace("seller_state", "seller_region")
    path.write_text("\n".join(lines) + "\n")
    problems = check_raw_files(raw_copy)
    assert len(problems) == 1 and "seller_state" in problems[0]
    with pytest.raises(SchemaError, match="data/README.md"):
        check_schema(raw_copy)


def test_original_misspelling_lenght_is_accepted():
    header = read_header(FIXTURE_DIR / "olist_products_dataset.csv")
    assert "product_name_length" in header and "product_name_lenght" not in header


def test_byte_order_mark_is_stripped():
    raw_bytes = (FIXTURE_DIR / "product_category_name_translation.csv").read_bytes()
    assert raw_bytes.startswith(b"\xef\xbb\xbf")  # the fixture really has a BOM
    assert read_header(FIXTURE_DIR / "product_category_name_translation.csv")[0] == (
        "product_category_name"
    )


def test_csv_folder_one_level_down_is_found(tmp_path):
    shutil.copytree(FIXTURE_DIR, tmp_path / "raw" / "archive")
    assert locate_csv_folder(tmp_path / "raw") == tmp_path / "raw" / "archive"


def test_kaggle_zip_is_extracted(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    with zipfile.ZipFile(raw / "archive.zip", "w") as archive:
        for csv_file in FIXTURE_DIR.glob("*.csv"):
            archive.write(csv_file, arcname=csv_file.name)
    assert locate_csv_folder(raw) == raw
    assert check_raw_files(raw) == []


def test_load_keeps_every_row_and_loads_text_only():
    con = duckdb.connect()
    counts = load_raw_tables(con, FIXTURE_DIR)
    # 14 order rows (one is a duplicate); 13 reviews even though one has a line break inside.
    assert counts["orders"] == 14
    assert counts["reviews"] == 13
    types = {row[1] for row in con.execute("DESCRIBE raw_orders").fetchall()}
    assert types == {"VARCHAR"}
    columns = [row[0] for row in con.execute("DESCRIBE raw_products").fetchall()]
    assert "product_description_length" in columns
