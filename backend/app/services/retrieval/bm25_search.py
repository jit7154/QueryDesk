import re

from rank_bm25 import BM25Okapi

from app.db import get_db_connection
from app.schemas.document import ChunkInfo

_bm25_index: BM25Okapi | None = None
_indexed_chunks: list[ChunkInfo] = []


def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric tokens."""
    return re.findall(r"\w+", text.lower())


def build_bm25_index() -> None:
    """Build or rebuild in-memory BM25 index from all document chunks."""
    global _bm25_index, _indexed_chunks
    chunks: list[ChunkInfo] = []
    sql = """
        SELECT chunk_id, document_name, section_title, page_number, chunk_index, content
        FROM document_chunks
        ORDER BY document_name, chunk_index;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            for r in rows:
                chunks.append(
                    ChunkInfo(
                        chunk_id=r["chunk_id"],
                        document_name=r["document_name"],
                        section_title=r["section_title"],
                        page_number=r["page_number"],
                        chunk_index=r["chunk_index"],
                        content=r["content"],
                        score=0.0,
                    )
                )

    _indexed_chunks = chunks
    if chunks:
        tokenized_corpus = [tokenize(c.content) for c in chunks]
        _bm25_index = BM25Okapi(tokenized_corpus)
    else:
        _bm25_index = None


def search_bm25(query: str, top_k: int = 10) -> list[ChunkInfo]:
    """Search document chunks using BM25Okapi lexical matching."""
    global _bm25_index, _indexed_chunks
    if _bm25_index is None:
        build_bm25_index()

    if _bm25_index is None or not _indexed_chunks:
        return []

    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    scores = _bm25_index.get_scores(query_tokens)
    scored_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

    results: list[ChunkInfo] = []
    for idx in scored_indices[:top_k]:
        if scores[idx] > 0:
            chunk = _indexed_chunks[idx]
            results.append(
                ChunkInfo(
                    chunk_id=chunk.chunk_id,
                    document_name=chunk.document_name,
                    section_title=chunk.section_title,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    score=float(scores[idx]),
                )
            )

    return results


def invalidate_bm25_index() -> None:
    """Clear BM25 index cache to trigger refresh on next search."""
    global _bm25_index, _indexed_chunks
    _bm25_index = None
    _indexed_chunks = []
