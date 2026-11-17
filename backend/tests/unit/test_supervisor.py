from unittest.mock import MagicMock, patch

from app.schemas.document import ChunkInfo
from app.services.observability.usage_logger import calculate_cost_usd
from app.services.sql.executor import SQLResult
from app.tools.rag_tool import search_documents
from app.tools.sql_tool import execute_sql_query


def test_calculate_cost_usd() -> None:
    """Cost calculation must match Gemini token pricing rules."""
    # 1,000,000 input tokens = $0.075, 1,000,000 output tokens = $0.30
    cost = calculate_cost_usd(1_000_000, 1_000_000)
    assert cost == 0.375

    # 1,000 input tokens, 200 output tokens
    small_cost = calculate_cost_usd(1000, 200)
    assert small_cost > 0.0


@patch("app.tools.rag_tool.hybrid_retrieve")
def test_rag_tool_structure(mock_retrieve: MagicMock) -> None:
    """RAG tool returns structured dictionary without calling external APIs."""
    mock_retrieve.return_value = [
        ChunkInfo(
            chunk_id="test_chunk_1",
            document_name="Supplier_Contract_Apex.pdf",
            section_title="Section 7.2",
            page_number=3,
            chunk_index=1,
            content="Supplier shall incur late penalty of 4% per week.",
            score=0.95,
        )
    ]
    res = search_documents("late delivery penalty", top_k=2)
    assert "chunks" in res
    assert "citations" in res
    assert "count" in res
    assert isinstance(res["chunks"], list)
    assert res["count"] == 1
    assert res["citations"][0]["document"] == "Supplier_Contract_Apex.pdf"
    assert res["citations"][0]["section"] == "Section 7.2"


@patch("app.tools.sql_tool.execute_guarded_sql")
def test_sql_tool_structure(mock_exec: MagicMock) -> None:
    """SQL tool executes guarded queries and returns output without live DB tables."""
    mock_exec.return_value = SQLResult(
        query="SELECT COUNT(*) AS total FROM orders LIMIT 50;",
        columns=["total"],
        rows=[{"total": 99441}],
        row_count=1,
        execution_time_ms=12.5,
        error=None,
    )
    res = execute_sql_query("SELECT COUNT(*) AS total FROM orders;")
    assert "columns" in res
    assert "rows" in res
    assert res["error"] is None
    assert len(res["rows"]) == 1
    assert res["rows"][0]["total"] == 99441
