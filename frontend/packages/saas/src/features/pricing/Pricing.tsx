/**
 * Pricing Page — 套餐对比展示页
 * 对内测用户免费开放，暗示未来收费，不挡人。
 */
import { BRAND_SAAS } from "@looma/shared-core";

interface PlanCard {
  tier: string;
  name: string;
  price: string;
  desc: string;
  features: string[];
  highlight: boolean;
  badge?: string;
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
      "每日 10 次智能问答",
      "每日 3 次简历解析",
      "每日 3 次职位匹配",
      "基础报告生成",
      "诗词文库浏览",
    ],
  },
  {
    tier: "pro",
    name: "专业版",
    price: "¥99/月",
    desc: "深度使用，释放 AI 全部能力",
    highlight: true,
    badge: "推荐",
    features: [
      "每日 100 次智能问答",
      "每日 50 次简历解析",
      "每日 50 次职位匹配",
      "企业征信查证",
      "高级数据分析报告",
      "PDF / Word 报告导出",
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
      "私有化部署可选",
      "定制化数据报告",
      "7×24 专属技术支持",
    ],
  },
];

export default function Pricing() {
  return (
    <div className="max-w-5xl mx-auto" style={{ paddingTop: "1rem" }}>
      {/* 页头 */}
      <div className="text-center mb-10">
        <h1
          className="text-3xl font-bold mb-3"
          style={{ color: "var(--color-text-primary)" }}
        >
          选择适合你的方案
        </h1>
        <p
          className="text-sm max-w-md mx-auto"
          style={{ color: "var(--color-text-secondary)", lineHeight: 1.8 }}
        >
          {BRAND_SAAS.slogan}
        </p>
      </div>

      {/* 三栏套餐 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        {plans.map((plan) => (
          <div
            key={plan.tier}
            className="rounded-xl p-6 flex flex-col relative transition-shadow hover:shadow-lg"
            style={{
              backgroundColor: "var(--color-bg-card)",
              boxShadow: plan.highlight
                ? "0 0 0 2px var(--color-primary), var(--shadow-md)"
                : "var(--shadow-sm)",
              transform: plan.highlight ? "scale(1.03)" : "scale(1)",
            }}
          >
            {/* Badge */}
            {plan.badge && (
              <span
                className="absolute -top-3 left-6 px-3 py-0.5 rounded-full text-xs font-medium text-white"
                style={{
                  backgroundColor: plan.highlight
                    ? "var(--color-primary)"
                    : "var(--color-text-muted)",
                }}
              >
                {plan.badge}
              </span>
            )}

            {/* 套餐名 + 价格 */}
            <h3
              className="text-lg font-bold mb-1"
              style={{ color: "var(--color-text-primary)" }}
            >
              {plan.name}
            </h3>
            <div className="flex items-baseline gap-1 mb-3">
              <span
                className="text-3xl font-bold"
                style={{ color: "var(--color-primary)" }}
              >
                {plan.price}
              </span>
            </div>
            <p
              className="text-xs mb-5"
              style={{ color: "var(--color-text-muted)" }}
            >
              {plan.desc}
            </p>

            {/* 分隔线 */}
            <div
              className="mb-5"
              style={{
                height: 1,
                backgroundColor: "var(--color-border)",
              }}
            />

            {/* 功能列表 */}
            <ul className="flex-1 space-y-3 mb-6">
              {plan.features.map((f) => (
                <li
                  key={f}
                  className="flex items-start gap-2 text-sm"
                  style={{ color: "var(--color-text-secondary)" }}
                >
                  <span style={{ color: "var(--color-success)", flexShrink: 0 }}>✓</span>
                  {f}
                </li>
              ))}
            </ul>

            {/* CTA */}
            <button
              disabled
              className="w-full py-2.5 text-sm rounded-lg font-medium cursor-not-allowed opacity-50"
              style={{
                backgroundColor: plan.highlight
                  ? "var(--color-primary)"
                  : "var(--color-bg-surface)",
                color: plan.highlight ? "#fff" : "var(--color-text-secondary)",
              }}
            >
              即将开放
            </button>
          </div>
        ))}
      </div>

      {/* 底部暗示 */}
      <div
        className="text-center rounded-xl p-6"
        style={{
          backgroundColor: "var(--color-bg-card)",
          boxShadow: "var(--shadow-sm)",
        }}
      >
        <p
          className="text-sm font-medium mb-1"
          style={{ color: "var(--color-text-primary)" }}
        >
          🚀 内测期间，所有功能免费开放
        </p>
        <p className="text-xs" style={{ color: "var(--color-text-muted)" }}>
          尽情体验全部能力，正式上线后我们将保留你的使用记录和偏好设置
        </p>
      </div>
    </div>
  );
}
