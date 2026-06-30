/**
 * PlanetX App - C-end brand entry point.
 * Owner: Jason
 *
 * Routes:
 *   /auth     - Login/Register screen
 *   /         - PlanetX Home (game hub)
 *   /tspace   - T-space Navigator narrative experience (Act 1)
 *   /quiz     - Personality quiz
 *   /result   - Quiz result
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { PlanetXAuthGuard } from './features/auth/PlanetXAuthGuard'
import ErrorBoundary from './brand/components/ErrorBoundary'
import PlanetXHome from './features/PlanetXHome'
import TspaceNavigatorScreen from './features/tspace/TspaceNavigatorScreen'

/** 轻量 ErrorBoundary 包装器，用于隔离单个功能的崩溃 */
function FeatureGuard({ children }: { children: React.ReactNode }) {
  return <ErrorBoundary>{children}</ErrorBoundary>;
}

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          {/* /auth redirects to main hub — PlanetXHome handles auth internally */}
          <Route path="/auth" element={<Navigate to="/" replace />} />

          {/* Main game hub (handles all screens internally: loading/auth/onboarding/hub/quiz/result) */}
          <Route path="/" element={<PlanetXHome />} />

          {/* T-space Navigator narrative experience — Act 1 direct entry */}
          <Route path="/tspace" element={<TspaceNavigatorScreen />} />

          {/* Protected routes (require login) — feature-isolated */}
          <Route element={<PlanetXAuthGuard />}>
            <Route path="/quiz" element={<FeatureGuard><PlanetXHome /></FeatureGuard>} />
            <Route path="/result" element={<FeatureGuard><PlanetXHome /></FeatureGuard>} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  )
}
