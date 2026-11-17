import re

import sqlglot
from sqlglot import exp

ALLOWED_TABLES = {
    "orders",
    "order_items",
    "products",
    "sellers",
    "customers",
    "order_payments",
}

BLOCKED_FUNCTIONS = {
    "pg_sleep",
    "query_to_xml",
    "pg_read_file",
    "pg_read_binary_file",
    "pg_ls_dir",
    "pg_stat_file",
    "dblink",
    "lo_export",
    "lo_import",
    "current_setting",
    "set_config",
}

DEFAULT_LIMIT = 50
MAX_LIMIT = 100


class SQLSecurityException(Exception):
    """Raised when a candidate query violates AST safety rules."""


def validate_and_guard_sql(raw_sql: str) -> str:
    """Validate SQL query against AST security rules and inject safe LIMIT clause."""
    clean_sql = raw_sql.strip()
    if clean_sql.endswith(";"):
        clean_sql = clean_sql[:-1].strip()

    # Block comment-based statement separation tricks before parsing
    if re.search(r";\s*--", raw_sql) or re.search(r"--[^\n]*\n\s*;", raw_sql):
        raise SQLSecurityException("Stacked queries disguised with comments are blocked")

    try:
        statements = [s for s in sqlglot.parse(clean_sql, read="postgres") if s is not None]
    except Exception as exc:
        raise SQLSecurityException(f"Failed to parse SQL syntax: {exc}") from exc

    # Multi-statement injection defense
    if len(statements) != 1:
        raise SQLSecurityException(
            "Only single statements are permitted; stacked queries are blocked"
        )

    parsed = statements[0]

    # Only read-only SELECT or set operations composed of SELECT are allowed
    if not isinstance(parsed, (exp.Select, exp.Union)):
        stmt_type = parsed.key.upper()
        raise SQLSecurityException(
            f"Statement '{stmt_type}' is not allowed. Only SELECT is permitted"
        )

    # Table allow-list defense: inspect all Table references in AST
    tables = [t.name.lower() for t in parsed.find_all(exp.Table) if t.name]
    if not tables:
        raise SQLSecurityException("Queries must select from an authorized business table")

    for tbl in tables:
        if tbl not in ALLOWED_TABLES:
            allowed_list = ", ".join(sorted(ALLOWED_TABLES))
            raise SQLSecurityException(
                f"Access to table '{tbl}' is forbidden. Allowed tables: {allowed_list}"
            )

    # Block administrative and file exfiltration functions
    funcs = [f.name.lower() for f in parsed.find_all((exp.Anonymous, exp.Func)) if f.name]
    for fn in funcs:
        if fn in BLOCKED_FUNCTIONS:
            raise SQLSecurityException(f"Execution of function '{fn}' is blocked for security")

    # Enforce result limits to prevent unbounded memory consumption and denial of service
    limit_expr = parsed.find(exp.Limit)
    if limit_expr is None:
        parsed = parsed.limit(DEFAULT_LIMIT)
    else:
        try:
            val = int(limit_expr.expression.this)
            if val > MAX_LIMIT or val <= 0:
                limit_expr.set("expression", exp.Literal.number(MAX_LIMIT))
        except (ValueError, AttributeError):
            limit_expr.set("expression", exp.Literal.number(MAX_LIMIT))

    return parsed.sql(dialect="postgres")
