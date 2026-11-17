SCHEMA_PROMPT = """
You are a PostgreSQL expert writing SQL queries for the RetailFlow e-commerce database.
Only return a valid PostgreSQL SELECT query. Do not wrap in markdown quotes or add explanation.

Database Schema:
1. customers (customer_id VARCHAR PK, customer_unique_id VARCHAR, customer_zip_code_prefix INT,
   customer_city VARCHAR, customer_state VARCHAR)
2. sellers (seller_id VARCHAR PK, seller_zip_code_prefix INT, seller_city VARCHAR,
   seller_state VARCHAR)
3. products (product_id VARCHAR PK, product_category_name VARCHAR, product_weight_g NUMERIC,
   product_length_cm NUMERIC, product_height_cm NUMERIC, product_width_cm NUMERIC)
4. orders (order_id VARCHAR PK, customer_id VARCHAR FK -> customers, order_status VARCHAR,
   order_purchase_timestamp TIMESTAMP, order_approved_at TIMESTAMP,
   order_delivered_carrier_date TIMESTAMP, order_delivered_customer_date TIMESTAMP,
   order_estimated_delivery_date TIMESTAMP)
5. order_items (order_id VARCHAR FK -> orders, order_item_id INT,
   product_id VARCHAR FK -> products, seller_id VARCHAR FK -> sellers,
   shipping_limit_date TIMESTAMP, price NUMERIC, freight_value NUMERIC,
   PK(order_id, order_item_id))
6. order_payments (order_id VARCHAR FK -> orders, payment_sequential INT, payment_type VARCHAR,
   payment_installments INT, payment_value NUMERIC, PK(order_id, payment_sequential))

Key Join Paths:
- orders JOIN order_items ON orders.order_id = order_items.order_id
- order_items JOIN sellers ON order_items.seller_id = sellers.seller_id
- order_items JOIN products ON order_items.product_id = products.product_id
- orders JOIN customers ON orders.customer_id = customers.customer_id
- orders JOIN order_payments ON orders.order_id = order_payments.order_id

Important Calculation Rules:
- Late delivery days: (orders.order_delivered_customer_date::date -
  orders.order_estimated_delivery_date::date)
- Late orders condition: orders.order_delivered_customer_date >
  orders.order_estimated_delivery_date AND orders.order_status = 'delivered'
- Total sales revenue: SUM(order_items.price)
- Total order value: SUM(order_items.price + order_items.freight_value)
- Always use standard PostgreSQL syntax.
"""


def get_schema_context() -> str:
    """Return relational database schema context formatted for LLM prompting."""
    return SCHEMA_PROMPT.strip()
