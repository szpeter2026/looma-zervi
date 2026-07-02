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
import { createAuthApi, createQuotaApi, type UserProfile, type QuotaResponse } from "@looma/shared-core";
import { createSaasApiClient } from "../../api/saasApiClient";

export type QuotaInfo = QuotaResponse;

function getClient() {
  return createSaasApiClient();
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
  /** 写入新 JWT 并刷新 profile/quota（tier 升级等场景） */
  applySessionToken: (accessToken: string) => Promise<void>;
  /** 从 PlanetX 共享的 looma_token 自动登录 */
  tryAutoLogin: () => Promise<void>;
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
        const resp = await api.login({ email, password });
        set({ token: resp.access_token, user: resp.user as UserProfile, isAuthenticated: true, isLoading: false });
        // 写入共享 localStorage，PlanetX 侧也可识别（为未来双向 SSO 做准备）
        getClient().setToken(resp.access_token);
        // 登录后拉取完整 profile（含 is_early_adopter / created_at）
        await get().fetchProfile();
        await get().fetchQuota();
      },

      register: async (email, password, name) => {
        set({ isLoading: true });
        const api = getAuthApi();
        const resp = await api.register({ email, password, name });
        set({ token: resp.access_token, user: resp.user as UserProfile, isAuthenticated: true, isLoading: false });
        getClient().setToken(resp.access_token);
        await get().fetchProfile();
        await get().fetchQuota();
      },

      logout: () => {
        // 清除共享 localStorage token
        getClient().clearToken();
        set({ token: null, user: null, quota: null, isAuthenticated: false, isLoading: false });
      },

      fetchProfile: async () => {
        const token = get().token;
        if (!token) return;
        try {
          const api = getAuthApi();
          const profile = await api.profile();
          set({ user: profile, isAuthenticated: true });
        } catch {
          get().logout();
        }
      },

      fetchQuota: async () => {
        if (!get().token) return;
        try {
          const api = createQuotaApi(getClient());
          const data = await api.get();
          set({ quota: data });
        } catch {
          /* ignore */
        }
      },

      applySessionToken: async (accessToken: string) => {
        getClient().setToken(accessToken);
        set({ token: accessToken, isAuthenticated: true });
        await get().fetchProfile();
        await get().fetchQuota();
      },

      /** 从 PlanetX 共享的 looma_token 自动登录（C→B 互通核心） */
      tryAutoLogin: async () => {
        const state = get();
        if (state.token && state.isAuthenticated) return;

        const sharedToken = localStorage.getItem("looma_token") || state.token;
        if (!sharedToken) return;

        set({ token: sharedToken, isLoading: true });
        try {
          await get().fetchProfile();
          await get().fetchQuota();
        } catch {
          get().logout();
        } finally {
          set({ isLoading: false });
        }
      },
    }),
    {
      name: "saas-auth",
      partialize: (state) => ({ token: state.token }),
    }
  )
);
