/**
 * Sidebar - SaaS navigation shell.
 * Owner: szbenyx
 *
 * Tier/role differentiation:
 * - admin: show Admin nav
 * - free: show lock badge on supporter+ features (still navigable → upgrade CTA)
 */
import { useMemo } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { hasMinTier, isAdmin, isPaidTier, type Tier } from "@looma/shared-core";
import { useSaasAuthStore } from "../../features/auth/authStore";
import { useBrand } from "../useBrand";
import { IS_OVERSEAS } from "../../config/region";

interface NavItem {
  path: string;
  labelKey: string;
  icon: string;
  overseasHidden?: boolean;
  mainlandHidden?: boolean;
  /** Minimum tier to unlock; free users see a lock badge. */
  minTier?: Tier;
}

function tierLabel(tier: string, t: (key: string) => string) {
  if (tier === "free") return t("tier.free");
  if (tier === "supporter") return t("tier.supporter");
  return t("tier.pro");
}

export default function Sidebar() {
  const { t } = useTranslation();
  const brand = useBrand();
  const { user, quota, logout } = useSaasAuthStore();
  const navigate = useNavigate();
  const userTier = user?.tier ?? quota?.tier ?? "free";

  const navItems: NavItem[] = useMemo(() => {
    const items: NavItem[] = [
      { path: "/", labelKey: "nav.dashboard", icon: "◉" },
      { path: "/query", labelKey: "nav.query", icon: "◈" },
      { path: "/poetry", labelKey: "nav.poetry", icon: "◇" },
      { path: "/poetry/challenge", labelKey: "nav.challenge", icon: "✧", mainlandHidden: true },
      {
        path: "/candidates",
        labelKey: IS_OVERSEAS ? "nav.profile" : "nav.candidates",
        icon: "◎",
        overseasHidden: true,
        minTier: "supporter",
      },
      { path: "/jobs", labelKey: IS_OVERSEAS ? "nav.jobsOverseas" : "nav.jobs", icon: "◈" },
      { path: "/resume", labelKey: "nav.resume", icon: "◈" },
      { path: "/reports", labelKey: "nav.reports", icon: "◆" },
      { path: "/settings/consent", labelKey: "nav.consent", icon: "🛡" },
    ];
    if (isAdmin(user?.role)) {
      items.push({ path: "/admin", labelKey: "nav.admin", icon: "⚙" });
    }
    return items.filter(
      (item) =>
        !(IS_OVERSEAS && item.overseasHidden) &&
        !(!IS_OVERSEAS && item.mainlandHidden),
    );
  }, [user?.role]);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const askRecord = quota?.records?.find((r) => r.resource === "ask");
  const paid = isPaidTier(userTier);
  const usagePercent = askRecord && askRecord.daily_limit > 0
    ? Math.round((askRecord.used / askRecord.daily_limit) * 100)
    : 0;
  const remaining = askRecord
    ? Math.max(askRecord.daily_limit - askRecord.used, 0)
    : null;

  return (
    <aside className="fixed left-0 top-0 bottom-0 flex flex-col z-50"
      style={{
        width: "var(--sidebar-width)",
        backgroundColor: "var(--color-bg-sidebar)",
        color: "var(--color-text-sidebar)",
      }}
    >
      <div className="px-5 py-5 border-b border-white/10">
        <h1 className="text-lg font-bold tracking-wide text-white">
          {brand.name}
        </h1>
        <p className="text-xs text-white/40 mt-1">{brand.slogan}</p>
      </div>

      <nav className="flex-1 py-4 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => {
          const locked = Boolean(
            item.minTier && user && !hasMinTier(userTier, item.minTier),
          );
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-5 py-2.5 text-sm transition-colors no-underline
                ${locked ? "opacity-55" : ""}
                ${isActive
                  ? "bg-white/10 text-white border-r-2 border-r-[var(--color-primary)]"
                  : "text-white/60 hover:bg-white/5 hover:text-white"
                }`
              }
            >
              <span className="text-base">{item.icon}</span>
              <span className="flex-1 truncate">{t(item.labelKey)}</span>
              {locked && (
                <span
                  className="text-[10px] px-1.5 py-0.5 rounded border border-white/20 text-white/50 shrink-0"
                  title={t("tier.lockHint")}
                >
                  {t("tier.lockBadge")}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {user && quota && (
        <div className="px-5 py-3 border-t border-white/10">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-white/40">{t("dashboard.todayQuota")}</span>
            <span className="text-xs text-white/70">
              {paid
                ? t("tier.unlimited")
                : remaining !== null && askRecord
                  ? `${remaining}/${askRecord.daily_limit}`
                  : "—"}
            </span>
          </div>
          {!paid && (
            <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-300"
                style={{
                  width: `${Math.min(usagePercent, 100)}%`,
                  backgroundColor: usagePercent >= 90
                    ? "var(--color-warning, #f59e0b)"
                    : "var(--color-primary)",
                }}
              />
            </div>
          )}
          <div className="mt-1.5 flex items-center justify-between">
            <span className="text-xs text-white/30">
              {tierLabel(quota.tier, t)}
            </span>
            <NavLink
              to="/pricing"
              className="text-xs text-white/40 hover:text-white transition-colors no-underline"
            >
              {paid ? t("dashboard.viewPlans") : t("dashboard.upgrade")}
            </NavLink>
          </div>
        </div>
      )}

      {user && (
        <div className="px-5 py-3 border-t border-white/10 flex items-center justify-between">
          <div className="min-w-0 flex-1">
            <p className="text-sm truncate text-white/90">{user.name || user.email}</p>
            <p className="text-xs text-white/40 truncate">{user.email}</p>
          </div>
          <button
            onClick={handleLogout}
            className="ml-3 text-white/50 hover:text-white transition-colors bg-transparent border-none cursor-pointer text-lg leading-none p-1"
            title={t("auth.logout")}
          >
            ⏻
          </button>
        </div>
      )}
    </aside>
  );
}
