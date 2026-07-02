/**
 * Dashboard - SaaS main dashboard with health status, quota, and quick actions.
 * Owner: szbenyx
 *
 * Pure CSS + Tailwind (no tdesign-react).
 * Uses authStore for user/quota, ApiClient for health check.
 */
import { useEffect, useState } from "react";
import { useSaasAuthStore } from "../auth/authStore";
import { BRAND_SAAS } from "@looma/shared-core";

interface HealthStatus {
  status: "healthy" | "degraded";
  version: string;
  uptime_seconds: number;
  llm_provider?: string;
  embedding_model?: string;
  vector_store_size?: number;
}

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export default function Dashboard() {
  const { user, quota, isAuthenticated, fetchQuota } = useSaasAuthStore();
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    if (isAuthenticated) void fetchQuota();
  }, [isAuthenticated, fetchQuota]);

  useEffect(() => {
    if (!API_BASE) return;
    fetch(`${API_BASE.replace(/\/$/, "")}/health`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => data && setHealth(data))
      .catch(() => {});
  }, []);

  const askRecord = quota?.records?.find((r) => r.resource === "ask");
  const usagePercent = askRecord && askRecord.daily_limit > 0
    ? Math.round((askRecord.used / askRecord.daily_limit) * 100)
    : 0;

  const handleQuickQuery = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      const q = (e.target as HTMLInputElement).value.trim();
      if (q) window.location.href = `/query?q=${encodeURIComponent(q)}`;
    }
  };

  // ===== 未登录：自由浏览模式 =====
  if (!isAuthenticated) {
    return (
      <div className="max-w-3xl mx-auto text-center" style={{ paddingTop: "4rem" }}>
        <h1 className="text-3xl font-bold mb-2" style={{ color: "var(--color-text-primary)" }}>
          {BRAND_SAAS.name}
        </h1>
        <p className="text-lg mb-8" style={{ color: "var(--color-text-secondary)" }}>
          {BRAND_SAAS.slogan}
        </p>

        {/* CTA */}
        <div className="flex justify-center gap-4 mb-10">
          <a
            href="/register"
            className="px-6 py-3 rounded-lg text-white text-sm font-medium no-underline transition-opacity hover:opacity-90"
            style={{ backgroundColor: "var(--color-primary)" }}
          >
            免费注册
          </a>
          <a
            href="/login"
            className="px-6 py-3 rounded-lg text-sm font-medium no-underline border transition-colors"
            style={{
              borderColor: "var(--color-primary)",
              color: "var(--color-primary)",
            }}
          >
            已有账号？登录
          </a>
        </div>

        {/* 能力卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
          {[
            { icon: "🧠", title: "AI 知识问答", desc: "接入 DeepSeek，秒级响应" },
            { icon: "📄", title: "简历智能解析", desc: "上传即结构化，匹配岗位" },
            { icon: "📊", title: "数据报告", desc: "日/周/月智能报告生成" },
          ].map((item) => (
            <div
              key={item.title}
              className="rounded-lg p-5 text-left"
              style={{
                backgroundColor: "var(--color-bg-card)",
                boxShadow: "var(--shadow-sm)",
              }}
            >
              <div className="text-2xl mb-2">{item.icon}</div>
              <h3 className="text-sm font-medium mb-1" style={{ color: "var(--color-text-primary)" }}>
                {item.title}
              </h3>
              <p className="text-xs" style={{ color: "var(--color-text-muted)" }}>
                {item.desc}
              </p>
            </div>
          ))}
        </div>

        {/* 系统状态（无需登录也能看到） */}
        {health && (
          <div className="flex items-center justify-center gap-2 text-xs" style={{ color: "var(--color-text-muted)" }}>
            <span
              className="inline-block w-2 h-2 rounded-full"
              style={{
                backgroundColor:
                  health.status === "healthy" ? "var(--color-success)" : "var(--color-warning)",
              }}
            />
            <span>系统 {health.status === "healthy" ? "运行正常" : "服务降级"}</span>
            <span>·</span>
            <span>v{health.version}</span>
          </div>
        )}

        {/* 底部提示 */}
        <p className="text-xs mt-6" style={{ color: "var(--color-text-muted)" }}>
          从 PlanetX 过来的？你的账号已自动同步 ✨
        </p>
      </div>
    );
  }

  // ===== 已登录：完整看板 =====

  return (
    <div className="max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-1" style={{ color: "var(--color-text-primary)" }}>
        {BRAND_SAAS.name}
      </h1>
      <p className="text-sm mb-6" style={{ color: "var(--color-text-secondary)" }}>
        欢迎回来，{user?.name || user?.email}
      </p>

      {/* 状态卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {/* 系统状态 */}
        <div
          className="rounded-lg p-5"
          style={{
            backgroundColor: "var(--color-bg-card)",
            boxShadow: "var(--shadow-sm)",
          }}
        >
          <h3 className="text-sm font-medium mb-3" style={{ color: "var(--color-text-secondary)" }}>
            系统状态
          </h3>
          <div className="flex items-center gap-2 mb-3">
            <span
              className="inline-block w-2.5 h-2.5 rounded-full"
              style={{
                backgroundColor:
                  health?.status === "healthy" ? "var(--color-success)" : "var(--color-warning)",
              }}
            />
            <span
              className="font-medium text-sm"
              style={{
                color:
                  health?.status === "healthy" ? "var(--color-success)" : "var(--color-warning)",
              }}
            >
              {health?.status === "healthy" ? "运行正常" : "服务降级"}
            </span>
          </div>
          <div className="text-xs space-y-1" style={{ color: "var(--color-text-muted)" }}>
            {health?.llm_provider && <p>LLM: {health.llm_provider}</p>}
            {health?.embedding_model && <p>嵌入: {health.embedding_model}</p>}
            {health?.vector_store_size != null && (
              <p>向量库: {health.vector_store_size.toLocaleString()} 条</p>
            )}
          </div>
        </div>

        {/* 今日配额 */}
        <div
          className="rounded-lg p-5"
          style={{
            backgroundColor: "var(--color-bg-card)",
            boxShadow: "var(--shadow-sm)",
          }}
        >
          <h3 className="text-sm font-medium mb-3" style={{ color: "var(--color-text-secondary)" }}>
            今日配额
          </h3>
          {quota && askRecord ? (
            <>
              <div className="flex items-baseline gap-1 mb-3">
                <span
                  className="text-3xl font-bold"
                  style={{ color: "var(--color-primary)" }}
                >
                  {askRecord.daily_limit - askRecord.used}
                </span>
                <span style={{ color: "var(--color-text-muted)" }}>
                  / {askRecord.daily_limit} 次
                </span>
              </div>
              <div
                className="h-2 rounded-full overflow-hidden"
                style={{ backgroundColor: "var(--color-bg-surface)" }}
              >
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${Math.min(usagePercent, 100)}%`,
                    backgroundColor:
                      usagePercent > 80 ? "var(--color-warning)" : "var(--color-primary)",
                  }}
                />
              </div>
              <div className="flex items-center justify-between mt-2">
                <p className="text-xs" style={{ color: "var(--color-text-muted)" }}>
                  {quota.tier === "free" ? "免费版" : quota.tier === "supporter" ? "支持版" : "专业版"}
                </p>
                <a
                  href="/pricing"
                  className="text-xs no-underline hover:underline"
                  style={{ color: "var(--color-primary)" }}
                >
                  升级 →
                </a>
              </div>
            </>
          ) : (
            <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
              加载中...
            </p>
          )}
        </div>

        {/* 快捷操作 */}
        <div
          className="rounded-lg p-5"
          style={{
            backgroundColor: "var(--color-bg-card)",
            boxShadow: "var(--shadow-sm)",
          }}
        >
          <h3 className="text-sm font-medium mb-3" style={{ color: "var(--color-text-secondary)" }}>
            快捷操作
          </h3>
          <div className="space-y-2">
            <a
              href="/query"
              className="block w-full text-center px-4 py-2 text-sm rounded-md border transition-colors no-underline"
              style={{
                borderColor: "var(--color-primary)",
                color: "var(--color-primary)",
              }}
            >
              开始提问
            </a>
            <a
              href="/resume"
              className="block w-full text-center px-4 py-2 text-sm rounded-md border transition-colors no-underline"
              style={{
                borderColor: "var(--color-primary)",
                color: "var(--color-primary)",
              }}
            >
              解析简历
            </a>
            <a
              href="/jobs"
              className="block w-full text-center px-4 py-2 text-sm rounded-md border transition-colors no-underline"
              style={{
                borderColor: "var(--color-primary)",
                color: "var(--color-primary)",
              }}
            >
              职位匹配
            </a>
          </div>
        </div>
      </div>

      {/* 快速问答 */}
      <div
        className="rounded-lg p-5 mb-6"
        style={{
          backgroundColor: "var(--color-bg-card)",
          boxShadow: "var(--shadow-sm)",
        }}
      >
        <h3 className="text-sm font-medium mb-3" style={{ color: "var(--color-text-secondary)" }}>
          快速问答
        </h3>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="输入问题，按 Enter 跳转到问答页..."
            className="flex-1 px-4 py-2.5 text-sm rounded-lg border outline-none transition-colors"
            style={{
              borderColor: "#e0e0e0",
              color: "var(--color-text-primary)",
            }}
            onKeyDown={handleQuickQuery}
            onFocus={(e) => {
              e.target.style.borderColor = "var(--color-primary)";
            }}
            onBlur={(e) => {
              e.target.style.borderColor = "#e0e0e0";
            }}
          />
          <button
            className="px-5 py-2.5 text-sm rounded-lg text-white cursor-pointer border-none transition-colors"
            style={{ backgroundColor: "var(--color-primary)" }}
          >
            提问
          </button>
        </div>
      </div>

      {/* 版本信息 */}
      {health && (
        <p className="text-xs text-center" style={{ color: "var(--color-text-muted)" }}>
          v{health.version} · 已运行 {Math.floor(health.uptime_seconds / 3600)}h
          {Math.floor((health.uptime_seconds % 3600) / 60)}m
        </p>
      )}
    </div>
  );
}
