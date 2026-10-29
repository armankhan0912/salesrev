"""
visualizations.py
------------------
All Plotly chart-building functions for the dashboard. Each function
takes a (already filtered) DataFrame and returns a Plotly Figure object,
keeping chart construction separate from Streamlit layout code.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src import kpi_calculator as kpi

# Consistent color palette across all charts
COLOR_SEQUENCE = px.colors.qualitative.Set2
TEMPLATE = "plotly_white"


def revenue_trend_chart(df: pd.DataFrame) -> go.Figure:
    """Line chart of monthly revenue over time."""
    trend = kpi.monthly_trend(df)
    fig = px.line(
        trend, x="Month", y="Revenue", markers=True,
        title="Revenue Trend Over Time", template=TEMPLATE,
    )
    fig.update_traces(line_color=COLOR_SEQUENCE[0], line_width=3)
    fig.update_layout(yaxis_title="Revenue ($)", xaxis_title="Month", hovermode="x unified")
    return fig


def monthly_sales_trend_chart(df: pd.DataFrame) -> go.Figure:
    """Bar chart of monthly order volume (sales count) over time."""
    trend = kpi.monthly_trend(df)
    fig = px.bar(
        trend, x="Month", y="Orders",
        title="Monthly Sales Volume (Orders)", template=TEMPLATE,
        color_discrete_sequence=[COLOR_SEQUENCE[1]],
    )
    fig.update_layout(yaxis_title="Number of Orders", xaxis_title="Month")
    return fig


def top_products_chart(df: pd.DataFrame, n: int = 10) -> go.Figure:
    """Horizontal bar chart of top N products by revenue."""
    data = kpi.top_products(df, n).sort_values("Revenue")
    fig = px.bar(
        data, x="Revenue", y="ProductName", orientation="h",
        title=f"Top {n} Products by Revenue", template=TEMPLATE,
        color="Revenue", color_continuous_scale="Blues",
        text="Revenue",
    )
    fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
    fig.update_layout(yaxis_title="", xaxis_title="Revenue ($)", coloraxis_showscale=False)
    return fig


def category_sales_chart(df: pd.DataFrame) -> go.Figure:
    """Pie/donut chart of revenue share by product category."""
    data = kpi.top_categories(df, n=20)
    fig = px.pie(
        data, names="ProductCategory", values="Revenue", hole=0.45,
        title="Sales by Category", template=TEMPLATE,
        color_discrete_sequence=COLOR_SEQUENCE,
    )
    fig.update_traces(textinfo="percent+label")
    return fig


def region_revenue_chart(df: pd.DataFrame) -> go.Figure:
    """Bar chart of revenue by region."""
    data = kpi.top_regions(df, n=20).sort_values("Revenue")
    fig = px.bar(
        data, x="Revenue", y="Region", orientation="h",
        title="Revenue by Region", template=TEMPLATE,
        color="Revenue", color_continuous_scale="Teal", text="Revenue",
    )
    fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
    fig.update_layout(yaxis_title="", xaxis_title="Revenue ($)", coloraxis_showscale=False)
    return fig


def profit_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """Box plot showing profit distribution across product categories."""
    completed = df[df["OrderStatus"] == "Completed"] if "OrderStatus" in df.columns else df
    fig = px.box(
        completed, x="ProductCategory", y="Profit",
        title="Profit Distribution by Category", template=TEMPLATE,
        color="ProductCategory", color_discrete_sequence=COLOR_SEQUENCE,
    )
    fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Profit ($)")
    return fig


def segment_sales_chart(df: pd.DataFrame) -> go.Figure:
    """Bar chart of revenue by customer segment."""
    data = kpi.revenue_by_segment(df)
    fig = px.bar(
        data, x="CustomerSegment", y="Revenue",
        title="Sales by Customer Segment", template=TEMPLATE,
        color="CustomerSegment", color_discrete_sequence=COLOR_SEQUENCE,
        text="Revenue",
    )
    fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
    fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Revenue ($)")
    return fig


def revenue_contribution_chart(df: pd.DataFrame) -> go.Figure:
    """Treemap showing revenue contribution % across category > product."""
    completed = df[df["OrderStatus"] == "Completed"] if "OrderStatus" in df.columns else df
    data = (
        completed.groupby(["ProductCategory", "ProductName"], as_index=False)["NetRevenue"]
        .sum()
        .rename(columns={"NetRevenue": "Revenue"})
    )
    fig = px.treemap(
        data, path=["ProductCategory", "ProductName"], values="Revenue",
        title="Revenue Contribution by Category & Product", template=TEMPLATE,
        color="Revenue", color_continuous_scale="Blues",
    )
    fig.update_traces(textinfo="label+percent parent")
    return fig


def profit_margin_gauge(df: pd.DataFrame) -> go.Figure:
    """Gauge chart showing overall profit margin."""
    margin = kpi.profit_margin(df)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=margin,
        title={"text": "Profit Margin (%)"},
        gauge={
            "axis": {"range": [0, 60]},
            "bar": {"color": COLOR_SEQUENCE[0]},
            "steps": [
                {"range": [0, 15], "color": "#fde2e2"},
                {"range": [15, 30], "color": "#fff3cd"},
                {"range": [30, 60], "color": "#d4edda"},
            ],
        },
    ))
    fig.update_layout(template=TEMPLATE, height=280, margin=dict(l=20, r=20, t=50, b=10))
    return fig
