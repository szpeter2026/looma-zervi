/**
 * Persisted resume × JD match reports (user-owned).
 */
import type { GapItem } from "./resume";

export interface MatchReportMetadata {
  total_jobs: number;
  matched_at: string;
  pipeline_version: string;
  max_score?: number;
  avg_score?: number;
}

export interface MatchReportItem {
  id: string;
  report_id: string;
  job_title: string;
  company_name: string;
  location: string;
  salary_range: string;
  overall_score: number;
  background_match: number;
  skills_overlap: number;
  experience_relevance: number;
  seniority: number;
  language_requirement: number;
  company_score: number;
  salary_match: number;
  location_match: number;
  culture_workload_match: number;
  match_reason: string;
  matched_skills: string[];
  missing_skills: string[];
  fit_bullets: string[];
  gap_analysis: GapItem[];
  improvement_plan: string;
  credit_snapshot: Record<string, unknown>;
  rank_order: number;
  created_at: string;
}

export interface MatchReportSummary {
  id: string;
  user_id: string;
  title: string;
  status: "draft" | "completed" | "archived" | "deleted" | string;
  summary: string;
  metadata: MatchReportMetadata;
  created_at: string;
  updated_at: string;
}

export interface MatchReport extends MatchReportSummary {
  resume_id?: string;
  resume_snapshot?: string;
  items: MatchReportItem[];
}

export interface CreateMatchReportRequest {
  resume_text: string;
  matches: unknown[];
  title?: string;
  summary?: string;
  resume_id?: string;
}

export interface MatchReportListResponse {
  reports: MatchReportSummary[];
  total: number;
  page: number;
  page_size: number;
}
