/**
 * PlanetX App - C-end brand entry point.
 * Owner: Jason
 *
 * Routes:
 *   /auth     - Login/Register screen
 *   /         - Hub screen (home)
 *   /quiz     - Personality quiz
 *   /result   - Quiz result
 *   /fleet    - Fleet (team) screen
 *   /profile  - User profile
 */
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { PlanetXAuthGuard } from "./features/auth/PlanetXAuthGuard";
import { Placeholder } from "./brand/components/Placeholder";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/auth" element={<Placeholder title="Auth" />} />

        {/* Protected routes */}
        <Route element={<PlanetXAuthGuard />}>
          <Route path="/" element={<Placeholder title="Hub" />} />
          <Route path="/quiz" element={<Placeholder title="Personality Quiz" />} />
          <Route path="/result" element={<Placeholder title="Result" />} />
          <Route path="/fleet" element={<Placeholder title="Fleet" />} />
          <Route path="/profile" element={<Placeholder title="Profile" />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
