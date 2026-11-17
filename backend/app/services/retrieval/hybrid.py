from app.schemas.document import ChunkInfo, Citation
from app.services.ingestion.embedder import embed_text
from app.services.retrieval.bm25_search import search_bm25
from app.services.retrieval.rrf import reciprocal_rank_fusion
from app.services.retrieval.vector_search import search_vector


def hybrid_retrieve(query: str, top_k: int = 5) -> list[ChunkInfo]:
    """Execute hybrid retrieval combining dense vector search and sparse BM25 with RRF."""
    query_emb = embed_text(query)
    candidate_k = max(top_k * 2, 10)

    vector_candidates = search_vector(query_emb, top_k=candidate_k)
    bm25_candidates = search_bm25(query, top_k=candidate_k)

    return reciprocal_rank_fusion(
        ranked_lists=[vector_candidates, bm25_candidates],
        k=60,
        top_k=top_k,
    )


def chunks_to_citations(chunks: list[ChunkInfo]) -> list[Citation]:
    """Convert retrieved chunks into structured citation objects."""
    citations: list[Citation] = []
    seen_chunks: set[str] = set()

    for c in chunks:
        if c.chunk_id in seen_chunks:
            continue
        seen_chunks.add(c.chunk_id)
        snippet = c.content[:150] + "..." if len(c.content) > 150 else c.content
        citations.append(
            Citation(
                document=c.document_name,
                section=c.section_title,
                page=c.page_number,
                chunk_id=c.chunk_id,
                snippet=snippet,
            )
        )

    return citations
