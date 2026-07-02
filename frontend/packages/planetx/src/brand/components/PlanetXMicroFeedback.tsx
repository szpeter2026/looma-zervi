import { useState } from "react";
import {
  createAnalyticsApi,
  getAnalyticsSessionId,
  MICRO_FEEDBACK_CONTEXT,
} from "@looma/shared-core";
import { getApiClient } from "../../features/auth/planetxAuthStore";

export default function PlanetXMicroFeedback() {
  const [done, setDone] = useState(false);

  const submit = async (score: number) => {
    try {
      const client = getApiClient();
      await createAnalyticsApi(client).microFeedback({
        context: MICRO_FEEDBACK_CONTEXT.PLANETX_RESULT,
        score,
        session_id: getAnalyticsSessionId(),
        platform: "planetx_web",
      });
    } catch {
      /* best-effort */
    }
    setDone(true);
  };

  if (done) {
    return (
      <p style={{ textAlign: "center", fontSize: 12, color: "#888", marginTop: 12 }}>
        感谢反馈 ✨
      </p>
    );
  }

  return (
    <div
      style={{
        marginTop: 16,
        padding: 12,
        borderRadius: 12,
        background: "#0D0D1A",
        border: "1px solid rgba(255,255,255,0.1)",
        textAlign: "center",
      }}
    >
      <p style={{ fontSize: 12, color: "#B8B8C8", marginBottom: 8 }}>这份描述像你吗？</p>
      <div style={{ display: "flex", justifyContent: "center", gap: 12 }}>
        <button
          type="button"
          onClick={() => void submit(0)}
          style={{
            padding: "6px 16px",
            borderRadius: 8,
            fontSize: 13,
            border: "1px solid rgba(255,255,255,0.15)",
            background: "transparent",
            color: "#B8B8C8",
            cursor: "pointer",
          }}
        >
          👎 不太像
        </button>
        <button
          type="button"
          onClick={() => void submit(1)}
          style={{
            padding: "6px 16px",
            borderRadius: 8,
            fontSize: 13,
            border: "1px solid rgba(200,255,80,0.3)",
            background: "rgba(200,255,80,0.05)",
            color: "#C8FF50",
            cursor: "pointer",
          }}
        >
          👍 很像
        </button>
      </div>
    </div>
  );
}
