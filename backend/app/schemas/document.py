from datetime import datetime

from pydantic import BaseModel


class Citation(BaseModel):
    document: str
    section: str
    page: int
    chunk_id: str
    snippet: str = ""


class ChunkInfo(BaseModel):
    chunk_id: str
    document_name: str
    section_title: str
    page_number: int
    chunk_index: int
    content: str
    score: float = 0.0


class DocumentSummary(BaseModel):
    document_name: str
    file_type: str
    total_pages: int
    total_chunks: int
    created_at: datetime | None = None


class DocumentUploadResponse(BaseModel):
    document_name: str
    file_type: str
    total_pages: int
    chunks_created: int
    message: str = "Document processed and indexed successfully"
