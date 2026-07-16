/**
 * Reports — match reports (user-owned) + ops daily/weekly/monthly.
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  createMatchReportsApi,
  createReportsApi,
  formatDate,
  type MatchReport,
  type MatchReportSummary,
  type Report,
  type ReportType,
} from "@looma/shared-core";
import { createSaasApiClient } from "../../api/saasApiClient";
import { useSaasAuthStore } from "../auth/authStore";

const typeMap: Record<string, { label: string; emoji: string }> = {
  daily: { label: "日报", emoji: "📊" },
  weekly: { label: "周报", emoji: "📈" },
  monthly: { label: "月报", emoji: "📋" },
};

export default function Reports() {
  const [searchParams, setSearchParams] = useSearchParams();
  const token = useSaasAuthStore((s) => s.token);
  const api = useMemo(() => createSaasApiClient(), []);
  const reportsApi = useMemo(() => createReportsApi(api), [api]);
  const matchReportsApi = useMemo(() => createMatchReportsApi(api), [api]);

  const [opsReports, setOpsReports] = useState<Report[]>([]);
  const [type, setType] = useState<ReportType>("daily");
  const [generating, setGenerating] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const [matchReports, setMatchReports] = useState<MatchReportSummary[]>([]);
  const [matchTotal, setMatchTotal] = useState(0);
  const [activeMatch, setActiveMatch] = useState<MatchReport | null>(null);
  const [loadingMatch, setLoadingMatch] = useState(false);

  const fetchOpsReports = useCallback(async () => {
    try {
      const res = await reportsApi.list();
      setOpsReports(res.reports);
    } catch {
      /* ignore */
    }
  }, [reportsApi]);

  const fetchMatchReports = useCallback(async () => {
    try {
      const res = await matchReportsApi.list({ page_size: 20 });
      setMatchReports(res.reports);
      setMatchTotal(res.total);
    } catch {
      /* ignore */
    }
  }, [matchReportsApi]);

  const openMatchReport = useCallback(
    async (id: string) => {
      setLoadingMatch(true);
      try {
        const detail = await matchReportsApi.get(id);
        setActiveMatch(detail);
        setSearchParams({ match: id }, { replace: true });
      } catch {
        setMsg("加载匹配报告失败");
      } finally {
        setLoadingMatch(false);
      }
    },
    [matchReportsApi, setSearchParams],
  );

  useEffect(() => {
    if (!token) return;
    void fetchOpsReports();
    void fetchMatchReports();
  }, [token, fetchOpsReports, fetchMatchReports]);

  const focusMatchId = searchParams.get("match");
  useEffect(() => {
    if (focusMatchId && token) void openMatchReport(focusMatchId);
    // intentionally only react to query id / token
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusMatchId, token]);

  const handleGenerate = async () => {
    setGenerating(true);
    setMsg(null);
    try {
      await reportsApi.generate({ type });
      setMsg("报告生成成功");
      void fetchOpsReports();
    } catch {
      setMsg("生成失败，请检查后端服务");
    } finally {
      setGenerating(false);
    }
  };

  const handleDeleteMatch = async (id: string) => {
    try {
      await matchReportsApi.remove(id);
      if (activeMatch?.id === id) {
        setActiveMatch(null);
        setSearchParams({}, { replace: true });
      }
      void fetchMatchReports();
    } catch {
      setMsg("删除匹配报告失败");
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6" style={{ color: "var(--color-text-primary)" }}>
        报告中心
      </h1>

      {/* ── Match reports ── */}
      <section className="mb-10">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium" style={{ color: "var(--color-text-primary)" }}>
            📊 我的匹配报告
          </h2>
          <span className="text-xs" style={{ color: "var(--color-text-muted)" }}>
            共 {matchTotal} 份
          </span>
        </div>

        {matchReports.length === 0 ? (
          <div
            className="rounded-lg p-8 text-center"
            style={{ backgroundColor: "var(--color-bg-card)", boxShadow: "var(--shadow-sm)" }}
          >
            <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
              暂无匹配报告。在「职位匹配」完成后点击「保存为报告」。
            </p>
          </div>
        ) : (
          <div className="space-y-3 mb-4">
            {matchReports.map((r) => (
              <div
                key={r.id}
                className="rounded-lg p-4 flex items-start justify-between gap-3"
                style={{ backgroundColor: "var(--color-bg-card)", boxShadow: "var(--shadow-sm)" }}
              >
                <button
                  type="button"
                  onClick={() => void openMatchReport(r.id)}
                  className="text-left flex-1 bg-transparent border-none cursor-pointer p-0"
                >
                  <p className="font-medium text-sm" style={{ color: "var(--color-text-primary)" }}>
                    {r.title}
                  </p>
                  <p className="text-xs mt-1" style={{ color: "var(--color-text-muted)" }}>
                    {r.metadata?.total_jobs ?? 0} 个职位
                    {r.metadata?.max_score != null ? ` · 最高 ${r.metadata.max_score}` : ""}
                    {r.metadata?.avg_score != null ? ` · 平均 ${r.metadata.avg_score}` : ""}
                    {" · "}
                    {r.created_at ? formatDate(r.created_at) : ""}
                  </p>
                  {r.summary && (
                    <p className="text-xs mt-1 line-clamp-2" style={{ color: "var(--color-text-secondary)" }}>
                      {r.summary}
                    </p>
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => void handleDeleteMatch(r.id)}
                  className="text-xs bg-transparent border-none cursor-pointer shrink-0"
                  style={{ color: "var(--color-text-muted)" }}
                >
                  删除
                </button>
              </div>
            ))}
          </div>
        )}

        {(loadingMatch || activeMatch) && (
          <div
            className="rounded-lg p-5 mt-2"
            style={{ backgroundColor: "var(--color-bg-card)", boxShadow: "var(--shadow-sm)" }}
          >
            {loadingMatch && !activeMatch ? (
              <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>加载详情…</p>
            ) : activeMatch ? (
              <>
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div>
                    <h3 className="font-medium" style={{ color: "var(--color-text-primary)" }}>
                      {activeMatch.title}
                    </h3>
                    <p className="text-xs mt-1" style={{ color: "var(--color-text-muted)" }}>
                      {activeMatch.summary}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setActiveMatch(null);
                      setSearchParams({}, { replace: true });
                    }}
                    className="text-xs bg-transparent border-none cursor-pointer"
                    style={{ color: "var(--color-text-muted)" }}
                  >
                    收起
                  </button>
                </div>
                <ul className="space-y-3">
                  {activeMatch.items.map((item) => (
                    <li
                      key={item.id}
                      className="p-3 rounded"
                      style={{ backgroundColor: "var(--color-bg-surface)" }}
                    >
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <p className="text-sm font-medium" style={{ color: "var(--color-text-primary)" }}>
                          {item.job_title}
                          <span className="font-normal" style={{ color: "var(--color-text-muted)" }}>
                            {" · "}{item.company_name}
                          </span>
                        </p>
                        <span className="text-sm font-bold" style={{ color: "var(--color-primary)" }}>
                          {Math.round(item.overall_score)}
                        </span>
                      </div>
                      {item.match_reason && (
                        <p className="text-xs mb-1" style={{ color: "var(--color-text-secondary)" }}>
                          {item.match_reason}
                        </p>
                      )}
                      {item.gap_analysis?.length > 0 && (
                        <p className="text-xs" style={{ color: "var(--color-warning)" }}>
                          差距：{item.gap_analysis.map((g) => g.skill).join("、")}
                        </p>
                      )}
                    </li>
                  ))}
                </ul>
              </>
            ) : null}
          </div>
        )}
      </section>

      {/* ── Ops reports ── */}
      <section>
        <h2 className="text-lg font-medium mb-4" style={{ color: "var(--color-text-primary)" }}>
          运营报告（日/周/月）
        </h2>

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
              onChange={(e) => setType(e.target.value as ReportType)}
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
                color: msg.includes("成功") || msg.includes("已保存")
                  ? "var(--color-success)"
                  : "var(--color-danger)",
              }}
            >
              {msg}
            </p>
          )}
        </div>

        <div className="space-y-4">
          {opsReports.length === 0 ? (
            <div className="text-center py-10" style={{ color: "var(--color-text-muted)" }}>
              <span className="text-4xl block mb-2 opacity-30">📋</span>
              <p>暂无运营报告，点击上方按钮生成</p>
            </div>
          ) : (
            opsReports.map((r) => (
              <div
                key={r.path}
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
                        {typeMap[r.type]?.label ?? r.type}报告
                      </h3>
                      <span className="text-xs" style={{ color: "var(--color-text-muted)" }}>
                        {r.generated_at ? formatDate(r.generated_at) : ""}
                      </span>
                    </div>
                    <p
                      className="text-sm line-clamp-1"
                      style={{ color: "var(--color-text-secondary)" }}
                    >
                      {r.path}
                    </p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}
