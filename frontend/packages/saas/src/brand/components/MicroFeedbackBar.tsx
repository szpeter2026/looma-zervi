/**
 * One-question micro feedback bar (内测 UX).
 */
import { useState } from "react";
import {
  createApiClient,
  createAnalyticsApi,
  getAnalyticsSessionId,
  type MicroFeedbackContext,
} from "@looma/shared-core";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:5000";

interface Props {
  context: MicroFeedbackContext;
  question: string;
  platform?: "tspace_web" | "planetx_web";
  shareCode?: string;
  getToken?: () => string | null;
}

export function MicroFeedbackBar({
  context,
  question,
  platform = "tspace_web",
  shareCode,
  getToken,
}: Props) {
  const [done, setDone] = useState(false);

  const submit = async (score: number) => {
    try {
      const client = createApiClient({
        baseURL: API_BASE,
        getToken: getToken ?? (() => null),
      });
      await createAnalyticsApi(client).microFeedback({
        context,
        score,
        session_id: getAnalyticsSessionId(),
        platform,
        share_code: shareCode,
      });
    } catch {
      /* best-effort */
    }
    setDone(true);
  };

  if (done) {
    return (
      <p className="text-xs text-center mt-3" style={{ color: "var(--color-text-muted)" }}>
        感谢反馈 ✨
      </p>
    );
  }

  return (
    <div
      className="mt-4 p-3 rounded-lg text-center"
      style={{ backgroundColor: "var(--color-bg-surface)", border: "1px solid var(--color-border)" }}
    >
      <p className="text-xs mb-2" style={{ color: "var(--color-text-secondary)" }}>
        {question}
      </p>
      <div className="flex justify-center gap-3">
        <button
          type="button"
          onClick={() => void submit(0)}
          className="px-4 py-1.5 rounded-lg text-sm border"
          style={{ borderColor: "var(--color-border)" }}
        >
          👎 不够
        </button>
        <button
          type="button"
          onClick={() => void submit(1)}
          className="px-4 py-1.5 rounded-lg text-sm border"
          style={{ borderColor: "var(--color-primary)", color: "var(--color-primary)" }}
        >
          👍 有用
        </button>
      </div>
    </div>
  );
}
