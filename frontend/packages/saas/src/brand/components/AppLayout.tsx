/**
 * App Layout - SaaS shell with sidebar + header + content.
 * Owner: szbenyx
 */
import { Outlet, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useSaasAuthStore } from "../../features/auth/authStore";
import { LanguageSwitcher } from "../../components/LanguageSwitcher";
import Sidebar from "./Sidebar";

export function AppLayout() {
  const { t } = useTranslation();
  const { user, logout } = useSaasAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar />

      <div
        className="flex-1 flex flex-col min-h-screen"
        style={{ marginLeft: "var(--sidebar-width)" }}
      >
        <header
          className="flex items-center justify-between px-6 border-b border-gray-200 shrink-0"
          style={{
            height: "var(--header-height)",
            backgroundColor: "var(--color-bg-card)",
          }}
        >
          <span className="text-sm text-[var(--color-text-secondary)]">
            {user?.email || t("common.loading")}
          </span>
          <div className="flex items-center gap-4">
            <LanguageSwitcher />
            <button
              onClick={handleLogout}
              className="bg-transparent border-none cursor-pointer text-sm"
              style={{ color: "var(--color-danger)" }}
            >
              {t("auth.logout")}
            </button>
          </div>
        </header>

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
