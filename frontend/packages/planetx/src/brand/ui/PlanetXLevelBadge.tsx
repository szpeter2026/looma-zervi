/**
 * PlanetX LevelBadge — pure UI component.
 * Shapes: circle / hexagon / diamond
 * Tiers: bronze / silver / gold / platinum / diamond
 */
import type { PlanetXLevelBadgeProps } from "./types";

const TIER_COLORS: Record<string, string> = {
  bronze: "var(--px-color-tier-bronze)",
  silver: "var(--px-color-tier-silver)",
  gold: "var(--px-color-tier-gold)",
  platinum: "var(--px-color-tier-platinum)",
  diamond: "var(--px-color-tier-diamond)",
};

export default function PlanetXLevelBadge({
  level,
  shape = "circle",
  tier = "gold",
  size = 64,
  glowing = false,
  label,
}: PlanetXLevelBadgeProps) {
  const tierColor = TIER_COLORS[tier];

  const baseStyle: React.CSSProperties = {
    width: size,
    height: size,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: size * 0.36,
    fontWeight: "var(--px-font-weight-black)",
    color: tierColor,
    background: "var(--px-color-bg-surface)",
    border: `2px solid ${tierColor}`,
    boxShadow: glowing ? `0 0 20px ${tierColor}` : "var(--px-shadow-card)",
    animation: glowing ? "glowPulse 2s ease-in-out infinite" : undefined,
    position: "relative",
    flexShrink: 0,
  };

  const shapeStyles: Record<string, React.CSSProperties> = {
    circle: { borderRadius: "50%" },
    hexagon: {
      clipPath: "polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)",
      borderRadius: 0,
      border: "none",
      boxShadow: glowing ? `0 0 20px ${tierColor}` : "var(--px-shadow-card)",
    },
    diamond: {
      transform: "rotate(45deg)",
      borderRadius: "var(--px-radius-sm)",
    },
  };

  const innerTextStyle: React.CSSProperties = shape === "diamond"
    ? { transform: "rotate(-45deg)" }
    : {};

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "var(--px-spacing-xs)" }}>
      <div style={{ ...baseStyle, ...shapeStyles[shape] }}>
        <span style={innerTextStyle}>{level}</span>
      </div>
      {label && (
        <span style={{
          fontSize: "var(--px-font-size-xs)",
          color: "var(--px-color-text-muted)",
          letterSpacing: "var(--px-letter-spacing-wide)",
        }}>
          {label}
        </span>
      )}
    </div>
  );
}
