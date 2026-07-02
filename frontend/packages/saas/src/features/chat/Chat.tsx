/**
 * Chat - RAG knowledge base Q&A page.
 * Owner: szbenyx
 *
 * Pure CSS + Tailwind (no tdesign-react).
 * Uses local useChat hook with SSE streaming.
 */
import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import { createSaasApiClient } from "../../api/saasApiClient";
import { useConsent } from "../../compliance/useConsent";
import { useChat, type DocSource } from "./useChat";

type ChatMode = "chat" | "deepseek" | "fast";

function truncate(s: string, maxLen: number): string {
  return s.length > maxLen ? s.slice(0, maxLen) + "..." : s;
}

export default function Chat() {
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<ChatMode>("chat");
  const api = useMemo(() => createSaasApiClient(), []);
  const { ensureConsent, consentPrompt } = useConsent(() => api);
  const ensureAskConsent = useCallback(
    () => ensureConsent("ask_rag"),
    [ensureConsent],
  );
  const { messages, isStreaming, error, sendStream, clear } = useChat({
    mode,
    ensureAskConsent,
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = useCallback(async () => {
    const q = input.trim();
    if (!q || isStreaming) return;
    const allowed = await ensureConsent("ask_rag");
    if (!allowed) return;
    setInput("");
    sendStream(q);
  }, [input, isStreaming, sendStream, ensureConsent]);

  return (
    <>
    {consentPrompt}
    <div className="max-w-4xl mx-auto flex flex-col" style={{ height: "calc(100vh - 120px)" }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4 shrink-0">
        <h1 className="text-2xl font-bold" style={{ color: "var(--color-text-primary)" }}>
          智能问答
        </h1>
        <div className="flex items-center gap-3">
          {/* Mode switcher */}
          <div
            className="flex rounded-md overflow-hidden border text-xs"
            style={{ borderColor: "#e0e0e0" }}
          >
            {(["chat", "deepseek", "fast"] as ChatMode[]).map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className="px-3 py-1.5 border-none cursor-pointer transition-colors"
                style={{
                  backgroundColor: mode === m ? "var(--color-primary)" : "transparent",
                  color: mode === m ? "#fff" : "var(--color-text-secondary)",
                }}
              >
                {m === "chat" ? "对话" : m === "deepseek" ? "深度" : "快速"}
              </button>
            ))}
          </div>
          <button
            onClick={clear}
            className="text-sm bg-transparent border-none cursor-pointer p-1"
            style={{ color: "var(--color-text-muted)" }}
            title="清空对话"
          >
            ✕ 清空
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-2" style={{ color: "var(--color-text-muted)" }}>
            <span className="text-5xl opacity-20">💬</span>
            <p className="text-lg font-medium">开始一段新的对话</p>
            <p className="text-sm">基于您的知识库，获得智能、准确的回答</p>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
          >
            {/* Avatar */}
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-sm"
              style={{
                backgroundColor:
                  msg.role === "user" ? "var(--color-primary)" : "var(--color-bg-surface)",
                color: msg.role === "user" ? "#fff" : "var(--color-text-secondary)",
              }}
            >
              {msg.role === "user" ? "U" : "AI"}
            </div>

            {/* Message bubble */}
            <div
              className="max-w-[75%] rounded-xl px-4 py-3 text-sm leading-relaxed"
              style={{
                backgroundColor:
                  msg.role === "user" ? "var(--color-primary)" : "var(--color-bg-card)",
                color: msg.role === "user" ? "#fff" : "var(--color-text-primary)",
                boxShadow: msg.role === "user" ? "none" : "var(--shadow-sm)",
                border: msg.role === "user" ? "none" : "1px solid #f0f0f0",
              }}
            >
              <div className="whitespace-pre-wrap break-words">{msg.content}</div>

              {/* Sources */}
              {msg.role === "assistant" && msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 pt-2 border-t border-gray-100">
                  <p className="text-xs mb-1" style={{ color: "var(--color-text-muted)" }}>
                    引用来源：
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {msg.sources.map((s: DocSource, i: number) => (
                      <span
                        key={i}
                        className="text-xs px-2 py-0.5 rounded border"
                        style={{
                          borderColor: "#e0e0e0",
                          color: "var(--color-text-secondary)",
                        }}
                      >
                        {truncate(s.filename, 20)}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Error display */}
        {error && (
          <div className="text-center">
            <span
              className="inline-block text-sm px-3 py-1 rounded"
              style={{
                backgroundColor: "#fff0f0",
                color: "var(--color-danger)",
              }}
            >
              {error}
            </span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="mt-4 shrink-0">
        <div
          className="border-t mb-3"
          style={{ borderColor: "#e0e0e0" }}
        />
        <div className="flex gap-3 items-end">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder={isStreaming ? "AI 正在回复..." : "输入您的问题，Enter 发送，Shift+Enter 换行"}
            disabled={isStreaming}
            rows={1}
            className="flex-1 px-4 py-2.5 text-sm rounded-lg border resize-none outline-none transition-colors"
            style={{
              borderColor: "#e0e0e0",
              color: "var(--color-text-primary)",
              backgroundColor: "var(--color-bg-card)",
              minHeight: "44px",
              maxHeight: "120px",
            }}
            onFocus={(e) => {
              e.target.style.borderColor = "var(--color-primary)";
            }}
            onBlur={(e) => {
              e.target.style.borderColor = "#e0e0e0";
            }}
            onInput={(e) => {
              const el = e.target as HTMLTextAreaElement;
              el.style.height = "auto";
              el.style.height = Math.min(el.scrollHeight, 120) + "px";
            }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isStreaming}
            className="w-11 h-11 rounded-full flex items-center justify-center text-white border-none cursor-pointer shrink-0 disabled:opacity-40 transition-colors"
            style={{ backgroundColor: "var(--color-primary)" }}
            title="发送"
          >
            {isStreaming ? "⋯" : "↑"}
          </button>
        </div>
      </div>
    </div>
    </>
  );
}
