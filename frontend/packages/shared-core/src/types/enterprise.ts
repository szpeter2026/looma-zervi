/**
 * Enterprise / T空间 B-end type definitions.
 */

export interface CreateEnterpriseRequest {
  name: string;
  domain?: string;
}

export interface JoinEnterpriseRequest {
  enterprise_id: string;
}

export interface EnterpriseProfile {
  id: string;
  name: string;
  domain?: string;
  role: "admin" | "member";
  created_at?: string;
}

export interface Candidate {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  status?: string;
  profile_data?: Record<string, any>;
  created_at?: string;
}

export interface AddCandidateRequest {
  name: string;
  email?: string;
  phone?: string;
  profile_data?: Record<string, any>;
}

export interface AddCandidateResponse {
  name: string;
  email?: string;
  status: string;
}
