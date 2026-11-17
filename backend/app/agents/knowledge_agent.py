from typing import Any

from google.adk import Agent

from app.config import get_settings
from app.services.retrieval.rag_service import answer_document_query
from app.tools.rag_tool import search_documents

KNOWLEDGE_INSTRUCTION = (
    "You are the Knowledge Agent for RetailFlow. Your role is to search internal company "
    "documents (supplier contracts, refund and returns policies, operations reports, SOPs) "
    "and answer business questions with exact document, section, and page citations."
)


def get_knowledge_agent() -> Agent:
    """Instantiate Google ADK Knowledge Agent configured with hybrid RAG tool."""
    settings = get_settings()
    model_name = settings.llm_model.replace("models/", "")
    return Agent(
        name="knowledge_agent",
        model=model_name,
        instruction=KNOWLEDGE_INSTRUCTION,
        tools=[search_documents],
    )


def run_knowledge_agent(query: str, top_k: int = 5) -> dict[str, Any]:
    """Execute knowledge retrieval and answer synthesis."""
    rag_res = answer_document_query(query, top_k=top_k)
    return {
        "agent": "knowledge_agent",
        "answer": rag_res.answer,
        "citations": [c.model_dump() for c in rag_res.citations],
        "chunks_used": [c.chunk_id for c in rag_res.citations],
    }
