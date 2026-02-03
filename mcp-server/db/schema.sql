-- Institutional Policy store with pgvector for Constitutional AI / compliance context.
-- Run against a PostgreSQL 15+ instance with pgvector extension.
-- Usage: psql $DATABASE_URL -f db/schema.sql

CREATE EXTENSION IF NOT EXISTS vector;

-- Policies are stored as excerpts with embeddings for similarity search.
-- Embedding dimension 1536 matches OpenAI text-embedding-3-small.
CREATE TABLE IF NOT EXISTS institutional_policies (
    id SERIAL PRIMARY KEY,
    policy_id VARCHAR(64) NOT NULL UNIQUE,
    title VARCHAR(512) NOT NULL,
    excerpt TEXT NOT NULL,
    full_text TEXT,
    policy_type VARCHAR(64) NOT NULL DEFAULT 'institutional', -- e.g. 'institutional', 'trading', 'risk', 'aml'
    embedding vector(1536),
    effective_from TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_institutional_policies_policy_type ON institutional_policies(policy_type);
CREATE INDEX IF NOT EXISTS idx_institutional_policies_effective_from ON institutional_policies(effective_from);

-- IVFFlat index for cosine similarity (<=> operator). Tune lists for table size.
CREATE INDEX IF NOT EXISTS idx_institutional_policies_embedding
ON institutional_policies USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

COMMENT ON TABLE institutional_policies IS 'Institutional policy excerpts for Constitutional AI; used for semantic retrieval before trading tool execution.';
