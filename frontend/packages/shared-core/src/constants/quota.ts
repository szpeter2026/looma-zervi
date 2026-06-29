/**
 * Quota constants shared across brands.
 */

export const QUOTA_LIMITS = {
  free: 30,
  supporter: 999999,
  pro: 999999,
} as const;

export const TIER_ORDER = {
  free: 0,
  supporter: 1,
  pro: 2,
} as const;
