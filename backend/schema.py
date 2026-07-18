from __future__ import annotations

SCHEMA_TEXT = """
Tables:
customers(id, name, city, signup_date, is_repeat)
products(id, name, category, price)
orders(id, customer_id, order_date, total_amount, city)
order_items(id, order_id, product_id, quantity)
returns(id, order_id, reason, return_date)

Relationships:
- orders.customer_id -> customers.id
- order_items.order_id -> orders.id
- order_items.product_id -> products.id
- returns.order_id -> orders.id

Notes:
- is_repeat is 1 for repeat customers, 0 otherwise.
- Dates are stored as TEXT in YYYY-MM-DD format.
- When a question uses a relative date like "last week", anchor it to the latest
  order_date present in the data rather than the current calendar date.
""".strip()

SCHEMA_MAP = {
    "customers": ["id", "name", "city", "signup_date", "is_repeat"],
    "products": ["id", "name", "category", "price"],
    "orders": ["id", "customer_id", "order_date", "total_amount", "city"],
    "order_items": ["id", "order_id", "product_id", "quantity"],
    "returns": ["id", "order_id", "reason", "return_date"],
}

RELATIONSHIP_NOTES = [
    "An order belongs to a customer through orders.customer_id = customers.id.",
    "Order items belong to an order through order_items.order_id = orders.id.",
    "Each order item references a product through order_items.product_id = products.id.",
    "A return references an order through returns.order_id = orders.id.",
]

VALID_TABLES = set(SCHEMA_MAP.keys())
VALID_COLUMNS = {table: set(columns) for table, columns in SCHEMA_MAP.items()}
