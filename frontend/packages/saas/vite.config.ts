import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

/**
 * Dev API proxy target.
 * - Default: local Flask :5200
 * - Point at overseas without CORS pain (keep VITE_API_BASE unset so the
 *   browser stays same-origin and Vite proxies):
 *     VITE_PROXY_TARGET=https://api.genz.ltd pnpm --filter @looma/saas dev
 * - If VITE_API_BASE is set, the browser calls that host directly (needs CORS).
 */
const proxyTarget =
  process.env.VITE_PROXY_TARGET ||
  process.env.VITE_API_BASE ||
  "http://localhost:5200";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@looma/shared-core": path.resolve(__dirname, "../shared-core/src"),
      "@saas": path.resolve(__dirname, "src"),
    },
  },
  server: {
    port: 5174,
    proxy: {
      "/v1": {
        target: proxyTarget,
        changeOrigin: true,
        secure: true,
      },
      "/health": {
        target: proxyTarget,
        changeOrigin: true,
        secure: true,
      },
    },
  },
  build: {
    outDir: "dist",
    rollupOptions: {
      // Ensure PlanetX code never enters SaaS bundle
      external: ["../planetx"],
    },
  },
});
