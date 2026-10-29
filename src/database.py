"""
database.py
------------
Lightweight helper utilities for working with the bundled SQLite sales
database, and for building SQLAlchemy connection strings for MySQL /
PostgreSQL if a user wants to point the dashboard at a live database.
"""

import sqlite3
from pathlib import Path

import pandas as pd


def get_default_db_path() -> Path:
    base_dir = Path(__file__).resolve().parent.parent
    return base_dir / "data" / "sales_database.db"


def query_sqlite(db_path, query: str) -> pd.DataFrame:
    """Run an arbitrary SQL query against a SQLite database and return a DataFrame."""
    conn = sqlite3.connect(db_path)
    try:
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()


def build_mysql_connection_string(user: str, password: str, host: str, port: int, database: str) -> str:
    """Build a SQLAlchemy connection string for MySQL (requires `pymysql`)."""
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"


def build_postgres_connection_string(user: str, password: str, host: str, port: int, database: str) -> str:
    """Build a SQLAlchemy connection string for PostgreSQL (requires `psycopg2-binary`)."""
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"


def list_tables(db_path) -> list[str]:
    """List all table names in a SQLite database."""
    conn = sqlite3.connect(db_path)
    try:
        tables = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table';", conn
        )
        return tables["name"].tolist()
    finally:
        conn.close()
