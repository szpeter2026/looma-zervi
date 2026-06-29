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
import { SaasAuthGuard } from "./features/auth/SaasAuthGuard";
import { AppLayout } from "./brand/components/AppLayout";
import Login from "./features/auth/Login";
import Register from "./features/auth/Register";
import Dashboard from "./features/dashboard/Dashboard";
import Chat from "./features/chat/Chat";
import Jobs from "./features/hr/Jobs";
import Resume from "./features/hr/Resume";
import Reports from "./features/reports/Reports";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Protected routes with layout */}
        <Route element={<SaasAuthGuard />}>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/query" element={<Chat />} />
            <Route path="/jobs" element={<Jobs />} />
            <Route path="/resume" element={<Resume />} />
            <Route path="/reports" element={<Reports />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
