/**
 * Resume / Job / Hiring type definitions.
 */

export interface ResumeExperience {
  company: string;
  title: string;
  start_date?: string;
  end_date?: string;
  description?: string;
}

export interface ResumeEducation {
  school: string;
  degree: string;
  field?: string;
  start_date?: string;
  end_date?: string;
}

export interface ResumeProject {
  name: string;
  description?: string;
  url?: string;
}

export interface ParsedResume {
  name?: string;
  email?: string;
  phone?: string;
  summary?: string;
  skills?: string[];
  experiences?: ResumeExperience[];
  education?: ResumeEducation[];
  projects?: ResumeProject[];
  languages?: string[];
  certifications?: string[];
  raw?: Record<string, any>;
}

export interface Job {
  id: string;
  title: string;
  company: string;
  location?: string;
  salary_range?: string;
  description?: string;
  requirements?: string[];
  tags?: string[];
  posted_at?: string;
  url?: string;
}

/**
 * Actual API match item returned by POST /v1/jobs/match.
 * The pipeline returns flat fields + a nested scores object (11 dimensions).
 */
export interface JobMatchItem {
  job_id: string;
  title: string;
  company: string;
  location: string;
  salary_range: string;
  /** Multi-dimension scores (来自 Tatha 评分引擎 11 维度) */
  scores: JobMatchScore;
  /** 一句话匹配摘要 */
  reason: string;
  matched_skills?: string[];
  missing_skills?: string[];
  fit_bullets?: string[];
}

export interface JobMatchRequest {
  resume_text: string;
}

export interface JobMatchResponse {
  matches: JobMatchItem[];
  total_evaluated: number;
}

// Legacy alias – kept for backward compatibility with any code that imported JobMatchResult
/** @deprecated use JobMatchItem instead */
export type JobMatchResult = JobMatchItem;

// ============================================================
// Enhanced job types (migrated from Tatha scoring engine)
// ============================================================

/** Multi-dimension match score (11 dimensions from Tatha) */
export interface JobMatchScore {
  overall: number;
  background_match: number;
  skills_overlap: number;
  experience_relevance: number;
  seniority: number;
  language_requirement: number;
  company_score: number;
  salary_match: number;
  location_match: number;
  culture_workload_match: number;
  summary: string;
  keywords: string[];
  fit_bullets: string[];
}

/** Parsed job info from LLM extraction */
export interface ParsedJob {
  id?: string;
  title: string;
  company: string;
  location?: string;
  salary_range?: string;
  description?: string;
  requirements?: string[];
  responsibilities?: string[];
  tags?: string[];
  seniority_level?: string;
  employment_type?: string;
  remote_policy?: string;
  source?: string;
  posted_at?: string;
  url?: string;
}

/** Return type for POST /v1/jobs/upload (file → parsed + metadata) */
export interface JobUploadResult {
  parsed: ParsedJob | null;
  markdown: string;
  filename: string;
  job_id: string | null;
  error?: string;
}

// ============================================================
// Company Credit types (Tripod leg 3: Resume → Job → Company)
// ============================================================

/** Parsed credit analysis from LLM (migrated from Tatha CreditAnalysis) */
export interface CreditAnalysis {
  entity_name?: string;
  report_type?: string;
  summary?: string;
}

/** Request body for POST /v1/credit/check-company */
export interface CheckCompanyRequest {
  company_name: string;
  location?: string;
  industry?: string;
}

/** Return type for POST /v1/resume/upload (file → parsed + metadata) */
export interface ResumeUploadResult {
  extracted: ParsedResume | null;
  markdown: string;
  filename: string;
  resume_id: string | null;
  error?: string;
}
