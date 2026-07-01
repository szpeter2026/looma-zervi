import { useEffect } from "react";
import { createApiClient, initAnalytics } from "@looma/shared-core";
import { useSaasAuthStore } from "../features/auth/authStore";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:5000";

export function useSaasAnalytics() {
  useEffect(() => {
    const client = createApiClient({
      baseURL: API_BASE,
      getToken: () => useSaasAuthStore.getState().token,
    });
    initAnalytics(client, "tspace_web");
  }, []);
}
