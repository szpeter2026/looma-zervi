import type { ApiClient } from "../api/ApiClient";
import { createComplianceApi } from "../api/createApi";
import type { ConsentScope } from "../types/compliance";

export function isConsentRequiredError(err: unknown): err is { status: number; body: { error: string; required_scope?: ConsentScope } } {
  if (!err || typeof err !== "object") return false;
  const e = err as { status?: number; body?: { error?: string } };
  return e.status === 403 && e.body?.error === "consent_required";
}

/** Check whether user has already granted a scope. */
export async function hasConsent(client: ApiClient, scope: ConsentScope): Promise<boolean> {
  const api = createComplianceApi(client);
  const res = await api.status();
  return Boolean(res.status[scope]);
}

/** Grant a single consent scope. */
export async function grantConsent(client: ApiClient, scope: ConsentScope): Promise<void> {
  const api = createComplianceApi(client);
  await api.grant(scope);
}

/**
 * Ensure consent before a sensitive action.
 * Returns true if granted (existing or newly granted), false if user declined or API failed.
 */
export async function ensureConsent(
  client: ApiClient,
  scope: ConsentScope,
  prompt: (scope: ConsentScope) => Promise<boolean>,
): Promise<boolean> {
  try {
    if (await hasConsent(client, scope)) return true;
  } catch {
    return false;
  }
  const accepted = await prompt(scope);
  if (!accepted) return false;
  try {
    await grantConsent(client, scope);
    return true;
  } catch {
    return false;
  }
}
