export type QueryMode = "trusted-llm" | "llm" | "rule-based";

export interface QueryAnswer {
  columns: string[];
  rows: Array<Array<string | number | null>>;
  row_count: number;
}

export interface GuardrailsPayload {
  status: string;
  reason: string;
  read_only: boolean;
  dangerous_keywords: string[];
  table_validation?: {
    ok: boolean;
    referenced_tables: string[];
    unknown_tables: string[];
  };
  column_validation?: {
    ok: boolean;
    unknown_columns: string[];
  };
  sqlite_validation?: {
    ok: boolean;
    message: string;
  };
}

export interface ProviderPayload {
  source?: string | null;
  name?: string | null;
  model?: string | null;
  available_models?: string[];
  message?: string;
}

export interface AskResponse {
  status: string;
  mode: QueryMode;
  question: string;
  sql: string | null;
  explanation: string;
  answer: QueryAnswer | null;
  guardrails: GuardrailsPayload | null;
  provider: ProviderPayload | null;
  trust_note: string;
}

export interface HistoryItem extends AskResponse {
  id: number;
  provider_name?: string | null;
  provider_model?: string | null;
  created_at: string;
}

export interface HealthResponse {
  status: string;
  database_ready: boolean;
  provider: ProviderPayload;
  recent_queries: number;
}
