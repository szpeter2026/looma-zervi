/**
 * Jobs - Position matching & JD upload page.
 * Owner: szbenyx
 *
 * Features:
 *   - Browse persisted + mock jobs
 *   - Upload JD file (PDF/DOCX) for AI parsing
 *   - Paste JD text for quick parse
 *   - Resume × Job multi-dimension matching (11 dimensions from Tatha)
 *
 * Pure CSS + Tailwind (no tdesign-react).
 * Uses shared-core typed API factories for backend contract alignment.
 */
import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { createApiClient, createJobsApi, createCreditApi, type Job, type JobMatchItem, type CreditAnalysis } from "@looma/shared-core";
import { useSaasAuthStore } from "../auth/authStore";
import { useConsent } from "../../compliance/useConsent";

// ── Types ──

interface ParsedJobData {
  title: string;
  company: string;
  location?: string;
  salary_range?: string;
  description?: string;
  requirements?: string[];
  tags?: string[];
}

type TabId = "browse" | "upload";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

// ── Helpers ──

function getScoreColor(score: number): string {
  if (score >= 80) return "var(--color-success)";
  if (score >= 60) return "var(--color-warning)";
  return "var(--color-danger)";
}

/** Short label for scoring dimensions */
const SCORE_LABELS: Record<string, string> = {
  skills_overlap: "技能",
  experience_relevance: "经历",
  seniority: "职级",
  salary_match: "薪资",
  location_match: "地点",
  culture_workload_match: "强度",
  company_score: "公司",
};

// ── Component ──

export default function Jobs() {
  const { token } = useSaasAuthStore();
  const [tab, setTab] = useState<TabId>("browse");
  const [jobs, setJobs] = useState<Job[]>([]);
  const [matches, setMatches] = useState<JobMatchItem[] | null>(null);
  const [resumeText, setResumeText] = useState("");
  const [matching, setMatching] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  // Credit check state (Tripod leg 3)
  const [creditResults, setCreditResults] = useState<Record<string, CreditAnalysis | null>>({});
  const [creditLoading, setCreditLoading] = useState<Record<string, boolean>>({});

  // Upload state
  const [uploading, setUploading] = useState(false);
  const [parsedJob, setParsedJob] = useState<ParsedJobData | null>(null);
  const [jdText, setJdText] = useState("");
  const [parsing, setParsing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropRef = useRef<HTMLDivElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const api = useMemo(() => createApiClient({
    baseURL: API_BASE,
    getToken: () => token,
  }), [token]);
  const jobsApi = createJobsApi(api);
  const creditApi = createCreditApi(api);
  const { ensureConsent, consentPrompt } = useConsent(() => api);

  // Load job list
  const loadJobs = useCallback(() => {
    jobsApi
      .list()
      .then((res) => setJobs(res.jobs))
      .catch(() => setMsg("加载职位列表失败"));
  }, [token]);

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  // ── Job Upload ──

  const handleFileUpload = async (file: File) => {
    setUploading(true);
    setMsg(null);
    try {
      const result = await jobsApi.upload(file) as any;
      if (result.parsed) {
        setParsedJob(result.parsed);
        setMsg("JD 解析完成");
        loadJobs(); // Refresh job list
        // Auto-fill JD text for preview
        setJdText(result.markdown || "");
      } else if (result.error) {
        setMsg(result.error);
      } else {
        setMsg("JD 解析完成，但未能提取结构化信息");
      }
    } catch {
      setMsg("文件上传失败，请检查文件格式");
    } finally {
      setUploading(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileUpload(file);
    // Reset so same file can be re-selected
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFileUpload(file);
  };

  const handleParseText = async () => {
    if (!jdText.trim()) return;
    setParsing(true);
    setMsg(null);
    try {
      const result = await jobsApi.parse(jdText) as any;
      if (result.parsed) {
        setParsedJob(result.parsed);
        setMsg("JD 文本解析完成");
        loadJobs();
      } else {
        setMsg("文本解析未返回结果");
      }
    } catch {
      setMsg("文本解析失败");
    } finally {
      setParsing(false);
    }
  };

  // ── Job Match ──

  const handleMatch = async (jobId?: string) => {
    if (!resumeText.trim()) return;
    setMatching(true);
    setMsg(null);
    try {
      const payload: any = { resume_text: resumeText };
      if (jobId) payload.job_id = jobId;
      const res = await jobsApi.match(payload) as any;
      setMatches(res.matches);
    } catch {
      setMsg("匹配失败，请重试");
    } finally {
      setMatching(false);
    }
  };

  // ── Company Credit Check (Tripod leg 3) ──

  const handleCheckCredit = async (companyName: string) => {
    if (!companyName) return;
    const allowed = await ensureConsent("credit_query");
    if (!allowed) {
      setMsg("需要授权后才能查询企业征信");
      return;
    }
    setCreditLoading((prev) => ({ ...prev, [companyName]: true }));
    try {
      const result = await creditApi.checkCompany({ company_name: companyName }) as any;
      setCreditResults((prev) => ({ ...prev, [companyName]: result.extracted }));
    } catch {
      setCreditResults((prev) => ({
        ...prev,
        [companyName]: {
          entity_name: companyName,
          report_type: "企业信用评估",
          summary: "暂无法获取该公司征信信息，请稍后重试。",
        },
      }));
    } finally {
      setCreditLoading((prev) => ({ ...prev, [companyName]: false }));
    }
  };

  // ── Render Helpers ──

  const renderScoreBar = (label: string, value: number, max: number) => (
    <div key={label} className="flex items-center gap-2 text-xs">
      <span
        className="w-10 shrink-0 text-right"
        style={{ color: "var(--color-text-muted)" }}
      >
        {label}
      </span>
      <div
        className="flex-1 h-1.5 rounded-full"
        style={{ backgroundColor: "var(--color-bg-surface)" }}
      >
        <div
          className="h-1.5 rounded-full transition-all"
          style={{
            width: `${(value / max) * 100}%`,
            backgroundColor: getScoreColor((value / max) * 100),
          }}
        />
      </div>
      <span
        className="w-6 text-left font-mono"
        style={{ color: "var(--color-text-secondary)" }}
      >
        {value}
      </span>
    </div>
  );

  // ── Render ──

  return (
    <>
    {consentPrompt}
    <div className="max-w-5xl mx-auto">
      <h1
        className="text-2xl font-bold mb-6"
        style={{ color: "var(--color-text-primary)" }}
      >
        职位匹配
      </h1>

      {/* ── Tab Bar ── */}
      <div className="flex gap-1 mb-6 border-b" style={{ borderColor: "#e0e0e0" }}>
        {(["browse", "upload"] as TabId[]).map((id) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className="px-4 py-2 text-sm font-medium border-b-2 bg-transparent cursor-pointer transition-colors"
            style={{
              color: tab === id ? "var(--color-primary)" : "var(--color-text-muted)",
              borderColor: tab === id ? "var(--color-primary)" : "transparent",
              marginBottom: -1,
            }}
          >
            {id === "browse" ? "在招职位" : "上传JD"}
          </button>
        ))}
      </div>

      {/* ── Browse Tab: Job List + Match ── */}
      {tab === "browse" && (
        <>
          {/* Resume input + match bar */}
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
                rows={5}
                className="border rounded-lg px-3 py-2 text-sm outline-none resize-y w-full"
                style={{
                  borderColor: "#e0e0e0",
                  color: "var(--color-text-primary)",
                  backgroundColor: "var(--color-bg-surface)",
                }}
              />
              <div className="flex items-center justify-between">
                <button
                  onClick={() => handleMatch()}
                  disabled={!resumeText.trim() || matching}
                  className="px-4 py-2 text-sm rounded-lg text-white border-none cursor-pointer disabled:opacity-50 transition-colors"
                  style={{ backgroundColor: "var(--color-primary)" }}
                >
                  {matching ? "AI 匹配中..." : "开始匹配"}
                </button>
                <button
                  onClick={() => {
                    setMatches(null);
                    setResumeText("");
                  }}
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

          {/* Match Results */}
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
                      <h3
                        className="font-bold text-lg"
                        style={{ color: "var(--color-text-primary)" }}
                      >
                        {m.title}
                      </h3>
                      <p
                        className="text-sm mb-2"
                        style={{ color: "var(--color-text-secondary)" }}
                      >
                        {m.company}
                        {m.location && ` · ${m.location}`}
                        {m.salary_range && ` · ${m.salary_range}`}
                      </p>

                      {/* Multi-dimension scores */}
                      <div className="space-y-1.5 mb-3">
                        {((
                          [
                            ["skills_overlap", 30],
                            ["experience_relevance", 30],
                            ["seniority", 10],
                            ["salary_match", 10],
                            ["location_match", 10],
                            ["culture_workload_match", 10],
                            ["company_score", 10],
                          ] as [string, number][]
                        ).map(([key, max]) => {
                          const val = (m.scores as any)?.[key] ?? 5;
                          return renderScoreBar(SCORE_LABELS[key] || key, val, max);
                        }))}
                      </div>

                      {/* Summary + keywords */}
                      {m.reason && (
                        <p
                          className="text-sm mb-2 px-3 py-2 rounded"
                          style={{
                            color: "var(--color-text-secondary)",
                            backgroundColor: "var(--color-bg-surface)",
                          }}
                        >
                          💡 {m.reason}
                        </p>
                      )}

                      {/* Fit bullets */}
                      {m.fit_bullets && m.fit_bullets.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mb-2">
                          {m.fit_bullets.slice(0, 5).map((b, j) => (
                            <span
                              key={j}
                              className="text-xs px-2 py-0.5 rounded-full"
                              style={{
                                backgroundColor: "var(--color-primary-bg, #e8f4fd)",
                                color: "var(--color-primary)",
                              }}
                            >
                              ✓ {b}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Overall score ring */}
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

                      {/* Credit check button */}
                      {m.company && (
                        <button
                          onClick={() => handleCheckCredit(m.company!)}
                          disabled={creditLoading[m.company]}
                          className="mt-2 px-2 py-1 text-xs rounded border-none cursor-pointer disabled:opacity-50 transition-colors"
                          style={{
                            backgroundColor: creditResults[m.company]
                              ? "var(--color-success)"
                              : "var(--color-bg-surface)",
                            color: creditResults[m.company]
                              ? "#fff"
                              : "var(--color-text-secondary)",
                          }}
                        >
                          {creditLoading[m.company]
                            ? "查证中..."
                            : creditResults[m.company]
                            ? "已查征信 ✓"
                            : "查征信"}
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Credit result card (below match card) */}
                  {m.company && creditResults[m.company] && (
                    <div
                      className="mt-3 p-3 rounded border-l-4"
                      style={{
                        backgroundColor: "var(--color-bg-surface)",
                        borderColor: "var(--color-success)",
                      }}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span
                          className="text-xs font-medium"
                          style={{ color: "var(--color-success)" }}
                        >
                          🛡 企业征信
                        </span>
                        <span
                          className="text-xs px-1.5 py-0.5 rounded"
                          style={{
                            backgroundColor: "var(--color-success)",
                            color: "#fff",
                          }}
                        >
                          {creditResults[m.company]?.report_type || "企业信用报告"}
                        </span>
                      </div>
                      <p
                        className="text-xs"
                        style={{ color: "var(--color-text-secondary)" }}
                      >
                        <strong>主体：</strong>
                        {creditResults[m.company]?.entity_name || m.company}
                      </p>
                      <p
                        className="text-xs mt-1"
                        style={{ color: "var(--color-text-secondary)" }}
                      >
                        {creditResults[m.company]?.summary || "暂无评估信息"}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            /* Job List */
            <div className="space-y-3">
              <h3
                className="text-sm font-medium mb-3"
                style={{ color: "var(--color-text-muted)" }}
              >
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
                      <h4
                        className="font-medium"
                        style={{ color: "var(--color-text-primary)" }}
                      >
                        {job.title}
                      </h4>
                      <p
                        className="text-sm"
                        style={{ color: "var(--color-text-secondary)" }}
                      >
                        {job.company}
                        {job.location && ` · ${job.location}`}
                        {job.salary_range && ` · ${job.salary_range}`}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
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
                      <button
                        onClick={() => handleMatch(job.id)}
                        disabled={!resumeText.trim() || matching}
                        className="ml-3 px-3 py-1 text-xs rounded border-none cursor-pointer disabled:opacity-40 transition-colors shrink-0"
                        style={{
                          backgroundColor: "var(--color-primary)",
                          color: "#fff",
                        }}
                      >
                        匹配此职位
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* ── Upload Tab: JD File + Text ── */}
      {tab === "upload" && (
        <div className="space-y-6">
          {/* File drop zone */}
          <div
            ref={dropRef}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className="rounded-lg border-2 border-dashed p-8 text-center cursor-pointer transition-colors"
            style={{
              borderColor: dragOver ? "var(--color-primary)" : "#d0d0d0",
              backgroundColor: dragOver ? "var(--color-primary-bg, #e8f4fd)" : "var(--color-bg-card)",
            }}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.doc,.txt,.md"
              onChange={handleFileSelect}
              className="hidden"
            />
            {uploading ? (
              <p className="text-sm" style={{ color: "var(--color-primary)" }}>
                AI 正在解析 JD 文件...
              </p>
            ) : (
              <>
                <p className="text-sm font-medium mb-1" style={{ color: "var(--color-text-primary)" }}>
                  点击上传或拖拽 JD 文件到此处
                </p>
                <p className="text-xs" style={{ color: "var(--color-text-muted)" }}>
                  支持 PDF、Word、TXT、Markdown 格式
                </p>
              </>
            )}
          </div>

          {/* Divider */}
          <div className="flex items-center gap-3">
            <div className="flex-1 border-t" style={{ borderColor: "#e0e0e0" }} />
            <span className="text-xs" style={{ color: "var(--color-text-muted)" }}>
              或直接粘贴 JD 文本
            </span>
            <div className="flex-1 border-t" style={{ borderColor: "#e0e0e0" }} />
          </div>

          {/* Text paste area */}
          <div
            className="rounded-lg p-4"
            style={{
              backgroundColor: "var(--color-bg-card)",
              boxShadow: "var(--shadow-sm)",
            }}
          >
            <textarea
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              placeholder="在此粘贴职位描述文本，AI 将自动提取职位名称、公司、要求等信息..."
              rows={8}
              className="border rounded-lg px-3 py-2 text-sm outline-none resize-y w-full mb-3"
              style={{
                borderColor: "#e0e0e0",
                color: "var(--color-text-primary)",
                backgroundColor: "var(--color-bg-surface)",
              }}
            />
            <button
              onClick={handleParseText}
              disabled={!jdText.trim() || parsing}
              className="px-4 py-2 text-sm rounded-lg text-white border-none cursor-pointer disabled:opacity-50 transition-colors"
              style={{ backgroundColor: "var(--color-primary)" }}
            >
              {parsing ? "AI 解析中..." : "解析 JD 文本"}
            </button>
          </div>

          {msg && (
            <p className="text-sm text-center" style={{ color: "var(--color-danger)" }}>
              {msg}
            </p>
          )}

          {/* Parsed result preview */}
          {parsedJob && (
            <div
              className="rounded-lg p-5"
              style={{
                backgroundColor: "var(--color-bg-card)",
                boxShadow: "var(--shadow-sm)",
                borderLeft: "4px solid var(--color-success)",
              }}
            >
              <h3
                className="font-bold text-base mb-3"
                style={{ color: "var(--color-text-primary)" }}
              >
                ✅ JD 解析结果
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex gap-2">
                  <span style={{ color: "var(--color-text-muted)", minWidth: 60 }}>职位：</span>
                  <span style={{ color: "var(--color-text-primary)", fontWeight: 500 }}>
                    {parsedJob.title}
                  </span>
                </div>
                {parsedJob.company && (
                  <div className="flex gap-2">
                    <span style={{ color: "var(--color-text-muted)", minWidth: 60 }}>公司：</span>
                    <span style={{ color: "var(--color-text-primary)" }}>{parsedJob.company}</span>
                  </div>
                )}
                {parsedJob.location && (
                  <div className="flex gap-2">
                    <span style={{ color: "var(--color-text-muted)", minWidth: 60 }}>地点：</span>
                    <span style={{ color: "var(--color-text-primary)" }}>{parsedJob.location}</span>
                  </div>
                )}
                {parsedJob.salary_range && (
                  <div className="flex gap-2">
                    <span style={{ color: "var(--color-text-muted)", minWidth: 60 }}>薪资：</span>
                    <span style={{ color: "var(--color-text-primary)" }}>{parsedJob.salary_range}</span>
                  </div>
                )}
                {parsedJob.requirements && parsedJob.requirements.length > 0 && (
                  <div className="flex gap-2">
                    <span style={{ color: "var(--color-text-muted)", minWidth: 60 }}>要求：</span>
                    <div className="flex flex-wrap gap-1">
                      {parsedJob.requirements.map((r, j) => (
                        <span
                          key={j}
                          className="text-xs px-2 py-0.5 rounded"
                          style={{
                            backgroundColor: "var(--color-bg-surface)",
                            color: "var(--color-text-secondary)",
                          }}
                        >
                          {r}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <p className="text-xs mt-3" style={{ color: "var(--color-text-muted)" }}>
                JD 已保存到职位库，可在"在招职位"标签页查看
              </p>
            </div>
          )}
        </div>
      )}
    </div>
    </>
  );
}
