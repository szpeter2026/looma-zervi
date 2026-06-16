//! Zervi — Looma 的 Rust 客户端
//!
//! 本地优先的智能终端，支持：
//! - 本地 pgvector（用户私有文档索引）— P2
//! - 本地 Ollama 推理（离线问答）— P2
//! - 远程委托 Looma（公共知识 + 高质量推理）— P1 全部端点
//!
//! 当前阶段：P1 完整客户端，支持全部 Looma API 端点

use anyhow::Result;
use clap::{Parser, Subcommand};

mod client;
mod models;

const DEFAULT_LOOMA_URL: &str = "http://127.0.0.1:8010";

#[derive(Parser, Debug)]
#[command(name = "zervi", about = "Zervi — Looma 的 Rust 客户端")]
struct Args {
    /// Looma 服务端地址
    #[arg(long, global = true, default_value = DEFAULT_LOOMA_URL)]
    looma_url: String,

    /// Bearer Token（认证用）
    #[arg(long, global = true, default_value = "")]
    token: String,

    #[command(subcommand)]
    command: Option<Command>,
}

#[derive(Subcommand, Debug)]
enum Command {
    /// 健康检查
    Health,

    /// 单入口提问（中央大脑自动分发意图）
    Ask {
        /// 要问的问题
        query: Vec<String>,
        /// 执行位置：local / remote / auto
        #[arg(long, default_value = "auto")]
        hint: String,
        /// 检索范围：private / public / both
        #[arg(long, default_value = "public")]
        scope: String,
        /// 启用流式响应（SSE）
        #[arg(long)]
        stream: bool,
    },

    /// 职位匹配
    Jobs {
        #[command(subcommand)]
        cmd: JobsCommand,
    },

    /// 简历解析
    Resume {
        #[command(subcommand)]
        cmd: ResumeCommand,
    },

    /// RAG 知识库检索
    Rag {
        #[command(subcommand)]
        cmd: RagCommand,
    },

    /// 报告管理
    Reports {
        #[command(subcommand)]
        cmd: ReportsCommand,
    },

    /// 认证（注册/登录/配额）
    Auth {
        #[command(subcommand)]
        cmd: AuthCommand,
    },

    /// 地区与定价
    Region {
        /// 指定地区：CN / US / INTL
        #[arg(long)]
        country: Option<String>,
    },
}

#[derive(Subcommand, Debug)]
enum JobsCommand {
    /// 职位匹配
    Match {
        /// 简历文本
        resume_text: String,
        /// 返回前 N 条
        #[arg(long, default_value = "5")]
        top_k: usize,
    },
}

#[derive(Subcommand, Debug)]
enum ResumeCommand {
    /// 解析简历文件
    Parse {
        /// 简历文件路径（PDF/Word）
        file: String,
    },
}

#[derive(Subcommand, Debug)]
enum RagCommand {
    /// RAG 知识库检索问答
    Query {
        /// 检索查询
        query: Vec<String>,
        /// 返回前 N 条
        #[arg(long, default_value = "5")]
        top_k: usize,
        /// 相似度阈值
        #[arg(long, default_value = "0.3")]
        threshold: f64,
    },
}

#[derive(Subcommand, Debug)]
enum ReportsCommand {
    /// 生成报告
    Generate {
        /// 报告类型：daily / weekly / monthly
        #[arg(default_value = "daily")]
        report_type: String,
    },
    /// 查看报告列表
    List,
}

#[derive(Subcommand, Debug)]
enum AuthCommand {
    /// 注册
    Register {
        /// 邮箱
        email: String,
        /// 密码
        password: String,
        /// 显示名称
        #[arg(long)]
        display_name: Option<String>,
    },
    /// 登录
    Login {
        /// 邮箱
        email: String,
        /// 密码
        password: String,
    },
    /// 查询配额
    Quota,
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();
    let c = client::LoomaClient::new(&args.looma_url, &args.token);

    match args.command {
        None | Some(Command::Health) => {
            let status = c.health().await?;
            println!("状态: {}", status.status);
            println!("版本: {}", status.version);
            println!("运行时间: {} 秒", status.uptime_seconds);
        }

        Some(Command::Ask { query, hint, scope, stream }) => {
            let text = query.join(" ");
            if text.is_empty() {
                anyhow::bail!("请输入问题");
            }

            let resp = c.ask(&text, &hint, &scope).await?;
            println!("回答: {}", resp.answer);
            println!("意图: {} | 执行位置: {}", resp.intent, resp.executed_on);
            if !resp.sources.is_empty() {
                println!("\n--- 引用来源 ---");
                for (i, s) in resp.sources.iter().enumerate() {
                    println!("[{}] {} (相似度: {:?})", i + 1, s.chunk_text.chars().take(60).collect::<String>(), s.score);
                }
            }
        }

        Some(Command::Jobs { cmd }) => match cmd {
            JobsCommand::Match { resume_text, top_k } => {
                let resp = c.jobs_match(&resume_text, top_k).await?;
                println!("匹配职位数: {} / 参与打分: {}", resp.matches.len(), resp.total_evaluated);
                for (i, m) in resp.matches.iter().enumerate() {
                    println!("\n[{}] {} @ {} ({})", i + 1, m.title, m.company, m.location);
                    println!("  综合分: {:.0} | 钱多: {:.0} | 事少: {:.0} | 离家近: {:.0}",
                             m.scores.overall, m.scores.money, m.scores.workload, m.scores.proximity);
                    if !m.reason.is_empty() {
                        println!("  理由: {}", m.reason);
                    }
                }
            }
        },

        Some(Command::Resume { cmd }) => match cmd {
            ResumeCommand::Parse { file } => {
                let resp = c.resume_parse_from_file(&file).await?;
                println!("姓名: {:?}", resp.name);
                println!("邮箱: {:?}", resp.email);
                println!("电话: {:?}", resp.phone);
                if let Some(ref skills) = resp.skills {
                    println!("技能: {}", skills.join(", "));
                }
                if let Some(ref summary) = resp.summary {
                    println!("摘要: {}", summary);
                }
            }
        },

        Some(Command::Rag { cmd }) => match cmd {
            RagCommand::Query { query, top_k, threshold } => {
                let text = query.join(" ");
                if text.is_empty() {
                    anyhow::bail!("请输入检索查询");
                }
                let resp = c.rag_query(&text, top_k, threshold).await?;
                println!("检索到 {} 条结果", resp.results.len());
                for (i, r) in resp.results.iter().enumerate() {
                    println!("\n[{}] 相似度: {:.4}", i + 1, r.score);
                    println!("  {}", r.text.chars().take(200).collect::<String>());
                }
                if let Some(ref answer) = resp.answer {
                    println!("\n--- LLM 回答 ---");
                    println!("{}", answer);
                }
            }
        },

        Some(Command::Reports { cmd }) => match cmd {
            ReportsCommand::Generate { report_type } => {
                let resp = c.reports_generate(&report_type).await?;
                println!("报告 ID: {}", resp.report_id);
                println!("状态: {}", resp.status);
                println!("类型: {}", resp.report_type);
            }
            ReportsCommand::List => {
                let resp = c.reports_list().await?;
                println!("共 {} 个报告", resp.reports.len());
                for r in &resp.reports {
                    println!("  [{}] {} — {} ({})", r.r#type, r.title, r.status, r.id);
                }
            }
        },

        Some(Command::Auth { cmd }) => match cmd {
            AuthCommand::Register { email, password, display_name } => {
                let resp = c.auth_register(&email, &password, display_name.as_deref()).await?;
                println!("注册成功!");
                println!("Token: {}", resp.access_token);
                println!("档位: {}", resp.tier);
                println!("有效期: {} 秒", resp.expires_in);
            }
            AuthCommand::Login { email, password } => {
                let resp = c.auth_login(&email, &password).await?;
                println!("登录成功!");
                println!("Token: {}", resp.access_token);
                println!("档位: {}", resp.tier);
                println!("有效期: {} 秒", resp.expires_in);
                println!("\n提示: 后续调用时使用 --token \"{}\"", resp.access_token);
            }
            AuthCommand::Quota => {
                if args.token.is_empty() {
                    anyhow::bail!("请先登录获取 token，然后使用 --token 参数");
                }
                let resp = c.quota().await?;
                println!("档位: {}", resp.tier);
                for r in &resp.records {
                    println!("  {}: {}/{}", r.resource, r.used, r.daily_limit);
                }
            }
        },

        Some(Command::Region { country }) => {
            let resp = c.region(country.as_deref()).await?;
            println!("国家: {}", resp.country);
            println!("货币: {}", resp.currency);
            println!("地区: {}", resp.locale);
            if let Some(ref pricing) = resp.pricing {
                println!("定价: {} basic/月, {} pro/月",
                         pricing.basic_monthly, pricing.pro_monthly);
            }
        }
    }

    Ok(())
}