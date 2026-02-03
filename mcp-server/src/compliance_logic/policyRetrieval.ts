/**
 * pgvector-based retrieval of Institutional Policy excerpts.
 * Used to inject Constitutional AI context when trading tools are invoked.
 */

const EMBEDDING_DIM = 1536;
const DEFAULT_TOP_K = 5;
const DEFAULT_MIN_SIMILARITY = 0.7;

export interface PolicySnippet {
  id: number;
  policy_id: string;
  title: string;
  excerpt: string;
  policy_type: string;
  similarity: number;
}

export interface PolicyRetrievalResult {
  query: string;
  snippets: PolicySnippet[];
  error?: string;
}

export interface PolicyRetrievalConfig {
  databaseUrl: string;
  openaiApiKey?: string;
  embeddingModel?: string;
  topK?: number;
  minSimilarity?: number;
}

let pgClient: InstanceType<typeof import("pg").Client> | null = null;

async function getPgClient(databaseUrl: string): Promise<InstanceType<typeof import("pg").Client>> {
  if (!pgClient) {
    const { default: pg } = await import("pg");
    pgClient = new pg.Client({ connectionString: databaseUrl });
    await pgClient.connect();
  }
  return pgClient;
}

/**
 * Ensure the DB client is connected. Call once before queries.
 */
export async function ensurePolicyDbConnected(config: PolicyRetrievalConfig): Promise<boolean> {
  try {
    await getPgClient(config.databaseUrl);
    return true;
  } catch (e) {
    console.error("[policyRetrieval] DB connect failed:", e);
    return false;
  }
}

/**
 * Generate embedding for text using OpenAI. Returns null if key missing or request fails.
 */
export async function embedText(
  text: string,
  apiKey: string | undefined,
  model: string = "text-embedding-3-small"
): Promise<number[] | null> {
  if (!apiKey?.trim()) return null;
  try {
    const res = await fetch("https://api.openai.com/v1/embeddings", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({ model, input: text.slice(0, 8192) }),
    });
    if (!res.ok) {
      const err = await res.text();
      console.error("[policyRetrieval] OpenAI embed error:", res.status, err);
      return null;
    }
    const data = (await res.json()) as { data?: Array<{ embedding: number[] }> };
    const embedding = data.data?.[0]?.embedding;
    if (!embedding || embedding.length !== EMBEDDING_DIM) return null;
    return embedding;
  } catch (e) {
    console.error("[policyRetrieval] OpenAI embed exception:", e);
    return null;
  }
}

/**
 * Run similarity search: find policy excerpts whose embedding is closest to the query embedding.
 * Uses cosine distance (<=>) and returns rows with similarity >= minSimilarity.
 */
export async function searchPoliciesByEmbedding(
  config: PolicyRetrievalConfig,
  queryEmbedding: number[]
): Promise<PolicySnippet[]> {
  const client = await getPgClient(config.databaseUrl);
  const topK = config.topK ?? DEFAULT_TOP_K;
  const minSim = config.minSimilarity ?? DEFAULT_MIN_SIMILARITY;
  const vec = `[${queryEmbedding.join(",")}]`;

  const q = `
    SELECT id, policy_id, title, excerpt, policy_type,
           1 - (embedding <=> $1::vector) AS similarity
    FROM institutional_policies
    WHERE embedding IS NOT NULL
      AND (1 - (embedding <=> $1::vector)) >= $2
    ORDER BY embedding <=> $1::vector
    LIMIT $3
  `;
  const res = await client.query(q, [vec, minSim, topK]);
  return (res.rows as PolicySnippet[]) ?? [];
}

/**
 * High-level: given a query string, embed it and return relevant policy snippets.
 * If DB or OpenAI is unavailable, returns empty snippets and optional error.
 */
export async function retrievePolicyContext(
  config: PolicyRetrievalConfig,
  query: string
): Promise<PolicyRetrievalResult> {
  const result: PolicyRetrievalResult = { query, snippets: [] };

  if (!config.databaseUrl?.trim()) {
    result.error = "DATABASE_URL not configured";
    return result;
  }

  const connected = await ensurePolicyDbConnected(config);
  if (!connected) {
    result.error = "Could not connect to policy database";
    return result;
  }

  const embedding = await embedText(
    query,
    config.openaiApiKey,
    config.embeddingModel ?? "text-embedding-3-small"
  );
  if (!embedding) {
    result.error = "Embedding not available (missing OPENAI_API_KEY or API error)";
    return result;
  }

  try {
    result.snippets = await searchPoliciesByEmbedding(config, embedding);
  } catch (e) {
    console.error("[policyRetrieval] search error:", e);
    result.error = e instanceof Error ? e.message : "Search failed";
  }

  return result;
}

/**
 * Format snippets as a single block for injection into model context (Constitutional AI).
 */
export function formatPolicyContextForInjection(snippets: PolicySnippet[]): string {
  if (snippets.length === 0) return "";
  const lines = [
    "--- Institutional Policy (Constitutional AI context)",
    "Apply the following policy excerpts when executing this request:",
    "",
    ...snippets.map(
      (s) => `[${s.policy_type}] ${s.title}\n${s.excerpt}\n(similarity: ${s.similarity.toFixed(2)})`
    ),
    "---",
  ];
  return lines.join("\n");
}
