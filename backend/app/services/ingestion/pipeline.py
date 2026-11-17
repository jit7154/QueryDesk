from pathlib import Path

from app.db import get_db_connection
from app.services.ingestion.chunker import chunk_document
from app.services.ingestion.embedder import embed_batch
from app.services.ingestion.extract import extract_document
from app.services.retrieval.bm25_search import invalidate_bm25_index


def ingest_document_bytes(file_bytes: bytes, filename: str) -> tuple[int, int]:
    """Ingest, chunk, embed, and store document in PostgreSQL."""
    extracted = extract_document(file_bytes, filename)
    chunks = chunk_document(extracted)
    if not chunks:
        return extracted.total_pages, 0

    texts = [c.content for c in chunks]
    embeddings = embed_batch(texts)

    insert_sql = """
        INSERT INTO document_chunks (
            chunk_id, document_name, section_title, page_number, chunk_index, content, embedding
        ) VALUES (%s, %s, %s, %s, %s, %s, %s::vector)
        ON CONFLICT (chunk_id) DO NOTHING;
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Clean up prior records for idempotent ingestion
            cur.execute("DELETE FROM document_chunks WHERE document_name = %s;", (filename,))
            for chunk, emb in zip(chunks, embeddings, strict=True):
                vec_str = "[" + ",".join(str(f) for f in emb) + "]"
                cur.execute(
                    insert_sql,
                    (
                        chunk.chunk_id,
                        chunk.document_name,
                        chunk.section_title,
                        chunk.page_number,
                        chunk.chunk_index,
                        chunk.content,
                        vec_str,
                    ),
                )
        conn.commit()

    invalidate_bm25_index()
    return extracted.total_pages, len(chunks)


def ingest_documents_directory(directory: Path) -> dict[str, int]:
    """Batch ingest all supported documents from a directory with unified embedding calls."""
    files = sorted(list(directory.glob("*.pdf")) + list(directory.glob("*.docx")))
    all_chunks = []
    summary: dict[str, int] = {}

    for f in files:
        data = f.read_bytes()
        extracted = extract_document(data, f.name)
        chunks = chunk_document(extracted)
        summary[f.name] = len(chunks)
        all_chunks.extend(chunks)

    if not all_chunks:
        return summary

    texts = [c.content for c in all_chunks]
    embeddings = embed_batch(texts, batch_size=50)

    insert_sql = """
        INSERT INTO document_chunks (
            chunk_id, document_name, section_title, page_number, chunk_index, content, embedding
        ) VALUES (%s, %s, %s, %s, %s, %s, %s::vector)
        ON CONFLICT (chunk_id) DO NOTHING;
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for f in files:
                cur.execute("DELETE FROM document_chunks WHERE document_name = %s;", (f.name,))
            for chunk, emb in zip(all_chunks, embeddings, strict=True):
                vec_str = "[" + ",".join(str(f) for f in emb) + "]"
                cur.execute(
                    insert_sql,
                    (
                        chunk.chunk_id,
                        chunk.document_name,
                        chunk.section_title,
                        chunk.page_number,
                        chunk.chunk_index,
                        chunk.content,
                        vec_str,
                    ),
                )
        conn.commit()

    invalidate_bm25_index()
    return summary
