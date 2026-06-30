/**
 * Payment types — 与 backend/src/api/routes/payment_routes.py 对齐
 * Ownership: JOINT (dual-review required)
 */

import type { Tier } from "./auth";

/** 定价计划 */
export interface PaymentPlan {
  tier: Tier;
  name: string;
  price_monthly: number;
  features: string[];
}

/** GET /v1/payment/plans 响应 */
export interface PlansResponse {
  plans: PaymentPlan[];
}

/** GET /v1/payment/status 响应 */
export interface PaymentStatus {
  tier: Tier;
  plan: PaymentPlan;
  status: "active" | "expired" | "cancelled";
  expires_at: string | null;
}

/** POST /v1/payment/upgrade 请求 */
export interface UpgradeRequest {
  tier: "supporter" | "pro";
}

/** POST /v1/payment/upgrade 响应 */
export interface UpgradeResponse {
  tier: Tier;
  plan: PaymentPlan;
  status: string;
  message: string;
}
