/**
 * Sidebar - SaaS navigation shell.
 * Owner: szbenyx
 *
 * Pure CSS + HTML (no tdesign-react / tdesign-icons-react).
 * Uses @looma/shared-core for brand config and auth store.
 * Quota format aligned with backend: { tier, records }.
 *
 * Style: 浅色 B 端 SaaS 侧边栏，白色底 + 深蓝文字 + 专业蓝激活态
 */
import { NavLink, useNavigate } from "react-router-dom";
import { BRAND_SAAS } from "@looma/shared-core";
import { useSaasAuthStore } from "../../features/auth/authStore";

interface NavItem {
  path: string;
  label: string;
  icon: string;
}

const navItems: NavItem[] = [
  { path: "/", label: "仪表盘", icon: "◉" },
  { path: "/query", label: "智能问答", icon: "◈" },
  { path: "/poetry", label: "诗词文库", icon: "◇" },
  { path: "/candidates", label: "求职者画像", icon: "◎" },
  { path: "/jobs", label: "职位匹配", icon: "◈" },
  { path: "/resume", label: "简历解析", icon: "◈" },
  { path: "/reports", label: "报告中心", icon: "◆" },
  { path: "/settings/consent", label: "隐私授权", icon: "🛡" },
];

export default function Sidebar() {
  const { user, quota, logout } = useSaasAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const askRecord = quota?.records?.find((r) => r.resource === "ask");
  const usagePercent = askRecord && askRecord.daily_limit > 0
    ? Math.round((askRecord.used / askRecord.daily_limit) * 100)
    : 0;

  return (
    <aside
      className="fixed left-0 top-0 bottom-0 flex flex-col z-50"
      style={{
        width: "var(--sidebar-width)",
        backgroundColor: "var(--color-bg-sidebar)",
        color: "var(--color-text-sidebar)",
        borderRight: "1px solid var(--color-border)",
      }}
    >
      {/* 品牌 */}
      <div
        className="px-5 py-5"
        style={{ borderBottom: "1px solid var(--color-border)" }}
      >
        <h1
          className="text-lg font-semibold tracking-wide"
          style={{ color: "var(--color-text-primary)" }}
        >
          {BRAND_SAAS.name}
        </h1>
        <p
          className="text-xs mt-1"
          style={{ color: "var(--color-text-muted)" }}
        >
          {BRAND_SAAS.slogan}
        </p>
      </div>

      {/* 导航 */}
      <nav className="flex-1 py-4 px-3 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 text-sm rounded-lg transition-colors no-underline ${
                isActive
                  ? "font-medium"
                  : ""
              }`
            }
            style={({ isActive }) => ({
              color: isActive ? "var(--color-text-sidebar-active)" : "var(--color-text-sidebar)",
              backgroundColor: isActive ? "var(--sidebar-active-bg)" : "transparent",
            })}
          >
            <span className="text-base" style={{ opacity: 0.8 }}>
              {item.icon}
            </span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* 配额 */}
      {user && quota && (
        <div
          className="mx-4 mb-3 p-4 rounded-lg"
          style={{
            backgroundColor: "var(--color-bg-surface)",
            border: "1px solid var(--color-border-light)",
          }}
        >
          <div className="flex items-center justify-between mb-2">
            <span
              className="text-xs"
              style={{ color: "var(--color-text-muted)" }}
            >
              今日配额
            </span>
            <span
              className="text-xs font-medium"
              style={{ color: "var(--color-text-secondary)" }}
            >
              {askRecord
                ? `${askRecord.daily_limit - askRecord.used}/${askRecord.daily_limit}`
                : "—"}
            </span>
          </div>
          <div
            className="h-1.5 rounded-full overflow-hidden"
            style={{ backgroundColor: "var(--color-border-light)" }}
          >
            <div
              className="h-full rounded-full transition-all duration-300"
              style={{
                width: `${Math.min(usagePercent, 100)}%`,
                backgroundColor: "var(--color-primary)",
              }}
            />
          </div>
          <div className="mt-1.5 flex items-center justify-between">
            <span
              className="text-xs"
              style={{ color: "var(--color-text-muted)" }}
            >
              {quota.tier === "free"
                ? "免费版"
                : quota.tier === "supporter"
                ? "支持版"
                : "专业版"}
            </span>
            <NavLink
              to="/pricing"
              className="text-xs transition-colors no-underline hover:underline"
              style={{ color: "var(--color-primary)" }}
            >
              查看套餐 →
            </NavLink>
          </div>
        </div>
      )}

      {/* 用户信息 + 退出 */}
      {user && (
        <div
          className="px-5 py-3 flex items-center justify-between"
          style={{ borderTop: "1px solid var(--color-border)" }}
        >
          <div className="min-w-0 flex-1">
            <p
              className="text-sm truncate font-medium"
              style={{ color: "var(--color-text-primary)" }}
            >
              {user.name || user.email}
            </p>
            <p
              className="text-xs truncate"
              style={{ color: "var(--color-text-muted)" }}
            >
              {user.email}
            </p>
          </div>
          <button
            onClick={handleLogout}
            className="ml-3 transition-colors bg-transparent border-none cursor-pointer text-lg leading-none p-1"
            style={{ color: "var(--color-text-muted)" }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.color = "var(--color-danger)")
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.color = "var(--color-text-muted)")
            }
            title="退出登录"
          >
            ⏻
          </button>
        </div>
      )}
    </aside>
  );
}
