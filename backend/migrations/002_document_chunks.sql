-- Table for storing document chunks with dense vector embeddings
CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id VARCHAR(64) PRIMARY KEY,
    document_name VARCHAR(255) NOT NULL,
    section_title VARCHAR(255) NOT NULL DEFAULT 'General',
    page_number INTEGER NOT NULL DEFAULT 1,
    chunk_index INTEGER NOT NULL DEFAULT 0,
    content TEXT NOT NULL,
    embedding vector(768) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- HNSW index for fast approximate nearest neighbor cosine similarity search
CREATE INDEX IF NOT EXISTS idx_chunks_embedding 
ON document_chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_chunks_document_name 
ON document_chunks (document_name);

-- Permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON document_chunks TO querydesk_user;
GRANT SELECT ON document_chunks TO querydesk_ro;
