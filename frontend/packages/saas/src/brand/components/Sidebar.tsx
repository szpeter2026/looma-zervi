/**
 * Sidebar - SaaS navigation shell.
 * Owner: szbenyx
 *
 * Pure CSS + HTML (no tdesign-react / tdesign-icons-react).
 * Uses @looma/shared-core for brand config and auth store.
 * Quota format aligned with backend: { tier, records }.
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
  { path: "/jobs", label: "职位匹配", icon: "◈" },
  { path: "/resume", label: "简历解析", icon: "◈" },
  { path: "/reports", label: "报告中心", icon: "◆" },
];

export default function Sidebar() {
  const { user, quota, logout } = useSaasAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const usagePercent = quota
    ? Math.round(((quota.daily_limit - quota.remaining) / quota.daily_limit) * 100)
    : 0;

  return (
    <aside className="fixed left-0 top-0 bottom-0 flex flex-col z-50"
      style={{
        width: "var(--sidebar-width)",
        backgroundColor: "var(--color-bg-sidebar)",
        color: "var(--color-text-sidebar)",
      }}
    >
      {/* 品牌 */}
      <div className="px-5 py-5 border-b border-white/10">
        <h1 className="text-lg font-bold tracking-wide text-white">
          {BRAND_SAAS.name}
        </h1>
        <p className="text-xs text-white/40 mt-1">{BRAND_SAAS.slogan}</p>
      </div>

      {/* 导航 */}
      <nav className="flex-1 py-4 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-5 py-2.5 text-sm transition-colors no-underline
              ${isActive
                ? "bg-white/10 text-white border-r-2 border-r-[var(--color-primary)]"
                : "text-white/60 hover:bg-white/5 hover:text-white"
              }`
            }
          >
            <span className="text-base">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* 配额 */}
      {user && quota && (
        <div className="px-5 py-3 border-t border-white/10">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-white/40">今日配额</span>
            <span className="text-xs text-white/70">
              {quota.remaining}/{quota.daily_limit}
            </span>
          </div>
          <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-300"
              style={{
                width: `${Math.min(usagePercent, 100)}%`,
                backgroundColor: "var(--color-primary)",
              }}
            />
          </div>
          <div className="mt-1.5">
            <span className="text-xs text-white/30">
              {quota.tier === "free" ? "免费版" : quota.tier === "supporter" ? "支持版" : "专业版"}
            </span>
          </div>
        </div>
      )}

      {/* 用户信息 + 退出 */}
      {user && (
        <div className="px-5 py-3 border-t border-white/10 flex items-center justify-between">
          <div className="min-w-0 flex-1">
            <p className="text-sm truncate text-white/90">{user.name || user.email}</p>
            <p className="text-xs text-white/40 truncate">{user.email}</p>
          </div>
          <button
            onClick={handleLogout}
            className="ml-3 text-white/50 hover:text-white transition-colors bg-transparent border-none cursor-pointer text-lg leading-none p-1"
            title="退出登录"
          >
            ⏻
          </button>
        </div>
      )}
    </aside>
  );
}
