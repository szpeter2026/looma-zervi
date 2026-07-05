/**
 * API factory functions for MiniProgram.
 * 
 * This is a simplified version of createApi.ts that works with MiniApiClient.
 * Removes Web-specific dependencies (File, ReadableStream, TextDecoder, etc.)
 */

import type {
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  WechatAuthRequest,
  WechatAuthResponse,
  UserProfile,
  QuotaResponse,
} from "../types/auth";
import type {
  AskRequest,
  AskResponse,
  StreamCallbacks,
  RateRequest,
  LastQueryResponse,
} from "../types/chat";
import type {
  GameProfile,
  MissionCompleteRequest,
  MissionCompleteResponse,
  CreateFleetRequest,
  FleetResponse,
  JoinFleetRequest,
  MyFleetResponse,
  ProfileSyncRequest,
} from "../types/game";
import type {
  CreateEnterpriseRequest,
  EnterpriseProfile,
  JoinEnterpriseRequest,
  Candidate,
  AddCandidateRequest,
  AddCandidateResponse,
} from "../types/enterprise";
import type { ParsedResume, JobMatchRequest, JobMatchResponse, Job, ParsedJob, CreditAnalysis, CheckCompanyRequest } from "../types/resume";
import type { Report, GenerateReportRequest } from "../types/misc";
import { API_ROUTES } from "../constants/routes";

// 简化的 API 客户端接口，兼容 MiniApiClient
export interface MiniApiClientInterface {
  get<T = any>(url: string, params?: Record<string, any>, options?: any): Promise<T>;
  post<T = any>(url: string, data?: any, options?: any): Promise<T>;
  put<T = any>(url: string, data?: any, options?: any): Promise<T>;
  patch<T = any>(url: string, data?: any, options?: any): Promise<T>;
  delete<T = any>(url: string, options?: any): Promise<T>;
  stream?(url: string, data?: any, callbacks?: any, options?: any): Promise<void>;
  upload?(url: string, file: any, fieldName?: string, options?: any): Promise<any>;
}

// ============================================================
// Auth API
// ============================================================
export function createAuthApi(client: MiniApiClientInterface) {
  return {
    /** Web email/password registration */
    register: (payload: RegisterRequest) =>
      client.post<AuthResponse>(API_ROUTES.AUTH_REGISTER, payload),

    /** Web email/password login */
    login: (payload: LoginRequest) =>
      client.post<AuthResponse>(API_ROUTES.AUTH_LOGIN, payload),

    /** WeChat miniprogram login (wx.login code -> looma JWT) */
    wechat: (payload: WechatAuthRequest) =>
      client.post<WechatAuthResponse>(API_ROUTES.AUTH_WECHAT, payload),

    /** Bind WeChat account to existing email user */
    bind: (code: string) =>
      client.post<{ message: string }>(API_ROUTES.AUTH_BIND, { code }),

    /** Get current user profile */
    profile: () => client.get<UserProfile>(API_ROUTES.AUTH_PROFILE),

    /** Refresh JWT token */
    refresh: () =>
      client.post<{ access_token: string; token_type: "bearer"; expires_in: number }>(
        API_ROUTES.AUTH_REFRESH
      ),

    /** Bridge endpoint (MVP returns 501; no Supabase dependency) */
    bridge: () =>
      client.post<{ error: string; message: string }>(API_ROUTES.AUTH_BRIDGE),

    /** Get current quota usage */
    quota: () => client.get<QuotaResponse>(API_ROUTES.QUOTA),
  };
}

// ============================================================
// Chat / Ask API
// ============================================================
export function createChatApi(client: MiniApiClientInterface) {
  return {
    /** Non-streaming RAG question */
    ask: (payload: AskRequest) => client.post<AskResponse>(API_ROUTES.ASK, payload),

    /** SSE streaming RAG question with callbacks - not supported in miniprogram */
    askStream: async (_payload: AskRequest, _callbacks: StreamCallbacks) => {
      throw new Error('Streaming not supported in miniprogram');
    },

    /** Rate a previous query */
    rate: (payload: RateRequest) =>
      client.post<{ ok: boolean; query_id: number; rating: number }>(API_ROUTES.FEEDBACK_RATE, payload),

    /** Get user's last query ID */
    lastQuery: () => client.get<LastQueryResponse>(API_ROUTES.FEEDBACK_LAST_QUERY),
  };
}

// ============================================================
// Game API
// ============================================================
export function createGameApi(client: MiniApiClientInterface) {
  return {
    /** Sync personality test result to backend */
    profileSync: (payload: ProfileSyncRequest) =>
      client.post<GameProfile>(API_ROUTES.GAME_PROFILE_SYNC, payload),

    /** Get current game profile (XP + level + personality) */
    profile: () => client.get<GameProfile>(API_ROUTES.GAME_PROFILE),

    /** Complete a mission and earn XP */
    missionComplete: (payload: MissionCompleteRequest) =>
      client.post<MissionCompleteResponse>(API_ROUTES.GAME_MISSION_COMPLETE, payload),

    /** Create a new fleet */
    createFleet: (payload: CreateFleetRequest) =>
      client.post<FleetResponse>(API_ROUTES.GAME_FLEET_CREATE, payload),

    /** Join an existing fleet */
    joinFleet: (payload: JoinFleetRequest) =>
      client.post<{ message: string; fleet_id: string; fleet_name: string; captain_id: string; member_count: number }>(
        API_ROUTES.GAME_FLEET_JOIN,
        payload
      ),

    /** Get current user's fleet */
    myFleet: () => client.get<MyFleetResponse>(API_ROUTES.GAME_FLEET_MINE),

    /** Leave current fleet */
    leaveFleet: () => client.post<{ message: string }>(API_ROUTES.GAME_FLEET_LEAVE),
  };
}

// ============================================================
// Enterprise API (T空间 B-end)
// ============================================================
export function createEnterpriseApi(client: MiniApiClientInterface) {
  return {
    /** Create a new enterprise */
    create: (payload: CreateEnterpriseRequest) =>
      client.post<{ id: string; name: string; domain: string; role: string }>(
        API_ROUTES.ENTERPRISE_CREATE,
        payload
      ),

    /** Join an existing enterprise */
    join: (payload: JoinEnterpriseRequest) =>
      client.post<{ enterprise_id: string; role: string }>(API_ROUTES.ENTERPRISE_JOIN, payload),

    /** Get current user's enterprise profile */
    profile: () => client.get<EnterpriseProfile>(API_ROUTES.ENTERPRISE_PROFILE),

    /** List candidates for the enterprise */
    candidates: () => client.get<{ candidates: Candidate[] }>(API_ROUTES.ENTERPRISE_CANDIDATES),

    /** Add a candidate to the enterprise */
    addCandidate: (payload: AddCandidateRequest) =>
      client.post<AddCandidateResponse>(API_ROUTES.ENTERPRISE_CANDIDATES_ADD, payload),

    /** Get candidate detail by ID */
    getCandidate: (candidateId: string) =>
      client.get<Candidate>(`${API_ROUTES.ENTERPRISE_CANDIDATE}/${candidateId}`),

    /** Import candidate from PlanetX profile share code */
    importFromShare: (shareCode: string) =>
      client.post<Candidate>(API_ROUTES.ENTERPRISE_CANDIDATES_IMPORT_SHARE, {
        share_code: shareCode,
      }),
  };
}

// ============================================================
// Referral API (growth + profile share)
// ============================================================
export function createReferralApi(client: MiniApiClientInterface) {
  return {
    /** Create invite or profile share code */
    create: (payload?: import("../types/referral").CreateReferralRequest) =>
      client.post<import("../types/referral").CreateReferralResponse>(
        API_ROUTES.REFERRAL_CREATE,
        payload ?? {},
      ),

    /** Consume a referral invite code (not profile_share) */
    use: (code: string) =>
      client.post<import("../types/referral").UseReferralResponse>(API_ROUTES.REFERRAL_USE, {
        code,
      }),

    /** List codes created by current user */
    myCodes: () =>
      client.get<{ codes: import("../types/referral").ReferralCodeEntry[] }>(
        API_ROUTES.REFERRAL_MY_CODES,
      ),

    /** Public: view personality profile by share code (no auth required) */
    profileView: (code: string) =>
      client.get<import("../types/referral").ProfileShareView>(
        `${API_ROUTES.REFERRAL_PROFILE_VIEW}/${encodeURIComponent(code)}`,
      ),
  };
}

// ============================================================
// Resume API (miniprogram不支持文件上传)
// ============================================================
export function createResumeApi(client: MiniApiClientInterface) {
  return {
    /** Parse resume text into structured data */
    parse: (text: string) =>
      client.post<{ extracted: ParsedResume }>(API_ROUTES.RESUME_PARSE, { text }),

    /** Upload resume file for AI parsing - not supported in miniprogram */
    upload: (_file: any) => {
      throw new Error('File upload not supported in miniprogram');
    },
  };
}

// ============================================================
// Jobs API (miniprogram不支持文件上传)
// ============================================================
export function createJobsApi(client: MiniApiClientInterface) {
  return {
    /** List available jobs (persisted + mock fallback) */
    list: () => client.get<{ jobs: Job[]; total: number }>(API_ROUTES.JOBS_LIST),

    /** Upload JD file for AI parsing - not supported in miniprogram */
    upload: (_file: any) => {
      throw new Error('File upload not supported in miniprogram');
    },

    /** Parse plain JD text into structured data */
    parse: (text: string) =>
      client.post<{ parsed: ParsedJob }>(API_ROUTES.JOBS_PARSE, { text }),

    /** Match resume to job listings (with optional job_id filter) */
    match: (payload: JobMatchRequest & { job_id?: string; job_description?: string }) =>
      client.post<JobMatchResponse>(API_ROUTES.JOBS_MATCH, payload),
  };
}

// ============================================================
// Reports API
// ============================================================
export function createReportsApi(client: MiniApiClientInterface) {
  return {
    /** Generate a daily/weekly/monthly report */
    generate: (payload: GenerateReportRequest) =>
      client.post<Report>(API_ROUTES.REPORTS_GENERATE, payload),

    /** List generated reports */
    list: () => client.get<{ reports: Report[]; total: number }>(API_ROUTES.REPORTS_LIST),
  };
}

// ============================================================
// Credit API (Company evaluation — tripod leg 3)
// ============================================================
export function createCreditApi(client: MiniApiClientInterface) {
  return {
    /** Parse raw credit report text via LLM */
    analyze: (text: string) =>
      client.post<{ extracted: CreditAnalysis }>(API_ROUTES.CREDIT_ANALYZE, { text }),

    /** Evaluate a company by name (post-match flow) */
    checkCompany: (payload: CheckCompanyRequest) =>
      client.post<{ extracted: CreditAnalysis }>(API_ROUTES.CREDIT_CHECK_COMPANY, payload),
  };
}

// ============================================================
// Narrative API (Phase 0 feedback collection)
// ============================================================
export function createNarrativeApi(client: MiniApiClientInterface) {
  return {
    /** Start a new narrative session */
    start: (payload: import("../types/narrative").NarrativeStartRequest) =>
      client.post<import("../types/narrative").NarrativeStartResponse>(
        API_ROUTES.NARRATIVE_START,
        payload,
      ),

    /** Log a narrative event */
    event: (payload: import("../types/narrative").NarrativeEventRequest) =>
      client.post<{ ok: boolean }>(API_ROUTES.NARRATIVE_EVENT, payload),

    /** Mark session complete or abandoned */
    end: (payload: import("../types/narrative").NarrativeEndRequest) =>
      client.post<{ ok: boolean }>(API_ROUTES.NARRATIVE_END, payload),

    /** Submit convergence-point qualitative feedback */
    feedback: (payload: import("../types/narrative").NarrativeFeedbackRequest) =>
      client.post<{ ok: boolean }>(API_ROUTES.NARRATIVE_FEEDBACK, payload),

    /** Admin: get aggregated Phase 0 metrics */
    stats: () =>
      client.get<import("../types/narrative").NarrativeStats>(API_ROUTES.NARRATIVE_STATS),
  };
}

// ============================================================
// Act 1 State Machine API (GDD §5.1)
// ============================================================
export function createAct1Api(client: MiniApiClientInterface) {
  return {
    /** Initialize Act 1 session with a domain */
    init: (payload: import("../types/narrative").Act1InitRequest) =>
      client.post<import("../types/narrative").Act1SessionState>(
        API_ROUTES.ACT1_INIT,
        payload,
      ),

    /** Get current Act 1 state */
    state: (sessionId: string) =>
      client.get<import("../types/narrative").Act1SessionState>(
        `${API_ROUTES.ACT1_STATE}?session_id=${encodeURIComponent(sessionId)}`,
      ),

    /** Advance to next step */
    advance: (sessionId: string) =>
      client.post<import("../types/narrative").Act1AdvanceResponse>(
        API_ROUTES.ACT1_ADVANCE,
        { session_id: sessionId },
      ),

    /** Make a choice at step 3 */
    choice: (payload: import("../types/narrative").Act1ChoiceRequest) =>
      client.post<import("../types/narrative").Act1ChoiceResponse>(
        API_ROUTES.ACT1_CHOICE,
        payload,
      ),

    /** Reset session (hard=true clears domain) */
    reset: (sessionId: string, hard = false) =>
      client.post<{ ok: boolean }>(
        API_ROUTES.ACT1_RESET,
        { session_id: sessionId, hard },
      ),

    /** Get Act 1 content library */
    content: (domain?: string) =>
      client.get<import("../types/narrative").Act1ContentResponse>(
        domain
          ? `${API_ROUTES.ACT1_CONTENT}?domain=${encodeURIComponent(domain)}`
          : API_ROUTES.ACT1_CONTENT,
      ),
  };
}

// ============================================================
// Payment API
// ============================================================
export function createPaymentApi(client: MiniApiClientInterface) {
  return {
    /** List available pricing plans (?region=CN|US) */
    plans: (region?: import("../types/payment").PaymentRegion) => {
      const query = region ? `?region=${region}` : "";
      return client.get<import("../types/payment").PlansResponse>(
        `${API_ROUTES.PAYMENT_PLANS}${query}`,
      );
    },

    /** Get current user subscription status */
    status: () => client.get<import("../types/payment").PaymentStatus>(API_ROUTES.PAYMENT_STATUS),

    /** Upgrade tier (stub: no real payment) */
    upgrade: (tier: "supporter" | "pro") =>
      client.post<import("../types/payment").UpgradeResponse>(API_ROUTES.PAYMENT_UPGRADE, { tier }),
  };
}

// ============================================================
// Quota API
// ============================================================
export function createQuotaApi(client: MiniApiClientInterface) {
  return {
    /** Get current quota usage (new path /v1/quota) */
    get: () => client.get<QuotaResponse>(API_ROUTES.QUOTA),
  };
}

// ============================================================
// Analytics API (内测闭环漏斗)
// ============================================================
export function createAnalyticsApi(client: MiniApiClientInterface) {
  return {
    logEvents: (events: import("../types/analytics").ProductEventPayload[]) =>
      client.post<{ ok: boolean; ingested: number }>(API_ROUTES.ANALYTICS_EVENTS, { events }),

    funnel: (days = 30) =>
      client.get<import("../types/analytics").FunnelStatsResponse>(
        API_ROUTES.ANALYTICS_FUNNEL,
        { days },
      ),

    microFeedback: (payload: import("../types/analytics").MicroFeedbackRequest) =>
      client.post<{ ok: boolean; id: number }>(API_ROUTES.FEEDBACK_MICRO, payload),
  };
}

// ============================================================
// Compliance API (PIPL consent gate)
// ============================================================
export function createComplianceApi(client: MiniApiClientInterface) {
  return {
    grant: (scope: import("../types/compliance").ConsentScope, purpose?: string) =>
      client.post<import("../types/compliance").ConsentGrantResponse>(
        API_ROUTES.COMPLIANCE_CONSENT_GRANT,
        { scope, purpose },
      ),

    grantBatch: (scopes: import("../types/compliance").ConsentScope[]) =>
      client.post<import("../types/compliance").ConsentGrantResponse>(
        API_ROUTES.COMPLIANCE_CONSENT_GRANT,
        { scopes },
      ),

    revoke: (scope: import("../types/compliance").ConsentScope) =>
      client.post<{ revoked: boolean; consent_id?: string; reason?: string }>(
        API_ROUTES.COMPLIANCE_CONSENT_REVOKE,
        { scope },
      ),

    status: () =>
      client.get<import("../types/compliance").ConsentStatusResponse>(
        API_ROUTES.COMPLIANCE_CONSENT_STATUS,
      ),

    required: () =>
      client.get<import("../types/compliance").ConsentRequiredResponse>(
        API_ROUTES.COMPLIANCE_CONSENT_REQUIRED,
      ),
  };
}