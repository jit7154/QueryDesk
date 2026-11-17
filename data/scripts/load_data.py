#!/usr/bin/env python3
"""Load structured e-commerce CSVs into PostgreSQL with normalized schemas and indexes."""

import csv
import os
from pathlib import Path
import sys
import psycopg

RAW_DATA_DIR = Path(__file__).resolve().parent.parent / "raw"
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://querydesk_user:querydesk_password@localhost:5432/querydesk",
)

SCHEMA_SQL = """
DROP TABLE IF EXISTS order_payments CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS sellers CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE customers (
    customer_id VARCHAR(64) PRIMARY KEY,
    customer_unique_id VARCHAR(64) NOT NULL,
    customer_zip_code_prefix INTEGER,
    customer_city VARCHAR(100),
    customer_state VARCHAR(10)
);

CREATE TABLE sellers (
    seller_id VARCHAR(64) PRIMARY KEY,
    seller_zip_code_prefix INTEGER,
    seller_city VARCHAR(100),
    seller_state VARCHAR(10)
);

CREATE TABLE products (
    product_id VARCHAR(64) PRIMARY KEY,
    product_category_name VARCHAR(100),
    product_name_length INTEGER,
    product_description_length INTEGER,
    product_photos_qty INTEGER,
    product_weight_g NUMERIC,
    product_length_cm NUMERIC,
    product_height_cm NUMERIC,
    product_width_cm NUMERIC
);

CREATE TABLE orders (
    order_id VARCHAR(64) PRIMARY KEY,
    customer_id VARCHAR(64) REFERENCES customers(customer_id),
    order_status VARCHAR(50),
    order_purchase_timestamp TIMESTAMP,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP
);

CREATE TABLE order_items (
    order_id VARCHAR(64) REFERENCES orders(order_id),
    order_item_id INTEGER,
    product_id VARCHAR(64),
    seller_id VARCHAR(64) REFERENCES sellers(seller_id),
    shipping_limit_date TIMESTAMP,
    price NUMERIC(10, 2),
    freight_value NUMERIC(10, 2),
    PRIMARY KEY (order_id, order_item_id)
);

CREATE TABLE order_payments (
    order_id VARCHAR(64) REFERENCES orders(order_id),
    payment_sequential INTEGER,
    payment_type VARCHAR(50),
    payment_installments INTEGER,
    payment_value NUMERIC(10, 2),
    PRIMARY KEY (order_id, payment_sequential)
);

-- Performance Indexes
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(order_status);
CREATE INDEX idx_orders_purchase_timestamp ON orders(order_purchase_timestamp);
CREATE INDEX idx_order_items_seller_id ON order_items(seller_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_order_payments_order_id ON order_payments(order_id);

-- Read-only role grants
GRANT SELECT ON ALL TABLES IN SCHEMA public TO querydesk_ro;
"""


def clean_val(val: str) -> str | None:
    val = val.strip()
    return val if val else None


def load_customers(conn: psycopg.Connection, csv_path: Path) -> int:
    print(f"Loading customers from {csv_path.name}...")
    with open(csv_path, encoding="utf-8") as f, conn.cursor() as cur:
        reader = csv.DictReader(f)
        with cur.copy(
            "COPY customers (customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state) FROM STDIN"
        ) as copy:
            count = 0
            for row in reader:
                zip_prefix = int(row["customer_zip_code_prefix"]) if row.get("customer_zip_code_prefix") else None
                copy.write_row((
                    row["customer_id"],
                    row["customer_unique_id"],
                    zip_prefix,
                    clean_val(row.get("customer_city", "")),
                    clean_val(row.get("customer_state", "")),
                ))
                count += 1
    conn.commit()
    return count


def load_sellers(conn: psycopg.Connection, csv_path: Path) -> int:
    print(f"Loading sellers from {csv_path.name}...")
    with open(csv_path, encoding="utf-8") as f, conn.cursor() as cur:
        reader = csv.DictReader(f)
        with cur.copy(
            "COPY sellers (seller_id, seller_zip_code_prefix, seller_city, seller_state) FROM STDIN"
        ) as copy:
            count = 0
            for row in reader:
                zip_prefix = int(row["seller_zip_code_prefix"]) if row.get("seller_zip_code_prefix") else None
                copy.write_row((
                    row["seller_id"],
                    zip_prefix,
                    clean_val(row.get("seller_city", "")),
                    clean_val(row.get("seller_state", "")),
                ))
                count += 1
    conn.commit()
    return count


def load_products(conn: psycopg.Connection, csv_path: Path) -> int:
    print(f"Loading products from {csv_path.name}...")
    with open(csv_path, encoding="utf-8") as f, conn.cursor() as cur:
        reader = csv.DictReader(f)
        with cur.copy(
            "COPY products (product_id, product_category_name, product_name_length, product_description_length, product_photos_qty, product_weight_g, product_length_cm, product_height_cm, product_width_cm) FROM STDIN"
        ) as copy:
            count = 0
            for row in reader:
                copy.write_row((
                    row["product_id"],
                    clean_val(row.get("product_category_name", "")),
                    int(row["product_name_lenght"]) if clean_val(row.get("product_name_lenght", "")) else None,
                    int(row["product_description_lenght"]) if clean_val(row.get("product_description_lenght", "")) else None,
                    int(row["product_photos_qty"]) if clean_val(row.get("product_photos_qty", "")) else None,
                    float(row["product_weight_g"]) if clean_val(row.get("product_weight_g", "")) else None,
                    float(row["product_length_cm"]) if clean_val(row.get("product_length_cm", "")) else None,
                    float(row["product_height_cm"]) if clean_val(row.get("product_height_cm", "")) else None,
                    float(row["product_width_cm"]) if clean_val(row.get("product_width_cm", "")) else None,
                ))
                count += 1
    conn.commit()
    return count


def load_orders(conn: psycopg.Connection, csv_path: Path) -> int:
    print(f"Loading orders from {csv_path.name}...")
    with open(csv_path, encoding="utf-8") as f, conn.cursor() as cur:
        reader = csv.DictReader(f)
        with cur.copy(
            "COPY orders (order_id, customer_id, order_status, order_purchase_timestamp, order_approved_at, order_delivered_carrier_date, order_delivered_customer_date, order_estimated_delivery_date) FROM STDIN"
        ) as copy:
            count = 0
            for row in reader:
                copy.write_row((
                    row["order_id"],
                    row["customer_id"],
                    clean_val(row.get("order_status", "")),
                    clean_val(row.get("order_purchase_timestamp", "")),
                    clean_val(row.get("order_approved_at", "")),
                    clean_val(row.get("order_delivered_carrier_date", "")),
                    clean_val(row.get("order_delivered_customer_date", "")),
                    clean_val(row.get("order_estimated_delivery_date", "")),
                ))
                count += 1
    conn.commit()
    return count


def load_order_items(conn: psycopg.Connection, csv_path: Path) -> int:
    print(f"Loading order items from {csv_path.name}...")
    with open(csv_path, encoding="utf-8") as f, conn.cursor() as cur:
        reader = csv.DictReader(f)
        with cur.copy(
            "COPY order_items (order_id, order_item_id, product_id, seller_id, shipping_limit_date, price, freight_value) FROM STDIN"
        ) as copy:
            count = 0
            for row in reader:
                copy.write_row((
                    row["order_id"],
                    int(row["order_item_id"]),
                    clean_val(row.get("product_id", "")),
                    clean_val(row.get("seller_id", "")),
                    clean_val(row.get("shipping_limit_date", "")),
                    float(row["price"]) if clean_val(row.get("price", "")) else 0.0,
                    float(row["freight_value"]) if clean_val(row.get("freight_value", "")) else 0.0,
                ))
                count += 1
    conn.commit()
    return count


def load_order_payments(conn: psycopg.Connection, csv_path: Path) -> int:
    print(f"Loading order payments from {csv_path.name}...")
    with open(csv_path, encoding="utf-8") as f, conn.cursor() as cur:
        reader = csv.DictReader(f)
        with cur.copy(
            "COPY order_payments (order_id, payment_sequential, payment_type, payment_installments, payment_value) FROM STDIN"
        ) as copy:
            count = 0
            for row in reader:
                copy.write_row((
                    row["order_id"],
                    int(row["payment_sequential"]),
                    clean_val(row.get("payment_type", "")),
                    int(row["payment_installments"]) if clean_val(row.get("payment_installments", "")) else 1,
                    float(row["payment_value"]) if clean_val(row.get("payment_value", "")) else 0.0,
                ))
                count += 1
    conn.commit()
    return count


def main() -> None:
    print(f"Connecting to database at {DATABASE_URL}...")
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            print("Applying schema and indexes...")
            cur.execute(SCHEMA_SQL)
        conn.commit()

        c_count = load_customers(conn, RAW_DATA_DIR / "olist_customers_dataset.csv")
        s_count = load_sellers(conn, RAW_DATA_DIR / "olist_sellers_dataset.csv")
        p_count = load_products(conn, RAW_DATA_DIR / "olist_products_dataset.csv")
        o_count = load_orders(conn, RAW_DATA_DIR / "olist_orders_dataset.csv")
        oi_count = load_order_items(conn, RAW_DATA_DIR / "olist_order_items_dataset.csv")
        op_count = load_order_payments(conn, RAW_DATA_DIR / "olist_order_payments_dataset.csv")

        print("Data load complete:")
        print(f" - customers: {c_count:,}")
        print(f" - sellers: {s_count:,}")
        print(f" - products: {p_count:,}")
        print(f" - orders: {o_count:,}")
        print(f" - order_items: {oi_count:,}")
        print(f" - order_payments: {op_count:,}")


if __name__ == "__main__":
    main()
