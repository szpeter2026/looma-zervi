/**
 * Bridge Resume parsing → Jobs matching without merging the two product stages.
 * Stores a plain-text snapshot the user can review before matching.
 */
import type { ParsedResume } from "@looma/shared-core";

export const RESUME_MATCH_TEXT_KEY = "saas-resume-match-text";

export function buildResumeMatchText(resume: ParsedResume): string {
  const parts: string[] = [];

  if (resume.name) parts.push(`姓名：${resume.name}`);
  if (resume.email) parts.push(`邮箱：${resume.email}`);
  if (resume.phone) parts.push(`电话：${resume.phone}`);
  if (resume.summary) parts.push(`\n摘要：\n${resume.summary}`);

  if (resume.skills?.length) {
    parts.push(`\n技能：\n${resume.skills.join("、")}`);
  }

  if (resume.experiences?.length) {
    parts.push("\n工作经历：");
    for (const exp of resume.experiences) {
      const period = [exp.start_date || "", exp.end_date || "至今"].filter(Boolean).join(" ~ ");
      parts.push(`- ${exp.title || ""} @ ${exp.company || ""} (${period})`);
      if (exp.description) parts.push(`  ${exp.description}`);
    }
  }

  if (resume.education?.length) {
    parts.push("\n教育背景：");
    for (const edu of resume.education) {
      parts.push(
        `- ${edu.school || ""} ${edu.degree || ""} ${edu.field || ""}`.trim(),
      );
    }
  }

  if (resume.projects?.length) {
    parts.push("\n项目：");
    for (const p of resume.projects) {
      parts.push(`- ${p.name || ""}${p.description ? `：${p.description}` : ""}`);
    }
  }

  if (resume.languages?.length) {
    parts.push(`\n语言：${resume.languages.join("、")}`);
  }

  if (resume.certifications?.length) {
    parts.push(`\n证书：${resume.certifications.join("、")}`);
  }

  return parts.join("\n").trim();
}

export function saveResumeMatchText(text: string): void {
  try {
    localStorage.setItem(RESUME_MATCH_TEXT_KEY, text);
  } catch {
    /* ignore quota / private mode */
  }
}

export function loadResumeMatchText(): string | null {
  try {
    return localStorage.getItem(RESUME_MATCH_TEXT_KEY);
  } catch {
    return null;
  }
}

export function clearResumeMatchText(): void {
  try {
    localStorage.removeItem(RESUME_MATCH_TEXT_KEY);
  } catch {
    /* ignore */
  }
}
