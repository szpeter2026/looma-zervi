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
 *
 * Style: 浅色 B 端 SaaS，白色顶栏 + 浅灰内容区
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
          className="flex items-center justify-between px-6 shrink-0"
          style={{
            height: "var(--header-height)",
            backgroundColor: "var(--color-bg-card)",
            borderBottom: "1px solid var(--color-border)",
          }}
        >
          <span
            className="text-sm"
            style={{ color: "var(--color-text-muted)" }}
          >
            {user?.email || "加载中..."}
          </span>
          <button
            onClick={handleLogout}
            className="btn text-sm bg-transparent border-none cursor-pointer transition-colors"
            style={{
              color: "var(--color-danger)",
              padding: "4px 12px",
            }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.backgroundColor = "var(--color-danger-light)")
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.backgroundColor = "transparent")
            }
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
