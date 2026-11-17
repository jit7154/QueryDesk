export interface Citation {
  document: string;
  section: string;
  page: number;
  chunk_id: string;
  snippet?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  agentPath?: "document_only" | "sql_only" | "hybrid";
  citations?: Citation[];
  sqlQuery?: string | null;
  sqlRows?: Record<string, unknown>[];
  verificationPassed?: boolean;
  retried?: boolean;
  retryFixed?: boolean;
  latencyMs?: number;
  executionSteps?: string[];
}

export interface DocumentSummary {
  document_name: string;
  file_type: string;
  total_pages: number;
  total_chunks: number;
  created_at: string | null;
}

export interface ChunkInfo {
  chunk_id: string;
  document_name: string;
  section_title: string;
  page_number: number;
  chunk_index: number;
  content: string;
  score?: number;
}

export interface AnalyticsData {
  total_queries: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  avg_cost_usd: number;
  total_cost_usd: number;
  verification_pass_rate: number;
  total_retried: number;
  total_retry_fixed: number;
  route_split: Record<string, number>;
  top_documents: { document: string; citations: number }[];
  recent_queries: {
    query_id: string;
    created_at: string;
    query_text: string;
    agent_path: string;
    sql_query: string | null;
    latency_ms: number;
    estimated_cost_usd: number;
    verification_passed: boolean;
    retried: boolean;
    retry_fixed: boolean;
  }[];
}
