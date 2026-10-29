"""
app.py
------
Sales & Revenue Analysis Dashboard — main Streamlit application.

Run with:
    streamlit run app.py

This file is intentionally kept as the UI/orchestration layer only.
Data loading lives in src/data_loader.py, KPI math in
src/kpi_calculator.py, and chart building in src/visualizations.py.
"""

from datetime import date

import pandas as pd
import streamlit as st

from src import data_loader, kpi_calculator as kpi, visualizations as viz

# ----------------------------------------------------------------------
# Page configuration
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Sales & Revenue Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Minimal custom styling for a cleaner, more "professional dashboard" feel
st.markdown("""
<style>
    div[data-testid="stMetric"] {
        background-color: #f8f9fb;
        border: 1px solid #e6e6e6;
        border-radius: 10px;
        padding: 14px 16px 8px 16px;
    }
    div[data-testid="stMetricLabel"] { font-weight: 600; }
    .block-container { padding-top: 1.6rem; }
    .insight-box {
        background-color: #eef6ff;
        border-left: 4px solid #4a90e2;
        padding: 10px 16px;
        border-radius: 6px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------
# Sidebar — Data source selection
# ----------------------------------------------------------------------
st.sidebar.title("📊 Dashboard Controls")
st.sidebar.markdown("### 1. Data Source")

source_type = st.sidebar.radio(
    "Choose a data source",
    ["Sample Dataset", "Upload CSV", "Upload Excel", "SQLite Database"],
    index=0,
)

df = None
load_error = None

try:
    if source_type == "Sample Dataset":
        df = data_loader.load_csv(data_loader.get_default_dataset_path())

    elif source_type == "Upload CSV":
        uploaded = st.sidebar.file_uploader("Upload a CSV file", type=["csv"])
        if uploaded is not None:
            df = data_loader.load_csv(uploaded)
        else:
            st.sidebar.info("Upload a .csv file to continue, or switch to Sample Dataset.")

    elif source_type == "Upload Excel":
        uploaded = st.sidebar.file_uploader("Upload an Excel file", type=["xlsx"])
        if uploaded is not None:
            df = data_loader.load_excel(uploaded)
        else:
            st.sidebar.info("Upload a .xlsx file to continue, or switch to Sample Dataset.")

    elif source_type == "SQLite Database":
        uploaded = st.sidebar.file_uploader("Upload a SQLite .db file", type=["db", "sqlite"])
        table_name = st.sidebar.text_input("Table name", value="sales")
        if uploaded is not None:
            # Streamlit's uploader gives an in-memory file; write to a temp path for sqlite3
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
                tmp.write(uploaded.getvalue())
                tmp_path = tmp.name
            df = data_loader.load_sqlite(tmp_path, table_name=table_name)
        else:
            st.sidebar.info("Upload a SQLite database file, or switch to Sample Dataset.")
            st.sidebar.caption(
                "For MySQL/PostgreSQL, see `src/data_loader.load_sql_connection()` "
                "and pass a connection string — usable outside the file-upload UI."
            )

except data_loader.DataLoadError as exc:
    load_error = str(exc)

if load_error:
    st.sidebar.error(f"⚠️ {load_error}")

if df is None:
    st.title("📊 Sales & Revenue Analysis Dashboard")
    st.warning(
        "No data loaded yet. Select **Sample Dataset** in the sidebar to explore "
        "the dashboard immediately, or upload your own CSV / Excel / SQLite file."
    )
    st.stop()


# ----------------------------------------------------------------------
# Sidebar — Filters / Slicers
# ----------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.markdown("### 2. Filters")

min_date, max_date = df["OrderDate"].min().date(), df["OrderDate"].max().date()
date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

categories = sorted(df["ProductCategory"].unique().tolist())
selected_categories = st.sidebar.multiselect("Product category", categories, default=categories)

regions = sorted(df["Region"].unique().tolist())
selected_regions = st.sidebar.multiselect("Region", regions, default=regions)

segments = sorted(df["CustomerSegment"].unique().tolist())
selected_segments = st.sidebar.multiselect("Customer segment", segments, default=segments)

statuses = sorted(df["OrderStatus"].unique().tolist())
selected_statuses = st.sidebar.multiselect("Order status", statuses, default=statuses)

search_term = st.sidebar.text_input("🔎 Search product name", value="")

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Reset all filters"):
    st.rerun()

# ----------------------------------------------------------------------
# Apply filters
# ----------------------------------------------------------------------
filtered_df = df[
    (df["OrderDate"].dt.date >= start_date)
    & (df["OrderDate"].dt.date <= end_date)
    & (df["ProductCategory"].isin(selected_categories))
    & (df["Region"].isin(selected_regions))
    & (df["CustomerSegment"].isin(selected_segments))
    & (df["OrderStatus"].isin(selected_statuses))
]

if search_term:
    filtered_df = filtered_df[filtered_df["ProductName"].str.contains(search_term, case=False, na=False)]

if filtered_df.empty:
    st.title("📊 Sales & Revenue Analysis Dashboard")
    st.warning("No records match the current filter selection. Try widening your filters.")
    st.stop()


# ----------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------
st.title("📊 Sales & Revenue Analysis Dashboard")
st.caption(
    f"Showing **{filtered_df['OrderID'].nunique():,}** orders from "
    f"**{start_date}** to **{end_date}** &nbsp;|&nbsp; Data source: {source_type}"
)

# ----------------------------------------------------------------------
# KPI Row 1
# ----------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Sales (Units)", f"{kpi.total_sales(filtered_df):,}")
c2.metric("Total Revenue", f"${kpi.total_revenue(filtered_df):,.2f}")
c3.metric("Total Orders", f"{kpi.total_orders(filtered_df):,}")
c4.metric("Avg. Order Value", f"${kpi.average_order_value(filtered_df):,.2f}")

# ----------------------------------------------------------------------
# KPI Row 2
# ----------------------------------------------------------------------
c5, c6, c7 = st.columns(3)
c5.metric("Total Profit", f"${kpi.total_profit(filtered_df):,.2f}")
c6.metric("Profit Margin", f"{kpi.profit_margin(filtered_df):.1f}%")
growth = kpi.monthly_revenue_growth(filtered_df)
c7.metric("Monthly Revenue Growth", f"{growth:+.1f}%", delta=f"{growth:+.1f}%")

st.markdown("---")

# ----------------------------------------------------------------------
# Business Insights
# ----------------------------------------------------------------------
with st.expander("💡 Auto-Generated Business Insights", expanded=True):
    insights = kpi.generate_business_insights(filtered_df)
    for insight in insights:
        st.markdown(f"<div class='insight-box'>{insight}</div>", unsafe_allow_html=True)

st.markdown("---")

# ----------------------------------------------------------------------
# Tabs for chart organization
# ----------------------------------------------------------------------
tab_trends, tab_products, tab_regions, tab_profit, tab_data = st.tabs(
    ["📈 Trends", "🏆 Products & Categories", "🌍 Regions & Segments", "💰 Profitability", "📋 Raw Data"]
)

with tab_trends:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(viz.revenue_trend_chart(filtered_df), use_container_width=True)
    with col2:
        st.plotly_chart(viz.monthly_sales_trend_chart(filtered_df), use_container_width=True)

with tab_products:
    top_n = st.slider("Number of top products to show", min_value=5, max_value=20, value=10)
    st.plotly_chart(viz.top_products_chart(filtered_df, top_n), use_container_width=True)
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(viz.category_sales_chart(filtered_df), use_container_width=True)
    with col2:
        st.plotly_chart(viz.revenue_contribution_chart(filtered_df), use_container_width=True)

with tab_regions:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(viz.region_revenue_chart(filtered_df), use_container_width=True)
    with col2:
        st.plotly_chart(viz.segment_sales_chart(filtered_df), use_container_width=True)

with tab_profit:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.plotly_chart(viz.profit_distribution_chart(filtered_df), use_container_width=True)
    with col2:
        st.plotly_chart(viz.profit_margin_gauge(filtered_df), use_container_width=True)

with tab_data:
    st.markdown("#### Filtered Dataset")
    st.dataframe(filtered_df, use_container_width=True, height=420)
    csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download filtered data as CSV",
        data=csv_bytes,
        file_name="filtered_sales_data.csv",
        mime="text/csv",
    )

st.markdown("---")
st.caption("Built with Streamlit, Pandas & Plotly · Sales & Revenue Analysis Dashboard")
