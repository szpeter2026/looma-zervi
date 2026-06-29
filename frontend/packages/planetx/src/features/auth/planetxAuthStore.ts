/**
 * PlanetX Auth Store - Zustand store for authentication state.
 * Owner: Jason
 *
 * Uses looma JWT (NOT Supabase).
 * Token is stored in localStorage.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";
import { createApiClient, createAuthApi, type User } from "@looma/shared-core";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:5000";

function getApi() {
  return createAuthApi(
    createApiClient({
      baseURL: API_BASE,
      getToken: () => usePlanetXAuthStore.getState().token,
      onUnauthorized: () => usePlanetXAuthStore.getState().logout(),
    })
  );
}

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => void;
  fetchProfile: () => Promise<void>;
}

export const usePlanetXAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (email, password) => {
        const api = getApi();
        const resp = await api.login(email, password);
        set({ token: resp.access_token, user: resp.user, isAuthenticated: true });
      },

      register: async (email, password, name) => {
        const api = getApi();
        const resp = await api.register(email, password, name);
        set({ token: resp.access_token, user: resp.user, isAuthenticated: true });
      },

      logout: () => {
        set({ token: null, user: null, isAuthenticated: false });
      },

      fetchProfile: async () => {
        const api = getApi();
        const profile = await api.getProfile();
        set({ user: profile });
      },
    }),
    {
      name: "planetx-auth",
      partialize: (state) => ({ token: state.token }),
    }
  )
);
