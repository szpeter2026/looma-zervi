/**
 * Referral / growth type definitions.
 */

import type { Candidate } from "./enterprise";

export type ReferralPurpose = "referral" | "profile_share";

export interface CreateReferralRequest {
  purpose?: ReferralPurpose;
  tier_grant?: string;
}

export interface CreateReferralResponse {
  code: string;
  purpose?: ReferralPurpose;
  tier_grant?: string;
}

export interface UseReferralRequest {
  code: string;
}

export interface UseReferralResponse {
  consumed: boolean;
  code: string;
  tier_granted: string;
}

export interface ReferralCodeEntry {
  code: string;
  tier_grant?: string;
  purpose?: ReferralPurpose;
  used_by?: string | null;
  used_at?: string | null;
  created_at?: string;
}

export interface ProfileShareView {
  share_code: string;
  user_id: string;
  user_display: string;
  personality_type?: string;
  personality_detail?: Record<string, unknown> | string | null;
  xp: number;
  level: number;
}

export interface ImportShareRequest {
  share_code: string;
}

export interface ImportShareResponse extends Candidate {
  imported?: boolean;
}
