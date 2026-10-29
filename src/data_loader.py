"""
data_loader.py
---------------
Handles loading sales data from multiple source types: CSV, Excel, and
SQL databases (SQLite out of the box; MySQL/PostgreSQL via SQLAlchemy
connection strings if the relevant driver is installed).

Also handles cleaning, validation, and type coercion so the rest of the
app can always assume a consistent schema.
"""

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

# Columns the app expects downstream. Used for validation after loading.
REQUIRED_COLUMNS = [
    "OrderID", "OrderDate", "CustomerSegment", "Region", "ProductCategory",
    "ProductName", "Quantity", "UnitPrice", "NetRevenue", "Profit", "OrderStatus",
]


class DataLoadError(Exception):
    """Raised when a data source cannot be loaded or fails validation."""


@st.cache_data(show_spinner=False)
def load_csv(file_or_path) -> pd.DataFrame:
    """Load sales data from a CSV file path or uploaded file object."""
    try:
        df = pd.read_csv(file_or_path)
    except Exception as exc:  # noqa: BLE001 - surface a friendly error upstream
        raise DataLoadError(f"Could not read CSV file: {exc}") from exc
    return _clean_and_validate(df)


@st.cache_data(show_spinner=False)
def load_excel(file_or_path, sheet_name=0) -> pd.DataFrame:
    """Load sales data from an Excel (.xlsx) file path or uploaded file object."""
    try:
        df = pd.read_excel(file_or_path, sheet_name=sheet_name, engine="openpyxl")
    except Exception as exc:  # noqa: BLE001
        raise DataLoadError(f"Could not read Excel file: {exc}") from exc
    return _clean_and_validate(df)


@st.cache_data(show_spinner=False)
def load_sqlite(db_path, table_name: str = "sales") -> pd.DataFrame:
    """Load sales data from a SQLite database file."""
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        conn.close()
    except Exception as exc:  # noqa: BLE001
        raise DataLoadError(f"Could not read SQLite database: {exc}") from exc
    return _clean_and_validate(df)


def load_sql_connection(connection_string: str, query: str = "SELECT * FROM sales") -> pd.DataFrame:
    """
    Load sales data from any SQLAlchemy-compatible database
    (MySQL, PostgreSQL, etc.). Requires the relevant driver package,
    e.g. `pymysql` for MySQL or `psycopg2-binary` for PostgreSQL.

    Example connection strings:
      MySQL:      mysql+pymysql://user:password@host:3306/dbname
      PostgreSQL: postgresql+psycopg2://user:password@host:5432/dbname
    """
    try:
        from sqlalchemy import create_engine
        engine = create_engine(connection_string)
        df = pd.read_sql(query, engine)
    except Exception as exc:  # noqa: BLE001
        raise DataLoadError(f"Could not connect to database: {exc}") from exc
    return _clean_and_validate(df)


def _clean_and_validate(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column types and validate schema. Raises DataLoadError on failure."""
    if df.empty:
        raise DataLoadError("The uploaded file contains no data.")

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise DataLoadError(
            "The dataset is missing required columns: "
            f"{', '.join(missing)}. Please check the file format."
        )

    df = df.copy()

    # Parse dates
    try:
        df["OrderDate"] = pd.to_datetime(df["OrderDate"], errors="coerce")
    except Exception as exc:  # noqa: BLE001
        raise DataLoadError(f"Could not parse OrderDate column: {exc}") from exc

    invalid_dates = df["OrderDate"].isna().sum()
    if invalid_dates:
        df = df.dropna(subset=["OrderDate"])

    # Coerce numeric columns, dropping rows that fail to convert
    numeric_cols = ["Quantity", "UnitPrice", "NetRevenue", "Profit"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=numeric_cols)

    # Fill any missing optional/text columns gracefully
    for col in ["DiscountPercent", "GrossRevenue", "DiscountAmount", "TotalCost", "UnitCost"]:
        if col not in df.columns:
            df[col] = 0
    for col in ["SalesRep", "PaymentMethod"]:
        if col not in df.columns:
            df[col] = "Unknown"

    if df.empty:
        raise DataLoadError("No valid rows remained after cleaning the dataset.")

    return df.reset_index(drop=True)


def get_default_dataset_path() -> Path:
    """Returns path to the bundled sample dataset shipped with the repo."""
    base_dir = Path(__file__).resolve().parent.parent
    return base_dir / "data" / "sample_sales_data.csv"
