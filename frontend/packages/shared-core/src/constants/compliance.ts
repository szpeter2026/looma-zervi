import type { ConsentScope } from "../types/compliance";

/** Human-readable labels for consent prompts (PIPL 单独同意) */
export const CONSENT_SCOPE_LABELS: Record<ConsentScope, string> = {
  resume_upload: "上传简历文件",
  resume_parse: "简历结构化提取",
  credit_query: "企业征信查询",
  credit_analyze: "征信文本分析",
  profile_share: "分享人格分析结果",
  ask_rag: "AI 知识库问答",
  job_match: "职位智能匹配",
  mbti_analyze: "MBTI 性格测评",
  navigator_memory: "对话记忆持久化",
  report_generate: "生成并保存匹配报告",
  report_share: "授权匹配报告给合伙人",
};

export const CONSENT_SCOPE_DESCRIPTIONS: Record<ConsentScope, string> = {
  resume_upload: "允许上传并临时处理您的简历文件，仅用于解析与匹配，不会超出必要范围存储。",
  resume_parse: "允许系统从简历文本中提取结构化字段（教育、经历等），用于求职匹配。",
  credit_query: "允许基于您输入的企业名称进行信用风险参考评估（当前为 AI 参考，非正式征信报告）。",
  credit_analyze: "允许分析您粘贴的征信/企业文本，生成结构化摘要。",
  profile_share: "允许生成可分享的公开人格画像链接，供 HR 查看（不含敏感联系方式）。",
  ask_rag: "允许将您的问题发送至 AI 知识库助手，可能结合检索片段生成回答。",
  job_match: "允许使用您的简历内容与职位库进行智能匹配评分。",
  mbti_analyze: "允许分析您输入的文字以推断性格倾向（娱乐/参考用途）。",
  navigator_memory: "允许 Navigator 在会话间记住您的域选择与关键决策，以延续叙事体验。",
  report_generate: "允许将本次匹配评分结果持久化为报告，供您后续查看与对比。",
  report_share: "允许将匹配报告中的选定维度授权给职业成长合伙人查看。",
};
