import type { ConsentScope } from "@looma/shared-core";
import { CONSENT_SCOPE_DESCRIPTIONS, CONSENT_SCOPE_LABELS } from "@looma/shared-core";

interface ConsentModalProps {
  scope: ConsentScope;
  onAccept: () => void;
  onDecline: () => void;
}

/** PIPL 单独同意弹窗 — PlanetX C 端（星空主题） */
export default function ConsentModal({ scope, onAccept, onDecline }: ConsentModalProps) {
  const title = CONSENT_SCOPE_LABELS[scope];
  const description = CONSENT_SCOPE_DESCRIPTIONS[scope];

  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "rgba(5, 10, 30, 0.75)",
        padding: "16px",
      }}
      onClick={onDecline}
    >
      <div
        style={{
          maxWidth: "400px",
          width: "100%",
          background: "linear-gradient(145deg, #1a1f3a 0%, #0d1225 100%)",
          border: "1px solid rgba(120, 160, 255, 0.3)",
          borderRadius: "16px",
          padding: "24px",
          color: "#e8ecff",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ fontSize: "20px", marginBottom: "8px" }}>🛡️ 授权确认</div>
        <div style={{ fontSize: "15px", fontWeight: 600, marginBottom: "8px" }}>{title}</div>
        <p style={{ fontSize: "13px", lineHeight: 1.6, opacity: 0.85, marginBottom: "16px" }}>{description}</p>
        <p style={{ fontSize: "11px", opacity: 0.55, marginBottom: "20px" }}>
          单独同意后可继续使用该功能，您可随时在账户设置中撤回。
        </p>
        <div style={{ display: "flex", gap: "10px", justifyContent: "flex-end" }}>
          <button
            type="button"
            onClick={onDecline}
            style={{
              padding: "8px 16px",
              borderRadius: "8px",
              border: "1px solid rgba(255,255,255,0.2)",
              background: "transparent",
              color: "#aab",
              cursor: "pointer",
            }}
          >
            取消
          </button>
          <button
            type="button"
            onClick={onAccept}
            style={{
              padding: "8px 16px",
              borderRadius: "8px",
              border: "none",
              background: "linear-gradient(90deg, #6366f1, #8b5cf6)",
              color: "#fff",
              cursor: "pointer",
            }}
          >
            同意并继续
          </button>
        </div>
      </div>
    </div>
  );
}
