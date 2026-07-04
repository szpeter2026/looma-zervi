import type { Preview } from "@storybook/react-vite";
import type { CSSProperties } from "react";

import "../packages/saas/src/brand/tokens.css";
import "../packages/saas/src/brand/markdown.css";
import "../packages/planetx/src/brand/tokens.css";
import "../packages/planetx/src/brand/animations.css";

function brandCanvas(title: string | undefined): CSSProperties {
  if (title?.startsWith("PlanetX/")) {
    return {
      background: "var(--px-color-bg-page)",
      color: "var(--px-color-text-bright)",
      padding: 24,
      minHeight: 160,
      fontFamily: "var(--px-font-family)",
    };
  }

  return {
    background: "var(--color-bg-page)",
    color: "var(--color-text-primary)",
    padding: 24,
    minHeight: 160,
    fontFamily: "var(--font-family)",
  };
}

const preview: Preview = {
  parameters: {
    layout: "fullscreen",
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    a11y: {
      test: "todo",
    },
    options: {
      storySort: {
        order: ["PlanetX", "SaaS"],
      },
    },
  },
  decorators: [
    (Story, context) => (
      <div style={brandCanvas(context.title)}>
        <Story />
      </div>
    ),
  ],
};

export default preview;
