from app.db import get_db_connection
from app.schemas.document import ChunkInfo


def search_vector(query_embedding: list[float], top_k: int = 10) -> list[ChunkInfo]:
    """Search document chunks using pgvector cosine distance over HNSW index."""
    vector_str = "[" + ",".join(str(f) for f in query_embedding) + "]"
    sql = """
        SELECT 
            chunk_id, 
            document_name, 
            section_title, 
            page_number, 
            chunk_index, 
            content,
            1.0 - (embedding <=> %s::vector) AS similarity_score
        FROM document_chunks
        ORDER BY embedding <=> %s::vector ASC
        LIMIT %s;
    """
    results: list[ChunkInfo] = []
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (vector_str, vector_str, top_k))
            rows = cur.fetchall()
            for r in rows:
                results.append(
                    ChunkInfo(
                        chunk_id=r["chunk_id"],
                        document_name=r["document_name"],
                        section_title=r["section_title"],
                        page_number=r["page_number"],
                        chunk_index=r["chunk_index"],
                        content=r["content"],
                        score=float(r["similarity_score"]),
                    )
                )
    return results
