/**
 * Narrative types — Phase 0 feedback collection.
 * Ownership: Jason
 *
 * Tracks narrative sessions, events, and convergence-point
 * qualitative feedback for the Phase 0 Navigator text adventure.
 */

/** Valid narrative domains (六域 + 迷雾域) */
export type NarrativeDomain =
  | "职业域"
  | "诗域"
  | "自我域"
  | "身份域"
  | "信任域"
  | "迷雾域"
  | "career"
  | "poetry"
  | "self"
  | "identity"
  | "trust"
  | "unknown";

/** Event types logged during a narrative session */
export type NarrativeEventType =
  | "domain_enter"
  | "choice_made"
  | "convergence_reached"
  | "share_attempt"
  | "replay";

/** POST /v1/narrative/start request */
export interface NarrativeStartRequest {
  domain: NarrativeDomain;
}

/** POST /v1/narrative/start response */
export interface NarrativeStartResponse {
  session_id: string;
  domain: string;
}

/** POST /v1/narrative/event request */
export interface NarrativeEventRequest {
  session_id: string;
  event_type: NarrativeEventType;
  domain?: string;
  choice?: string;
  navigator_line?: string;
  metadata?: Record<string, unknown>;
}

/** POST /v1/narrative/end request */
export interface NarrativeEndRequest {
  session_id: string;
  completed: boolean;
  duration_seconds: number;
}

/** POST /v1/narrative/feedback request */
export interface NarrativeFeedbackRequest {
  session_id: string;
  /** Did Navigator touch you? (required) */
  resonated: boolean;
  /** A Navigator line the user can recall (optional) */
  navigator_quote?: string;
  /** 0=no, 1=maybe, 2=yes */
  would_replay?: number;
  /** Did the user share? */
  shared?: boolean;
  /** Where did they share? */
  share_channel?: "wechat" | "moments" | "link" | "other";
  /** Free-text qualitative feedback */
  open_feedback?: string;
}

/** GET /v1/narrative/stats response */
export interface NarrativeStats {
  total_sessions: number;
  completed_sessions: number;
  completion_rate: number;
  feedback_count: number;
  resonance_rate: number;
  share_rate: number;
  replay_intent_rate: number;
  top_quotes: Array<{ quote: string; count: number }>;
  domains: Array<{ domain: string; count: number }>;
  open_feedback: Array<{ domain: string; text: string; at: string }>;
}
