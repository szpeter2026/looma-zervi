/**
 * Jobs - Position matching page.
 * Owner: szbenyx
 *
 * Pure CSS + Tailwind (no tdesign-react).
 * Uses shared-core typed API factories for backend contract alignment.
 */
import { useState, useEffect } from "react";
import { createApiClient, createJobsApi, type Job } from "@looma/shared-core";
import { useSaasAuthStore } from "../auth/authStore";

/** Backend actual match response item shape */
interface MatchItem {
  job_id: string;
  title: string;
  company: string;
  location: string;
  salary_range: string;
  scores: {
    overall: number;
    money?: number;
    workload?: number;
    proximity?: number;
  };
  reason: string;
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
  const [matches, setMatches] = useState<MatchItem[] | null>(null);
  const [resumeText, setResumeText] = useState("");
  const [matching, setMatching] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const api = createApiClient({
    baseURL: API_BASE,
    getToken: () => token,
  });
  const jobsApi = createJobsApi(api);

  useEffect(() => {
    jobsApi
      .list()
      .then((res) => setJobs(res.jobs))
      .catch(() => setMsg("加载职位列表失败"));
  }, [token]);

  const handleMatch = async () => {
    if (!resumeText.trim()) return;
    setMatching(true);
    setMsg(null);
    try {
      const res = await jobsApi.match({ resume_text: resumeText });
      setMatches(res.matches);
    } catch {
      setMsg("匹配失败，请重试");
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
        className="rounded-lg p-4 mb-6"
        style={{
          backgroundColor: "var(--color-bg-card)",
          boxShadow: "var(--shadow-sm)",
        }}
      >
        <div className="flex flex-col gap-3">
          <textarea
            value={resumeText}
            onChange={(e) => setResumeText(e.target.value)}
            placeholder="在此粘贴简历文本，AI 将为你匹配最合适的职位..."
            rows={6}
            className="border rounded-lg px-3 py-2 text-sm outline-none resize-y w-full"
            style={{ borderColor: "#e0e0e0", color: "var(--color-text-primary)", backgroundColor: "var(--color-bg-surface)" }}
          />
          <div className="flex items-center justify-between">
            <button
              onClick={handleMatch}
              disabled={!resumeText.trim() || matching}
              className="px-4 py-2 text-sm rounded-lg text-white border-none cursor-pointer disabled:opacity-50 transition-colors"
              style={{ backgroundColor: "var(--color-primary)" }}
            >
              {matching ? "AI 匹配中..." : "开始匹配"}
            </button>
            <button
              onClick={() => { setMatches(null); setResumeText(""); }}
              className="text-sm bg-transparent border-none cursor-pointer"
              style={{ color: "var(--color-text-muted)" }}
            >
              重置
            </button>
          </div>
        </div>
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
                    {m.title}
                  </h3>
                  <p className="text-sm mb-2" style={{ color: "var(--color-text-secondary)" }}>
                    {m.company}
                    {m.location && ` · ${m.location}`}
                    {m.salary_range && ` · ${m.salary_range}`}
                  </p>
                  {m.reason && (
                    <p className="text-sm mb-4 px-3 py-2 rounded" style={{ color: "var(--color-text-secondary)", backgroundColor: "var(--color-bg-surface)" }}>
                      💡 {m.reason}
                    </p>
                  )}

                  <div className="border-t pt-3" style={{ borderColor: "#e0e0e0" }}>
                    <div className="grid grid-cols-3 gap-3 text-center text-xs">
                      <div>
                        <p className="mb-1" style={{ color: "var(--color-text-muted)" }}>综合评分</p>
                        <span className="font-bold" style={{ color: getScoreColor(m.scores.overall) }}>
                          {Math.round(m.scores.overall)}%
                        </span>
                      </div>
                      <div>
                        <p className="mb-1" style={{ color: "var(--color-text-muted)" }}>薪酬匹配</p>
                        <span className="font-bold" style={{ color: getScoreColor((m.scores.money ?? 0) * 3.3) }}>
                          {Math.round((m.scores.money ?? 0) * 3.3)}%
                        </span>
                      </div>
                      <div>
                        <p className="mb-1" style={{ color: "var(--color-text-muted)" }}>匹配亲和度</p>
                        <span className="font-bold" style={{ color: getScoreColor((m.scores.proximity ?? 0) * 2) }}>
                          {Math.round((m.scores.proximity ?? 0) * 2)}%
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
                      stroke={getScoreColor(m.scores.overall)}
                      strokeWidth="6"
                      strokeDasharray={`${(m.scores.overall / 100) * 213.6} 213.6`}
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
                      {Math.round(m.scores.overall)}
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
                  {(job.requirements ?? []).slice(0, 5).map((req, j) => (
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
