//! Zervi — 数据模型（对齐 Looma api.yaml v1.1.0）
use serde::{Deserialize, Serialize};

// ── /v1/health ─────────────────────────────

#[derive(Deserialize, Debug)]
pub struct HealthStatus {
    pub status: String,
    pub version: String,
    pub uptime_seconds: u64,
}

// ── /v1/ask ────────────────────────────────

#[derive(Serialize)]
pub struct AskRequest {
    pub query: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub execution_hint: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub context_scope: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub stream: Option<bool>,
}

#[derive(Deserialize, Debug)]
pub struct AskResponse {
    pub answer: String,
    pub intent: String,
    #[serde(default)]
    pub sources: Vec<SourceNode>,
    #[serde(default)]
    pub executed_on: String,
    #[serde(default)]
    pub tokens_used: u64,
}

#[derive(Deserialize, Debug)]
pub struct SourceNode {
    #[serde(default)]
    pub chunk_text: String,
    #[serde(default)]
    pub score: Option<f64>,
}

// ── /v1/jobs ───────────────────────────────

#[derive(Serialize)]
pub struct JobMatchRequest {
    pub resume_text: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub top_k: Option<usize>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub scope: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub include_analysis: Option<bool>,
}

#[derive(Deserialize, Debug)]
pub struct JobMatchResponse {
    #[serde(default)]
    pub matches: Vec<JobMatchItem>,
    #[serde(default)]
    pub total_evaluated: i32,
}

#[derive(Deserialize, Debug)]
pub struct JobMatchItem {
    pub title: String,
    pub company: String,
    #[serde(default)]
    pub location: String,
    #[serde(default)]
    pub salary_range: Option<String>,
    pub scores: JobScores,
    #[serde(default)]
    pub reason: String,
}

#[derive(Deserialize, Debug)]
pub struct JobScores {
    #[serde(default)]
    pub money: f64,
    #[serde(default)]
    pub workload: f64,
    #[serde(default)]
    pub proximity: f64,
    #[serde(default)]
    pub overall: f64,
}

// ── /v1/resume ─────────────────────────────

#[derive(Deserialize, Debug)]
pub struct ResumeAnalysis {
    #[serde(default)]
    pub name: Option<String>,
    #[serde(default)]
    pub email: Option<String>,
    #[serde(default)]
    pub phone: Option<String>,
    #[serde(default)]
    pub education: Option<Vec<serde_json::Value>>,
    #[serde(default)]
    pub experience: Option<Vec<serde_json::Value>>,
    #[serde(default)]
    pub skills: Option<Vec<String>>,
    #[serde(default)]
    pub summary: Option<String>,
}

// ── /v1/rag ─────────────────────────────────

#[derive(Serialize)]
pub struct RagQueryRequest {
    pub query: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub scope: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub top_k: Option<usize>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub score_threshold: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub execution_hint: Option<String>,
}

#[derive(Deserialize, Debug)]
pub struct RagQueryResponse {
    #[serde(default)]
    pub results: Vec<RagResultItem>,
    #[serde(default)]
    pub answer: Option<String>,
}

#[derive(Deserialize, Debug)]
pub struct RagResultItem {
    #[serde(default)]
    pub text: String,
    #[serde(default)]
    pub score: f64,
    #[serde(default)]
    pub source: String,
}

// ── /v1/auth ────────────────────────────────

#[derive(Serialize)]
pub struct AuthRegisterRequest {
    pub email: String,
    pub password: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub display_name: Option<String>,
}

#[derive(Serialize)]
pub struct AuthLoginRequest {
    pub email: String,
    pub password: String,
}

#[derive(Deserialize, Debug)]
pub struct AuthResponse {
    pub access_token: String,
    pub refresh_token: String,
    pub tier: String,
    pub expires_in: i32,
    #[serde(default)]
    pub user_id: Option<String>,
}

// ── /v1/quota ───────────────────────────────

#[derive(Deserialize, Debug)]
pub struct QuotaResponse {
    pub tier: String,
    pub records: Vec<QuotaRecord>,
}

#[derive(Deserialize, Debug)]
pub struct QuotaRecord {
    pub resource: String,
    pub used: i32,
    pub daily_limit: i32,
}

// ── /v1/region ──────────────────────────────

#[derive(Deserialize, Debug)]
pub struct RegionResponse {
    pub country: String,
    pub currency: String,
    #[serde(default)]
    pub locale: String,
    #[serde(default)]
    pub pricing: Option<RegionPricing>,
}

#[derive(Deserialize, Debug)]
pub struct RegionPricing {
    #[serde(alias = "basic_monthly")]
    pub basic_monthly: serde_json::Value,
    #[serde(alias = "pro_monthly")]
    pub pro_monthly: serde_json::Value,
}

// ── /v1/reports ─────────────────────────────

#[derive(Serialize)]
pub struct ReportGenerateRequest {
    #[serde(rename = "type")]
    pub report_type: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub scope: Option<String>,
}

#[derive(Deserialize, Debug)]
pub struct ReportGenerateResponse {
    #[serde(default)]
    pub report_id: String,
    #[serde(default)]
    pub status: String,
    #[serde(default)]
    pub path: Option<String>,
    #[serde(rename = "type", default)]
    pub report_type: String,
}

#[derive(Deserialize, Debug)]
pub struct ReportListResponse {
    #[serde(default)]
    pub reports: Vec<ReportMeta>,
}

#[derive(Deserialize, Debug)]
pub struct ReportMeta {
    #[serde(default)]
    pub id: String,
    #[serde(default)]
    pub title: String,
    #[serde(default)]
    pub status: String,
    #[serde(rename = "type", default)]
    pub r#type: String,
    #[serde(default)]
    pub created_at: String,
}

// ── 通用错误 ────────────────────────────────

#[derive(Deserialize, Debug)]
pub struct ErrorResponse {
    #[serde(default)]
    pub detail: String,
}