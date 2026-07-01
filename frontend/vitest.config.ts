import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  test: {
    globals: true,
    environment: "node",
    include: ["packages/**/src/**/*.test.ts"],
    coverage: {
      provider: "v8",
      include: ["packages/shared-core/src/**/*.ts"],
      exclude: ["**/*.test.ts", "**/index.ts"],
    },
  },
  resolve: {
    alias: {
      "@looma/shared-core": path.resolve(__dirname, "packages/shared-core/src"),
    },
  },
});
