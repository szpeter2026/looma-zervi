/**
 * SaaS Auth Guard - protects routes that require authentication.
 * Owner: szbenyx
 *
 * Checks for looma JWT in the auth store.
 * If not authenticated, redirects to /login.
 */
import { ReactNode, useEffect } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useSaasAuthStore } from "./authStore";

export function SaasAuthGuard({ children }: { children?: ReactNode }) {
  const { token, isAuthenticated, fetchProfile } = useSaasAuthStore();
  const location = useLocation();

  useEffect(() => {
    if (token && !isAuthenticated) {
      fetchProfile().catch(() => {
        useSaasAuthStore.getState().logout();
      });
    }
  }, [token, isAuthenticated, fetchProfile]);

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children ? <>{children}</> : <Outlet />;
}
