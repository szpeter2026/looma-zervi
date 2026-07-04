/**
 * PlanetX Card — pure UI component.
 * Variants: default / highlight / glass
 * Padding: sm / md / lg
 */
import type { PlanetXCardProps } from "./types";

export default function PlanetXCard({
  variant = "default",
  highlighted = false,
  padding = "md",
  onClick,
  children,
  className = "",
}: PlanetXCardProps) {
  const paddings: Record<string, string> = {
    sm: "var(--px-spacing-md)",
    md: "var(--px-card-padding)",
    lg: "var(--px-card-padding-lg)",
  };

  const styles: React.CSSProperties = {
    background: variant === "highlight"
      ? "var(--px-card-bg-highlight)"
      : variant === "glass"
      ? "rgba(13, 13, 26, 0.6)"
      : "var(--px-card-bg)",
    border: highlighted ? "var(--px-card-border-highlight)" : "var(--px-card-border)",
    borderRadius: "var(--px-card-radius)",
    padding: paddings[padding],
    boxShadow: highlighted ? "var(--px-shadow-accent)" : "var(--px-shadow-card)",
    transition: "var(--px-anim-normal)",
    cursor: onClick ? "pointer" : "default",
  };

  return (
    <div
      className={`px-anim-screenIn ${className}`}
      style={styles}
      onClick={onClick}
      onMouseEnter={(e) => {
        if (onClick) e.currentTarget.style.boxShadow = "var(--px-shadow-card-hover)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = highlighted ? "var(--px-shadow-accent)" : "var(--px-shadow-card)";
      }}
    >
      {children}
    </div>
  );
}
