/**
 * T-space App - B-end brand entry point.
 * Owner: szbenyx
 *
 * Routes:
 *   /           - Dashboard
 *   /query      - RAG knowledge base chat
 *   /jobs       - Position matching
 *   /resume     - Resume parsing
 *   /reports    - Report center
 *   /login      - Login
 *   /register   - Registration
 */
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useEffect } from "react";
import { SaasAuthGuard } from "./features/auth/SaasAuthGuard";
import { useSaasAuthStore } from "./features/auth/authStore";
import { AppLayout } from "./brand/components/AppLayout";
import ErrorBoundary from "./brand/components/ErrorBoundary";
import Login from "./features/auth/Login";
import Register from "./features/auth/Register";
import Dashboard from "./features/dashboard/Dashboard";
import Chat from "./features/chat/Chat";
import Poetry from "./features/poetry/Poetry";
import Jobs from "./features/hr/Jobs";
import Resume from "./features/hr/Resume";
import Reports from "./features/reports/Reports";

export default function App() {
  const tryAutoLogin = useSaasAuthStore((s) => s.tryAutoLogin);

  // 挂载时尝试从 PlanetX 共享 token 自动登录（C→B 互通）
  useEffect(() => {
    tryAutoLogin();
  }, [tryAutoLogin]);

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Dashboard — 自由浏览，无需登录 */}
          <Route element={<AppLayout />}>
            <Route path="/" element={<Dashboard />} />
          </Route>

          {/* Protected routes (需要登录的功能页) */}
          <Route element={<SaasAuthGuard />}>
            <Route element={<AppLayout />}>
              <Route path="/query" element={<Chat />} />
              <Route path="/poetry" element={<Poetry />} />
              <Route path="/jobs" element={<Jobs />} />
              <Route path="/resume" element={<Resume />} />
              <Route path="/reports" element={<Reports />} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
