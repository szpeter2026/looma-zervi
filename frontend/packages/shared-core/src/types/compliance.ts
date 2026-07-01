/** Consent scopes — keep in sync with backend ALL_SCOPES */
export type ConsentScope =
  | "resume_upload"
  | "resume_parse"
  | "credit_query"
  | "credit_analyze"
  | "profile_share"
  | "ask_rag"
  | "job_match"
  | "mbti_analyze"
  | "navigator_memory";

export interface ConsentRecord {
  id: string;
  scope: ConsentScope;
  purpose?: string;
  status: "granted" | "revoked" | "expired";
  granted_at?: string;
  revoked_at?: string | null;
}

export interface ConsentStatusResponse {
  user_id: string;
  consents: ConsentRecord[];
  status: Record<ConsentScope, boolean>;
}

export interface ConsentGrantResponse {
  consent_id?: string;
  already_granted?: boolean;
  granted?: number;
  results?: Array<{ scope: string; consent_id?: string; error?: string }>;
}

export interface ConsentRequiredResponse {
  available_scopes: ConsentScope[];
  details: Record<ConsentScope, string>;
}

export interface ConsentRequiredError {
  error: "consent_required";
  message: string;
  required_scope: ConsentScope;
  action?: "grant_consent";
}
