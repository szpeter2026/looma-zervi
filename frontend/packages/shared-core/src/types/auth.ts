/**
 * Auth-related type definitions.
 * These mirror the backend response structures exactly.
 * Backend changes must update these types first (dual review).
 */

export type Tier = "free" | "supporter" | "pro";
export type Role = "user" | "admin";

export interface User {
  id: string;
  email: string | null;
  name: string;
  tier: Tier;
  role: Role;
}

export interface UserProfile extends User {
  is_early_adopter: boolean;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: User;
}

export interface RegisterResponse extends LoginResponse {}

export interface WechatLoginResponse extends LoginResponse {}

export interface TokenPayload {
  sub: string;        // looma user_id
  iat: number;        // issued at (unix timestamp)
  exp: number;        // expiry (unix timestamp)
  iss: "looma";
  tier?: Tier;
  email?: string;
}
