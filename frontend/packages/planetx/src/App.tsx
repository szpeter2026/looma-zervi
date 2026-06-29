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
import AuthScreen from './features/auth/AuthScreen'
import PlanetXHome from './features/PlanetXHome'

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/auth" element={<AuthScreen />} />

          {/* Main game hub (handles all screens internally) */}
          <Route element={<PlanetXAuthGuard />}>
            <Route path="/" element={<PlanetXHome />} />
            <Route path="/quiz" element={<PlanetXHome />} />
            <Route path="/result" element={<PlanetXHome />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  )
}
