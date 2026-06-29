/**
 * PlanetX Miniprogram - Shared Types
 * Mirrors @looma/shared-core type definitions.
 * Backend changes must update these types first (dual review).
 */

// ============ Auth Types ============
export type Tier = 'free' | 'supporter' | 'pro' | 'enterprise'
export type Role = 'user' | 'admin'

export interface User {
  id: string
  email: string | null
  name: string
  tier: Tier
  role: Role
}

export interface UserProfile extends User {
  is_early_adopter: boolean
  created_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: 'bearer'
  expires_in: number
  user: User
}

export interface QuotaRecord {
  resource: string
  daily_limit: number
  used: number
}

export interface QuotaResponse {
  tier: Tier
  records: QuotaRecord[]
}

// ============ Game / XP / Personality ============
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

export interface QuizOption {
  text: string
  trait: TraitKey
}

export interface QuizQuestion {
  q: string
  options: QuizOption[]
}

export type MissionId = 'personality' | 'team' | 'match' | 'share'

export interface Fleet {
  id: string
  name: string
  invite_code: string
  captain_id: string
}

export type RankName =
  | '星际新兵' | '星域探索者' | '银河领航员'
  | '星际指挥官' | '宇宙传奇'

export function getRankName(level: number): RankName {
  if (level <= 3) return '星际新兵'
  if (level <= 6) return '星域探索者'
  if (level <= 10) return '银河领航员'
  if (level <= 15) return '星际指挥官'
  return '宇宙传奇'
}

// ============ Chat / Ask ============
export interface DocSource {
  chunk_text: string
  score?: number
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  sources?: DocSource[]
  timestamp?: string
}

export interface AskResponse {
  answer: string
  intent?: string
  sources?: DocSource[]
  tokens_used?: number
}

// ============ Game Profile (from backend) ============
export interface GameProfile {
  identity?: Identity
  level: number
  xp: number
  xp_to_next: number
  personality_type?: PersonalityType
  missions_completed: MissionId[]
  fleet?: Fleet
  team_size: number
  fleet_members: string[]
}

// ============ Quota Constants ============
export const RESOURCE_ASK = 'ask'
export const RESOURCE_JOB_MATCH = 'job_match'
export const RESOURCE_RESUME_PARSE = 'resume_parse'

export const QUOTA_LIMITS: Record<string, Record<string, number>> = {
  guest: { [RESOURCE_JOB_MATCH]: 1, [RESOURCE_ASK]: 3, [RESOURCE_RESUME_PARSE]: 1 },
  free: { [RESOURCE_JOB_MATCH]: 5, [RESOURCE_ASK]: 30, [RESOURCE_RESUME_PARSE]: 3 },
  supporter: { [RESOURCE_JOB_MATCH]: 99999, [RESOURCE_ASK]: 99999, [RESOURCE_RESUME_PARSE]: 99999 },
  pro: { [RESOURCE_JOB_MATCH]: 99999, [RESOURCE_ASK]: 99999, [RESOURCE_RESUME_PARSE]: 99999 },
  enterprise: { [RESOURCE_JOB_MATCH]: 99999, [RESOURCE_ASK]: 99999, [RESOURCE_RESUME_PARSE]: 99999 },
}

// ============ Brand ============
export const BRAND = {
  PLANETX: {
    name: 'PlanetX',
    slogan: '你的职业飞行器',
    primaryColor: '#6C63FF',
  },
} as const

// ============ Event Bus Types ============
export type AppEvent =
  | 'auth:login'     // login succeeded
  | 'auth:logout'    // logout
  | 'auth:expired'   // token expired
  | 'profile:loaded' // profile data loaded
  | 'xp:added'       // xp gained
  | 'achievement'    // achievement unlocked
