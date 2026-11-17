from fastapi import APIRouter

from app.agents.supervisor import orchestrate_query
from app.schemas.document import Citation
from app.schemas.rag import ChatRequest, ChatResponse, RAGQueryRequest, RAGQueryResponse
from app.services.retrieval.rag_service import answer_document_query

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def handle_chat(request: ChatRequest) -> ChatResponse:
    """Process natural language business query via multi-agent supervisor orchestrator."""
    result = orchestrate_query(request.query)

    citations = [
        Citation(
            document=c.get("document", ""),
            section=c.get("section", ""),
            page=int(c.get("page", 1)),
            chunk_id=c.get("chunk_id", ""),
            snippet=c.get("snippet", ""),
        )
        for c in result.citations
    ]

    return ChatResponse(
        answer=result.answer,
        agent_path=result.agent_path,
        citations=citations,
        sql_query=result.sql_query,
        sql_rows=result.sql_rows,
        verification_passed=result.verification_passed,
        retried=result.retried,
        retry_fixed=result.retry_fixed,
        latency_ms=result.latency_ms,
        execution_steps=result.execution_steps,
    )


@router.post("/rag", response_model=RAGQueryResponse)
def query_rag(request: RAGQueryRequest) -> RAGQueryResponse:
    """Answer business questions over unstructured documents via hybrid RRF retrieval."""
    return answer_document_query(query=request.query, top_k=request.top_k)
