/**
 * Jobs - Position matching page.
 * Owner: szbenyx
 *
 * Pure CSS + Tailwind (no tdesign-react).
 * Uses authStore for token, direct fetch for API calls.
 */
import { useState, useEffect } from "react";
import { createApiClient } from "@looma/shared-core";
import { useSaasAuthStore } from "../auth/authStore";

interface Job {
  id: string;
  title: string;
  company: string;
  location?: string;
  salary_range?: string;
  description?: string;
  requirements: string[];
}

interface JobMatchResult {
  job: Job;
  overall_score: number;
  skill_match: number;
  experience_match: number;
  education_match: number;
}

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:5000";

function getScoreColor(score: number): string {
  if (score >= 80) return "var(--color-success)";
  if (score >= 60) return "var(--color-warning)";
  return "var(--color-danger)";
}

export default function Jobs() {
  const { token } = useSaasAuthStore();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [matches, setMatches] = useState<JobMatchResult[] | null>(null);
  const [selectedResume, setSelectedResume] = useState<string>("");
  const [matching, setMatching] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const api = createApiClient({
    baseURL: API_BASE,
    getToken: () => token,
  });

  useEffect(() => {
    api
      .get<Job[]>("/v1/jobs/")
      .then(setJobs)
      .catch(() => setMsg("加载职位列表失败"));
  }, [token]);

  useEffect(() => {
    api
      .get<{ id: string }[]>("/v1/resume/mine")
      .then((list) => {
        if (list.length > 0) setSelectedResume(list[0].id);
      })
      .catch(() => {});
  }, [token]);

  const handleMatch = async () => {
    if (!selectedResume) return;
    setMatching(true);
    setMsg(null);
    try {
      const data = await api.post<JobMatchResult[]>("/v1/jobs/match", {
        resume_id: selectedResume,
      });
      setMatches(data);
    } catch {
      setMsg("匹配失败");
    } finally {
      setMatching(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-6" style={{ color: "var(--color-text-primary)" }}>
        职位匹配
      </h1>

      {/* 操作栏 */}
      <div
        className="rounded-lg p-4 mb-6 flex items-center justify-between"
        style={{
          backgroundColor: "var(--color-bg-card)",
          boxShadow: "var(--shadow-sm)",
        }}
      >
        <div className="flex items-center gap-3">
          <select
            value={selectedResume}
            onChange={(e) => setSelectedResume(e.target.value)}
            className="border rounded-lg px-3 py-2 text-sm outline-none"
            style={{ borderColor: "#e0e0e0", color: "var(--color-text-primary)" }}
          >
            <option value="">选择简历</option>
          </select>
          <button
            onClick={handleMatch}
            disabled={!selectedResume || matching}
            className="px-4 py-2 text-sm rounded-lg text-white border-none cursor-pointer disabled:opacity-50 transition-colors"
            style={{ backgroundColor: "var(--color-primary)" }}
          >
            {matching ? "匹配中..." : "开始匹配"}
          </button>
        </div>
        <button
          onClick={() => setMatches(null)}
          className="text-sm bg-transparent border-none cursor-pointer"
          style={{ color: "var(--color-text-muted)" }}
        >
          重置
        </button>
      </div>

      {msg && (
        <p className="text-sm mb-4 text-center" style={{ color: "var(--color-danger)" }}>
          {msg}
        </p>
      )}

      {/* 匹配结果 */}
      {matches ? (
        <div className="space-y-4">
          {matches.map((m, i) => (
            <div
              key={i}
              className="rounded-lg p-5 transition-shadow hover:shadow-md"
              style={{
                backgroundColor: "var(--color-bg-card)",
                boxShadow: "var(--shadow-sm)",
              }}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-bold text-lg" style={{ color: "var(--color-text-primary)" }}>
                    {m.job.title}
                  </h3>
                  <p className="text-sm mb-2" style={{ color: "var(--color-text-secondary)" }}>
                    {m.job.company}
                    {m.job.location && ` · ${m.job.location}`}
                  </p>
                  <p className="text-sm line-clamp-2 mb-4" style={{ color: "var(--color-text-secondary)" }}>
                    {m.job.description}
                  </p>

                  <div className="border-t pt-3" style={{ borderColor: "#e0e0e0" }}>
                    <div className="grid grid-cols-3 gap-3 text-center text-xs">
                      <div>
                        <p className="mb-1" style={{ color: "var(--color-text-muted)" }}>技能匹配</p>
                        <span className="font-bold" style={{ color: getScoreColor(m.skill_match) }}>
                          {m.skill_match}%
                        </span>
                      </div>
                      <div>
                        <p className="mb-1" style={{ color: "var(--color-text-muted)" }}>经验匹配</p>
                        <span className="font-bold" style={{ color: getScoreColor(m.experience_match) }}>
                          {m.experience_match}%
                        </span>
                      </div>
                      <div>
                        <p className="mb-1" style={{ color: "var(--color-text-muted)" }}>学历匹配</p>
                        <span className="font-bold" style={{ color: getScoreColor(m.education_match) }}>
                          {m.education_match}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 综合匹配得分圆环 */}
                <div className="ml-6 text-center shrink-0">
                  <svg width="80" height="80" viewBox="0 0 80 80">
                    <circle cx="40" cy="40" r="34" fill="none" stroke="#e0e0e0" strokeWidth="6" />
                    <circle
                      cx="40"
                      cy="40"
                      r="34"
                      fill="none"
                      stroke={getScoreColor(m.overall_score)}
                      strokeWidth="6"
                      strokeDasharray={`${(m.overall_score / 100) * 213.6} 213.6`}
                      strokeLinecap="round"
                      transform="rotate(-90 40 40)"
                    />
                    <text
                      x="40"
                      y="40"
                      textAnchor="middle"
                      dy="0.35em"
                      fontSize="16"
                      fontWeight="bold"
                      fill="var(--color-text-primary)"
                    >
                      {m.overall_score}
                    </text>
                  </svg>
                  <p className="text-xs mt-1" style={{ color: "var(--color-text-muted)" }}>
                    综合匹配
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* 职位列表 */
        <div className="space-y-3">
          <h3 className="text-sm font-medium mb-3" style={{ color: "var(--color-text-muted)" }}>
            当前职位 ({jobs.length})
          </h3>
          {jobs.map((job) => (
            <div
              key={job.id}
              className="rounded-lg p-4 transition-shadow hover:shadow-sm"
              style={{
                backgroundColor: "var(--color-bg-card)",
                boxShadow: "var(--shadow-sm)",
              }}
            >
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="font-medium" style={{ color: "var(--color-text-primary)" }}>
                    {job.title}
                  </h4>
                  <p className="text-sm" style={{ color: "var(--color-text-secondary)" }}>
                    {job.company}
                    {job.location && ` · ${job.location}`}
                    {job.salary_range && ` · ${job.salary_range}`}
                  </p>
                </div>
                <div className="flex flex-wrap gap-1 max-w-sm">
                  {job.requirements.slice(0, 5).map((req, j) => (
                    <span
                      key={j}
                      className="text-xs px-2 py-0.5 rounded"
                      style={{
                        backgroundColor: "var(--color-bg-surface)",
                        color: "var(--color-text-secondary)",
                      }}
                    >
                      {req}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
