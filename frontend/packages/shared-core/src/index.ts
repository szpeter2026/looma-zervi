/**
 * @looma/shared-core entry point
 *
 * RULE: This package only contains contracts (types, API factory, constants).
 * It does NOT contain AuthGuard, Store, CSS, or UI components.
 * Changes to exports require dual review (Jason + szbenyx).
 */

// API
export { ApiClient, createApiClient } from "./api/ApiClient";
export { createAuthApi } from "./api/createApi";

// Types
export type {
  User,
  LoginResponse,
  RegisterResponse,
  WechatLoginResponse,
  UserProfile,
  TokenPayload,
} from "./types/auth";

export type {
  ApiResponse,
  PaginatedResponse,
  Pagination,
} from "./types/common";

export {
  BRAND,
  BRAND_PLANETX,
  BRAND_SAAS,
} from "./types/brand";

// Constants
export { QUOTA_LIMITS, TIER_ORDER } from "./constants/quota";
export { API_ROUTES } from "./constants/routes";

// Utils
export { formatDate, formatNumber, formatRelativeTime } from "./utils/format";
export { isValidEmail, isPasswordStrong } from "./utils/validation";
