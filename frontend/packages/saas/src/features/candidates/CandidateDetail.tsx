/**
 * Single candidate detail — HR view of PlanetX personality profile.
 */
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { createEnterpriseApi, type Candidate } from "@looma/shared-core";
import { createSaasApiClient } from "../../api/saasApiClient";

export default function CandidateDetail() {
  const { id } = useParams<{ id: string }>();
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    const client = createSaasApiClient();
    createEnterpriseApi(client)
      .getCandidate(id)
      .then(setCandidate)
      .catch(() => setError("无法加载候选人"));
  }, [id]);

  if (error) {
    return (
      <div>
        <p style={{ color: "var(--color-text-muted)" }}>{error}</p>
        <Link to="/candidates" style={{ color: "var(--color-primary)" }}>← 返回列表</Link>
      </div>
    );
  }

  if (!candidate) {
    return <p style={{ color: "var(--color-text-muted)" }}>加载中…</p>;
  }

  const profile = candidate.profile_data as {
    personality_type?: string;
    personality_detail?: { name?: string; emoji?: string; tagline?: string; desc?: string; traits?: string[] };
    xp?: number;
    level?: number;
  } | undefined;

  const detail = profile?.personality_detail;
  const emoji = detail?.emoji ?? "🪐";
  const name = detail?.name ?? profile?.personality_type ?? "未知类型";

  return (
    <div className="max-w-2xl">
      <Link to="/candidates" className="text-sm mb-4 inline-block" style={{ color: "var(--color-primary)" }}>
        ← 返回候选人列表
      </Link>

      <div
        className="rounded-2xl p-8 mb-6"
        style={{ backgroundColor: "var(--color-bg-card)", boxShadow: "var(--shadow-md)" }}
      >
        <div className="text-center mb-6">
          <div className="text-5xl mb-3">{emoji}</div>
          <h1 className="text-xl font-bold" style={{ color: "var(--color-text-primary)" }}>
            {candidate.name}
          </h1>
          <p className="text-sm mt-1" style={{ color: "var(--color-text-muted)" }}>
            {name} · Lv.{profile?.level ?? 1}
          </p>
          {candidate.email && (
            <p className="text-xs mt-1" style={{ color: "var(--color-text-muted)" }}>{candidate.email}</p>
          )}
        </div>

        {detail?.tagline && (
          <p className="text-center italic mb-4 text-sm" style={{ color: "var(--color-primary)" }}>
            「{detail.tagline}」
          </p>
        )}

        {detail?.traits && detail.traits.length > 0 && (
          <div className="flex flex-wrap justify-center gap-2 mb-4">
            {detail.traits.map((t) => (
              <span
                key={t}
                className="px-3 py-1 rounded-full text-xs"
                style={{ backgroundColor: "var(--color-bg-surface)" }}
              >
                {t}
              </span>
            ))}
          </div>
        )}

        {detail?.desc && (
          <p className="text-sm leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
            {detail.desc}
          </p>
        )}
      </div>

      <Link
        to="/pricing"
        className="inline-block px-5 py-2 rounded-lg text-sm text-white no-underline"
        style={{ backgroundColor: "var(--color-primary)" }}
      >
        升级 Pro，解锁更多匹配能力 →
      </Link>
    </div>
  );
}
