import { AnalyticsData, ChatMessage, ChunkInfo, DocumentSummary } from "../types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  const headers = new Headers(options.headers || {});
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    const errorBody = await response.text();
    let message = `API request to ${endpoint} failed with status ${response.status}`;
    try {
      const parsed = JSON.parse(errorBody);
      if (parsed.detail) message = parsed.detail;
    } catch {
      if (errorBody) message = errorBody;
    }
    throw new ApiError(response.status, message);
  }

  return response.json() as Promise<T>;
}

export const apiClient = {
  async sendChat(query: string, conversationId?: string): Promise<ChatMessage> {
    const raw = await request<{
      answer: string;
      agent_path: "document_only" | "sql_only" | "hybrid";
      citations: Array<{ document: string; section: string; page: number; chunk_id: string; snippet?: string }>;
      sql_query: string | null;
      sql_rows: Record<string, unknown>[];
      verification_passed: boolean;
      retried: boolean;
      retry_fixed: boolean;
      latency_ms: number;
      execution_steps: string[];
    }>("/api/chat", {
      method: "POST",
      body: JSON.stringify({ query, conversation_id: conversationId }),
    });

    return {
      id: crypto.randomUUID(),
      role: "assistant",
      content: raw.answer,
      timestamp: new Date().toISOString(),
      agentPath: raw.agent_path,
      citations: raw.citations,
      sqlQuery: raw.sql_query,
      sqlRows: raw.sql_rows,
      verificationPassed: raw.verification_passed,
      retried: raw.retried,
      retryFixed: raw.retry_fixed,
      latencyMs: raw.latency_ms,
      executionSteps: raw.execution_steps,
    };
  },

  async getDocuments(): Promise<DocumentSummary[]> {
    return request<DocumentSummary[]>("/api/documents");
  },

  async getDocumentChunks(documentName: string): Promise<ChunkInfo[]> {
    return request<ChunkInfo[]>(`/api/documents/${encodeURIComponent(documentName)}`);
  },

  async uploadDocument(file: File): Promise<{ document_name: string; total_pages: number; chunks_created: number }> {
    const formData = new FormData();
    formData.append("file", file);
    return request("/api/documents/upload", {
      method: "POST",
      body: formData,
    });
  },

  async deleteDocument(documentName: string): Promise<{ message: string }> {
    return request<{ message: string }>(`/api/documents/${encodeURIComponent(documentName)}`, {
      method: "DELETE",
    });
  },

  async getAnalytics(): Promise<AnalyticsData> {
    return request<AnalyticsData>("/api/analytics");
  },

  async getHealth(): Promise<{ status: string; database: string; environment: string }> {
    return request<{ status: string; database: string; environment: string }>("/api/health");
  },
};
