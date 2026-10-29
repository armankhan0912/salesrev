"""
data_generator.py
------------------
Generates a realistic, synthetic Sales & Revenue dataset for the dashboard.

Why synthetic data?
Academic/demo projects need a ready-to-run dataset without depending on a
real (often private) company dataset. This script creates ~3 years of
transaction-level sales data with realistic seasonality, multiple product
categories, regions, and customer segments so every dashboard feature
(trends, top products, regional analysis, filters) has meaningful data
to work with.

Run directly to regenerate the CSV and SQLite database:
    python utils/data_generator.py
"""

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
RANDOM_SEED = 42
START_DATE = "2022-01-01"
END_DATE = "2024-12-31"
NUM_ORDERS = 6000

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

CSV_PATH = DATA_DIR / "sample_sales_data.csv"
DB_PATH = DATA_DIR / "sales_database.db"

# Product catalog: category -> list of (product_name, unit_cost, unit_price)
PRODUCT_CATALOG = {
    "Electronics": [
        ("Wireless Mouse", 8, 19.99),
        ("Mechanical Keyboard", 35, 79.99),
        ("27-inch Monitor", 130, 249.99),
        ("Noise Cancelling Headphones", 60, 149.99),
        ("Smartphone Stand", 4, 12.99),
        ("Portable SSD 1TB", 55, 109.99),
        ("Smart Watch", 90, 199.99),
        ("Bluetooth Speaker", 25, 59.99),
    ],
    "Office Supplies": [
        ("Ergonomic Office Chair", 90, 189.99),
        ("Standing Desk", 150, 349.99),
        ("Notebook Pack (5)", 3, 9.99),
        ("Desk Organizer", 6, 15.99),
        ("Printer Paper (Ream)", 3, 6.99),
        ("Whiteboard 3x2ft", 20, 44.99),
    ],
    "Furniture": [
        ("Bookshelf 5-Tier", 70, 149.99),
        ("Filing Cabinet", 60, 129.99),
        ("Conference Table", 300, 699.99),
        ("Guest Chair", 40, 89.99),
    ],
    "Software & Licenses": [
        ("Productivity Suite (1yr)", 20, 69.99),
        ("Antivirus License (1yr)", 8, 39.99),
        ("Cloud Storage 1TB (1yr)", 15, 59.99),
        ("Project Management Tool (1yr)", 40, 119.99),
    ],
    "Accessories": [
        ("Laptop Backpack", 15, 44.99),
        ("USB-C Hub", 10, 29.99),
        ("Cable Organizer Kit", 3, 9.99),
        ("Webcam HD 1080p", 18, 49.99),
    ],
}

REGIONS = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East & Africa"]
REGION_WEIGHTS = [0.35, 0.28, 0.20, 0.10, 0.07]

CUSTOMER_SEGMENTS = ["Consumer", "Small Business", "Enterprise", "Government"]
SEGMENT_WEIGHTS = [0.45, 0.30, 0.18, 0.07]

SALES_REPS = [
    "Alex Johnson", "Priya Sharma", "Wei Chen", "Maria Garcia", "James Smith",
    "Fatima Al-Sayed", "Liam O'Brien", "Sofia Rossi", "Chidi Okafor", "Emma Wilson",
]

PAYMENT_METHODS = ["Credit Card", "Bank Transfer", "PayPal", "Cash on Delivery"]
PAYMENT_WEIGHTS = [0.55, 0.20, 0.20, 0.05]

ORDER_STATUS = ["Completed", "Completed", "Completed", "Completed", "Returned", "Cancelled"]


def generate_sales_data(num_orders: int = NUM_ORDERS, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Generate a transaction-level sales DataFrame with realistic patterns."""
    rng = np.random.default_rng(seed)

    date_range = pd.date_range(START_DATE, END_DATE, freq="D")

    # Build a flat list of (category, product, cost, price) for weighted sampling
    flat_products = []
    for category, items in PRODUCT_CATALOG.items():
        for name, cost, price in items:
            flat_products.append((category, name, cost, price))

    records = []
    for order_id in range(1, num_orders + 1):
        # --- Seasonality: bias order dates towards Nov/Dec (holiday sales)
        # and slight overall upward trend year over year.
        year_weights = {2022: 1.0, 2023: 1.15, 2024: 1.3}
        month_seasonality = {
            1: 0.85, 2: 0.80, 3: 0.90, 4: 0.95, 5: 1.0, 6: 1.0,
            7: 0.95, 8: 0.90, 9: 1.05, 10: 1.15, 11: 1.45, 12: 1.55,
        }
        # sample a date weighted by seasonality
        probs = np.array([
            year_weights[d.year] * month_seasonality[d.month] for d in date_range
        ])
        probs = probs / probs.sum()
        order_date = rng.choice(date_range, p=probs)
        order_date = pd.Timestamp(order_date)

        category, product_name, unit_cost, unit_price = flat_products[
            rng.integers(0, len(flat_products))
        ]

        quantity = int(rng.choice([1, 2, 3, 4, 5, 6], p=[0.40, 0.25, 0.15, 0.10, 0.06, 0.04]))

        # small random price fluctuation (+/-5%) to simulate discounts/promos
        price_factor = rng.uniform(0.90, 1.05)
        final_unit_price = round(unit_price * price_factor, 2)

        discount_pct = float(rng.choice([0, 0, 0, 5, 10, 15, 20], p=[0.5, 0.15, 0.1, 0.1, 0.08, 0.05, 0.02]))

        gross_revenue = round(final_unit_price * quantity, 2)
        discount_amount = round(gross_revenue * (discount_pct / 100), 2)
        net_revenue = round(gross_revenue - discount_amount, 2)
        total_cost = round(unit_cost * quantity, 2)
        profit = round(net_revenue - total_cost, 2)

        region = rng.choice(REGIONS, p=REGION_WEIGHTS)
        segment = rng.choice(CUSTOMER_SEGMENTS, p=SEGMENT_WEIGHTS)
        sales_rep = rng.choice(SALES_REPS)
        payment_method = rng.choice(PAYMENT_METHODS, p=PAYMENT_WEIGHTS)
        status = rng.choice(ORDER_STATUS)

        # Returned/Cancelled orders contribute 0 net revenue & profit for KPI purposes
        # but are kept in the dataset to allow status-based analysis.
        records.append({
            "OrderID": f"ORD-{order_id:05d}",
            "OrderDate": order_date.strftime("%Y-%m-%d"),
            "CustomerSegment": segment,
            "Region": region,
            "ProductCategory": category,
            "ProductName": product_name,
            "Quantity": quantity,
            "UnitPrice": final_unit_price,
            "DiscountPercent": discount_pct,
            "GrossRevenue": gross_revenue,
            "DiscountAmount": discount_amount,
            "NetRevenue": net_revenue,
            "UnitCost": unit_cost,
            "TotalCost": total_cost,
            "Profit": profit,
            "SalesRep": sales_rep,
            "PaymentMethod": payment_method,
            "OrderStatus": status,
        })

    df = pd.DataFrame(records)
    df["OrderDate"] = pd.to_datetime(df["OrderDate"])
    df = df.sort_values("OrderDate").reset_index(drop=True)
    return df


def save_to_csv(df: pd.DataFrame, path: Path = CSV_PATH) -> None:
    df.to_csv(path, index=False)
    print(f"CSV saved to: {path}")


def save_to_sqlite(df: pd.DataFrame, path: Path = DB_PATH, table_name: str = "sales") -> None:
    conn = sqlite3.connect(path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()
    print(f"SQLite database saved to: {path} (table: {table_name})")


if __name__ == "__main__":
    print("Generating synthetic sales dataset...")
    sales_df = generate_sales_data()
    save_to_csv(sales_df)
    save_to_sqlite(sales_df)
    print(f"Done. Generated {len(sales_df):,} order records "
          f"from {sales_df['OrderDate'].min().date()} to {sales_df['OrderDate'].max().date()}.")
