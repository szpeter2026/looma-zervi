/**
 * API route constants.
 * Centralized so both brands use the same paths.
 */

export const API_ROUTES = {
  // Auth
  AUTH_REGISTER: "/v1/auth/register",
  AUTH_LOGIN: "/v1/auth/login",
  AUTH_WECHAT: "/v1/auth/wechat",
  AUTH_BIND: "/v1/auth/bind",
  AUTH_PROFILE: "/v1/auth/profile",
  AUTH_REFRESH: "/v1/auth/refresh",
  AUTH_BRIDGE: "/v1/auth/bridge",

  // Game (Jason)
  GAME_PROFILE_SYNC: "/v1/game/profile-sync",
  GAME_PROFILE: "/v1/game/profile",
  GAME_MISSION_COMPLETE: "/v1/game/mission-complete",
  GAME_FLEET_CREATE: "/v1/game/fleet/create",
  GAME_FLEET_JOIN: "/v1/game/fleet/join",
  GAME_FLEET_MINE: "/v1/game/fleet/mine",

  // Enterprise (szbenyx)
  ENTERPRISE_USERS: "/v1/enterprise/users",
  ENTERPRISE_CANDIDATE: "/v1/enterprise/candidate",
  ENTERPRISE_INVITE: "/v1/enterprise/invite",
  ENTERPRISE_USAGE: "/v1/enterprise/usage",

  // Knowledge base
  ASK: "/v1/ask",

  // Jobs (szbenyx)
  JOBS_LIST: "/v1/jobs/",
  JOBS_MATCH: "/v1/jobs/match",

  // Resume (szbenyx)
  RESUME_UPLOAD: "/v1/resume/upload",
  RESUME_MINE: "/v1/resume/mine",

  // Reports (szbenyx)
  REPORTS_DAILY: "/v1/reports/daily",
  REPORTS_WEEKLY: "/v1/reports/weekly",
  REPORTS_MONTHLY: "/v1/reports/monthly",
  REPORTS_GENERATE: "/v1/reports/generate",

  // Referral (Jason)
  REFERRAL_GENERATE: "/v1/referral/generate",
  REFERRAL_MINE: "/v1/referral/mine",

  // Quota (joint)
  QUOTA: "/v1/quota",

  // Health
  HEALTH: "/health",
} as const;
