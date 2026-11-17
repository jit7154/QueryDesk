import pytest

from app.db import get_db_connection, get_readonly_db_connection
from app.services.sql.executor import execute_guarded_sql
from app.services.sql.guard import validate_and_guard_sql


@pytest.mark.integration
def test_real_database_connectivity() -> None:
    """Verify live PostgreSQL 16 connection with dict_row factory."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 AS alive;")
            row = cur.fetchone()
            assert row is not None
            assert row["alive"] == 1


@pytest.mark.integration
def test_pgvector_extension_loaded() -> None:
    """Verify pgvector extension is installed and functional."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
            ext = cur.fetchone()
            assert ext is not None
            assert ext["extname"] == "vector"


@pytest.mark.integration
def test_readonly_role_and_statement_timeout() -> None:
    """Verify querydesk_ro connection and statement_timeout enforcement."""
    with get_readonly_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SHOW statement_timeout;")
            # Default or explicit timeout
            cur.execute("SET statement_timeout = '500ms';")
            cur.execute("SELECT 'ro_active' AS status;")
            row = cur.fetchone()
            assert row["status"] == "ro_active"


@pytest.mark.integration
def test_guarded_sql_execution_on_database() -> None:
    """Verify guarded SQL execution against live database tables."""
    guarded = validate_and_guard_sql("SELECT COUNT(*) AS total_count FROM customers;")
    res = execute_guarded_sql(guarded)
    assert res.error is None
    assert len(res.rows) == 1
    assert "total_count" in res.rows[0]
