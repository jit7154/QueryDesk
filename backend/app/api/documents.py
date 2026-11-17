from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.db import get_db_connection
from app.schemas.document import ChunkInfo, DocumentSummary, DocumentUploadResponse
from app.services.ingestion.pipeline import ingest_document_bytes
from app.services.retrieval.bm25_search import invalidate_bm25_index

router = APIRouter(prefix="/api/documents", tags=["documents"])

MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB limit
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
    """Upload and ingest a PDF or DOCX document into vector and lexical indexes."""
    filename = file.filename or "unknown"
    ext = "." + filename.split(".")[-1].lower() if "." in filename else ""

    if ext not in ALLOWED_EXTENSIONS:
        types_str = ", ".join(ALLOWED_EXTENSIONS)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed types are: {types_str}",
        )

    content = await file.read()
    max_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {max_mb} MB",
        )

    total_pages, chunks_created = ingest_document_bytes(content, filename)

    return DocumentUploadResponse(
        document_name=filename,
        file_type=ext.replace(".", ""),
        total_pages=total_pages,
        chunks_created=chunks_created,
    )


@router.get("", response_model=list[DocumentSummary])
def list_documents() -> list[DocumentSummary]:
    """Retrieve list of all ingested documents with page and chunk counts."""
    sql = """
        SELECT 
            document_name,
            MAX(page_number) AS total_pages,
            COUNT(*) AS total_chunks,
            MIN(created_at) AS created_at
        FROM document_chunks
        GROUP BY document_name
        ORDER BY document_name ASC;
    """
    summaries: list[DocumentSummary] = []
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            for r in rows:
                ext = r["document_name"].split(".")[-1] if "." in r["document_name"] else ""
                summaries.append(
                    DocumentSummary(
                        document_name=r["document_name"],
                        file_type=ext,
                        total_pages=r["total_pages"],
                        total_chunks=r["total_chunks"],
                        created_at=r["created_at"],
                    )
                )
    return summaries


@router.get("/{document_name}", response_model=list[ChunkInfo])
def get_document_chunks(document_name: str) -> list[ChunkInfo]:
    """Retrieve all chunks belonging to a specific document."""
    sql = """
        SELECT chunk_id, document_name, section_title, page_number, chunk_index, content
        FROM document_chunks
        WHERE document_name = %s
        ORDER BY chunk_index ASC;
    """
    chunks: list[ChunkInfo] = []
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (document_name,))
            rows = cur.fetchall()
            if not rows:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document '{document_name}' not found",
                )
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
    return chunks


@router.delete("/{document_name}")
def delete_document(document_name: str) -> dict[str, str]:
    """Delete all chunks for a document from storage and invalidate search indexes."""
    sql = "DELETE FROM document_chunks WHERE document_name = %s;"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (document_name,))
            deleted = cur.rowcount
        conn.commit()

    if deleted == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_name}' not found",
        )

    invalidate_bm25_index()
    return {"message": f"Successfully deleted '{document_name}' ({deleted} chunks removed)"}
