/**
 * PlanetX AchievementPopup — pure UI component.
 * Shows a centered popup with bounceIn animation + claimPulse.
 */
import type { PlanetXAchievementPopupProps } from "./types";

export default function PlanetXAchievementPopup({
  visible,
  title,
  description,
  icon = "🏆",
  onClose,
}: PlanetXAchievementPopupProps) {
  if (!visible) return null;

  return (
    <>
      {/* Overlay */}
      <div
        onClick={onClose}
        style={{
          position: "fixed",
          inset: 0,
          background: "var(--px-modal-overlay)",
          zIndex: "var(--px-z-popup)",
        }}
      />
      {/* Popup */}
      <div
        className="px-anim-bounceIn"
        style={{
          position: "fixed",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          zIndex: "var(--px-z-popup)",
          maxWidth: "var(--px-modal-max-width)",
          width: "90%",
          textAlign: "center",
          background: "var(--px-modal-bg)",
          border: "var(--px-modal-border)",
          borderRadius: "var(--px-modal-radius)",
          padding: "var(--px-modal-padding)",
          boxShadow: "var(--px-modal-shadow)",
        }}
      >
        <div
          className="px-anim-claimPulse"
          style={{ fontSize: 48, marginBottom: "var(--px-spacing-sm)" }}
        >
          {icon}
        </div>
        <div
          style={{
            fontSize: "var(--px-font-size-lg)",
            fontWeight: "var(--px-font-weight-black)",
            color: "var(--px-color-gold)",
          }}
        >
          {title}
        </div>
        {description && (
          <div
            style={{
              fontSize: "var(--px-font-size-sm)",
              color: "var(--px-color-text-muted)",
              marginTop: "var(--px-spacing-xs)",
            }}
          >
            {description}
          </div>
        )}
      </div>
    </>
  );
}
