/**
 * API factory functions.
 *
 * This module aggregates API modules previously scattered across endpoints.ts,
 * with all Supabase references removed and all paths aligned with the new Flask backend.
 */
import { ApiClient } from "./ApiClient";
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
import type { ParsedResume, JobMatchRequest, JobMatchResponse, Job } from "../types/resume";
import type { Report, GenerateReportRequest } from "../types/misc";
import { API_ROUTES } from "../constants/routes";

// ============================================================
// Auth API
// ============================================================
export function createAuthApi(client: ApiClient) {
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
export function createChatApi(client: ApiClient) {
  return {
    /** Non-streaming RAG question */
    ask: (payload: AskRequest) => client.post<AskResponse>(API_ROUTES.ASK, payload),

    /** SSE streaming RAG question with callbacks */
    askStream: async (payload: AskRequest, callbacks: StreamCallbacks) => {
      const stream = await client.stream(API_ROUTES.ASK, payload);
      const reader = stream.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed.startsWith("data:")) continue;
            const data = trimmed.slice(5).trim();
            if (data === "[DONE]") continue;
            try {
              const parsed = JSON.parse(data);
              callbacks.onMessage?.(parsed);
            } catch {
              callbacks.onMessage?.(data);
            }
          }
        }

        // Flush any remaining bytes
        if (buffer.trim()) {
          const trimmed = buffer.trim();
          if (trimmed.startsWith("data:")) {
            const data = trimmed.slice(5).trim();
            if (data !== "[DONE]") {
              try {
                callbacks.onMessage?.(JSON.parse(data));
              } catch {
                callbacks.onMessage?.(data);
              }
            }
          }
        }

        callbacks.onComplete?.();
      } catch (err) {
        callbacks.onError?.(err instanceof Error ? err : new Error(String(err)));
      } finally {
        reader.releaseLock();
      }
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
export function createGameApi(client: ApiClient) {
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
export function createEnterpriseApi(client: ApiClient) {
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
  };
}

// ============================================================
// Resume API
// ============================================================
export function createResumeApi(client: ApiClient) {
  return {
    /** Parse resume text into structured data */
    parse: (text: string) =>
      client.post<{ extracted: ParsedResume }>(API_ROUTES.RESUME_PARSE, { text }),

    /** Upload resume file (MVP: 501) */
    upload: (file: File) => client.upload(API_ROUTES.RESUME_UPLOAD, file, "file"),
  };
}

// ============================================================
// Jobs API
// ============================================================
export function createJobsApi(client: ApiClient) {
  return {
    /** List available jobs */
    list: () => client.get<{ jobs: Job[]; total: number }>(API_ROUTES.JOBS_LIST),

    /** Match resume to job listings */
    match: (payload: JobMatchRequest) =>
      client.post<JobMatchResponse>(API_ROUTES.JOBS_MATCH, payload),
  };
}

// ============================================================
// Reports API
// ============================================================
export function createReportsApi(client: ApiClient) {
  return {
    /** Generate a daily/weekly/monthly report */
    generate: (payload: GenerateReportRequest) =>
      client.post<Report>(API_ROUTES.REPORTS_GENERATE, payload),

    /** List generated reports */
    list: () => client.get<{ reports: Report[]; total: number }>(API_ROUTES.REPORTS_LIST),
  };
}

// ============================================================
// Narrative API (Phase 0 feedback collection)
// ============================================================
export function createNarrativeApi(client: ApiClient) {
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
// Payment API
// ============================================================
export function createPaymentApi(client: ApiClient) {
  return {
    /** List available pricing plans */
    plans: () => client.get<import("../types/payment").PlansResponse>(API_ROUTES.PAYMENT_PLANS),

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
export function createQuotaApi(client: ApiClient) {
  return {
    /** Get current quota usage (new path /v1/quota) */
    get: () => client.get<QuotaResponse>(API_ROUTES.QUOTA),
  };
}
