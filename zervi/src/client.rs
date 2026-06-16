//! Zervi — Looma HTTP 客户端
//!
//! 封装所有 Looma API 调用，对齐 api.yaml v1.1.0。

use anyhow::{bail, Result};
use reqwest::Client;
use std::path::Path;

use crate::models::*;

pub struct LoomaClient {
    base_url: String,
    token: String,
    client: Client,
}

impl LoomaClient {
    pub fn new(base_url: &str, token: &str) -> Self {
        Self {
            base_url: base_url.trim_end_matches('/').to_string(),
            token: token.to_string(),
            client: Client::new(),
        }
    }

    fn auth_header(&self) -> Option<(&str, &str)> {
        if self.token.is_empty() {
            None
        } else {
            Some(("Authorization", self.token.as_str()))
        }
    }

    fn build_get(&self, path: &str) -> reqwest::RequestBuilder {
        let mut req = self.client.get(format!("{}{}", self.base_url, path));
        if let Some((k, v)) = self.auth_header() {
            req = req.header(k, format!("Bearer {}", v));
        }
        req
    }

    fn build_post(&self, path: &str) -> reqwest::RequestBuilder {
        let mut req = self.client.post(format!("{}{}", self.base_url, path));
        if let Some((k, v)) = self.auth_header() {
            req = req.header(k, format!("Bearer {}", v));
        }
        req
    }

    // ── 健康检查 ────────────────────────────

    pub async fn health(&self) -> Result<HealthStatus> {
        let resp = self.client
            .get(format!("{}/v1/health", self.base_url))
            .send()
            .await?;

        if !resp.status().is_success() {
            bail!("健康检查失败: {}", resp.status());
        }

        Ok(resp.json().await?)
    }

    // ── /v1/ask 单入口 ──────────────────────

    pub async fn ask(&self, query: &str, hint: &str, scope: &str) -> Result<AskResponse> {
        let req = AskRequest {
            query: query.to_string(),
            execution_hint: Some(hint.to_string()),
            context_scope: Some(scope.to_string()),
            stream: None,
        };

        let resp = self.build_post("/v1/ask")
            .json(&req)
            .send()
            .await?;

        if resp.status() == 429 {
            bail!("配额已用尽 (429)");
        }
        if !resp.status().is_success() {
            let err: ErrorResponse = resp.json().await.unwrap_or(ErrorResponse { detail: String::new() });
            bail!("API 错误: {}", err.detail);
        }

        Ok(resp.json().await?)
    }

    // ── /v1/jobs/match ──────────────────────

    pub async fn jobs_match(&self, resume_text: &str, top_k: usize) -> Result<JobMatchResponse> {
        let req = JobMatchRequest {
            resume_text: resume_text.to_string(),
            top_k: Some(top_k),
            scope: None,
            include_analysis: Some(true),
        };

        let resp = self.build_post("/v1/jobs/match")
            .json(&req)
            .send()
            .await?;

        if !resp.status().is_success() {
            bail!("职位匹配失败: {}", resp.status());
        }

        Ok(resp.json().await?)
    }

    // ── /v1/resume/parse ────────────────────

    pub async fn resume_parse_from_file(&self, file_path: &str) -> Result<ResumeAnalysis> {
        let path = Path::new(file_path);
        if !path.exists() {
            bail!("文件不存在: {}", file_path);
        }

        let content = tokio::fs::read(path).await?;
        let filename = path.file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("resume.pdf");

        let part = reqwest::multipart::Part::bytes(content)
            .file_name(filename.to_string())
            .mime_str("application/octet-stream")?;

        let form = reqwest::multipart::Form::new()
            .part("file", part);

        let mut req = self.client
            .post(format!("{}/v1/resume/parse", self.base_url))
            .multipart(form);

        if let Some((k, v)) = self.auth_header() {
            req = req.header(k, format!("Bearer {}", v));
        }

        let resp = req.send().await?;

        if !resp.status().is_success() {
            bail!("简历解析失败: {}", resp.status());
        }

        Ok(resp.json().await?)
    }

    // ── /v1/rag/query ───────────────────────

    pub async fn rag_query(&self, query: &str, top_k: usize, threshold: f64) -> Result<RagQueryResponse> {
        let req = RagQueryRequest {
            query: query.to_string(),
            scope: Some("hybrid".to_string()),
            top_k: Some(top_k),
            score_threshold: Some(threshold),
            execution_hint: Some("auto".to_string()),
        };

        let resp = self.build_post("/v1/rag/query")
            .json(&req)
            .send()
            .await?;

        if !resp.status().is_success() {
            bail!("RAG 检索失败: {}", resp.status());
        }

        Ok(resp.json().await?)
    }

    // ── /v1/auth/register ───────────────────

    pub async fn auth_register(&self, email: &str, password: &str, display_name: Option<&str>) -> Result<AuthResponse> {
        let req = AuthRegisterRequest {
            email: email.to_string(),
            password: password.to_string(),
            display_name: display_name.map(|s| s.to_string()),
        };

        let resp = self.client
            .post(format!("{}/v1/auth/register", self.base_url))
            .json(&req)
            .send()
            .await?;

        if resp.status() == 409 {
            bail!("邮箱已注册");
        }
        if !resp.status().is_success() {
            bail!("注册失败: {}", resp.status());
        }

        Ok(resp.json().await?)
    }

    // ── /v1/auth/login ──────────────────────

    pub async fn auth_login(&self, email: &str, password: &str) -> Result<AuthResponse> {
        let req = AuthLoginRequest {
            email: email.to_string(),
            password: password.to_string(),
        };

        let resp = self.client
            .post(format!("{}/v1/auth/login", self.base_url))
            .json(&req)
            .send()
            .await?;

        if resp.status() == 401 {
            bail!("邮箱或密码错误");
        }
        if !resp.status().is_success() {
            bail!("登录失败: {}", resp.status());
        }

        Ok(resp.json().await?)
    }

    // ── /v1/quota ───────────────────────────

    pub async fn quota(&self) -> Result<QuotaResponse> {
        let resp = self.build_get("/v1/quota")
            .send()
            .await?;

        if !resp.status().is_success() {
            bail!("查询配额失败: {}", resp.status());
        }

        Ok(resp.json().await?)
    }

    // ── /v1/region ───────────────────────────

    pub async fn region(&self, country: Option<&str>) -> Result<RegionResponse> {
        let mut url = format!("{}/v1/region", self.base_url);
        if let Some(c) = country {
            url = format!("{}?country={}", url, c);
        }

        let resp = self.client.get(&url).send().await?;

        if !resp.status().is_success() {
            bail!("获取地区信息失败: {}", resp.status());
        }

        Ok(resp.json().await?)
    }

    // ── /v1/reports/generate ────────────────

    pub async fn reports_generate(&self, report_type: &str) -> Result<ReportGenerateResponse> {
        let req = ReportGenerateRequest {
            report_type: report_type.to_string(),
            scope: Some("private".to_string()),
        };

        let resp = self.build_post("/v1/reports/generate")
            .json(&req)
            .send()
            .await?;

        if !resp.status().is_success() {
            bail!("报告生成失败: {}", resp.status());
        }

        Ok(resp.json().await?)
    }

    // ── /v1/reports ─────────────────────────

    pub async fn reports_list(&self) -> Result<ReportListResponse> {
        let resp = self.build_get("/v1/reports")
            .send()
            .await?;

        if !resp.status().is_success() {
            bail!("获取报告列表失败: {}", resp.status());
        }

        Ok(resp.json().await?)
    }
}