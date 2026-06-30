/**
 * Global store for miniprogram.
 * Centralized state management using app.globalData + event bus.
 * Pages subscribe to events and read from store.
 */

import { eventBus } from './event-bus'
import type { User, GameProfile, Identity, PersonalityType, MissionId, Fleet } from '../types/index'

interface StoreState {
  // Auth
  token: string | null
  user: User | null

  // Game
  identity: Identity | undefined
  personalityType: PersonalityType | undefined
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
}

export const store = {
  get: <K extends keyof StoreState>(key: K): StoreState[K] => state[key],

  getAll: (): StoreState => state,

  set: <K extends keyof StoreState>(key: K, value: StoreState[K]) => {
    state[key] = value
  },

  /** Update game profile from backend response */
  applyGameProfile(data: Partial<GameProfile>) {
    if (data.identity !== undefined) state.identity = data.identity
    if (data.level !== undefined) state.level = data.level
    if (data.xp !== undefined) state.xp = data.xp
    if (data.xp_to_next !== undefined) state.xpToNext = data.xp_to_next
    if (data.personality_type !== undefined) {
      // Backend returns "" for no personality; treat as undefined
      const pt = data.personality_type as any
      state.personalityType = (pt && typeof pt === 'object') ? pt : undefined
    }
    if (data.missions_completed !== undefined) {
      // Backend may return a count (number) or an array; ensure array
      const mc = data.missions_completed as any
      state.missionsCompleted = Array.isArray(mc) ? mc : []
    }
    if (data.fleet !== undefined) state.fleet = data.fleet
    if (data.team_size !== undefined) state.teamSize = data.team_size
    if (data.fleet_members !== undefined) state.fleetMembers = data.fleet_members
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
