/**
 * @looma/shared-core entry point
 *
 * RULE: This package only contains contracts (types, API factory, constants, utils).
 * It does NOT contain AuthGuard, Store, CSS, or UI components.
 * Changes to exports require dual review (Jason + szbenyx).
 */

// API
export {
  ApiClient,
  createApiClient,
  ApiError,
  webStorageAdapter,
  wxStorageAdapter,
} from "./api/ApiClient";
export type {
  ApiClientConfig,
  StorageAdapter,
  RequestOptions,
} from "./api/ApiClient";

export {
  createAuthApi,
  createChatApi,
  createGameApi,
  createEnterpriseApi,
  createReferralApi,
  createResumeApi,
  createJobsApi,
  createReportsApi,
  createPaymentApi,
  createQuotaApi,
  createNarrativeApi,
  createAct1Api,
  createCreditApi,
  createAnalyticsApi,
  createComplianceApi,
} from "./api/createApi";

// Types
export type {
  Tier,
  Role,
  User,
  UserProfile,
  AuthResponse,
  LoginResponse,
  RegisterResponse,
  WechatLoginResponse,
  LoginRequest,
  RegisterRequest,
  WechatAuthRequest,
  WechatAuthResponse,
  QuotaRecord,
  QuotaResponse,
  TokenPayload,
} from "./types/auth";

export type {
  ChatMessage,
  DocSource,
  AskRequest,
  AskResponse,
  StreamCallbacks,
  RateRequest,
  LastQueryResponse,
} from "./types/chat";

export type {
  Identity,
  PersonalityType,
  TraitKey,
  QuizQuestion,
  QuizOption,
  RankName,
  MissionId,
  Mission,
  GameProfile,
  Fleet,
  FleetMember,
  GameScreen,
  SharePlatform,
  ProfileSyncRequest,
  MissionCompleteRequest,
  MissionCompleteResponse,
  CreateFleetRequest,
  JoinFleetRequest,
  FleetResponse,
  MyFleetResponse,
} from "./types/game";

export { RANK_NAMES, getRankName } from "./types/game";

// PlanetX game (quiz / personality / identity) — canonical for planetx + miniprogram
export type {
  Identity as PlanetXIdentity,
  TraitKey as PlanetXTraitKey,
  PersonalityType as PlanetXPersonalityType,
  QuizOption as PlanetXQuizOption,
  QuizQuestion as PlanetXQuizQuestion,
  PlanetXRankName,
  PlanetXMissionId,
  PlanetXGameScreen,
  PlanetXFleet,
} from "./types/planetx-game";

export {
  IDENTITY_LABELS,
  getPlanetXRankName,
} from "./types/planetx-game";

export { QUIZ_QUESTIONS } from "./constants/quiz";

export {
  PERSONALITY_MAP,
  PERSONALITY_FALLBACK_MAP,
} from "./constants/personality";

export { computePersonality, hydratePersonality } from "./utils/quiz";

export { getShareText } from "./utils/share";
export type { SharePlatform as PlanetXSharePlatform } from "./utils/share";

/** JWT localStorage key — G2 aligned (planetx / saas / portal) */
export const LOOMA_TOKEN_KEY = "looma_token";

export type {
  ParsedResume,
  ResumeExperience,
  ResumeEducation,
  ResumeProject,
  ResumeUploadResult,
  Job,
  JobMatchItem,
  JobMatchResult,
  JobMatchRequest,
  JobMatchResponse,
  ParsedJob,
  JobUploadResult,
  JobMatchScore,
  CreditAnalysis,
  CheckCompanyRequest,
} from "./types/resume";

export type {
  CreateEnterpriseRequest,
  JoinEnterpriseRequest,
  EnterpriseProfile,
  Candidate,
  AddCandidateRequest,
  AddCandidateResponse,
} from "./types/enterprise";

export type {
  CreateReferralRequest,
  CreateReferralResponse,
  UseReferralRequest,
  UseReferralResponse,
  ReferralCodeEntry,
  ProfileShareView,
  ImportShareRequest,
} from "./types/referral";

export type {
  Report,
  ReportType,
  ReportRequest,
  GenerateReportRequest,
  HealthStatus,
  PaginatedResponse,
  ApiError as ApiErrorType,
  Poem,
} from "./types/misc";

export type {
  PaymentPlan,
  PlansResponse,
  PaymentStatus,
  UpgradeRequest,
  UpgradeResponse,
} from "./types/payment";

export type {
  ApiResponse,
  Pagination,
  PaginatedResponse as CommonPaginatedResponse,
} from "./types/common";

export type {
  NarrativeDomain,
  NarrativeEventType,
  NarrativeStartRequest,
  NarrativeStartResponse,
  NarrativeEventRequest,
  NarrativeEndRequest,
  NarrativeFeedbackRequest,
  NarrativeStats,
  Act1DomainSummary,
  Act1Step,
  ConvergenceTexture,
  Act1ContentResponse,
  Act1ChoiceOption,
  Act1SessionState,
  Act1AdvanceResponse,
  Act1ChoiceRequest,
  Act1ChoiceResponse,
  Act1InitRequest,
} from "./types/narrative";

export {
  BRAND,
  BRAND_PLANETX,
  BRAND_SAAS,
} from "./types/brand";
export type { BrandId, BrandConfig } from "./types/brand";

// Constants
export {
  QUOTA_LIMITS,
  TIER_ORDER,
  TOP_N_LIMIT,
  RESOURCE_ASK,
  RESOURCE_JOB_MATCH,
  RESOURCE_RESUME_PARSE,
  RESOURCE_RAG,
} from "./constants/quota";

export { API_ROUTES } from "./constants/routes";

// Utils
export {
  formatDate,
  formatDateTime,
  formatNumber,
  formatRelativeTime,
  truncate,
  formatPercent,
  clamp,
} from "./utils/format";

export {
  isValidEmail,
  isPasswordStrong,
  isNotEmpty,
  isValidPhone,
  isValidUrl,
} from "./utils/validation";

export type {
  AnalyticsPlatform,
  ClosedLoopEventName,
  ProductEventPayload,
  MicroFeedbackContext,
  MicroFeedbackRequest,
  FunnelStatsResponse,
} from "./types/analytics";

export {
  CLOSED_LOOP_EVENTS,
  MICRO_FEEDBACK_CONTEXT,
  ANALYTICS_SESSION_KEY,
} from "./constants/analytics";

export {
  initAnalytics,
  getAnalyticsSessionId,
  trackEvent,
  flushEvents,
} from "./analytics/track";

export type {
  ConsentScope,
  ConsentRecord,
  ConsentStatusResponse,
  ConsentGrantResponse,
  ConsentRequiredResponse,
  ConsentRequiredError,
} from "./types/compliance";

export {
  CONSENT_SCOPE_LABELS,
  CONSENT_SCOPE_DESCRIPTIONS,
} from "./constants/compliance";

export {
  ensureConsent,
  grantConsent,
  hasConsent,
  isConsentRequiredError,
} from "./compliance/ensureConsent";
