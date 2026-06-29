/**
 * T-space App - B-end brand entry point.
 * Owner: szbenyx
 *
 * Routes:
 *   /login      - Login screen
 *   /register   - Registration screen
 *   /dashboard  - Main dashboard
 *   /chat       - RAG knowledge base chat
 *   /hr         - HR candidate management
 *   /docs       - Document management
 *   /enterprise - Enterprise settings
 */
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { SaasAuthGuard } from "./features/auth/SaasAuthGuard";
import { AppLayout } from "./brand/components/AppLayout";
import { Placeholder } from "./brand/components/Placeholder";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<Placeholder title="Login" />} />
        <Route path="/register" element={<Placeholder title="Register" />} />

        {/* Protected routes with layout */}
        <Route element={<SaasAuthGuard />}>
          <Route element={<AppLayout />}>
            <Route path="/dashboard" element={<Placeholder title="Dashboard" />} />
            <Route path="/chat" element={<Placeholder title="Knowledge Base Chat" />} />
            <Route path="/hr" element={<Placeholder title="HR Candidates" />} />
            <Route path="/docs" element={<Placeholder title="Documents" />} />
            <Route path="/enterprise" element={<Placeholder title="Enterprise Settings" />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
