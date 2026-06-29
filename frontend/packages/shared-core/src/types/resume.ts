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

export interface JobMatchResult {
  job: Job;
  score: number;
  reason: string;
  matched_skills?: string[];
  missing_skills?: string[];
}

export interface JobMatchRequest {
  resume_text: string;
}

export interface JobMatchResponse {
  matches: JobMatchResult[];
  total_evaluated: number;
}
