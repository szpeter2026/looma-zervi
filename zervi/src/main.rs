//! Zervi — Looma 的 Rust 客户端
//!
//! 本地优先的智能终端，支持：
//! - 本地 pgvector（用户私有文档索引）
//! - 本地 Ollama 推理（离线问答）
//! - 远程委托 Looma（公共知识 + 高质量推理）
//!
//! 当前阶段：P1 骨架，仅实现 /v1/ask HTTP 调用

use anyhow::Result;
use clap::Parser;
use serde::{Deserialize, Serialize};

const DEFAULT_LOOMA_URL: &str = "http://127.0.0.1:8010";

#[derive(Parser, Debug)]
#[command(name = "zervi", about = "Zervi — Looma 的 Rust 客户端")]
struct Args {
    /// Looma 服务端地址
    #[arg(long, default_value = DEFAULT_LOOMA_URL)]
    looma_url: String,

    /// 要问的问题
    query: Option<String>,
}

// ── 对齐 api.yaml v1.1.0 的请求/响应类型 ──

#[derive(Serialize)]
struct AskRequest {
    query: String,
    execution_hint: String,
    context_scope: String,
}

#[derive(Deserialize, Debug)]
struct AskResponse {
    answer: String,
    intent: String,
    executed_on: String,
    tokens_used: u64,
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();

    // 健康检查
    let health_url = format!("{}/v1/health", args.looma_url);
    let resp = reqwest::get(&health_url).await?;

    if resp.status().is_success() {
        println!("Looma 服务端连接正常");
    } else {
        anyhow::bail!("Looma 服务端连接失败: {}", resp.status());
    }

    // 如果提供了 query，调 /v1/ask
    if let Some(query) = args.query {
        let ask_url = format!("{}/v1/ask", args.looma_url);
        let req = AskRequest {
            query,
            execution_hint: "auto".to_string(),
            context_scope: "public".to_string(),
        };

        let client = reqwest::Client::new();
        let resp = client.post(&ask_url).json(&req).send().await?;
        let answer: AskResponse = resp.json().await?;

        println!("\n回答: {}", answer.answer);
        println!("意图: {} | 执行: {} | Token: {}", answer.intent, answer.executed_on, answer.tokens_used);
    } else {
        println!("用法: zervi \"你的问题\"");
    }

    Ok(())
}
