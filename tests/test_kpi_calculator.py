"""
test_kpi_calculator.py
-----------------------
Unit tests for src/kpi_calculator.py using a small, hand-crafted DataFrame
so expected values can be verified by hand rather than depending on the
large synthetic sample dataset.

Run with:
    pytest tests/
"""

import pandas as pd
import pytest

from src import kpi_calculator as kpi


@pytest.fixture
def sample_df():
    data = [
        # OrderID, OrderDate, Segment, Region, Category, Product, Qty, UnitPrice, NetRevenue, Profit, Status
        ("ORD-001", "2024-01-10", "Consumer", "North America", "Electronics", "Mouse", 2, 10.0, 20.0, 8.0, "Completed"),
        ("ORD-002", "2024-01-15", "Enterprise", "Europe", "Electronics", "Keyboard", 1, 50.0, 50.0, 20.0, "Completed"),
        ("ORD-003", "2024-02-05", "Consumer", "North America", "Furniture", "Chair", 1, 100.0, 100.0, 40.0, "Completed"),
        ("ORD-004", "2024-02-20", "Small Business", "Asia Pacific", "Furniture", "Desk", 1, 200.0, 200.0, 60.0, "Returned"),
        ("ORD-005", "2024-03-01", "Consumer", "Europe", "Electronics", "Mouse", 3, 10.0, 30.0, 12.0, "Completed"),
    ]
    columns = [
        "OrderID", "OrderDate", "CustomerSegment", "Region", "ProductCategory",
        "ProductName", "Quantity", "UnitPrice", "NetRevenue", "Profit", "OrderStatus",
    ]
    df = pd.DataFrame(data, columns=columns)
    df["OrderDate"] = pd.to_datetime(df["OrderDate"])
    return df


def test_total_sales_excludes_non_completed(sample_df):
    # Completed rows: 2 + 1 + 1 + 3 = 7 units (Returned order excluded)
    assert kpi.total_sales(sample_df) == 7


def test_total_revenue_excludes_non_completed(sample_df):
    # 20 + 50 + 100 + 30 = 200 (Returned $200 excluded)
    assert kpi.total_revenue(sample_df) == 200.0


def test_total_orders_counts_all_statuses(sample_df):
    assert kpi.total_orders(sample_df) == 5


def test_average_order_value(sample_df):
    # 200 revenue / 4 completed orders = 50.0
    assert kpi.average_order_value(sample_df) == 50.0


def test_total_profit(sample_df):
    assert kpi.total_profit(sample_df) == 80.0  # 8+20+40+12


def test_profit_margin(sample_df):
    # 80 / 200 * 100 = 40%
    assert kpi.profit_margin(sample_df) == 40.0


def test_profit_margin_zero_revenue():
    empty_df = pd.DataFrame(columns=[
        "OrderID", "OrderDate", "CustomerSegment", "Region", "ProductCategory",
        "ProductName", "Quantity", "UnitPrice", "NetRevenue", "Profit", "OrderStatus",
    ])
    assert kpi.profit_margin(empty_df) == 0.0


def test_top_products_ranking(sample_df):
    top = kpi.top_products(sample_df, n=1)
    assert top.iloc[0]["ProductName"] == "Chair"  # highest single-product revenue (100)


def test_top_categories_ranking(sample_df):
    top = kpi.top_categories(sample_df, n=1)
    # Electronics: 20+50+30=100, Furniture (completed only): 100 -> tie broken by sort stability
    assert top.iloc[0]["ProductCategory"] in ("Electronics", "Furniture")


def test_top_regions_ranking(sample_df):
    top = kpi.top_regions(sample_df, n=10)
    assert set(top["Region"]) == {"North America", "Europe"}  # Asia Pacific order was Returned


def test_revenue_by_segment(sample_df):
    result = kpi.revenue_by_segment(sample_df)
    consumer_revenue = result[result["CustomerSegment"] == "Consumer"]["Revenue"].iloc[0]
    assert consumer_revenue == 150.0  # 20 + 100 + 30


def test_generate_business_insights_returns_list(sample_df):
    insights = kpi.generate_business_insights(sample_df)
    assert isinstance(insights, list)
    assert len(insights) > 0
    assert all(isinstance(i, str) for i in insights)


def test_generate_business_insights_empty_df():
    empty_df = pd.DataFrame(columns=[
        "OrderID", "OrderDate", "CustomerSegment", "Region", "ProductCategory",
        "ProductName", "Quantity", "UnitPrice", "NetRevenue", "Profit", "OrderStatus",
    ])
    insights = kpi.generate_business_insights(empty_df)
    assert insights == ["No completed orders in the current filter selection."]
