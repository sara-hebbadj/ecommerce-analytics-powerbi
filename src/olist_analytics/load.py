"""Find the raw Olist CSVs and load them into DuckDB as text tables (raw_*).

Decision: every column is loaded as text (VARCHAR). Types are cast explicitly in
sql/stage_1_clean.sql with TRY_CAST, so a bad value becomes NULL and is counted in the
data-quality log, instead of the loader guessing a type (and, for example, turning the
zip prefix "01310" into the number 1310).
"""

import zipfile
from pathlib import Path

import duckdb

from olist_analytics.schema import EXPECTED_FILES, normalise_column

ANCHOR_FILE = "olist_orders_dataset.csv"  # if this file is in a folder, the others should be too


def _find_anchor(raw_dir: Path) -> Path | None:
    """Look for the anchor CSV in raw_dir and in its direct sub-folders."""
    candidates = [raw_dir] + sorted(p for p in raw_dir.iterdir() if p.is_dir())
    for folder in candidates:
        if (folder / ANCHOR_FILE).exists():
            return folder
    return None


def locate_csv_folder(raw_dir: Path) -> Path:
    """Return the folder that holds the CSVs: raw_dir itself or one sub-folder below it.

    Unzip tools sometimes create an extra folder (e.g. data/raw/archive/). If only the
    Kaggle .zip file is present, its CSV files are extracted into raw_dir first.
    """
    raw_dir = Path(raw_dir)
    if not raw_dir.exists():
        return raw_dir
    found = _find_anchor(raw_dir)
    if found is None:
        zips = sorted(raw_dir.glob("*.zip"))
        if zips:
            with zipfile.ZipFile(zips[0]) as archive:
                # Only extract CSV files; skip anything else that might be in the archive.
                csv_names = [n for n in archive.namelist() if n.lower().endswith(".csv")]
                archive.extractall(raw_dir, members=csv_names)
            found = _find_anchor(raw_dir)
    return found or raw_dir


def _sql_path(path: Path) -> str:
    """Quote a file path for use inside a SQL string literal."""
    return str(path).replace("'", "''")


def load_raw_tables(con: duckdb.DuckDBPyConnection, csv_dir: Path) -> dict[str, int]:
    """Create one raw_<name> table per CSV file and return the row count of each."""
    row_counts = {}
    for table, (file_name, _columns) in EXPECTED_FILES.items():
        path = Path(csv_dir) / file_name
        con.execute(
            f"""
            CREATE OR REPLACE TABLE raw_{table} AS
            SELECT * FROM read_csv(
                '{_sql_path(path)}',
                header = true, all_varchar = true,
                delim = ',', quote = '"', escape = '"'  -- review comments contain quoted newlines
            )
            """
        )
        _normalise_column_names(con, f"raw_{table}")
        row_counts[table] = con.execute(f"SELECT COUNT(*) FROM raw_{table}").fetchone()[0]
    return row_counts


def _normalise_column_names(con: duckdb.DuckDBPyConnection, table: str) -> None:
    """Rename columns to their normalised form (no BOM, lower case, 'lenght' -> 'length')."""
    columns = [row[0] for row in con.execute(f"DESCRIBE {table}").fetchall()]
    for col in columns:
        new_name = normalise_column(col)
        if new_name != col:
            con.execute(f'ALTER TABLE {table} RENAME COLUMN "{col}" TO "{new_name}"')
