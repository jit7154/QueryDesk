from typing import Any

from google.adk import Agent

from app.config import get_settings
from app.services.ingestion.embedder import get_genai_client
from app.services.sql.executor import run_text_to_sql
from app.tools.sql_tool import text_to_sql_query

DATA_ANALYST_INSTRUCTION = (
    "You are the Data Analyst Agent for RetailFlow. Your role is to formulate safe, "
    "read-only PostgreSQL queries over relational e-commerce tables (orders, order_items, "
    "sellers, products, customers, order_payments) and summarize the quantitative results."
)


def get_data_analyst_agent() -> Agent:
    """Instantiate Google ADK Data Analyst Agent configured with SQL execution tool."""
    settings = get_settings()
    model_name = settings.llm_model.replace("models/", "")
    return Agent(
        name="data_analyst_agent",
        model=model_name,
        instruction=DATA_ANALYST_INSTRUCTION,
        tools=[text_to_sql_query],
    )


def run_data_analyst_agent(query: str) -> dict[str, Any]:
    """Execute natural language to guarded SQL translation and summarize findings."""
    sql_res = run_text_to_sql(query)
    if sql_res.error:
        return {
            "agent": "data_analyst_agent",
            "answer": f"Unable to execute SQL analysis: {sql_res.error}",
            "sql_query": sql_res.query,
            "sql_rows": [],
            "row_count": 0,
            "execution_time_ms": sql_res.execution_time_ms,
        }

    # Format answer narrative with LLM based on execution results
    settings = get_settings()
    client = get_genai_client()
    model_name = settings.llm_model.replace("models/", "")

    prompt = (
        "You are the Data Analyst Agent for RetailFlow. Present the following database query\n"
        "results in a clear, concise professional summary. State the exact numbers accurately\n"
        "without altering values.\n\n"
        f"User Question: {query}\n"
        f"SQL Executed: {sql_res.query}\n"
        f"SQL Result Data (first 10 rows): {sql_res.rows[:10]}\n\n"
        "Summary:"
    )

    try:
        resp = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        answer = resp.text.strip() if resp.text else "Query completed successfully."
    except Exception as exc:
        sample_rows = sql_res.rows[:5]
        answer = (
            f"Query executed successfully with {sql_res.row_count} rows: "
            f"{sample_rows} (Summary error: {exc})"
        )

    return {
        "agent": "data_analyst_agent",
        "answer": answer,
        "sql_query": sql_res.query,
        "sql_rows": sql_res.rows,
        "row_count": sql_res.row_count,
        "execution_time_ms": sql_res.execution_time_ms,
    }
