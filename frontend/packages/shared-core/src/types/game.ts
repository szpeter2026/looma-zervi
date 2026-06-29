/**
 * Game / XP / Fleet / Personality type definitions.
 */

export type Identity = "explorer" | "builder" | "connector" | "strategist";

export type PersonalityType =
  | "INTJ"
  | "INTP"
  | "ENTJ"
  | "ENTP"
  | "INFJ"
  | "INFP"
  | "ENFJ"
  | "ENFP"
  | "ISTJ"
  | "ISFJ"
  | "ESTJ"
  | "ESFJ"
  | "ISTP"
  | "ISFP"
  | "ESTP"
  | "ESFP";

export type TraitKey =
  | "E"
  | "I"
  | "S"
  | "N"
  | "T"
  | "F"
  | "J"
  | "P";

export interface QuizOption {
  label: string;
  value: string;
  trait: TraitKey;
  weight?: number;
}

export interface QuizQuestion {
  id: string;
  text: string;
  options: QuizOption[];
}

export type RankName =
  | "青铜星尘"
  | "白银陨石"
  | "黄金行星"
  | "铂金星云"
  | "钻石星系"
  | "星舰指挥官";

export const RANK_NAMES: Record<number, RankName> = {
  1: "青铜星尘",
  2: "白银陨石",
  3: "黄金行星",
  4: "铂金星云",
  5: "钻石星系",
  6: "星舰指挥官",
};

export function getRankName(level: number): RankName {
  const rank = Math.min(Math.max(level, 1), 6);
  return RANK_NAMES[rank] ?? "青铜星尘";
}

export type MissionId =
  | "first_ask"
  | "complete_resume"
  | "job_match"
  | "share_planetx"
  | "join_fleet"
  | "daily_login"
  | string;

export interface Mission {
  id: MissionId;
  name: string;
  description: string;
  xp_reward: number;
  completed?: boolean;
  completed_at?: string;
}

export interface GameProfile {
  id: string;
  user_id: string;
  personality_type: string;
  personality_detail: string;
  xp: number;
  level: number;
  missions_completed: number;
  total_mission_xp: number;
  updated_at: string;
}

export interface ProfileSyncRequest {
  personality_type: string;
  personality_detail?: string;
}

export interface MissionCompleteRequest {
  mission_id: MissionId;
  xp_reward?: number;
}

export interface MissionCompleteResponse {
  message: string;
  mission_id: MissionId;
  xp_earned: number;
  total_xp: number;
  level: number;
}

export interface Fleet {
  id: string;
  name: string;
  captain_id: string;
  description?: string;
  member_count: number;
  created_at: string;
}

export interface FleetMember {
  user_id: string;
  name: string;
  role: "captain" | "member";
  joined_at: string;
}

export interface CreateFleetRequest {
  name: string;
  description?: string;
}

export interface JoinFleetRequest {
  fleet_id: string;
}

export interface FleetResponse {
  id: string;
  name: string;
  captain_id: string;
  description?: string;
  member_count: number;
  created_at: string;
}

export interface MyFleetResponse {
  fleet?: Fleet;
  members?: FleetMember[];
  member_count: number;
  message?: string;
}

export type GameScreen =
  | "home"
  | "profile"
  | "missions"
  | "fleet"
  | "quiz"
  | "rank"
  | "shop";

export type SharePlatform = "wechat" | "moment" | "copy" | "qq" | "weibo";
