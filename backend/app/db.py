from collections.abc import Generator
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.config import get_settings

_pool: ConnectionPool | None = None
_ro_pool: ConnectionPool | None = None


def init_db_pools() -> None:
    """Initialize connection pools for primary and read-only databases."""
    global _pool, _ro_pool
    settings = get_settings()
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=settings.database_url,
            min_size=1,
            max_size=10,
            open=True,
            kwargs={"row_factory": dict_row},
        )
    if _ro_pool is None:
        _ro_pool = ConnectionPool(
            conninfo=settings.database_readonly_url,
            min_size=1,
            max_size=10,
            open=True,
            kwargs={"row_factory": dict_row},
        )


def close_db_pools() -> None:
    """Close all active database connection pools."""
    global _pool, _ro_pool
    if _pool is not None:
        _pool.close()
        _pool = None
    if _ro_pool is not None:
        _ro_pool.close()
        _ro_pool = None


@contextmanager
def get_db_connection() -> Generator[psycopg.Connection, None, None]:
    """Yield a database connection from the primary pool."""
    global _pool
    if _pool is None:
        init_db_pools()
    assert _pool is not None
    with _pool.connection() as conn:
        yield conn


@contextmanager
def get_readonly_db_connection() -> Generator[psycopg.Connection, None, None]:
    """Yield a database connection from the read-only pool."""
    global _ro_pool
    if _ro_pool is None:
        init_db_pools()
    assert _ro_pool is not None
    with _ro_pool.connection() as conn:
        yield conn


def check_db_health() -> bool:
    """Execute a simple query to verify database connectivity."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                row = cur.fetchone()
                return row is not None
    except Exception:
        return False
