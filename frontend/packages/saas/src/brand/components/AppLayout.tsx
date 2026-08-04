/**
 * App Layout - SaaS shell with responsive sidebar/drawer + header + content.
 * Owner: szbenyx
 *
 * Structure (Desktop >= 768px):
 *   ┌──────────────────────────────────────┐
 *   │ Sidebar │      Header                 │
 *   │         ├─────────────────────────────┤
 *   │         │                             │
 *   │         │       <Outlet />            │
 *   │         │                             │
 *   └─────────┴─────────────────────────────┘
 *
 * Structure (Mobile < 768px):
 *   ┌─────────────────────┐
 *   │  ☰ Header (sticky)  │
 *   ├─────────────────────┤
 *   │                     │
 *   │    <Outlet />       │
 *   │                     │
 *   ├─────────────────────┤
 *   │  Bottom Tab Bar     │
 *   └─────────────────────┘
 *   ┌─────────┐
 *   │ Drawer  │ ← slide-in from left
 *   │ (overlay)│
 *   └─────────┘
 *
 * Style: 浅色 B 端 SaaS，白色顶栏 + 浅灰内容区
 */
import { useState } from "react";
import { Outlet, useNavigate } from "react-router-dom";
import { useSaasAuthStore } from "../../features/auth/authStore";
import Sidebar from "./Sidebar";
import MobileDrawer from "./MobileDrawer";
import MobileBottomNav from "./MobileBottomNav";

export function AppLayout() {
  const { user, logout } = useSaasAuthStore();
  const navigate = useNavigate();
  const [drawerOpen, setDrawerOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="flex min-h-screen">
      {/* ── Desktop Sidebar (hidden on mobile) ── */}
      <Sidebar />

      {/* ── Mobile Drawer ── */}
      <MobileDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />

      {/* ── Main content area ── */}
      <div
        className="flex-1 flex flex-col min-h-screen"
        style={{ marginLeft: "var(--sidebar-width)" }}
      >
        {/* Header */}
        <header
          className="flex items-center justify-between px-4 md:px-6 shrink-0 sticky top-0 z-30"
          style={{
            height: "var(--header-height)",
            backgroundColor: "var(--color-bg-card)",
            borderBottom: "1px solid var(--color-border)",
          }}
        >
          {/* Left: hamburger on mobile, empty on desktop */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setDrawerOpen(true)}
              className="md:hidden flex items-center justify-center"
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "var(--radius-md)",
                border: "none",
                background: "transparent",
                color: "var(--color-text-primary)",
                fontSize: "20px",
                cursor: "pointer",
              }}
              aria-label="打开菜单"
            >
              ☰
            </button>
            {/* Mobile brand name */}
            <span
              className="md:hidden text-base font-semibold"
              style={{ color: "var(--color-primary)" }}
            >
              T 空间
            </span>
          </div>

          {/* Right: user info + logout */}
          <div className="flex items-center gap-3">
            <span
              className="text-sm hidden sm:inline"
              style={{ color: "var(--color-text-muted)" }}
            >
              {user?.email || "加载中..."}
            </span>
            <button
              onClick={handleLogout}
              className="hidden md:inline-flex btn text-sm bg-transparent border-none cursor-pointer transition-colors"
              style={{
                color: "var(--color-danger)",
                padding: "4px 12px",
              }}
            >
              退出登录
            </button>
          </div>
        </header>

        {/* Page content */}
        <main
          className="flex-1 p-4 md:p-6"
          style={{
            backgroundColor: "var(--color-bg-page)",
            paddingBottom: "calc(env(safe-area-inset-bottom, 16px) + 72px)",
          }}
        >
          <Outlet />
        </main>

        {/* ── Mobile Bottom Nav ── */}
        <MobileBottomNav />
      </div>
    </div>
  );
}