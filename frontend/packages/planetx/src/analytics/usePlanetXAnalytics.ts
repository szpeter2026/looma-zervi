/**
 * PlanetX analytics bootstrap — call once on app mount.
 */
import { useEffect } from "react";
import { initAnalytics } from "@looma/shared-core";
import { getApiClient } from "../features/auth/planetxAuthStore";

export function usePlanetXAnalytics() {
  useEffect(() => {
    const client = getApiClient();
    initAnalytics(client, "planetx_web");
  }, []);
}
