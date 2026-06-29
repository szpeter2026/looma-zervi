/**
 * PlanetX Auth Guard - protects routes that require authentication.
 * Owner: Jason
 *
 * Checks for looma JWT in the auth store.
 * If not authenticated, redirects to /auth.
 */
import { ReactNode, useEffect } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { usePlanetXAuthStore } from "./planetxAuthStore";

export function PlanetXAuthGuard({ children }: { children?: ReactNode }) {
  const { token, isAuthenticated, fetchProfile } = usePlanetXAuthStore();
  const location = useLocation();

  useEffect(() => {
    if (token && !isAuthenticated) {
      fetchProfile().catch(() => {
        usePlanetXAuthStore.getState().logout();
      });
    }
  }, [token, isAuthenticated, fetchProfile]);

  if (!token) {
    return <Navigate to="/auth" state={{ from: location }} replace />;
  }

  return children ? <>{children}</> : <Outlet />;
}
