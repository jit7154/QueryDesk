from typing import Any

from pydantic import BaseModel, Field

from app.schemas.document import Citation


class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Natural language question to answer")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of source chunks to retrieve")


class RAGQueryResponse(BaseModel):
    query: str
    answer: str
    citations: list[Citation]
    retrieval_method: str = "hybrid_rrf"


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=2, description="User business question")
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    agent_path: str
    citations: list[Citation] = []
    sql_query: str | None = None
    sql_rows: list[dict[str, Any]] = []
    verification_passed: bool = True
    retried: bool = False
    retry_fixed: bool = False
    latency_ms: int = 0
    execution_steps: list[str] = []
