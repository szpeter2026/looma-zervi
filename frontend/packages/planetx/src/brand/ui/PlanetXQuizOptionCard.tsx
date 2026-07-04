/**
 * PlanetX QuizOptionCard — pure UI component.
 * States: default / selected / correct / wrong / disabled
 */
import type { PlanetXQuizOptionCardProps } from "./types";

const STATE_STYLES: Record<string, { bg: string; border: string; color: string; shadow: string }> = {
  default: {
    bg: "var(--px-color-bg-card)",
    border: "1px solid var(--px-border-default)",
    color: "var(--px-color-text)",
    shadow: "var(--px-shadow-card)",
  },
  selected: {
    bg: "var(--px-color-bg-surface)",
    border: "1.5px solid var(--px-color-primary)",
    color: "var(--px-color-text-bright)",
    shadow: "var(--px-shadow-glow)",
  },
  correct: {
    bg: "var(--px-color-success-light)",
    border: "1.5px solid var(--px-color-success)",
    color: "var(--px-color-success)",
    shadow: "0 0 20px rgba(0, 217, 163, 0.3)",
  },
  wrong: {
    bg: "var(--px-color-danger-light)",
    border: "1.5px solid var(--px-color-danger)",
    color: "var(--px-color-danger)",
    shadow: "0 0 20px rgba(255, 71, 87, 0.3)",
  },
  disabled: {
    bg: "var(--px-color-bg-deep)",
    border: "1px solid var(--px-border-subtle)",
    color: "var(--px-color-text-dim)",
    shadow: "none",
  },
};

const INDEX_LETTERS = ["A", "B", "C", "D", "E", "F"];

export default function PlanetXQuizOptionCard({
  label,
  description,
  index = 0,
  state = "default",
  onClick,
}: PlanetXQuizOptionCardProps) {
  const s = STATE_STYLES[state];
  const isInteractive = state === "default" || state === "selected";

  return (
    <div
      className="px-anim-fadeIn"
      onClick={isInteractive ? onClick : undefined}
      style={{
        display: "flex",
        alignItems: "center",
        gap: "var(--px-spacing-md)",
        padding: "var(--px-card-padding)",
        background: s.bg,
        border: s.border,
        borderRadius: "var(--px-card-radius)",
        boxShadow: s.shadow,
        cursor: isInteractive ? "pointer" : "default",
        opacity: state === "disabled" ? 0.5 : 1,
        transition: "var(--px-anim-fast)",
        userSelect: "none",
      }}
      onMouseEnter={(e) => {
        if (!isInteractive) return;
        e.currentTarget.style.transform = "translateY(-2px)";
        e.currentTarget.style.boxShadow = "var(--px-shadow-card-hover)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = "translateY(0)";
        e.currentTarget.style.boxShadow = s.shadow;
      }}
    >
      {/* Index badge */}
      <div
        style={{
          width: 32,
          height: 32,
          borderRadius: "var(--px-radius-md)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "var(--px-font-size-sm)",
          fontWeight: "var(--px-font-weight-bold)",
          background: state === "selected" ? "var(--px-color-primary)" : "var(--px-color-bg-surface)",
          color: state === "selected" ? "#fff" : "var(--px-color-text-muted)",
          border: "1px solid var(--px-border-default)",
          flexShrink: 0,
        }}
      >
        {INDEX_LETTERS[index] ?? index + 1}
      </div>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: "var(--px-font-size-base)", fontWeight: "var(--px-font-weight-medium)", color: s.color }}>
          {label}
        </div>
        {description && (
          <div style={{ fontSize: "var(--px-font-size-xs)", color: "var(--px-color-text-muted)", marginTop: "var(--px-spacing-xs)" }}>
            {description}
          </div>
        )}
      </div>

      {/* State indicator */}
      {state === "correct" && <span style={{ fontSize: 20 }}>✓</span>}
      {state === "wrong" && <span style={{ fontSize: 20 }}>✗</span>}
      {state === "selected" && <span style={{ fontSize: 20, color: "var(--px-color-primary)" }}>●</span>}
    </div>
  );
}
