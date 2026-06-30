/**
 * API route constants.
 * Centralized so both brands use the same paths and stay aligned with the Flask backend.
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

  // Quota (new top-level path; /v1/auth/quota kept as alias on backend)
  QUOTA: "/v1/quota",

  // Game
  GAME_PROFILE_SYNC: "/v1/game/profile-sync",
  GAME_PROFILE: "/v1/game/profile",
  GAME_MISSION_COMPLETE: "/v1/game/mission-complete",
  GAME_FLEET_CREATE: "/v1/game/fleet/create",
  GAME_FLEET_JOIN: "/v1/game/fleet/join",
  GAME_FLEET_MINE: "/v1/game/fleet/mine",
  GAME_FLEET_LEAVE: "/v1/game/fleet/leave",

  // Enterprise (T空间 B-end)
  ENTERPRISE_CREATE: "/v1/enterprise/create",
  ENTERPRISE_JOIN: "/v1/enterprise/join",
  ENTERPRISE_PROFILE: "/v1/enterprise/profile",
  ENTERPRISE_CANDIDATES: "/v1/enterprise/candidates",
  ENTERPRISE_CANDIDATES_ADD: "/v1/enterprise/candidates/add",

  // Ask / RAG / Feedback
  ASK: "/v1/ask",
  FEEDBACK_RATE: "/v1/feedback/rate",
  FEEDBACK_LAST_QUERY: "/v1/feedback/last-query",

  // Jobs
  JOBS_LIST: "/v1/jobs/list",
  JOBS_MATCH: "/v1/jobs/match",
  JOBS_UPLOAD: "/v1/jobs/upload",
  JOBS_PARSE: "/v1/jobs/parse",

  // Resume
  RESUME_PARSE: "/v1/resume/parse",
  RESUME_UPLOAD: "/v1/resume/upload",
  RESUME_IMPROVE: "/v1/resume/improve",

  // Reports
  REPORTS_GENERATE: "/v1/reports/generate",
  REPORTS_LIST: "/v1/reports/list",

  // Payment
  PAYMENT_PLANS: "/v1/payment/plans",
  PAYMENT_STATUS: "/v1/payment/status",
  PAYMENT_UPGRADE: "/v1/payment/upgrade",

  // Credit (company evaluation — tripod leg 3: Resume → Job → Company)
  CREDIT_ANALYZE: "/v1/credit/analyze",
  CREDIT_CHECK_COMPANY: "/v1/credit/check-company",

  // Health
  HEALTH: "/health",

  // Narrative (Phase 0 feedback collection)
  NARRATIVE_START: "/v1/narrative/start",
  NARRATIVE_EVENT: "/v1/narrative/event",
  NARRATIVE_END: "/v1/narrative/end",
  NARRATIVE_FEEDBACK: "/v1/narrative/feedback",
  NARRATIVE_STATS: "/v1/narrative/stats",

  // Act 1 State Machine (GDD §5.1)
  ACT1_INIT: "/v1/narrative/engine/act1/init",
  ACT1_STATE: "/v1/narrative/engine/act1/state",
  ACT1_ADVANCE: "/v1/narrative/engine/act1/advance",
  ACT1_CHOICE: "/v1/narrative/engine/act1/choice",
  ACT1_RESET: "/v1/narrative/engine/act1/reset",
  ACT1_CONTENT: "/v1/narrative/engine/act1/content",
} as const;
