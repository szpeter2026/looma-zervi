/**
 * Auth API factory.
 * Shared by both brands - both need login/register/profile.
 *
 * NOTE: This does NOT aggregate other API modules (chat, docs, resume, etc.)
 * Each brand defines its own additional API modules in its own package.
 */
import { ApiClient } from "./ApiClient";
import type {
  LoginResponse,
  RegisterResponse,
  WechatLoginResponse,
  UserProfile,
} from "../types/auth";

export function createAuthApi(client: ApiClient) {
  return {
    /** Web email/password registration */
    register: (email: string, password: string, name?: string) =>
      client.post<RegisterResponse>("/v1/auth/register", { email, password, name }),

    /** Web email/password login */
    login: (email: string, password: string) =>
      client.post<LoginResponse>("/v1/auth/login", { email, password }),

    /** WeChat miniprogram login (openid -> JWT) */
    wechatLogin: (code: string) =>
      client.post<WechatLoginResponse>("/v1/auth/wechat", { code }),

    /** Bind WeChat account to existing user */
    bind: (code: string) =>
      client.post<{ message: string }>("/v1/auth/bind", { code }),

    /** Get current user profile */
    getProfile: () =>
      client.get<UserProfile>("/v1/auth/profile"),

    /** Refresh JWT token */
    refresh: () =>
      client.post<{ access_token: string; expires_in: number }>("/v1/auth/refresh"),

    /** [OPTIONAL] Supabase JWT -> looma JWT bridge (MVP: 501) */
    bridge: (supabaseJwt: string) =>
      client.post<LoginResponse>("/v1/auth/bridge", { token: supabaseJwt }),
  };
}
