/**
 * PlanetX 游戏状态管理 — Zustand + Looma API 同步
 * 迁移自旧 planetxStore.ts，移除 Supabase，改用 looma JWT 认证
 * Owner: Jason
 */
import { create } from 'zustand'
import {
  createApiClient,
  createAuthApi,
  createReferralApi,
  QUIZ_QUESTIONS,
  computePersonality,
  hydratePersonality,
  getShareText,
  IDENTITY_LABELS,
  getPlanetXRankName,
  type ApiClient,
  type User,
  type PlanetXIdentity as Identity,
  type PlanetXTraitKey as TraitKey,
  type PlanetXPersonalityType as PersonalityType,
  type PlanetXQuizOption as QuizOption,
  type PlanetXQuizQuestion as QuizQuestion,
  type PlanetXRankName as RankName,
  type PlanetXMissionId as MissionId,
  type PlanetXFleet as Fleet,
  type PlanetXGameScreen as GameScreen,
} from '@looma/shared-core'

export {
  IDENTITY_LABELS,
  QUIZ_QUESTIONS,
  computePersonality,
  hydratePersonality,
  getShareText,
}
export type { Identity, TraitKey, PersonalityType, QuizOption, QuizQuestion, GameScreen, MissionId, Fleet, RankName }

export function getRankName(level: number): RankName {
  return getPlanetXRankName(level)
}

// ============ API Client 初始化 ============
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:5200'
const SAAS_BASE = import.meta.env.VITE_SAAS_URL ?? 'http://localhost:5174'

const MISSION_XP: Record<MissionId, number> = {
  personality: 50,
  share: 30,
  team: 80,
  match: 40,
}

const VALID_IDENTITIES: Identity[] = ['explorer', 'captain', 'wanderer']

/** 老用户：有人格/任务进度则直达 Hub，避免重复 onboarding */
function resolvePostAuthScreen(state: {
  identity?: Identity
  personalityType?: PersonalityType
  quizFinished: boolean
  missionsCompleted: MissionId[]
}): GameScreen {
  if (
    state.identity ||
    state.personalityType ||
    state.quizFinished ||
    state.missionsCompleted.length > 0
  ) {
    return 'hub'
  }
  return 'onboarding'
}

function parseIdentity(value: unknown): Identity | undefined {
  if (typeof value === 'string' && (VALID_IDENTITIES as string[]).includes(value)) {
    return value as Identity
  }
  return undefined
}

export function getApiClient(): ApiClient {
  return createApiClient({
    baseURL: API_BASE,
    getToken: () => usePlanetXStore.getState().token,
    onUnauthorized: () => usePlanetXStore.getState().logout(),
  })
}

function getAuthApi() {
  return createAuthApi(getApiClient())
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
  identity: Identity | undefined
  personalityType: PersonalityType | undefined

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
  profileShareCode: string

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
  getHrShareUrl: () => string
  ensureProfileShareCode: () => Promise<string>
  ensureReferralCode: () => Promise<string>
}

export const usePlanetXStore = create<PlanetXState>((set, get) => ({
  screen: 'loading',
  setScreen: (screen) => set({ screen }),

  token: null,
  user: null,
  isAuthenticated: false,
  isLoading: false,

  identity: undefined,
  personalityType: undefined,

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
  profileShareCode: '',
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
    const previous = missionsCompleted
    set({ missionsCompleted: [...missionsCompleted, id] })

    const { token } = get()
    if (token) {
      getApiClient()
        .post<{ total_xp?: number; level?: number; error?: string; message?: string }>(
          '/v1/game/mission-complete',
          {
            mission_id: id,
            xp_reward: MISSION_XP[id] ?? 10,
          },
        )
        .then((data) => {
          if (data?.total_xp != null) {
            set({ xp: data.total_xp, level: data.level ?? get().level })
          }
        })
        .catch((err: { body?: { message?: string }; response?: { data?: { message?: string } }; message?: string }) => {
          set({ missionsCompleted: previous })
          const msg =
            err?.body?.message ||
            err?.response?.data?.message ||
            err?.message ||
            '任务同步失败，请稍后重试'
          get().setToast(`任务未完成：${msg}`)
        })
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
    get().setAchievement({ title: '🔮 星际人格觉醒！', desc: `你被认证为「${personality.name}」` })
    get().syncProfile()
    return personality
  },

  setIdentity: (identity) => {
    set({ identity })
    get().addXP(10)
    const { token } = get()
    if (token) {
      getApiClient()
        .post('/v1/game/profile-sync', { identity })
        .catch(() => get().setToast('身份同步失败，请稍后重试'))
    }
  },

  // ======= Auth (Looma JWT) =======
  login: async (email, password) => {
    try {
      const authApi = getAuthApi()
      const resp = await authApi.login({ email, password })
      set({
        token: resp.access_token,
        user: { ...resp.user, identity: undefined, personality_type: undefined } as any,
        isAuthenticated: true,
      })
      // 写入共享 localStorage，T 空间可自动识别
      getApiClient().setToken(resp.access_token)
      // 加载完整 profile
      await get().loadProfile()
      get().setToast('跃迁成功！欢迎回来 🪐')
      const s = get()
      get().setScreen(resolvePostAuthScreen(s))
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
      const resp = await authApi.register({ email, password })
      set({
        token: resp.access_token,
        user: { ...resp.user, identity: undefined, personality_type: undefined } as any,
        isAuthenticated: true,
      })
      // 写入共享 localStorage，T 空间可自动识别
      getApiClient().setToken(resp.access_token)
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
    // 清除共享 localStorage token
    getApiClient().clearToken()
    set({
      token: null, user: null, isAuthenticated: false,
      identity: undefined, personalityType: undefined,
      level: 1, xp: 0, xpToNext: 100, missionsCompleted: [],
      fleet: null, teamSize: 0, fleetMembers: [],
      screen: 'auth',
    })
  },

  checkSession: async () => {
    const state = get()
    let token = state.token
    if (!token) {
      try {
        token = localStorage.getItem("looma_token")
      } catch {
        token = null
      }
    }
    if (!token) {
      setTimeout(() => set({ screen: 'auth' }), 2000)
      return
    }
    if (token !== state.token) {
      set({ token })
      getApiClient().setToken(token)
    }
    try {
      await get().loadProfile()
      const s = get()
      setTimeout(() => set({ screen: resolvePostAuthScreen(s) }), 1500)
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
        identity?: string
        level?: number
        xp?: number
        xp_to_next?: number
        personality_type?: string
        personality_detail?: string
        missions_completed?: MissionId[] | number
        fleet?: Fleet
        team_size?: number
        fleet_members?: string[]
      }>('/v1/game/profile')

      if (data) {
        const missions = Array.isArray(data.missions_completed)
          ? data.missions_completed
          : []
        const personality = hydratePersonality(
          data.personality_type,
          data.personality_detail,
        )
        set({
          identity: parseIdentity(data.identity),
          level: data.level ?? 1,
          xp: data.xp ?? 0,
          xpToNext: data.xp_to_next ?? 100,
          personalityType: personality,
          quizFinished: !!personality,
          missionsCompleted: missions as MissionId[],
          fleet: data.fleet ?? null,
          teamSize: data.team_size ?? 0,
          fleetMembers: data.fleet_members ?? [],
        })
      }
      // 如果 profile 中有舰队，检查任务
      const s = get()
      if (s.fleet && s.teamSize >= 3 && !s.missionsCompleted.includes('team')) {
        get().completeMission('team')
        get().setAchievement({ title: '🤝 舰队集结完毕！', desc: '3人成团 · 隐藏星图已解锁' })
      }
    } catch { /* defaults */ }
  },

  syncProfile: async () => {
    const { token, personalityType, identity } = get()
    if (!token) return
    const payload: Record<string, string> = {}
    if (identity) payload.identity = identity
    if (personalityType?.name) {
      payload.personality_type = personalityType.name
      payload.personality_detail = JSON.stringify(personalityType)
    }
    if (!payload.identity && !payload.personality_type) return
    try {
      const client = getApiClient()
      await client.post('/v1/game/profile-sync', payload)
    } catch {
      /* best-effort */
    }
  },

  // ======= Fleet (Looma API) =======
  createFleet: async () => {
    const { token } = get()
    if (!token) return
    try {
      const client = getApiClient()
      const data = await client.post<Fleet & { invite_code: string; team_size: number }>('/v1/game/fleet/create')
      if (data) {
        set({ fleet: data, teamSize: data.team_size ?? 1, fleetMembers: [data.captain_id] })
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
          get().setAchievement({ title: '🤝 舰队集结完毕！', desc: '3人成团 · 隐藏星图已解锁' })
        }
      }
    } catch { /* no fleet */ }
  },

  ensureProfileShareCode: async () => {
    const { profileShareCode, token } = get()
    if (profileShareCode) return profileShareCode
    if (!token) return ''
    try {
      const resp = await createReferralApi(getApiClient()).create({ purpose: 'profile_share' })
      set({ profileShareCode: resp.code })
      return resp.code
    } catch {
      return ''
    }
  },

  ensureReferralCode: async () => {
    const { refCode, token } = get()
    if (refCode) return refCode
    if (!token) return ''
    try {
      const resp = await createReferralApi(getApiClient()).create({ purpose: 'referral' })
      set({ refCode: resp.code })
      return resp.code
    } catch {
      return ''
    }
  },

  getInviteUrl: () => {
    const { refCode } = get()
    const base = window.location.origin + window.location.pathname
    return refCode ? `${base}?ref=${refCode}` : base
  },

  getHrShareUrl: () => {
    const { profileShareCode } = get()
    const base = SAAS_BASE.replace(/\/$/, '')
    return profileShareCode ? `${base}/candidate/share/${profileShareCode}` : base
  },
}))
