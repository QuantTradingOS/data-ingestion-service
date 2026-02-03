-- Example: insert Institutional Policy excerpts for Constitutional AI.
-- Embeddings must be generated externally (e.g. OpenAI text-embedding-3-small) and
-- inserted as vector(1536). This file shows placeholder vectors for schema testing;
-- use the Node seed script or your ETL to populate real embeddings.

-- Placeholder embedding (1536 zeros). Replace with real embeddings from OpenAI for semantic search.
INSERT INTO institutional_policies (policy_id, title, excerpt, full_text, policy_type, embedding)
VALUES (
  'POL-001',
  'Pre-Trade Compliance: Size and Concentration',
  'No single order may exceed 5% of average daily volume. Positions in a single issuer must not exceed 10% of portfolio at cost. All orders above the de minimis threshold require compliance pre-approval.',
  'Full text of policy POL-001...',
  'institutional',
  (SELECT array_fill(0.0, ARRAY[1536])::vector)
)
ON CONFLICT (policy_id) DO NOTHING;

-- After running the schema and this seed, run a proper seed script that calls OpenAI
-- to generate embeddings for each excerpt and UPDATE institutional_policies SET embedding = $1 WHERE policy_id = $2.
