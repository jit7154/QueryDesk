-- Table for tracking agent execution, latency, tokens, cost, and verification status
CREATE TABLE IF NOT EXISTS query_logs (
    query_id VARCHAR(64) PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    query_text TEXT NOT NULL,
    agent_path VARCHAR(50) NOT NULL,
    sql_query TEXT,
    latency_ms INTEGER NOT NULL,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    estimated_cost_usd NUMERIC(10, 6) NOT NULL DEFAULT 0.0,
    verification_passed BOOLEAN NOT NULL DEFAULT TRUE,
    retried BOOLEAN NOT NULL DEFAULT FALSE,
    retry_fixed BOOLEAN NOT NULL DEFAULT FALSE,
    tool_calls JSONB DEFAULT '[]'::jsonb,
    citations JSONB DEFAULT '[]'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_query_logs_created_at ON query_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_query_logs_agent_path ON query_logs (agent_path);

GRANT SELECT, INSERT, UPDATE, DELETE ON query_logs TO querydesk_user;
GRANT SELECT ON query_logs TO querydesk_ro;
