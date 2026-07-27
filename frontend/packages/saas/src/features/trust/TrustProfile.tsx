/**
 * Trust Profile — personal attestation cards (product exit for Trust Layer).
 * P0: list + refresh + empty CTA. Share/verify is P0.5.
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  ApiError,
  createTrustApi,
  type TrustAttestation,
} from "@looma/shared-core";
import { createSaasApiClient } from "../../api/saasApiClient";

const CLAIM_ORDER = ["identity", "collaboration", "communication", "influence"] as const;

function statusTone(status: string): { bg: string; fg: string } {
  if (status === "verified" || status === "verified_by_authority") {
    return { bg: "#e8f5e9", fg: "var(--color-success)" };
  }
  if (status === "weak") {
    return { bg: "#fff8e1", fg: "#b78103" };
  }
  return { bg: "#f5f5f5", fg: "var(--color-text-muted)" };
}

function AttestationCard({
  att,
  claimLabel,
  statusLabel,
  evidenceLabel,
  t,
}: {
  att: TrustAttestation;
  claimLabel: string;
  statusLabel: string;
  evidenceLabel: string;
  t: (key: string, opts?: Record<string, string | number>) => string;
}) {
  const tone = statusTone(att.verification_status);
  const confidencePct = Math.round((att.confidence_score ?? 0) * 100);
  const issued = att.issued_at
    ? new Date(att.issued_at).toLocaleDateString()
    : "—";

  return (
    <article
      className="rounded-lg p-4"
      style={{
        backgroundColor: "var(--color-bg-card)",
        boxShadow: "var(--shadow-sm)",
        border: "1px solid #f0f0f0",
      }}
    >
      <div className="flex items-start justify-between gap-3 flex-wrap mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <h3
            className="text-sm font-semibold m-0"
            style={{ color: "var(--color-text-primary)" }}
          >
            {claimLabel}
          </h3>
          <span
            className="text-xs px-2 py-0.5 rounded"
            style={{ backgroundColor: tone.bg, color: tone.fg }}
          >
            {statusLabel}
          </span>
        </div>
        <span className="text-xs" style={{ color: "var(--color-text-muted)" }}>
          {t("trust.confidenceHint", { pct: confidencePct })}
        </span>
      </div>
      <p
        className="text-sm leading-relaxed m-0 mb-3"
        style={{ color: "var(--color-text-secondary)" }}
      >
        {att.claim_statement}
      </p>
      <div
        className="flex flex-wrap gap-x-4 gap-y-1 text-xs"
        style={{ color: "var(--color-text-muted)" }}
      >
        <span>{t("trust.evidence", { type: evidenceLabel })}</span>
        <span>{t("trust.issued", { date: issued })}</span>
        {att.signature ? <span>{t("trust.signed")}</span> : null}
      </div>
    </article>
  );
}

export default function TrustProfile() {
  const { t } = useTranslation();
  const api = useMemo(() => createTrustApi(createSaasApiClient()), []);
  const [attestations, setAttestations] = useState<TrustAttestation[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const res = await api.listAttestations();
      const list = res.attestations ?? [];
      list.sort((a, b) => {
        const ia = CLAIM_ORDER.indexOf(a.claim_type as (typeof CLAIM_ORDER)[number]);
        const ib = CLAIM_ORDER.indexOf(b.claim_type as (typeof CLAIM_ORDER)[number]);
        return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
      });
      setAttestations(list);
    } catch (err) {
      const msg =
        err instanceof ApiError && err.body?.message
          ? String(err.body.message)
          : t("trust.loadFailed");
      setError(msg);
      setAttestations([]);
    } finally {
      setLoading(false);
    }
  }, [api, t]);

  useEffect(() => {
    void load();
  }, [load]);

  const handleRefresh = async () => {
    setRefreshing(true);
    setError(null);
    try {
      const res = await api.refresh();
      const list = res.attestations ?? [];
      list.sort((a, b) => {
        const ia = CLAIM_ORDER.indexOf(a.claim_type as (typeof CLAIM_ORDER)[number]);
        const ib = CLAIM_ORDER.indexOf(b.claim_type as (typeof CLAIM_ORDER)[number]);
        return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
      });
      setAttestations(list);
    } catch (err) {
      const msg =
        err instanceof ApiError && err.body?.message
          ? String(err.body.message)
          : t("trust.refreshFailed");
      setError(msg);
    } finally {
      setRefreshing(false);
    }
  };

  const claimLabel = (type: string) => {
    const key = `trust.claim.${type}`;
    const translated = t(key);
    return translated === key ? type : translated;
  };

  const statusLabel = (status: string) => {
    const key = `trust.status.${status}`;
    const translated = t(key);
    return translated === key ? status : translated;
  };

  const evidenceLabel = (type: string) => {
    const key = `trust.evidenceType.${type}`;
    const translated = t(key);
    return translated === key ? type : translated;
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <header className="space-y-2">
        <h1
          className="text-2xl font-bold m-0"
          style={{ color: "var(--color-text-primary)" }}
        >
          {t("trust.title")}
        </h1>
        <p className="text-sm m-0" style={{ color: "var(--color-text-secondary)" }}>
          {t("trust.subtitle")}
        </p>
      </header>

      <div className="flex items-center justify-between gap-3 flex-wrap">
        <p className="text-sm m-0" style={{ color: "var(--color-text-muted)" }}>
          {loading
            ? t("trust.loading")
            : t("trust.count", { count: attestations.length })}
        </p>
        <button
          type="button"
          onClick={() => void handleRefresh()}
          disabled={loading || refreshing}
          className="px-4 py-2 text-sm rounded-lg text-white border-none cursor-pointer disabled:opacity-50"
          style={{ backgroundColor: "var(--color-primary)" }}
        >
          {refreshing ? t("trust.refreshing") : t("trust.refresh")}
        </button>
      </div>

      {error && (
        <p className="text-sm m-0" style={{ color: "var(--color-danger)" }}>
          {error}
        </p>
      )}

      {!loading && attestations.length === 0 && !error && (
        <div
          className="rounded-lg p-6 space-y-3"
          style={{
            backgroundColor: "var(--color-bg-card)",
            border: "1px dashed #e0e0e0",
          }}
        >
          <p className="text-sm m-0" style={{ color: "var(--color-text-secondary)" }}>
            {t("trust.empty")}
          </p>
          <div className="flex flex-wrap gap-3">
            <Link
              to="/jobs"
              className="text-sm no-underline"
              style={{ color: "var(--color-primary)" }}
            >
              {t("trust.ctaJobs")}
            </Link>
            <Link
              to="/resume"
              className="text-sm no-underline"
              style={{ color: "var(--color-primary)" }}
            >
              {t("trust.ctaResume")}
            </Link>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {attestations.map((att) => (
          <AttestationCard
            key={att.attestation_id}
            att={att}
            claimLabel={claimLabel(att.claim_type)}
            statusLabel={statusLabel(att.verification_status)}
            evidenceLabel={evidenceLabel(att.evidence_type)}
            t={t}
          />
        ))}
      </div>

      <p className="text-xs m-0" style={{ color: "var(--color-text-muted)" }}>
        {t("trust.noScoreNote")}
      </p>
    </div>
  );
}
