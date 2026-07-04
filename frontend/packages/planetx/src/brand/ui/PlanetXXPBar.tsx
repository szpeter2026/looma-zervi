/**
 * PlanetX XPBar — pure UI component.
 * Shows level badge + XP progress bar.
 * Tier colors: bronze / silver / gold / platinum / diamond
 */
import type { PlanetXXPBarProps } from "./types";

const TIER_COLORS: Record<string, string> = {
  bronze: "var(--px-color-tier-bronze)",
  silver: "var(--px-color-tier-silver)",
  gold: "var(--px-color-tier-gold)",
  platinum: "var(--px-color-tier-platinum)",
  diamond: "var(--px-color-tier-diamond)",
};

export default function PlanetXXPBar({
  level,
  xp,
  xpToNext,
  rankName,
  tier = "gold",
  size = "sm",
  animate = true,
}: PlanetXXPBarProps) {
  const pct = Math.min(100, xpToNext > 0 ? (xp / xpToNext) * 100 : 0);
  const tierColor = TIER_COLORS[tier];
  const barHeight = size === "lg" ? "var(--px-bar-height-lg)" : "var(--px-bar-height)";

  return (
    <div
      style={{
        background: "var(--px-color-bg-card)",
        border: "1px solid var(--px-border-default)",
        borderRadius: "var(--px-radius-md)",
        padding: "var(--px-spacing-md)",
        marginBottom: "var(--px-spacing-md)",
      }}
    >
      {/* Header row */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "var(--px-spacing-sm)",
        }}
      >
        <span
          style={{
            fontSize: "var(--px-font-size-xs)",
            color: "var(--px-color-text-muted)",
            letterSpacing: "var(--px-letter-spacing-wide)",
          }}
        >
          ⚡ 星际能量
        </span>
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "var(--px-spacing-xs)",
            background: "var(--px-badge-bg-level)",
            border: `1px solid ${tierColor === "var(--px-color-tier-gold)" ? "var(--px-border-accent)" : "var(--px-border-default)"}`,
            borderRadius: "var(--px-badge-radius)",
            padding: "2px 10px",
            fontSize: "var(--px-font-size-xs)",
            color: tierColor,
            fontWeight: "var(--px-font-weight-bold)",
          }}
        >
          🪐 Lv.{level}{rankName ? ` · ${rankName}` : ""}
        </span>
        <span
          style={{
            fontSize: "var(--px-font-size-xs)",
            color: "var(--px-color-accent)",
            fontWeight: "var(--px-font-weight-bold)",
          }}
          className={animate ? "px-anim-numberRoll" : ""}
        >
          {xp} / {xpToNext} XP
        </span>
      </div>

      {/* Progress bar */}
      <div
        style={{
          height: barHeight,
          background: "var(--px-bar-bg)",
          borderRadius: "var(--px-bar-radius)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            borderRadius: "var(--px-bar-radius)",
            background: "var(--px-bar-fill)",
            transition: "var(--px-bar-transition)",
            width: `${pct}%`,
          }}
        />
      </div>
    </div>
  );
}
