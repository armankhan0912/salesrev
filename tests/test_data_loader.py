"""
test_data_loader.py
--------------------
Unit tests for src/data_loader.py — validates error handling and
schema validation behave as expected.

Note: data_loader.py uses the @st.cache_data decorator from Streamlit.
These tests rely on Streamlit being installed (see requirements.txt).
Run with:
    pytest tests/
"""

import pandas as pd
import pytest

from src import data_loader


VALID_COLUMNS = [
    "OrderID", "OrderDate", "CustomerSegment", "Region", "ProductCategory",
    "ProductName", "Quantity", "UnitPrice", "NetRevenue", "Profit", "OrderStatus",
]


def _make_valid_df():
    return pd.DataFrame([
        {
            "OrderID": "ORD-001", "OrderDate": "2024-01-01", "CustomerSegment": "Consumer",
            "Region": "North America", "ProductCategory": "Electronics", "ProductName": "Mouse",
            "Quantity": 2, "UnitPrice": 10.0, "NetRevenue": 20.0, "Profit": 8.0,
            "OrderStatus": "Completed",
        }
    ])


def test_load_csv_valid_file(tmp_path):
    df = _make_valid_df()
    path = tmp_path / "valid.csv"
    df.to_csv(path, index=False)

    result = data_loader.load_csv(str(path))
    assert not result.empty
    assert "OrderDate" in result.columns
    assert pd.api.types.is_datetime64_any_dtype(result["OrderDate"])


def test_load_csv_missing_columns_raises(tmp_path):
    bad_df = pd.DataFrame({"foo": [1, 2, 3]})
    path = tmp_path / "bad.csv"
    bad_df.to_csv(path, index=False)

    with pytest.raises(data_loader.DataLoadError):
        data_loader.load_csv(str(path))


def test_load_csv_nonexistent_file_raises():
    with pytest.raises(data_loader.DataLoadError):
        data_loader.load_csv("this_file_does_not_exist.csv")


def test_load_csv_empty_file_raises(tmp_path):
    empty_df = pd.DataFrame(columns=VALID_COLUMNS)
    path = tmp_path / "empty.csv"
    empty_df.to_csv(path, index=False)

    with pytest.raises(data_loader.DataLoadError):
        data_loader.load_csv(str(path))


def test_load_excel_valid_file(tmp_path):
    df = _make_valid_df()
    path = tmp_path / "valid.xlsx"
    df.to_excel(path, index=False, engine="openpyxl")

    result = data_loader.load_excel(str(path))
    assert not result.empty


def test_get_default_dataset_path_exists():
    path = data_loader.get_default_dataset_path()
    assert path.name == "sample_sales_data.csv"
