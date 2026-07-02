/**
 * Pricing Page — 套餐对比 + 内测 Stub 试用
 */
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  BRAND_SAAS,
  createAuthApi,
  createPaymentApi,
  CLOSED_LOOP_EVENTS,
  trackEvent,
} from "@looma/shared-core";
import { createSaasApiClient } from "../../api/saasApiClient";
import { useSaasAuthStore } from "../auth/authStore";

interface PlanCard {
  tier: string;
  name: string;
  price: string;
  desc: string;
  features: string[];
  highlight: boolean;
  badge?: string;
  actionable?: boolean;
  actionLabel?: string;
}

const plans: PlanCard[] = [
  {
    tier: "free",
    name: "免费版",
    price: "¥0",
    desc: "入门体验，探索 AI 招聘潜力",
    highlight: false,
    badge: "内测中",
    features: [
      "每日 30 次智能问答",
      "每日 5 次职位匹配",
      "每日 3 次简历解析",
      "求职者画像导入",
      "诗词文库浏览",
    ],
  },
  {
    tier: "pro",
    name: "专业版",
    price: "¥29.9/月",
    desc: "深度使用，释放 AI 全部能力",
    highlight: true,
    badge: "7 天试用",
    actionable: true,
    actionLabel: "开始 7 天试用",
    features: [
      "AI 对话不限",
      "全功能岗位匹配",
      "简历解析不限",
      "求职者画像管理",
      "高级数据分析报告",
      "优先客服支持",
    ],
  },
  {
    tier: "enterprise",
    name: "企业版",
    price: "联系我们",
    desc: "为团队打造，定制化 AI 招聘方案",
    highlight: false,
    badge: "定制",
    features: [
      "不限次数所有功能",
      "专属知识库训练",
      "批量简历处理",
      "API 接口对接",
      "7×24 专属技术支持",
    ],
  },
];

export default function Pricing() {
  const { isAuthenticated, token, applySessionToken } = useSaasAuthStore();
  const navigate = useNavigate();
  const [upgrading, setUpgrading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleTrial = async () => {
    if (!isAuthenticated || !token) {
      navigate("/register?from=pricing");
      return;
    }
    setUpgrading(true);
    setMessage(null);
    trackEvent(CLOSED_LOOP_EVENTS.TRIAL_CLICKED);
    try {
      const client = createSaasApiClient();
      const resp = await createPaymentApi(client).upgrade("pro");
      if (resp.access_token) {
        await applySessionToken(resp.access_token);
      } else {
        const refreshed = await createAuthApi(client).refresh();
        await applySessionToken(refreshed.access_token);
      }
      setMessage("已开通 Pro 试用（内测 Stub，无需真实支付）");
    } catch {
      setMessage("升级失败，可能已是 Pro 用户");
    } finally {
      setUpgrading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto" style={{ paddingTop: "1rem" }}>
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold mb-3" style={{ color: "var(--color-text-primary)" }}>
          选择适合你的方案
        </h1>
        <p className="text-sm max-w-md mx-auto" style={{ color: "var(--color-text-secondary)", lineHeight: 1.8 }}>
          {BRAND_SAAS.slogan}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        {plans.map((plan) => (
          <div
            key={plan.tier}
            className="rounded-xl p-6 flex flex-col relative transition-shadow hover:shadow-lg"
            style={{
              backgroundColor: "var(--color-bg-card)",
              boxShadow: plan.highlight ? "0 0 0 2px var(--color-primary), var(--shadow-md)" : "var(--shadow-sm)",
              transform: plan.highlight ? "scale(1.03)" : "scale(1)",
            }}
          >
            {plan.badge && (
              <span
                className="absolute -top-3 left-6 px-3 py-0.5 rounded-full text-xs font-medium text-white"
                style={{ backgroundColor: plan.highlight ? "var(--color-primary)" : "var(--color-text-muted)" }}
              >
                {plan.badge}
              </span>
            )}

            <h3 className="text-lg font-bold mb-1" style={{ color: "var(--color-text-primary)" }}>
              {plan.name}
            </h3>
            <div className="flex items-baseline gap-1 mb-3">
              <span className="text-3xl font-bold" style={{ color: "var(--color-primary)" }}>
                {plan.price}
              </span>
            </div>
            <p className="text-xs mb-5" style={{ color: "var(--color-text-muted)" }}>{plan.desc}</p>

            <div className="mb-5" style={{ height: 1, backgroundColor: "var(--color-border)" }} />

            <ul className="flex-1 space-y-3 mb-6">
              {plan.features.map((f) => (
                <li key={f} className="flex items-start gap-2 text-sm" style={{ color: "var(--color-text-secondary)" }}>
                  <span style={{ color: "var(--color-success)", flexShrink: 0 }}>✓</span>
                  {f}
                </li>
              ))}
            </ul>

            {plan.actionable ? (
              <button
                onClick={() => void handleTrial()}
                disabled={upgrading}
                className="w-full py-2.5 text-sm rounded-lg font-medium text-white disabled:opacity-60"
                style={{ backgroundColor: "var(--color-primary)" }}
              >
                {upgrading ? "处理中…" : plan.actionLabel}
              </button>
            ) : (
              <button
                disabled
                className="w-full py-2.5 text-sm rounded-lg font-medium cursor-not-allowed opacity-50"
                style={{
                  backgroundColor: "var(--color-bg-surface)",
                  color: "var(--color-text-secondary)",
                }}
              >
                {plan.tier === "free" ? "当前默认" : "即将开放"}
              </button>
            )}
          </div>
        ))}
      </div>

      {message && (
        <p className="text-center text-sm mb-4" style={{ color: "var(--color-success)" }}>{message}</p>
      )}

      <div
        className="text-center rounded-xl p-6"
        style={{ backgroundColor: "var(--color-bg-card)", boxShadow: "var(--shadow-sm)" }}
      >
        <p className="text-sm font-medium mb-1" style={{ color: "var(--color-text-primary)" }}>
          🚀 内测期间，核心功能免费开放
        </p>
        <p className="text-xs mb-3" style={{ color: "var(--color-text-muted)" }}>
          Pro 试用为 Stub 升级，备案后将接入真实支付
        </p>
        {!isAuthenticated && (
          <Link to="/register" className="text-sm" style={{ color: "var(--color-primary)" }}>
            还没有账号？立即注册 →
          </Link>
        )}
      </div>
    </div>
  );
}
