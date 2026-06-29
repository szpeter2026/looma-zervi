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
  createResumeApi,
  createJobsApi,
  createReportsApi,
  createQuotaApi,
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

export type {
  ParsedResume,
  ResumeExperience,
  ResumeEducation,
  ResumeProject,
  Job,
  JobMatchResult,
  JobMatchRequest,
  JobMatchResponse,
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
  ApiResponse,
  Pagination,
  PaginatedResponse as CommonPaginatedResponse,
} from "./types/common";

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
