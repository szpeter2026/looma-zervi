/**
 * Live backend helpers for Playwright E2E (real Flask API, no mocks).
 */

export const API_BASE = process.env.E2E_API_BASE ?? "http://127.0.0.1:5200";
export const SAAS_BASE = process.env.E2E_SAAS_BASE ?? "http://localhost:5174";
export const PLANETX_BASE = process.env.E2E_PLANETX_BASE ?? "http://localhost:5173";

const TEST_PASS = "e2e-test-pass-123";

export interface SeededSeeker {
  email: string;
  password: string;
  token: string;
  shareCode: string;
  personalityName: string;
}

async function apiJson<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers as Record<string, string>),
    },
  });
  if (!resp.ok) {
    const body = await resp.text();
    throw new Error(`API ${init.method ?? "GET"} ${path} failed (${resp.status}): ${body}`);
  }
  return resp.json() as Promise<T>;
}

/** Register seeker, sync profile, create profile_share code. */
export async function seedSeekerWithShareCode(
  suffix = String(Date.now()),
): Promise<SeededSeeker> {
  const email = `e2e-seeker-${suffix}@test.local`;
  const password = TEST_PASS;
  const personalityName = "星云艺术家";
  const detail = JSON.stringify({
    name: personalityName,
    emoji: "🎨",
    tagline: "E2E test",
    desc: "Playwright seeded profile",
    traits: ["创造力"],
  });

  const reg = await apiJson<{ access_token: string }>("/v1/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, name: "E2ESeeker" }),
  });

  await apiJson("/v1/game/profile-sync", {
    method: "POST",
    headers: { Authorization: `Bearer ${reg.access_token}` },
    body: JSON.stringify({ personality_type: personalityName, personality_detail: detail }),
  });

  const share = await apiJson<{ code: string }>("/v1/referral/create", {
    method: "POST",
    headers: { Authorization: `Bearer ${reg.access_token}` },
    body: JSON.stringify({ purpose: "profile_share" }),
  });

  return {
    email,
    password,
    token: reg.access_token,
    shareCode: share.code,
    personalityName,
  };
}

export function uniqueHrEmail(suffix = String(Date.now())): string {
  return `e2e-hr-${suffix}@test.local`;
}

export { TEST_PASS };
