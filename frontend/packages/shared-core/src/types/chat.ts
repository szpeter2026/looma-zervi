/**
 * Chat / Ask / RAG type definitions.
 */

export interface DocSource {
  chunk_text: string;
  score?: number;
}

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  sources?: DocSource[];
  timestamp?: string;
}

export interface AskRequest {
  query: string;
  navigator_mode?: boolean;
  navigator_system_prompt?: string;
  session_history?: ChatMessage[];
  current_stage?: string;
  active_domain?: string;
}

export interface AskResponse {
  answer: string;
  intent?: string;
  sources?: DocSource[];
  tokens_used?: number;
  extracted?: Record<string, any>;
}

export interface StreamCallbacks {
  onMessage?: (chunk: any) => void;
  onError?: (error: Error) => void;
  onComplete?: () => void;
}

export interface RateRequest {
  query_id: number;
  rating: number;
}

export interface LastQueryResponse {
  has_query: boolean;
  query_id?: number;
}
