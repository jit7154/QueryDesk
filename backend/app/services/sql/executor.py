import time
from dataclasses import dataclass
from typing import Any

from app.config import get_settings
from app.db import get_readonly_db_connection
from app.services.ingestion.embedder import get_genai_client
from app.services.sql.guard import SQLSecurityException, validate_and_guard_sql
from app.services.sql.schema_context import get_schema_context


@dataclass
class SQLResult:
    query: str
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    execution_time_ms: float
    error: str | None = None


def execute_guarded_sql(guarded_sql: str) -> SQLResult:
    """Execute validated read-only SQL with an enforced 3-second statement timeout."""
    start_time = time.perf_counter()
    columns: list[str] = []
    rows: list[dict[str, Any]] = []

    with get_readonly_db_connection() as conn:
        with conn.cursor() as cur:
            # 3-second statement timeout prevents resource exhaustion from complex accidental joins
            cur.execute("SET statement_timeout = '3000ms';")
            cur.execute(guarded_sql)
            if cur.description:
                columns = [desc.name for desc in cur.description]
                raw_rows = cur.fetchall()
                for r in raw_rows:
                    rows.append(dict(r))

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    return SQLResult(
        query=guarded_sql,
        columns=columns,
        rows=rows,
        row_count=len(rows),
        execution_time_ms=round(elapsed_ms, 2),
    )


def generate_sql(natural_language_question: str) -> str:
    """Generate PostgreSQL query from natural language using Gemini and schema context."""
    settings = get_settings()
    client = get_genai_client()
    model_name = settings.llm_model.replace("models/", "")

    prompt = (
        f"{get_schema_context()}\n\n"
        f"User Question: {natural_language_question}\n"
        "PostgreSQL SELECT Query (Return only plain SQL, without code fences or explanation):"
    )

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            break
        except Exception as exc:
            err_str = str(exc)
            if any(k in err_str for k in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"]):
                time.sleep(4 * (attempt + 1))
            else:
                raise exc

    raw_sql = response.text.strip() if response.text else ""
    # Strip markdown code blocks if model included them
    if raw_sql.startswith("```"):
        lines = raw_sql.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        raw_sql = "\n".join(lines).strip()

    return raw_sql


def run_text_to_sql(question: str) -> SQLResult:
    """End-to-end text-to-SQL generation, validation, and safe read-only execution."""
    raw_sql = generate_sql(question)
    try:
        guarded_sql = validate_and_guard_sql(raw_sql)
        return execute_guarded_sql(guarded_sql)
    except SQLSecurityException as sec_err:
        return SQLResult(
            query=raw_sql,
            columns=[],
            rows=[],
            row_count=0,
            execution_time_ms=0.0,
            error=str(sec_err),
        )
    except Exception as exc:
        return SQLResult(
            query=raw_sql,
            columns=[],
            rows=[],
            row_count=0,
            execution_time_ms=0.0,
            error=f"Database execution error: {exc}",
        )
