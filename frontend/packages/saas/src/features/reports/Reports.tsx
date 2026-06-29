/**
 * Reports - Report generation and listing page.
 * Owner: szbenyx
 *
 * Pure CSS + Tailwind (no tdesign-react).
 * Uses authStore for token, direct fetch for API calls.
 */
import { useState, useEffect } from "react";
import { createApiClient, formatDate } from "@looma/shared-core";
import { useSaasAuthStore } from "../auth/authStore";

interface Report {
  id: string;
  title: string;
  type: "daily" | "weekly" | "monthly";
  content: string;
  generated_at: string;
  date_range: { start: string; end: string };
}

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:5000";

const typeMap: Record<string, { label: string; emoji: string }> = {
  daily: { label: "日报", emoji: "📊" },
  weekly: { label: "周报", emoji: "📈" },
  monthly: { label: "月报", emoji: "📋" },
};

export default function Reports() {
  const { token } = useSaasAuthStore();
  const [reports, setReports] = useState<Report[]>([]);
  const [type, setType] = useState<"daily" | "weekly" | "monthly">("daily");
  const [generating, setGenerating] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const api = createApiClient({
    baseURL: API_BASE,
    getToken: () => token,
  });

  const fetchReports = async () => {
    try {
      const data = await api.get<Report[]>("/v1/reports/daily");
      setReports(data);
    } catch {
      /* ignore */
    }
  };

  useEffect(() => {
    fetchReports();
  }, [token]);

  const handleGenerate = async () => {
    setGenerating(true);
    setMsg(null);
    try {
      await api.post("/v1/reports/generate", { type });
      setMsg("报告生成成功");
      fetchReports();
    } catch {
      setMsg("生成失败");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6" style={{ color: "var(--color-text-primary)" }}>
        报告中心
      </h1>

      {/* 生成区域 */}
      <div
        className="rounded-lg p-6 mb-6"
        style={{
          backgroundColor: "var(--color-bg-card)",
          boxShadow: "var(--shadow-sm)",
        }}
      >
        <h3 className="font-medium mb-4 flex items-center gap-2" style={{ color: "var(--color-text-primary)" }}>
          <span>📊</span> 生成报告
        </h3>
        <div className="flex items-center gap-3">
          <select
            value={type}
            onChange={(e) => setType(e.target.value as typeof type)}
            className="border rounded-lg px-3 py-2 text-sm outline-none"
            style={{
              borderColor: "#e0e0e0",
              color: "var(--color-text-primary)",
              width: "160px",
            }}
          >
            <option value="daily">日报</option>
            <option value="weekly">周报</option>
            <option value="monthly">月报</option>
          </select>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="px-4 py-2 text-sm rounded-lg text-white border-none cursor-pointer disabled:opacity-50 transition-colors"
            style={{ backgroundColor: "var(--color-primary)" }}
          >
            {generating ? "生成中..." : `生成${typeMap[type].label}`}
          </button>
        </div>
        {msg && (
          <p
            className="text-sm mt-3"
            style={{
              color: msg.includes("成功") ? "var(--color-success)" : "var(--color-danger)",
            }}
          >
            {msg}
          </p>
        )}
      </div>

      {/* 报告列表 */}
      <div className="space-y-4">
        {reports.length === 0 ? (
          <div className="text-center py-16" style={{ color: "var(--color-text-muted)" }}>
            <span className="text-4xl block mb-2 opacity-30">📋</span>
            <p>暂无报告，点击上方按钮生成</p>
          </div>
        ) : (
          reports.map((r) => (
            <div
              key={r.id}
              className="rounded-lg p-5 transition-shadow hover:shadow-sm"
              style={{
                backgroundColor: "var(--color-bg-card)",
                boxShadow: "var(--shadow-sm)",
              }}
            >
              <div className="flex items-start gap-3">
                <span className="text-2xl">{typeMap[r.type]?.emoji ?? "📄"}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium" style={{ color: "var(--color-text-primary)" }}>
                      {r.title}
                    </h3>
                    <span className="text-xs" style={{ color: "var(--color-text-muted)" }}>
                      {formatDate(r.generated_at)}
                    </span>
                  </div>
                  <p
                    className="text-sm line-clamp-3"
                    style={{ color: "var(--color-text-secondary)" }}
                  >
                    {r.content}
                  </p>
                  <p className="text-xs mt-2" style={{ color: "var(--color-text-muted)" }}>
                    {r.date_range.start} ~ {r.date_range.end}
                  </p>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
