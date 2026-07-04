import path from "node:path";
import { fileURLToPath } from "node:url";
import type { StorybookConfig } from "@storybook/react-vite";

const dirname = path.dirname(fileURLToPath(import.meta.url));

const config: StorybookConfig = {
  stories: [
    "../packages/saas/src/**/*.stories.@(ts|tsx)",
    "../packages/planetx/src/**/*.stories.@(ts|tsx)",
  ],
  addons: ["@storybook/addon-docs", "@storybook/addon-a11y"],
  framework: "@storybook/react-vite",
  docs: {
    defaultName: "Documentation",
  },
  async viteFinal(config) {
    config.resolve ??= {};
    config.resolve.alias = {
      ...config.resolve.alias,
      "@looma/shared-core": path.resolve(dirname, "../packages/shared-core/src"),
      "@saas": path.resolve(dirname, "../packages/saas/src"),
      "@planetx": path.resolve(dirname, "../packages/planetx/src"),
    };
    return config;
  },
};

export default config;
