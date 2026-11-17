import pytest

from app.services.sql.guard import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    SQLSecurityException,
    validate_and_guard_sql,
)


def test_guard_blocks_drop_table() -> None:
    """DDL operations such as DROP TABLE must be blocked."""
    with pytest.raises(SQLSecurityException, match="Only SELECT is permitted"):
        validate_and_guard_sql("DROP TABLE orders;")


def test_guard_blocks_update_dml() -> None:
    """DML mutations must be blocked."""
    with pytest.raises(SQLSecurityException, match="Only SELECT is permitted"):
        validate_and_guard_sql("UPDATE orders SET order_status = 'delivered'")


def test_guard_blocks_delete_dml() -> None:
    """DELETE statements must be blocked."""
    with pytest.raises(SQLSecurityException, match="Only SELECT is permitted"):
        validate_and_guard_sql("DELETE FROM order_items WHERE price < 10")


def test_guard_blocks_insert_dml() -> None:
    """INSERT statements must be blocked."""
    with pytest.raises(SQLSecurityException, match="Only SELECT is permitted"):
        validate_and_guard_sql("INSERT INTO customers VALUES ('c1', 'u1', 1234, 'city', 'SP')")


def test_guard_blocks_stacked_queries() -> None:
    """Stacked queries with multiple semicolons must be blocked."""
    with pytest.raises(SQLSecurityException, match="Only single statements are permitted"):
        validate_and_guard_sql("SELECT * FROM orders; DROP TABLE sellers;")


def test_guard_blocks_comment_tricks() -> None:
    """Comment obfuscation intended to bypass statement checks must be blocked."""
    with pytest.raises(SQLSecurityException):
        validate_and_guard_sql("SELECT * FROM orders; -- comment\nDROP TABLE products;")


def test_guard_blocks_forbidden_tables() -> None:
    """Queries referencing tables outside the allow-list must be blocked."""
    with pytest.raises(SQLSecurityException, match="Access to table 'pg_user' is forbidden"):
        validate_and_guard_sql("SELECT usename FROM pg_user")

    forbidden_pattern = "Access to table '(?:information_schema|tables)' is forbidden"
    with pytest.raises(SQLSecurityException, match=forbidden_pattern):
        validate_and_guard_sql("SELECT * FROM information_schema.tables")


def test_guard_blocks_union_table_injection() -> None:
    """UNION queries attempting to exfiltrate unauthorized tables must be blocked."""
    union_query = "SELECT order_id FROM orders UNION SELECT usename FROM pg_user"
    with pytest.raises(SQLSecurityException, match="Access to table 'pg_user' is forbidden"):
        validate_and_guard_sql(union_query)


def test_guard_blocks_dangerous_functions() -> None:
    """Execution of dangerous system routines like pg_sleep must be blocked."""
    with pytest.raises(SQLSecurityException, match="Execution of function 'pg_sleep' is blocked"):
        validate_and_guard_sql("SELECT pg_sleep(10) FROM orders")


def test_guard_injects_default_limit() -> None:
    """Queries without a limit clause must have DEFAULT_LIMIT injected."""
    result = validate_and_guard_sql("SELECT order_id, order_status FROM orders")
    assert f"LIMIT {DEFAULT_LIMIT}" in result


def test_guard_clamps_excessive_limit() -> None:
    """Limits exceeding MAX_LIMIT must be clamped down."""
    result = validate_and_guard_sql("SELECT order_id FROM orders LIMIT 9999")
    assert f"LIMIT {MAX_LIMIT}" in result


def test_guard_allows_valid_complex_query() -> None:
    """Legitimate business analytics queries across allowed tables must pass."""
    valid_query = """
        SELECT s.seller_id, s.seller_city, COUNT(oi.order_id) AS items_sold,
               SUM(oi.price) AS total_revenue
        FROM sellers s
        JOIN order_items oi ON s.seller_id = oi.seller_id
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY s.seller_id, s.seller_city
        ORDER BY total_revenue DESC
        LIMIT 10
    """
    result = validate_and_guard_sql(valid_query)
    assert "LIMIT 10" in result
    assert "sellers" in result
    assert "order_items" in result
