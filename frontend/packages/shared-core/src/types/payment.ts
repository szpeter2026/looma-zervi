/**
 * Payment types — 与 backend/contracts/payment.v1.json 对齐
 * Ownership: JOINT (dual-review required)
 */

import type { Tier } from "./auth";

/** 区域码（与 payment.v1.json regions 一致） */
export type PaymentRegion = "CN" | "US";

/** 定价计划（GET /v1/payment/plans 单条） */
export interface PaymentPlan {
  tier: Tier;
  name: string;
  price_monthly: number;
  currency: string;
  region: PaymentRegion;
  plan_id: string;
  features: string[];
  upgradable?: boolean;
}

/** GET /v1/payment/plans 响应 */
export interface PlansResponse {
  region: PaymentRegion;
  currency: string;
  payment_provider: "wechat" | "stripe";
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
  region?: PaymentRegion;
}

/** POST /v1/payment/upgrade 响应 */
export interface UpgradeResponse {
  tier: Tier;
  plan: PaymentPlan;
  status: string;
  message: string;
  access_token?: string;
  token_type?: "bearer";
  expires_in?: number;
}

/** 契约内 supporter 区域定价（文档/测试对照用） */
export const PAYMENT_SUPPORTER_PRICES = {
  CN: { amount: 9.9, currency: "CNY" as const },
  US: { amount: 1.99, currency: "USD" as const },
} as const;

/** 契约内 pro 区域定价 */
export const PAYMENT_PRO_PRICES = {
  CN: { amount: 29.9, currency: "CNY" as const },
  US: { amount: 5.99, currency: "USD" as const },
} as const;

/** @deprecated 旧 Tatha basic → supporter */
export const DEPRECATED_TIER_ALIASES = {
  basic: "supporter",
} as const;
