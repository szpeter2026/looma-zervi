/**
 * App Layout - SaaS shell with sidebar + header.
 * Owner: szbenyx
 *
 * Structure:
 *   ┌──────────────────────────────┐
 *   │ Sidebar │      Header         │
 *   │         ├─────────────────────┤
 *   │  - Dash │                     │
 *   │  - Chat │     <Outlet />      │
 *   │  - HR   │                     │
 *   │  - Docs │                     │
 *   │  - Ent  │                     │
 *   └─────────┴─────────────────────┘
 */
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useSaasAuthStore } from "../../features/auth/authStore";

const navItems = [
  { to: "/dashboard", label: "仪表盘" },
  { to: "/chat", label: "知识库" },
  { to: "/hr", label: "候选人" },
  { to: "/docs", label: "文档" },
  { to: "/enterprise", label: "企业设置" },
];

export function AppLayout() {
  const { user, logout } = useSaasAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      {/* Sidebar */}
      <aside
        style={{
          width: "var(--sidebar-width)",
          background: "var(--color-bg-sidebar)",
          color: "var(--color-text-sidebar)",
          padding: "16px 0",
          flexShrink: 0,
        }}
      >
        <div style={{ padding: "0 20px 20px", fontSize: "18px", fontWeight: 600 }}>
          T空间
        </div>
        <nav>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              style={({ isActive }) => ({
                display: "block",
                padding: "10px 20px",
                color: isActive
                  ? "var(--color-text-sidebar-active)"
                  : "var(--color-text-sidebar)",
                textDecoration: "none",
                background: isActive ? "rgba(255,255,255,0.1)" : "none",
              })}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <header
          style={{
            height: "var(--header-height)",
            background: "var(--color-bg-card)",
            borderBottom: "1px solid #e0e0e0",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 24px",
          }}
        >
          <span style={{ color: "var(--color-text-secondary)", fontSize: "14px" }}>
            {user?.email || "Loading..."}
          </span>
          <button
            onClick={handleLogout}
            style={{
              background: "none",
              border: "none",
              color: "var(--color-danger)",
              cursor: "pointer",
              fontSize: "14px",
            }}
          >
            退出
          </button>
        </header>
        <main style={{ flex: 1, padding: "24px", background: "var(--color-bg-page)" }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
