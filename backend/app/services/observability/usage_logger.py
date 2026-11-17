import json
import uuid
from decimal import Decimal
from typing import Any

from app.db import get_db_connection

# Cost calculation constants for Gemini 3.5 Flash per million tokens
COST_PER_MILLION_INPUT = 0.075
COST_PER_MILLION_OUTPUT = 0.30


def calculate_cost_usd(input_tokens: int, output_tokens: int) -> float:
    """Calculate estimated inference cost in USD based on token counts."""
    input_cost = (input_tokens / 1_000_000.0) * COST_PER_MILLION_INPUT
    output_cost = (output_tokens / 1_000_000.0) * COST_PER_MILLION_OUTPUT
    return round(input_cost + output_cost, 6)


def log_query_execution(
    query_text: str,
    agent_path: str,
    latency_ms: int,
    input_tokens: int = 0,
    output_tokens: int = 0,
    sql_query: str | None = None,
    verification_passed: bool = True,
    retried: bool = False,
    retry_fixed: bool = False,
    tool_calls: list[dict[str, Any]] | None = None,
    citations: list[dict[str, Any]] | None = None,
) -> str:
    """Persist request audit metrics into PostgreSQL query_logs table."""
    query_id = str(uuid.uuid4())
    cost = calculate_cost_usd(input_tokens, output_tokens)

    sql = """
        INSERT INTO query_logs (
            query_id, query_text, agent_path, sql_query, latency_ms,
            input_tokens, output_tokens, estimated_cost_usd,
            verification_passed, retried, retry_fixed,
            tool_calls, citations
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s::jsonb, %s::jsonb
        );
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    query_id,
                    query_text,
                    agent_path,
                    sql_query,
                    latency_ms,
                    input_tokens,
                    output_tokens,
                    Decimal(str(cost)),
                    verification_passed,
                    retried,
                    retry_fixed,
                    json.dumps(tool_calls or []),
                    json.dumps(citations or []),
                ),
            )
        conn.commit()

    return query_id


def get_analytics_metrics() -> dict[str, Any]:
    """Aggregate high-level metrics and usage trends from query_logs."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # 1. Total counts, latency, and costs
            cur.execute("""
                SELECT 
                    COUNT(*) AS total_queries,
                    COALESCE(AVG(latency_ms), 0) AS avg_latency_ms,
                    COALESCE(
                        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms), 0
                    ) AS p95_latency_ms,
                    COALESCE(AVG(estimated_cost_usd), 0) AS avg_cost_usd,
                    COALESCE(SUM(estimated_cost_usd), 0) AS total_cost_usd,
                    COUNT(*) FILTER (WHERE verification_passed = TRUE) AS passed_verification,
                    COUNT(*) FILTER (WHERE retried = TRUE) AS total_retried,
                    COUNT(*) FILTER (WHERE retry_fixed = TRUE) AS total_retry_fixed
                FROM query_logs;
            """)
            stats = cur.fetchone() or {}

            # 2. Agent Path Route Split
            cur.execute("""
                SELECT agent_path, COUNT(*) AS route_count
                FROM query_logs
                GROUP BY agent_path;
            """)
            route_rows = cur.fetchall()
            route_split = {r["agent_path"]: r["route_count"] for r in route_rows}

            # 3. Top Retrieved Documents (extracted from citations JSONB array)
            cur.execute("""
                SELECT 
                    cit->>'document' AS document_name,
                    COUNT(*) AS citation_count
                FROM query_logs,
                     jsonb_array_elements(citations) AS cit
                WHERE cit->>'document' IS NOT NULL
                GROUP BY document_name
                ORDER BY citation_count DESC
                LIMIT 10;
            """)
            doc_rows = cur.fetchall()
            top_docs = [
                {"document": r["document_name"], "citations": r["citation_count"]}
                for r in doc_rows
            ]

            # 4. Recent Queries Log (last 25 queries)
            cur.execute("""
                SELECT 
                    query_id, created_at, query_text, agent_path, sql_query,
                    latency_ms, estimated_cost_usd, verification_passed, retried, retry_fixed
                FROM query_logs
                ORDER BY created_at DESC
                LIMIT 25;
            """)
            recent_logs = cur.fetchall()

    total_queries = stats.get("total_queries", 0)
    passed_verif = stats.get("passed_verification", 0)
    verif_rate = (passed_verif / total_queries * 100.0) if total_queries > 0 else 100.0

    return {
        "total_queries": total_queries,
        "avg_latency_ms": round(float(stats.get("avg_latency_ms", 0)), 1),
        "p95_latency_ms": round(float(stats.get("p95_latency_ms", 0)), 1),
        "avg_cost_usd": round(float(stats.get("avg_cost_usd", 0)), 6),
        "total_cost_usd": round(float(stats.get("total_cost_usd", 0)), 4),
        "verification_pass_rate": round(verif_rate, 1),
        "total_retried": stats.get("total_retried", 0),
        "total_retry_fixed": stats.get("total_retry_fixed", 0),
        "route_split": route_split,
        "top_documents": top_docs,
        "recent_queries": [
            {
                "query_id": r["query_id"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                "query_text": r["query_text"],
                "agent_path": r["agent_path"],
                "sql_query": r["sql_query"],
                "latency_ms": r["latency_ms"],
                "estimated_cost_usd": float(r["estimated_cost_usd"]),
                "verification_passed": r["verification_passed"],
                "retried": r["retried"],
                "retry_fixed": r["retry_fixed"],
            }
            for r in recent_logs
        ],
    }
