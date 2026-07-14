/**
 * useChatNonStreaming - Non-streaming chat for SaaS RAG knowledge base.
 * Replacement for useChat to fix contract inconsistency with backend.
 * Owner: Jason (for MVP pressure test fix)
 *
 * Uses createChatApi().ask() instead of SSE streaming.
 * Backend compatibility: matches mini-program and shared-core contract.
 */
import { useState, useCallback, useRef, useMemo } from "react";
import { createSaasApiClient } from "../../api/saasApiClient";
import { createChatApi, type DocSource as ApiDocSource } from "@looma/shared-core";

const RETRY_DELAYS = [1000, 2000, 5000];
const MAX_RETRIES = 3;

export interface DocSource {
  filename: string;
  chunk_id?: string;
  score?: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  sources?: DocSource[];
}

interface UseChatNonStreamingOptions {
  mode?: "chat" | "deepseek" | "fast";
  top_k?: number;
  /** Pre-check / retry when backend returns consent_required */
  ensureAskConsent?: () => Promise<boolean>;
}

let _uid = 0;
function uid(): string {
  return `msg_${Date.now()}_${++_uid}`;
}

function mapSources(sources?: ApiDocSource[]): DocSource[] | undefined {
  if (!sources?.length) return undefined;
  return sources.map((s, i) => ({
    filename: s.chunk_text?.slice(0, 80) || `Source ${i + 1}`,
    score: s.score,
  }));
}

export function useChatNonStreaming(options: UseChatNonStreamingOptions = {}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [quotaExhausted, setQuotaExhausted] = useState(false);
  const retryCountRef = useRef(0);
  
  const apiClient = useMemo(() => createSaasApiClient(), []);
  const chatApi = useMemo(() => createChatApi(apiClient), [apiClient]);

  /** Non-streaming request using createChatApi().ask() */
  const send = useCallback(
    async (query: string) => {
      setError(null);
      setQuotaExhausted(false);
      setIsLoading(true);
      retryCountRef.current = 0;

      const userMsg: ChatMessage = {
        id: uid(),
        role: "user",
        content: query,
        created_at: new Date().toISOString(),
      };
      const assistantId = uid();

      setMessages((prev) => [
        ...prev,
        userMsg,
        {
          id: assistantId,
          role: "assistant",
          content: "",
          created_at: new Date().toISOString(),
        },
      ]);

      const attemptRequest = async (): Promise<void> => {
        try {
          const response = await chatApi.ask({
            query,
            session_history: messages.slice(-10).map((m) => ({
              role: m.role,
              content: m.content,
            })),
          });

          // Update assistant message with full answer
          setMessages((prev) =>
            prev.map((m): ChatMessage =>
              m.id === assistantId
                ? {
                    ...m,
                    content: response.answer,
                    sources: mapSources(response.sources),
                  }
                : m
            )
          );

          setIsLoading(false);
        } catch (err: any) {
          const errMsg = err.message || "请求失败";
          const errData = err.data || {};
          
          // Handle consent required
          if (
            err.status === 403 &&
            errData.error === "consent_required" &&
            options.ensureAskConsent
          ) {
            const allowed = await options.ensureAskConsent();
            if (allowed) return attemptRequest();
            setError(errData.message || "需要授权后才能使用 AI 问答");
            setIsLoading(false);
            return;
          }

          // Handle quota exhausted (429)
          if (
            err.status === 429 &&
            errData.error === "quota_exceeded"
          ) {
            setError(errData.message || "当日配额已用尽");
            setQuotaExhausted(true);
            setIsLoading(false);
            return;
          }

          // Retry logic
          if (retryCountRef.current < MAX_RETRIES) {
            const delay = RETRY_DELAYS[retryCountRef.current] ?? 5000;
            retryCountRef.current++;
            setError(`请求失败，${delay / 1000}s 后重试 (${retryCountRef.current}/${MAX_RETRIES})...`);
            await new Promise((r) => setTimeout(r, delay));
            setError(null);
            return attemptRequest();
          }

          setError(errMsg);
          setIsLoading(false);
        }
      };

      await attemptRequest();
    },
    [messages, options.mode, options.top_k, options.ensureAskConsent, chatApi]
  );

  const clear = useCallback(() => {
    setMessages([]);
    setError(null);
    setQuotaExhausted(false);
    setIsLoading(false);
  }, []);

  const resetQuotaError = useCallback(() => {
    setError(null);
    setQuotaExhausted(false);
  }, []);

  return { 
    messages, 
    isStreaming: isLoading, // Keep same interface as useChat
    error, 
    quotaExhausted,
    sendStream: send, // Keep same interface as useChat
    clear,
    resetQuotaError,
  };
}