/**
 * App Layout - SaaS shell with sidebar + header + content.
 * Owner: szbenyx
 *
 * Structure:
 *   ┌──────────────────────────────────────┐
 *   │ Sidebar │      Header                 │
 *   │         ├─────────────────────────────┤
 *   │         │                             │
 *   │         │       <Outlet />            │
 *   │         │                             │
 *   └─────────┴─────────────────────────────┘
 */
import { Outlet, useNavigate } from "react-router-dom";
import { useSaasAuthStore } from "../../features/auth/authStore";
import Sidebar from "./Sidebar";

export function AppLayout() {
  const { user, logout } = useSaasAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="flex min-h-screen">
      {/* Sidebar - fixed position component handles its own positioning */}
      <Sidebar />

      {/* Main content area - offset by sidebar width */}
      <div
        className="flex-1 flex flex-col min-h-screen"
        style={{ marginLeft: "var(--sidebar-width)" }}
      >
        {/* Header */}
        <header
          className="flex items-center justify-between px-6 border-b border-gray-200 shrink-0"
          style={{
            height: "var(--header-height)",
            backgroundColor: "var(--color-bg-card)",
          }}
        >
          <span className="text-sm text-[var(--color-text-secondary)]">
            {user?.email || "Loading..."}
          </span>
          <button
            onClick={handleLogout}
            className="bg-transparent border-none cursor-pointer text-sm"
            style={{ color: "var(--color-danger)" }}
          >
            退出登录
          </button>
        </header>

        {/* Page content */}
        <main
          className="flex-1 p-6"
          style={{ backgroundColor: "var(--color-bg-page)" }}
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
}
