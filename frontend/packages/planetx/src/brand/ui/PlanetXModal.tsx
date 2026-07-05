/**
 * PlanetX Modal — pure UI component.
 * Features: overlay, backdrop click close, size variants, centered.
 *
 * No store, no API — all data via props.
 */
import type { PlanetXModalProps } from "./types";

export default function PlanetXModal({
  isOpen,
  onClose,
  title,
  children,
  size = "md",
  showClose = true,
  overlayClickClose = true,
}: PlanetXModalProps) {
  if (!isOpen) return null;

  const sizeStyles: Record<string, React.CSSProperties> = {
    sm: { maxWidth: "320px", padding: "var(--px-spacing-lg)" },
    md: { maxWidth: "480px", padding: "var(--px-spacing-xl)" },
    lg: { maxWidth: "640px", padding: "var(--px-spacing-2xl)" },
    full: { maxWidth: "calc(100vw - 64px)", padding: "var(--px-spacing-2xl)" },
  };

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: "var(--px-z-modal)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "var(--px-spacing-lg)",
      }}
    >
      {/* Overlay */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: "var(--px-color-bg-overlay)",
          animation: "fadeIn 150ms ease-out",
        }}
        onClick={overlayClickClose ? onClose : undefined}
      />

      {/* Modal content */}
      <div
        style={{
          position: "relative",
          background: "var(--px-color-bg-card)",
          borderRadius: "var(--px-radius-lg)",
          border: "1px solid var(--px-border-gold)",
          boxShadow: "var(--px-modal-shadow)",
          width: "100%",
          maxHeight: "calc(100vh - 80px)",
          display: "flex",
          flexDirection: "column",
          animation: "slideUp 200ms ease-out",
          ...sizeStyles[size],
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        {(title || showClose) && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              paddingBottom: "var(--px-spacing-md)",
              borderBottom: "1px solid var(--px-border-default)",
              marginBottom: "var(--px-spacing-md)",
            }}
          >
            {title && (
              <h2
                style={{
                  margin: 0,
                  fontSize: "var(--px-font-size-xl)",
                  fontWeight: "var(--px-font-weight-bold)",
                  color: "var(--px-color-text-bright)",
                }}
              >
                {title}
              </h2>
            )}
            {showClose && (
              <button
                onClick={onClose}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--px-color-text-muted)",
                  cursor: "pointer",
                  padding: "var(--px-spacing-xs)",
                  borderRadius: "var(--px-radius-sm)",
                  fontSize: "1.5rem",
                  lineHeight: 1,
                  transition: "var(--px-anim-fast)",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.color = "var(--px-color-text)")}
                onMouseLeave={(e) => (e.currentTarget.style.color = "var(--px-color-text-muted)")}
              >
                ×
              </button>
            )}
          </div>
        )}

        {/* Body */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            maxHeight: "calc(100vh - 200px)",
          }}
        >
          {children}
        </div>

        {/* Footer (optional) */}
        {/* <div style={{ marginTop: "var(--px-spacing-lg)", display: "flex", gap: "var(--px-spacing-sm)", justifyContent: "flex-end" }}>
          <PlanetXButton variant="ghost" onClick={onClose}>Cancel</PlanetXButton>
          <PlanetXButton variant="primary">Confirm</PlanetXButton>
        </div> */}
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
}
