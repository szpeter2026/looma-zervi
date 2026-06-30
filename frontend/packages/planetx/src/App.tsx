/**
 * PlanetX App - C-end brand entry point.
 * Owner: Jason
 *
 * Routes:
 *   /auth     - Login/Register screen
 *   /         - PlanetX Home (game hub)
 *   /quiz     - Personality quiz
 *   /result   - Quiz result
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { PlanetXAuthGuard } from './features/auth/PlanetXAuthGuard'
import ErrorBoundary from './brand/components/ErrorBoundary'
import PlanetXHome from './features/PlanetXHome'
import NarrativeRedirect from './features/onboarding/NarrativeRedirect'

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          {/* /auth redirects to main hub — PlanetXHome handles auth internally */}
          <Route path="/auth" element={<Navigate to="/" replace />} />

          {/* Main game hub (handles all screens internally: loading/auth/onboarding/hub/quiz/result) */}
          <Route path="/" element={<PlanetXHome />} />

          {/* T-space / Navigator narrative experience lives in the SaaS app */}
          <Route path="/narrative" element={<NarrativeRedirect />} />

          {/* Protected routes (require login) */}
          <Route element={<PlanetXAuthGuard />}>
            <Route path="/quiz" element={<PlanetXHome />} />
            <Route path="/result" element={<PlanetXHome />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  )
}
