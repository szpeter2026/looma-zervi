/**
 * Miniprogram PIPL consent helper — wx.showModal + compliance API
 */
import { complianceApi } from './api'

type ConsentScope =
  | 'resume_upload'
  | 'resume_parse'
  | 'credit_query'
  | 'credit_analyze'
  | 'profile_share'
  | 'ask_rag'
  | 'job_match'
  | 'mbti_analyze'
  | 'navigator_memory'

const LABELS: Record<ConsentScope, string> = {
  resume_upload: '上传简历文件',
  resume_parse: '简历结构化提取',
  credit_query: '企业征信查询',
  credit_analyze: '征信文本分析',
  profile_share: '分享人格分析结果',
  ask_rag: 'AI 知识库问答',
  job_match: '职位智能匹配',
  mbti_analyze: 'MBTI 性格测评',
  navigator_memory: '对话记忆持久化',
}

const DESCRIPTIONS: Record<ConsentScope, string> = {
  resume_upload: '允许上传并临时处理您的简历文件，仅用于解析与匹配。',
  resume_parse: '允许从简历文本中提取结构化字段，用于求职匹配。',
  credit_query: '允许基于企业名称进行信用风险参考评估（当前为 AI 参考）。',
  credit_analyze: '允许分析您粘贴的征信/企业文本。',
  profile_share: '允许生成可分享的公开人格画像链接。',
  ask_rag: '允许将您的问题发送至 AI 知识库助手。',
  job_match: '允许使用简历内容与职位库进行智能匹配。',
  mbti_analyze: '允许分析您输入的文字以推断性格倾向。',
  navigator_memory: '允许 Navigator 记住您的域选择与关键决策。',
}

const cache: Partial<Record<ConsentScope, boolean>> = {}

export async function ensureConsent(scope: ConsentScope): Promise<boolean> {
  if (cache[scope]) return true

  try {
    const status = await complianceApi.status() as { status?: Record<string, boolean> }
    if (status.status?.[scope]) {
      cache[scope] = true
      return true
    }
  } catch {
    return false
  }

  return new Promise((resolve) => {
    wx.showModal({
      title: `需要授权：${LABELS[scope]}`,
      content: DESCRIPTIONS[scope],
      confirmText: '同意',
      cancelText: '取消',
      success: async (res) => {
        if (!res.confirm) {
          resolve(false)
          return
        }
        try {
          await complianceApi.grant(scope)
          cache[scope] = true
          resolve(true)
        } catch {
          resolve(false)
        }
      },
      fail: () => resolve(false),
    })
  })
}
