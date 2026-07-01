/**
 * PlanetX Quiz Constants
 * Mirrors planetxAuthStore.ts QUIZ_QUESTIONS + PERSONALITY_MAP
 */

import type { QuizQuestion, TraitKey, PersonalityType } from '../types/index'

// ============ 题库 (8题) ============
export const QUIZ_QUESTIONS: QuizQuestion[] = [
  {
    q: '周末的下午，你最想做什么？',
    options: [
      { text: '约朋友去新开的咖啡店打卡', trait: 'social' },
      { text: '一个人在家看剧/打游戏', trait: 'introvert' },
      { text: '去报名学一个新技能', trait: 'growth' },
      { text: '随便逛逛，走到哪算哪', trait: 'wanderer' },
    ],
  },
  {
    q: '面对一个全新的任务，你的第一反应是？',
    options: [
      { text: '先做个计划再开始', trait: 'planner' },
      { text: '直接上手，边做边调整', trait: 'action' },
      { text: '先问问做过的人的经验', trait: 'social' },
      { text: '先想清楚这个任务值不值得做', trait: 'thinker' },
    ],
  },
  {
    q: '工作中让你最不爽的是什么？',
    options: [
      { text: '重复无聊的任务', trait: 'creative' },
      { text: '不被理解/不被认可', trait: 'social' },
      { text: '没有成长空间', trait: 'growth' },
      { text: '996没自己的生活', trait: 'balance' },
    ],
  },
  {
    q: '如果加入一个团队项目，你希望扮演什么角色？',
    options: [
      { text: '出主意的那个人', trait: 'creative' },
      { text: '把大家组织起来的人', trait: 'leader' },
      { text: '把细节做完美的人', trait: 'perfectionist' },
      { text: '谁需要帮忙就去帮谁', trait: 'supporter' },
    ],
  },
  {
    q: '朋友心情不好找你倾诉，你通常会？',
    options: [
      { text: '认真听完，给具体建议', trait: 'thinker' },
      { text: '一起吐槽，情绪共鸣最重要', trait: 'social' },
      { text: '拉TA出去散心转换心情', trait: 'action' },
      { text: '分享一首诗或一首歌', trait: 'creative' },
    ],
  },
  {
    q: '看到朋友圈都在刷某个热点，你会？',
    options: [
      { text: '马上加入讨论', trait: 'social' },
      { text: '先自己查资料搞清楚再发言', trait: 'thinker' },
      { text: '有点烦，划过去不看', trait: 'introvert' },
      { text: '做成一个梗图发出去', trait: 'creative' },
    ],
  },
  {
    q: '最近一次让你感到"我太牛了"是因为？',
    options: [
      { text: '解决了一个棘手的技术问题', trait: 'thinker' },
      { text: '帮一个朋友度过了难关', trait: 'supporter' },
      { text: '完成了一件拖延很久的事', trait: 'action' },
      { text: '创造了一个让自己满意的作品', trait: 'creative' },
    ],
  },
  {
    q: '你对"内卷"的态度是？',
    options: [
      { text: '不卷不行，但想卷得聪明一点', trait: 'planner' },
      { text: '找到自己的节奏，不跟别人比', trait: 'balance' },
      { text: '换条赛道，不挤同一个独木桥', trait: 'creative' },
      { text: '找到志同道合的人一起对抗', trait: 'social' },
    ],
  },
]

// ============ 人格匹配表 ============
const PERSONALITY_MAP: Record<string, PersonalityType> = {
  creative_social: {
    name: '星云艺术家', emoji: '🎨', tagline: '创造力 + 感染力 = 你的超能力',
    desc: '你天生会讲故事。在团队里你是灵感的源头，你的想法总能点燃别人的热情。适合创意、内容、品牌向的工作。',
    traits: ['创造力爆表', '社交引力', '直觉驱动'],
  },
  creative_thinker: {
    name: '黑洞程序员', emoji: '💻', tagline: '思维深度穿透事件视界',
    desc: '你对世界的理解超越表面。安静、深邃、逻辑严密。适合技术、研发、数据分析向的工作。',
    traits: ['深度思考', '逻辑严谨', '独立作战'],
  },
  social_action: {
    name: '超新星领航员', emoji: '⭐', tagline: '你的能量可以点亮整个星系',
    desc: '你是人群中的太阳。行动力+社交力让你成为天然的Leader。适合管理、销售、创业向的工作。',
    traits: ['天然领袖', '行动力MAX', '感染力强'],
  },
  social_supporter: {
    name: '双星星系守护者', emoji: '🌓', tagline: '你的存在就是别人的安全感',
    desc: '你是团队的粘合剂。善解人意、温暖可靠。适合HR、客服、教育、心理咨询向的工作。',
    traits: ['共情力强', '可靠后盾', '温暖磁场'],
  },
  growth_balance: {
    name: '脉冲星修行者', emoji: '✨', tagline: '持续进化，但从不透支自己',
    desc: '你追求成长但不盲从。节奏感是你最强的武器。适合需要持续深耕的专业领域。',
    traits: ['长期主义', '自我节奏', '持续进化'],
  },
  wanderer_balance: {
    name: '暗物质漫游者', emoji: '🌌', tagline: '你的自由就是你的引力',
    desc: '你不急着定义自己。在探索中你会找到属于自己的独特轨道。适合自由职业、跨界领域。',
    traits: ['自由灵魂', '跨界思维', '不被定义'],
  },
}

const FALLBACK_MAP: Record<string, PersonalityType> = {
  creative: PERSONALITY_MAP['creative_social'],
  social: PERSONALITY_MAP['social_action'],
  thinker: PERSONALITY_MAP['creative_thinker'],
  action: PERSONALITY_MAP['social_action'],
  growth: PERSONALITY_MAP['growth_balance'],
  wanderer: PERSONALITY_MAP['wanderer_balance'],
}

export function computePersonality(traitCounts: Partial<Record<TraitKey, number>>): PersonalityType {
  const entries = Object.entries(traitCounts) as [TraitKey, number][]
  entries.sort((a, b) => b[1] - a[1])
  const topTwo = entries.slice(0, 2).map((e) => e[0])
  const key = topTwo.join('_')
  return PERSONALITY_MAP[key] ?? FALLBACK_MAP[topTwo[0]] ?? PERSONALITY_MAP['creative_social']
}

// ============ 分享文案 ============
export function getShareText(p: PersonalityType, inviteUrl: string): string {
  return `🪐 我的星际人格是「${p.name}」！\n"${p.tagline}"\n\n👉 测测你的是什么星球身份？\n${inviteUrl}`
}

/** Restore full PersonalityType from backend name / JSON detail. */
export function hydratePersonality(
  typeName?: string,
  detailRaw?: string,
): PersonalityType | undefined {
  if (detailRaw) {
    try {
      const parsed = JSON.parse(detailRaw) as PersonalityType
      if (parsed?.name) return parsed
    } catch { /* ignore */ }
  }
  if (typeof typeName === 'string' && typeName) {
    for (const p of Object.values(PERSONALITY_MAP)) {
      if (p.name === typeName) return p
    }
  }
  return undefined
}
