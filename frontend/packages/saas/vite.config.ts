import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

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
        target: "http://localhost:5000",
        changeOrigin: true,
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
