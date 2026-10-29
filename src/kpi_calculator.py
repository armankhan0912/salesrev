"""
kpi_calculator.py
------------------
Pure functions that compute the business KPIs shown on the dashboard.
Kept separate from the UI layer so the logic is easy to read, test,
and reuse (e.g. in a notebook or a future API).

Convention: unless noted otherwise, KPIs are computed only on orders
with OrderStatus == "Completed", since Returned/Cancelled orders should
not count towards realized revenue and profit.
"""

import pandas as pd


def _completed(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to only completed orders (used for revenue/profit KPIs)."""
    if "OrderStatus" in df.columns:
        return df[df["OrderStatus"] == "Completed"]
    return df


def total_sales(df: pd.DataFrame) -> int:
    """Total number of units sold (completed orders)."""
    return int(_completed(df)["Quantity"].sum())


def total_revenue(df: pd.DataFrame) -> float:
    """Total net revenue from completed orders."""
    return float(_completed(df)["NetRevenue"].sum())


def total_orders(df: pd.DataFrame) -> int:
    """Total number of distinct orders (all statuses, for order-volume tracking)."""
    return int(df["OrderID"].nunique())


def average_order_value(df: pd.DataFrame) -> float:
    """Average revenue per completed order."""
    completed = _completed(df)
    orders = completed["OrderID"].nunique()
    if orders == 0:
        return 0.0
    return float(completed["NetRevenue"].sum() / orders)


def total_profit(df: pd.DataFrame) -> float:
    """Total profit from completed orders."""
    return float(_completed(df)["Profit"].sum())


def profit_margin(df: pd.DataFrame) -> float:
    """Profit as a percentage of revenue."""
    revenue = total_revenue(df)
    if revenue == 0:
        return 0.0
    return float(total_profit(df) / revenue * 100)


def monthly_revenue_growth(df: pd.DataFrame) -> float:
    """
    Percentage change in revenue between the most recent complete month
    and the month before it, based on data currently in the (filtered) frame.
    Returns 0.0 if there isn't enough history to compare.
    """
    completed = _completed(df)
    if completed.empty:
        return 0.0
    monthly = (
        completed.set_index("OrderDate")
        .resample("ME")["NetRevenue"]
        .sum()
        .sort_index()
    )
    if len(monthly) < 2:
        return 0.0
    latest, previous = monthly.iloc[-1], monthly.iloc[-2]
    if previous == 0:
        return 0.0
    return float((latest - previous) / previous * 100)


def top_products(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N products ranked by net revenue."""
    completed = _completed(df)
    result = (
        completed.groupby("ProductName", as_index=False)
        .agg(Revenue=("NetRevenue", "sum"), UnitsSold=("Quantity", "sum"), Profit=("Profit", "sum"))
        .sort_values("Revenue", ascending=False)
        .head(n)
    )
    return result


def top_categories(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N product categories ranked by net revenue."""
    completed = _completed(df)
    result = (
        completed.groupby("ProductCategory", as_index=False)
        .agg(Revenue=("NetRevenue", "sum"), UnitsSold=("Quantity", "sum"), Profit=("Profit", "sum"))
        .sort_values("Revenue", ascending=False)
        .head(n)
    )
    return result


def top_regions(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N regions ranked by net revenue."""
    completed = _completed(df)
    result = (
        completed.groupby("Region", as_index=False)
        .agg(Revenue=("NetRevenue", "sum"), Orders=("OrderID", "nunique"), Profit=("Profit", "sum"))
        .sort_values("Revenue", ascending=False)
        .head(n)
    )
    return result


def revenue_by_segment(df: pd.DataFrame) -> pd.DataFrame:
    """Revenue broken down by customer segment."""
    completed = _completed(df)
    return (
        completed.groupby("CustomerSegment", as_index=False)
        .agg(Revenue=("NetRevenue", "sum"), Orders=("OrderID", "nunique"))
        .sort_values("Revenue", ascending=False)
    )


def monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly revenue, profit, and order count trend."""
    completed = _completed(df)
    if completed.empty:
        return pd.DataFrame(columns=["Month", "Revenue", "Profit", "Orders"])
    trend = (
        completed.set_index("OrderDate")
        .resample("ME")
        .agg(Revenue=("NetRevenue", "sum"), Profit=("Profit", "sum"), Orders=("OrderID", "nunique"))
        .reset_index()
        .rename(columns={"OrderDate": "Month"})
    )
    return trend


def generate_business_insights(df: pd.DataFrame) -> list[str]:
    """
    Generate a handful of plain-English, data-driven insights from the
    currently filtered dataset. This demonstrates basic business insight
    generation for the academic project requirement.
    """
    insights = []
    completed = _completed(df)
    if completed.empty:
        return ["No completed orders in the current filter selection."]

    # Best product
    top_prod = top_products(df, 1)
    if not top_prod.empty:
        row = top_prod.iloc[0]
        insights.append(
            f"**{row['ProductName']}** is the top-performing product, generating "
            f"${row['Revenue']:,.2f} in revenue from {int(row['UnitsSold'])} units sold."
        )

    # Best category
    top_cat = top_categories(df, 1)
    if not top_cat.empty:
        row = top_cat.iloc[0]
        share = row["Revenue"] / total_revenue(df) * 100 if total_revenue(df) else 0
        insights.append(
            f"The **{row['ProductCategory']}** category leads all categories, "
            f"contributing {share:.1f}% of total revenue."
        )

    # Best region
    top_reg = top_regions(df, 1)
    if not top_reg.empty:
        row = top_reg.iloc[0]
        insights.append(
            f"**{row['Region']}** is the strongest region with ${row['Revenue']:,.2f} "
            f"in revenue across {int(row['Orders'])} orders."
        )

    # Growth
    growth = monthly_revenue_growth(df)
    if growth > 0:
        insights.append(f"Revenue grew **{growth:.1f}%** month-over-month in the most recent period.")
    elif growth < 0:
        insights.append(f"Revenue declined **{abs(growth):.1f}%** month-over-month in the most recent period.")

    # Margin
    margin = profit_margin(df)
    if margin >= 30:
        insights.append(f"Profit margin is healthy at **{margin:.1f}%**, indicating efficient pricing and cost control.")
    elif margin < 15:
        insights.append(f"Profit margin is relatively low at **{margin:.1f}%** — consider reviewing discounting or cost structure.")

    # Return/cancellation rate
    if "OrderStatus" in df.columns and df["OrderID"].nunique() > 0:
        non_completed = df[df["OrderStatus"] != "Completed"]["OrderID"].nunique()
        rate = non_completed / df["OrderID"].nunique() * 100
        if rate > 10:
            insights.append(f"Returned/cancelled orders account for **{rate:.1f}%** of all orders — worth investigating.")

    return insights
