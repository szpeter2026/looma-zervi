/**
 * PlanetX Loading — pure UI component.
 * Shows a spinning brand icon with optional text.
 * Can be fullscreen or inline.
 */
import type { PlanetXLoadingProps } from "./types";

const SIZES: Record<string, number> = {
  sm: 24,
  md: 40,
  lg: 64,
};

export default function PlanetXLoading({
  size = "md",
  text,
  fullscreen = false,
}: PlanetXLoadingProps) {
  const px = SIZES[size];

  const spinner = (
    <div
      className="px-anim-xSpin"
      style={{
        width: px,
        height: px,
        border: `${Math.max(2, px / 16)}px solid var(--px-border-default)`,
        borderTopColor: "var(--px-color-accent)",
        borderRadius: "50%",
      }}
    />
  );

  if (fullscreen) {
    return (
      <div
        style={{
          position: "fixed",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: "var(--px-spacing-md)",
          background: "var(--px-color-bg-page)",
          zIndex: "var(--px-z-modal)",
        }}
      >
        {spinner}
        {text && (
          <span style={{
            color: "var(--px-color-text-muted)",
            fontSize: "var(--px-font-size-sm)",
            letterSpacing: "var(--px-letter-spacing-wide)",
          }}>
            {text}
          </span>
        )}
      </div>
    );
  }

  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: "var(--px-spacing-sm)" }}>
      {spinner}
      {text && (
        <span style={{
          color: "var(--px-color-text-muted)",
          fontSize: "var(--px-font-size-sm)",
        }}>
          {text}
        </span>
      )}
    </div>
  );
}
