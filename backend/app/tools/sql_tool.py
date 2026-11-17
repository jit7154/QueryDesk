from typing import Any

from app.services.sql.executor import execute_guarded_sql, generate_sql
from app.services.sql.guard import SQLSecurityException, validate_and_guard_sql


def execute_sql_query(query: str) -> dict[str, Any]:
    """Execute a guarded read-only SQL query against the RetailFlow e-commerce database."""
    try:
        guarded_sql = validate_and_guard_sql(query)
        res = execute_guarded_sql(guarded_sql)
        return {
            "query": res.query,
            "columns": res.columns,
            "rows": res.rows,
            "row_count": res.row_count,
            "execution_time_ms": res.execution_time_ms,
            "error": res.error,
        }
    except SQLSecurityException as sec_err:
        return {
            "query": query,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "execution_time_ms": 0.0,
            "error": str(sec_err),
        }


def text_to_sql_query(question: str) -> dict[str, Any]:
    """Translate natural language business inquiry to safe SQL, validate, and execute."""
    raw_sql = generate_sql(question)
    return execute_sql_query(raw_sql)
