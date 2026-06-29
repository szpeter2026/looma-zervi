/**
 * PlanetX 游戏状态管理 — Zustand + Looma API 同步
 * 迁移自旧 planetxStore.ts，移除 Supabase，改用 looma JWT 认证
 * Owner: Jason
 */
import { create } from 'zustand'
import { createApiClient, createAuthApi, type User } from '@looma/shared-core'

// ============ 类型定义（内联以保持 store 自包含） ============
export type Identity = 'explorer' | 'captain' | 'wanderer'

export const IDENTITY_LABELS: Record<Identity, string> = {
  explorer: '星际探索者 · 求职模式',
  captain: '舰队舰长 · 组队模式',
  wanderer: '星际漫游者 · 探索模式',
}

export type TraitKey =
  | 'social' | 'introvert' | 'growth' | 'wanderer'
  | 'planner' | 'action' | 'thinker' | 'creative'
  | 'balance' | 'leader' | 'perfectionist' | 'supporter'

export interface PersonalityType {
  name: string
  emoji: string
  tagline: string
  desc: string
  traits: string[]
}

export interface QuizQuestion {
  q: string
  options: QuizOption[]
}

export interface QuizOption {
  text: string
  trait: TraitKey
}

export type GameScreen = 'loading' | 'auth' | 'onboarding' | 'hub' | 'quiz' | 'result'

export type MissionId = 'personality' | 'team' | 'match' | 'share'

export interface Fleet {
  id: string
  name: string
  invite_code: string
  captain_id: string
}

export type RankName =
  | '星际新兵' | '星域探索者' | '银河领航员' | '星际指挥官' | '宇宙传奇'

export function getRankName(level: number): RankName {
  if (level <= 3) return '星际新兵'
  if (level <= 6) return '星域探索者'
  if (level <= 10) return '银河领航员'
  if (level <= 15) return '星际指挥官'
  return '宇宙传奇'
}

// ============ API Client 初始化 ============
const API_BASE = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE || 'http://localhost:5200'

function getApiClient() {
  return createApiClient({
    baseURL: API_BASE,
    getToken: () => usePlanetXStore.getState().token,
    onUnauthorized: () => usePlanetXStore.getState().logout(),
  })
}

function getAuthApi() {
  return createAuthApi(getApiClient())
}

// ============ 题库 ============
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

export function computePersonality(traitCounts: Record<TraitKey, number>): PersonalityType {
  const entries = Object.entries(traitCounts) as [TraitKey, number][]
  entries.sort((a, b) => b[1] - a[1])
  const topTwo = entries.slice(0, 2).map((e) => e[0])
  const key = topTwo.join('_')
  return PERSONALITY_MAP[key] ?? FALLBACK_MAP[topTwo[0]] ?? PERSONALITY_MAP['creative_social']
}

// ============ 分享文案 ============
export function getShareText(
  platform: 'wechat' | 'xiaohongshu' | 'weibo' | 'copy',
  p: PersonalityType,
  inviteUrl: string,
): string {
  const templates: Record<string, string> = {
    wechat: `🪐 我的星际人格是「${p.name}」！\n"${p.tagline}"\n\n👉 测测你的是什么星球身份？\n${inviteUrl}`,
    xiaohongshu: `🪐 PlanetX 星际人格测试 🪐\n\n我的身份：${p.emoji} ${p.name}\n标签：#${p.traits.join(' #')}\n\n"${p.tagline}"\n\n${p.desc}\n\n#PlanetX #星际人格 #MBTI #Z世代 #求职\n🔗 ${inviteUrl}`,
    weibo: `🪐 PlanetX星际人格认证：我是「${p.name}」${p.emoji}\n"${p.tagline}"\n${p.desc.slice(0, 60)}…\n\n你也来测测？${inviteUrl}\n#PlanetX星际人格# #00后求职#`,
    copy: `🪐 我在 PlanetX 的星际人格是「${p.name}」！\n${p.tagline}\n\n扫码来测测你的星际身份 → ${inviteUrl}`,
  }
  return templates[platform] ?? templates.copy
}

// ============ Zustand Store ============
interface PlanetXState {
  // 屏幕
  screen: GameScreen
  setScreen: (s: GameScreen) => void

  // 认证
  token: string | null
  user: (User & { identity?: Identity; personality_type?: PersonalityType }) | null
  isAuthenticated: boolean
  isLoading: boolean

  // 游戏
  identity: Identity | null
  personalityType: PersonalityType | null

  // XP
  level: number
  xp: number
  xpToNext: number

  // 任务
  missionsCompleted: MissionId[]

  // 舰队
  fleet: Fleet | null
  teamSize: number
  fleetMembers: string[]

  // 测评
  quizStep: number
  quizAnswers: number[]
  quizTraitCounts: Partial<Record<TraitKey, number>>
  quizFinished: boolean

  // 分享
  refCode: string

  // 提示
  toast: string | null
  achievement: { title: string; desc: string } | null

  // Actions
  setToast: (msg: string | null) => void
  setAchievement: (a: { title: string; desc: string } | null) => void
  addXP: (amount: number) => void
  completeMission: (id: MissionId) => void
  answerQuiz: (trait: TraitKey, idx: number) => void
  finishQuiz: () => PersonalityType
  setIdentity: (identity: Identity) => void

  // Auth (Looma JWT)
  login: (email: string, password: string) => Promise<boolean>
  register: (email: string, password: string) => Promise<boolean>
  logout: () => void
  checkSession: () => Promise<void>

  // Profile (Looma API)
  loadProfile: () => Promise<void>
  syncProfile: () => Promise<void>

  // Fleet (Looma API)
  createFleet: () => Promise<void>
  joinFleet: (code: string) => Promise<void>
  loadFleetData: () => Promise<void>

  getInviteUrl: () => string
}

export const usePlanetXStore = create<PlanetXState>((set, get) => ({
  screen: 'loading',
  setScreen: (screen) => set({ screen }),

  token: null,
  user: null,
  isAuthenticated: false,
  isLoading: false,

  identity: null,
  personalityType: null,

  level: 1,
  xp: 0,
  xpToNext: 100,

  missionsCompleted: [],

  fleet: null,
  teamSize: 0,
  fleetMembers: [],

  quizStep: 0,
  quizAnswers: [],
  quizTraitCounts: {},
  quizFinished: false,

  refCode: '',
  toast: null,
  achievement: null,

  setToast: (toast) => set({ toast }),
  setAchievement: (achievement) => {
    set({ achievement })
    if (achievement) setTimeout(() => set({ achievement: null }), 2500)
  },

  addXP: (amount) => {
    let { xp, level, xpToNext } = get()
    xp += amount
    let leveledUp = false
    while (xp >= xpToNext) {
      xp -= xpToNext
      level++
      xpToNext = Math.floor(xpToNext * 1.5)
      leveledUp = true
    }
    set({ xp, level, xpToNext })
    if (leveledUp) {
      const rank = getRankName(level)
      get().setAchievement({ title: '⬆️ 升级！', desc: `你已晋升为 Lv.${level} · ${rank}` })
    }
    get().syncProfile()
  },

  completeMission: (id) => {
    const { missionsCompleted } = get()
    if (missionsCompleted.includes(id)) return
    set({ missionsCompleted: [...missionsCompleted, id] })

    // 同步到后端
    const { token } = get()
    if (token) {
      getApiClient().post('/v1/game/mission-complete', { mission_id: id }).catch(() => {})
    }
    get().syncProfile()
  },

  answerQuiz: (trait, idx) => {
    const { quizTraitCounts, quizAnswers, quizStep } = get()
    set({
      quizTraitCounts: { ...quizTraitCounts, [trait]: (quizTraitCounts[trait] ?? 0) + 1 },
      quizAnswers: [...quizAnswers, idx + 1],
      quizStep: quizStep + 1,
    })
  },

  finishQuiz: () => {
    const { quizTraitCounts } = get()
    const personality = computePersonality(quizTraitCounts as Record<TraitKey, number>)
    set({ personalityType: personality, quizFinished: true })
    get().completeMission('personality')
    get().addXP(50)
    get().setAchievement({ title: '🔮 星际人格觉醒！', desc: `你被认证为「${personality.name}」` })
    get().syncProfile()
    return personality
  },

  setIdentity: (identity) => {
    set({ identity })
    get().addXP(10)
    get().syncProfile()
  },

  // ======= Auth (Looma JWT) =======
  login: async (email, password) => {
    try {
      const authApi = getAuthApi()
      const resp = await authApi.login(email, password)
      set({
        token: resp.access_token,
        user: { ...resp.user, identity: null, personality_type: null },
        isAuthenticated: true,
      })
      // 加载完整 profile
      await get().loadProfile()
      get().setToast('跃迁成功！欢迎回来 🪐')
      get().setScreen(get().identity ? 'hub' : 'onboarding')
      return true
    } catch (e) {
      const msg = (e as { response?: { data?: { message?: string } }; message?: string })
      get().setToast('登录失败: ' + (msg.response?.data?.message ?? msg.message ?? '未知错误'))
      return false
    }
  },

  register: async (email, password) => {
    try {
      const authApi = getAuthApi()
      const resp = await authApi.register(email, password)
      set({
        token: resp.access_token,
        user: { ...resp.user, identity: null, personality_type: null },
        isAuthenticated: true,
      })
      get().setToast('注册成功！欢迎加入 PlanetX 🚀')
      get().setScreen('onboarding')
      return true
    } catch (e) {
      const msg = (e as { response?: { data?: { message?: string } }; message?: string })
      get().setToast('注册失败: ' + (msg.response?.data?.message ?? msg.message ?? '未知错误'))
      return false
    }
  },

  logout: () => {
    set({
      token: null, user: null, isAuthenticated: false,
      identity: null, personalityType: null,
      level: 1, xp: 0, xpToNext: 100, missionsCompleted: [],
      fleet: null, teamSize: 0, fleetMembers: [],
      screen: 'auth',
    })
  },

  checkSession: async () => {
    // 检查 localStorage 中是否有 token（由 createApiClient 的 getToken 返回）
    const state = get()
    if (!state.token) {
      setTimeout(() => set({ screen: 'auth' }), 2000)
      return
    }
    try {
      // 验证 token + 加载 profile
      await get().loadProfile()
      setTimeout(() => set({ screen: get().identity ? 'hub' : 'onboarding' }), 1500)
    } catch {
      get().logout()
    }
  },

  // ======= Profile (Looma API) =======
  loadProfile: async () => {
    const { token } = get()
    if (!token) return
    try {
      const client = getApiClient()
      const data = await client.get<{
        identity?: Identity
        level?: number
        xp?: number
        xp_to_next?: number
        personality_type?: PersonalityType
        missions_completed?: MissionId[]
        fleet?: Fleet
        team_size?: number
        fleet_members?: string[]
      }>('/v1/game/profile')

      if (data) {
        set({
          identity: data.identity ?? null,
          level: data.level ?? 1,
          xp: data.xp ?? 0,
          xpToNext: data.xp_to_next ?? 100,
          personalityType: data.personality_type ?? null,
          missionsCompleted: data.missions_completed ?? [],
          fleet: data.fleet ?? null,
          teamSize: data.team_size ?? 0,
          fleetMembers: data.fleet_members ?? [],
        })
      }
      // 如果 profile 中有舰队，检查任务
      const s = get()
      if (s.fleet && s.teamSize >= 3 && !s.missionsCompleted.includes('team')) {
        get().completeMission('team')
        get().addXP(80)
        get().setAchievement({ title: '🤝 舰队集结完毕！', desc: '3人成团 · 隐藏星图已解锁' })
      }
    } catch { /* defaults */ }
  },

  syncProfile: async () => {
    const { token, identity, level, xp, xpToNext, personalityType } = get()
    if (!token) return
    try {
      const client = getApiClient()
      await client.post('/v1/game/profile-sync', {
        identity,
        level,
        xp,
        xp_to_next: xpToNext,
        personality_type: personalityType,
      })
    } catch { /* best-effort */ }
  },

  // ======= Fleet (Looma API) =======
  createFleet: async () => {
    const { token } = get()
    if (!token) return
    try {
      const client = getApiClient()
      const data = await client.post<Fleet>('/v1/game/fleet/create')
      if (data) {
        set({ fleet: data, teamSize: 1, fleetMembers: [data.captain_id] })
        get().setToast('舰队创建成功！发送邀请码给好友加入 🚀')
      }
    } catch (e) {
      get().setToast('创建舰队失败: ' + ((e as { message?: string }).message ?? '未知错误'))
    }
  },

  joinFleet: async (code) => {
    const { token } = get()
    if (!token) return
    try {
      const client = getApiClient()
      const data = await client.post<{ fleet: Fleet; team_size: number; fleet_members: string[] }>(
        '/v1/game/fleet/join',
        { invite_code: code.toUpperCase() }
      )
      if (data) {
        set({ fleet: data.fleet, teamSize: data.team_size, fleetMembers: data.fleet_members })
        get().setToast('成功加入舰队！👥')
        // 检查是否达成组队任务
        if (data.team_size >= 3 && !get().missionsCompleted.includes('team')) {
          get().completeMission('team')
          get().addXP(80)
          get().setAchievement({ title: '🤝 舰队集结完毕！', desc: '3人成团 · 隐藏星图已解锁' })
        }
      }
    } catch (e) {
      const msg = (e as { response?: { data?: { message?: string } }; message?: string })
      get().setToast('加入失败: ' + (msg.response?.data?.message ?? msg.message ?? '舰队不存在'))
    }
  },

  loadFleetData: async () => {
    const { token } = get()
    if (!token) return
    try {
      const client = getApiClient()
      const data = await client.get<{
        fleet?: Fleet
        team_size?: number
        fleet_members?: string[]
      }>('/v1/game/fleet/mine')

      if (data?.fleet) {
        set({
          fleet: data.fleet,
          teamSize: data.team_size ?? 0,
          fleetMembers: data.fleet_members ?? [],
        })
        // 检查任务
        if ((data.team_size ?? 0) >= 3 && !get().missionsCompleted.includes('team')) {
          get().completeMission('team')
          get().addXP(80)
          get().setAchievement({ title: '🤝 舰队集结完毕！', desc: '3人成团 · 隐藏星图已解锁' })
        }
      }
    } catch { /* no fleet */ }
  },

  getInviteUrl: () => {
    const { refCode, token } = get()
    let code = refCode
    if (!code) {
      code = token
        ? 'PX-' + token.substring(0, 8).toUpperCase()
        : 'PX-' + Math.random().toString(36).substring(2, 10).toUpperCase()
      set({ refCode: code })
    }
    return window.location.origin + window.location.pathname + '?ref=' + code
  },
}))
