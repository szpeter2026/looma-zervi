/**
 * PlanetX analytics bootstrap — call once on app mount.
 */
import { useEffect } from "react";
import { createApiClient, initAnalytics } from "@looma/shared-core";
import { usePlanetXStore } from "../features/auth/planetxAuthStore";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE || "http://127.0.0.1:5200";

export function usePlanetXAnalytics() {
  useEffect(() => {
    const client = createApiClient({
      baseURL: API_BASE,
      getToken: () => usePlanetXStore.getState().token,
    });
    initAnalytics(client, "planetx_web");
  }, []);
}
