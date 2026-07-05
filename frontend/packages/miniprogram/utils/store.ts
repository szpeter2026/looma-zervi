/**
 * Global store for miniprogram.
 * Centralized state management using app.globalData + event bus.
 * Pages subscribe to events and read from store.
 */

import { eventBus } from './event-bus'
import { 
  User, 
  Identity, 
  PersonalityType as PlanetXPersonalityType, 
  MissionId, 
  Fleet,
  GameProfile
} from '../types/index'
import { hydratePersonality } from '../constants/quiz'

interface StoreState {
  // Auth
  token: string | null
  user: User | null

  // Game
  identity: Identity | undefined
  personalityType: PlanetXPersonalityType | undefined
  level: number
  xp: number
  xpToNext: number
  missionsCompleted: MissionId[]

  // Fleet
  fleet: Fleet | null
  teamSize: number
  fleetMembers: string[]

  // Quiz
  quizStep: number
  quizTraitCounts: Partial<Record<string, number>>

  // UI
  achievement: { title: string; desc: string } | null
  personalityDetail?: string
}

const state: StoreState = {
  token: null,
  user: null,
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
  quizTraitCounts: {},
  achievement: null,
  personalityDetail: undefined,
}

export const store = {
  get: <K extends keyof StoreState>(key: K): StoreState[K] => state[key],

  getAll: (): StoreState => state,

  set: <K extends keyof StoreState>(key: K, value: StoreState[K]) => {
    state[key] = value
  },

  /** Update game profile from backend response */
  applyGameProfile(data: any) {
    // 兼容后端返回的字段命名（可能是 snake_case）
    const identity = data.identity !== undefined ? data.identity : undefined
    const level = data.level !== undefined ? data.level : undefined
    const xp = data.xp !== undefined ? data.xp : undefined
    const personality_type = data.personality_type !== undefined ? data.personality_type : data.personalityType
    const missions_completed = data.missions_completed !== undefined ? data.missions_completed : data.missionsCompleted
    const fleet = data.fleet !== undefined ? data.fleet : undefined
    const team_size = data.team_size !== undefined ? data.team_size : data.teamSize
    const fleet_members = data.fleet_members !== undefined ? data.fleet_members : data.fleetMembers
    const personality_detail = data.personality_detail !== undefined ? data.personality_detail : undefined

    if (identity !== undefined) state.identity = identity
    if (level !== undefined) state.level = level
    if (xp !== undefined) state.xp = xp
    // 注意：shared-core 的 GameProfile 中没有 xp_to_next 字段
    // 保持现有的 xpToNext 逻辑不变

    if (personality_detail !== undefined) {
      state.personalityDetail = personality_detail
    }

    const personality = hydratePersonality(
      typeof personality_type === 'string' ? personality_type : undefined,
      personality_detail,
    )
    if (personality) {
      state.personalityType = personality as any
    } else if (personality_type === '' || personality_type === null) {
      state.personalityType = undefined
    }

    if (missions_completed !== undefined) {
      // 处理 missions_completed 可能是数字或数组的情况
      if (Array.isArray(missions_completed)) {
        state.missionsCompleted = missions_completed as MissionId[]
      } else if (typeof missions_completed === 'number') {
        // 如果是数字，转换为空数组（因为小程序需要数组）
        state.missionsCompleted = []
      }
    }
    if (fleet !== undefined) state.fleet = fleet
    if (team_size !== undefined) state.teamSize = team_size
    if (fleet_members !== undefined) state.fleetMembers = fleet_members
    eventBus.emit('profile:loaded', state)
  },

  /** Add XP and handle level up */
  addXP(amount: number) {
    state.xp += amount
    let leveledUp = false
    while (state.xp >= state.xpToNext) {
      state.xp -= state.xpToNext
      state.level++
      state.xpToNext = Math.floor(state.xpToNext * 1.5)
      leveledUp = true
    }
    if (leveledUp) {
      store.setAchievement({
        title: '⬆️ 升级！',
        desc: `你已晋升为 Lv.${state.level}`,
      })
    }
    eventBus.emit('xp:added', { xp: state.xp, level: state.level })
  },

  /** Complete a mission */
  completeMission(id: MissionId) {
    if (state.missionsCompleted.includes(id)) return
    state.missionsCompleted = [...state.missionsCompleted, id]
  },

  /** Set achievement popup */
  setAchievement(a: { title: string; desc: string } | null) {
    state.achievement = a
    eventBus.emit('achievement', a)
    if (a) {
      setTimeout(() => {
        state.achievement = null
        eventBus.emit('achievement', null)
      }, 2500)
    }
  },

  /** Reset all state (logout) */
  reset() {
    state.token = null
    state.user = null
    state.identity = undefined
    state.personalityType = undefined
    state.level = 1
    state.xp = 0
    state.xpToNext = 100
    state.missionsCompleted = []
    state.fleet = null
    state.teamSize = 0
    state.fleetMembers = []
    state.quizStep = 0
    state.quizTraitCounts = {}
    state.achievement = null
  },
}
