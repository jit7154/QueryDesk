-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create read-only role for guarded SQL queries
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'querydesk_ro') THEN
    CREATE ROLE querydesk_ro WITH LOGIN PASSWORD 'querydesk_ro_password';
  END IF;
END
$$;

GRANT CONNECT ON DATABASE querydesk TO querydesk_ro;
GRANT USAGE ON SCHEMA public TO querydesk_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO querydesk_ro;
