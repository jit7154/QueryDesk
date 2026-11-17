from typing import Any

from app.services.retrieval.hybrid import chunks_to_citations, hybrid_retrieve


def search_documents(query: str, top_k: int = 5) -> dict[str, Any]:
    """Search internal RetailFlow documents via hybrid RRF retrieval."""
    chunks = hybrid_retrieve(query, top_k=top_k)
    citations = chunks_to_citations(chunks)
    return {
        "chunks": [c.model_dump() for c in chunks],
        "citations": [cit.model_dump() for cit in citations],
        "count": len(chunks),
    }
