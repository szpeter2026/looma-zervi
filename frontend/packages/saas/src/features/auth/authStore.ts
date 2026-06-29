/**
 * SaaS Auth Store - Zustand store for authentication state.
 * Owner: szbenyx
 *
 * Uses looma JWT (NOT Supabase).
 * Token is stored in localStorage via persist middleware.
 * API paths are aligned with Flask backend.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";
import { createApiClient, createAuthApi, type UserProfile } from "@looma/shared-core";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:5000";

export interface QuotaInfo {
  tier: string;
  records: number;
  remaining: number;
  daily_limit: number;
}

/** Creates an ApiClient bound to the current auth store token. */
function getClient() {
  return createApiClient({
    baseURL: API_BASE,
    getToken: () => useSaasAuthStore.getState().token,
    onUnauthorized: () => useSaasAuthStore.getState().logout(),
  });
}

function getAuthApi() {
  return createAuthApi(getClient());
}

interface AuthState {
  token: string | null;
  user: UserProfile | null;
  quota: QuotaInfo | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => void;
  fetchProfile: () => Promise<void>;
  fetchQuota: () => Promise<void>;
}

export const useSaasAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      quota: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (email, password) => {
        set({ isLoading: true });
        const api = getAuthApi();
        const resp = await api.login(email, password);
        set({ token: resp.access_token, user: resp.user, isAuthenticated: true, isLoading: false });
      },

      register: async (email, password, name) => {
        set({ isLoading: true });
        const api = getAuthApi();
        const resp = await api.register(email, password, name);
        set({ token: resp.access_token, user: resp.user, isAuthenticated: true, isLoading: false });
      },

      logout: () => {
        set({ token: null, user: null, quota: null, isAuthenticated: false, isLoading: false });
      },

      fetchProfile: async () => {
        const token = get().token;
        if (!token) return;
        try {
          const api = getAuthApi();
          const profile = await api.getProfile();
          set({ user: profile, isAuthenticated: true });
        } catch {
          // Token expired/invalid -> logout
          set({ token: null, user: null, isAuthenticated: false });
        }
      },

      fetchQuota: async () => {
        if (!get().isAuthenticated) return;
        try {
          const client = getClient();
          const data = await client.get<QuotaInfo>("/v1/quota");
          set({ quota: data });
        } catch {
          // Silently ignore quota fetch failures
        }
      },
    }),
    {
      name: "saas-auth",
      partialize: (state) => ({ token: state.token }),
    }
  )
);
