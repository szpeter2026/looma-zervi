import { useState } from 'react'
import { usePlanetXStore, IDENTITY_LABELS } from '../auth/planetxAuthStore'
import type { MissionId } from '../auth/planetxAuthStore'
import XPBar from '../../brand/components/XPBar'
import FleetPanel from '../../brand/components/FleetPanel'
import PlanetXIcon, { type PlanetXIconName } from '../../brand/ui/PlanetXIcon'

/**
 * HubScreen v2 — Figma 对齐版 (2026-08-08)
 * =============================================
 * 布局结构（由上到下）：
 *   1. Hero 区 — 头像 + 等级徽章 + XP 进度条（游戏化核心）
 *   2. 快捷入口 2x2 — 时间线 / 信任档案 / 星际匹配 / 舰队
 *   3. 任务列表 — 4 个任务卡片，含进度条和状态标签
 *   4. 个人统计 — 数值面板（仅 profile 标签内）
 *   5. 舰队面板 — 成员展示 + 创建/加入（仅 team 标签内）
 */
export default function HubScreen() {
  const [tab, setTab] = useState<'missions' | 'team' | 'profile'>('missions')
  const {
    identity, level, xp, xpToNext, missionsCompleted,
    personalityType, setScreen, logout, teamSize, spreadCount,
  } = usePlanetXStore()

  const TABS = ['missions', 'team', 'profile'] as const

  const missions: {
    id: MissionId; icon: PlanetXIconName; name: string; reward: string; xp: number; requires?: MissionId
  }[] = [
    { id: 'personality', icon: 'crystal', name: '人格冷启动测评', reward: '+50 XP · 生成初始假设', xp: 50 },
    { id: 'team', icon: 'handshake', name: '组建 3 人舰队', reward: '+80 XP · 解锁隐藏星图', xp: 80, requires: 'personality' },
    { id: 'match', icon: 'target', name: '首次星际匹配', reward: '+40 XP · 获得匹配星图', xp: 40, requires: 'team' },
    { id: 'share', icon: 'signal', name: '发送星际信号', reward: '+30 XP · 邀请好友获额外能量', xp: 30, requires: 'personality' },
  ]

  const allMissionsDone = (['personality', 'team', 'match', 'share'] as MissionId[]).every(
    (id) => missionsCompleted.includes(id),
  )

  const tabMeta: Record<typeof TABS[number], { icon: PlanetXIconName; label: string }> = {
    missions: { icon: 'target', label: '任务' },
    team: { icon: 'fleet', label: '舰队' },
    profile: { icon: 'profile', label: '我的' },
  }

  const isMissionUnlocked = (m: typeof missions[number]) => {
    if (!m.requires) return true
    if (m.id === 'match') return missionsCompleted.includes('team') || teamSize >= 2
    return missionsCompleted.includes(m.requires)
  }

  const isMissionDone = (id: MissionId) => missionsCompleted.includes(id)

  // ====== Styles (aligned to shared tokens) ======
  const s = {
    card: {
      width: '100%',
      background: 'var(--px-card-bg)',
      border: 'var(--px-card-border)',
      borderRadius: 'var(--px-card-radius)',
    } as React.CSSProperties,
    btnSubtle: {
      border: '1px solid var(--px-color-border-subtle)',
      borderRadius: 'var(--lo-radius-md)',
      background: 'var(--px-color-surface-glass)',
      cursor: 'pointer',
      transition: 'all var(--lo-anim-fast)',
      color: 'var(--px-color-text-primary)',
    } as React.CSSProperties,
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* ================================================================
       * 1. HERO 区 — 头像 + 等级 + XP 进度条
       * ================================================================ */}
      <div style={{ ...s.card, padding: 20, textAlign: 'center', border: '1px solid var(--px-color-border-default)' }}>
        {/* 头像 + 身份 */}
        <div style={{ marginBottom: 12 }}>
          <div style={{
            width: 64, height: 64, borderRadius: '50%',
            background: 'var(--px-gradient-hero)',
            margin: '0 auto',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 32,
            boxShadow: 'var(--px-shadow-glow)',
          }}>
            {personalityType?.emoji
              ? <span style={{ fontSize: 32 }}>{personalityType.emoji}</span>
              : <PlanetXIcon name="planet" size={32} color="var(--px-color-text-brand)" />}
          </div>
          <h2 style={{
            fontSize: 'var(--lo-font-size-2xl)',
            fontWeight: 'var(--lo-font-black)',
            color: 'var(--px-color-text-primary)',
            marginTop: 10, marginBottom: 2,
          }}>
            {personalityType?.name ?? '星际探索者'}
          </h2>
          <p style={{
            fontSize: 'var(--lo-font-size-xs)', color: 'var(--px-color-text-tertiary)',
            letterSpacing: 'var(--lo-tracking-wider)', margin: 0,
          }}>
            {identity ? IDENTITY_LABELS[identity] : ''}
          </p>
        </div>

        {/* XP 进度条 — 这里直接渲染 XP 条而不通过 XPBar 组件，使 Hero 一体化 */}
        <div style={{ marginTop: 14 }}>
          <div style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            marginBottom: 8, fontSize: 'var(--lo-font-size-xs)',
          }}>
            <span style={{ color: 'var(--px-color-text-secondary)', letterSpacing: 1, display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <PlanetXIcon name="spark" size={14} color="currentColor" />
              星际能量
            </span>
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              padding: '2px 12px', borderRadius: 'var(--lo-radius-full)',
              background: 'var(--px-color-surface-glass)',
              border: '1px solid var(--px-color-border-subtle)',
              color: 'var(--px-color-text-brand)', fontWeight: 700, fontSize: 11,
            }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                <PlanetXIcon name="planet" size={14} color="currentColor" />
                Lv.{level}
              </span>
            </span>
            <span style={{ color: 'var(--px-color-text-brand)', fontWeight: 700 }}>
              {xp}/{xpToNext} XP
            </span>
          </div>
          {/* Progress track */}
          <div style={{
            height: 8, borderRadius: 'var(--lo-radius-full)',
            background: 'rgba(108,99,255,0.12)',
            overflow: 'hidden',
          }}>
            <div style={{
              height: '100%', borderRadius: 'var(--lo-radius-full)',
              background: 'var(--px-gradient-xp-bar)',
              transition: 'width 0.8s var(--lo-anim-enter)',
              width: `${Math.min(100, (xp / xpToNext) * 100)}%`,
            }} />
          </div>
        </div>
      </div>

      {/* Extra XP milestone button when all done */}
      {allMissionsDone && (
        <button
          type="button"
          onClick={() => setScreen('trust')}
          style={{
            padding: '14px 16px', borderRadius: 'var(--lo-radius-md)',
            border: '1px solid rgba(255,215,0,0.35)',
            background: 'linear-gradient(135deg, rgba(255,215,0,0.12), rgba(108,99,255,0.1))',
            color: '#FFD700', fontWeight: 800, fontSize: 13,
            cursor: 'pointer', textAlign: 'left', width: '100%',
          }}
        >
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <PlanetXIcon name="trophy" size={16} color="#FFD700" />
            通关大奖已解锁 · 打开信任档案
          </span>
          <span style={{ display: 'block', fontSize: 11, fontWeight: 500, color: 'var(--px-color-text-tertiary)', marginTop: 4 }}>
            行为开始被看见 — 去查看声明，或继续在时间线沉淀
          </span>
        </button>
      )}

      {/* ================================================================
       * 2. 快捷入口 2×2 Grid
       * ================================================================ */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        {[
          { screen: 'timeline' as const, icon: 'timeline' as PlanetXIconName, label: '时间线', desc: '行为沉淀', color: '#C8FF50', bg: 'rgba(200,255,80,0.06)' },
          { screen: 'trust' as const, icon: 'shield' as PlanetXIconName, label: '信任档案', desc: '凭证可查', color: '#C4B5FD', bg: 'rgba(139,130,255,0.08)' },
          { screen: 'match' as const, icon: 'target' as PlanetXIconName, label: '星际匹配', desc: '寻找同伴', color: '#00E5FF', bg: 'rgba(0,229,255,0.06)' },
          undefined, // 第四个作为快捷入口，占位
        ].filter(Boolean).map((item) => item && (
          <button
            key={item.screen}
            type="button"
            onClick={() => setScreen(item.screen)}
            style={{
              ...s.btnSubtle,
              padding: '14px 12px',
              textAlign: 'left',
              background: item.bg,
              borderColor: 'var(--px-color-border-subtle)',
            }}
          >
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
              <PlanetXIcon name={item.icon} size={20} color={item.color} />
              <span style={{ fontWeight: 700, fontSize: 13, color: item.color }}>
                {item.label}
              </span>
            </div>
            <div style={{ fontSize: 11, color: 'var(--px-color-text-tertiary)', marginTop: 4 }}>
              {item.desc}
            </div>
          </button>
        ))}
      </div>

      {/* ================================================================
       * 3. TAB 切换 — 任务 / 舰队 / 我的
       * ================================================================ */}
      <div style={{
        display: 'flex', gap: 4, padding: 4,
        background: 'var(--px-card-bg)',
        border: 'var(--px-card-border)',
        borderRadius: 'var(--lo-radius-md)',
      }}>
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              flex: 1, padding: '10px 0', borderRadius: 'var(--lo-radius-sm)',
              fontSize: 12, fontWeight: 600, border: 'none',
              background: tab === t ? 'var(--px-color-surface-glass-hover)' : 'transparent',
              color: tab === t ? 'var(--px-color-text-primary)' : 'var(--px-color-text-tertiary)',
              cursor: 'pointer', transition: 'all var(--lo-anim-fast)',
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6,
            }}
          >
            <PlanetXIcon name={tabMeta[t].icon} size={14} color="currentColor" />
            {tabMeta[t].label}
          </button>
        ))}
      </div>

      {/* ================================================================
       * 4. TAB 内容区
       * ================================================================ */}

      {/* ——— 任务列表 ——— */}
      {tab === 'missions' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {missions.map((m) => {
            const unlocked = isMissionUnlocked(m)
            const done = isMissionDone(m.id)
            return (
              <button
                key={m.id}
                type="button"
                onClick={() => {
                  if (!unlocked || done) return
                  if (m.id === 'personality') setScreen('quiz')
                  else if (m.id === 'match') setScreen('match')
                  else if (m.id === 'share') setScreen('result')
                }}
                disabled={!unlocked}
                style={{
                  ...s.card,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  padding: 14,
                  textAlign: 'left',
                  cursor: unlocked && !done ? 'pointer' : 'default',
                  opacity: unlocked ? 1 : 0.4,
                  border: 'none',
                  color: 'var(--px-color-text-primary)',
                  transition: 'all var(--lo-anim-fast)',
                }}
              >
                {/* Icon */}
                <span style={{
                  width: 44, height: 44, display: 'flex',
                  alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0, borderRadius: 'var(--lo-radius-sm)',
                  background: done
                    ? 'var(--px-color-success-bg)'
                    : 'var(--px-color-surface-glass)',
                  color: done ? 'var(--px-color-success)' : 'var(--px-color-text-brand)',
                }}>
                  <PlanetXIcon name={m.icon} size={22} color="currentColor" />
                </span>

                {/* Text */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 14, fontWeight: 700 }}>
                    {done && (
                      <span style={{ display: 'inline-flex', alignItems: 'center', marginRight: 4 }}>
                        <PlanetXIcon name="check" size={14} color="var(--px-color-success)" />
                      </span>
                    )}
                    {m.name}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--px-color-text-brand)', marginTop: 2 }}>
                    {m.reward}
                  </div>
                </div>

                {/* Status badge */}
                <span style={{
                  fontSize: 11, padding: '4px 10px',
                  borderRadius: 'var(--lo-radius-full)',
                  flexShrink: 0, fontWeight: 600,
                  background: done
                    ? 'var(--px-color-success-bg)'
                    : unlocked
                      ? 'var(--px-color-info-bg)'
                      : 'rgba(255,255,255,0.04)',
                  color: done
                    ? 'var(--px-color-success)'
                    : unlocked
                      ? 'var(--px-color-info)'
                      : 'var(--px-color-text-disabled)',
                }}>
                  {done
                    ? '已完成'
                    : unlocked
                      ? m.id === 'match'
                        ? `待匹配`
                        : `+${m.xp}XP`
                      : m.id === 'match'
                        ? '需舰队≥2人'
                        : `需完成${m.requires === 'personality' ? '人格测试' : '组队'}`}
                </span>
              </button>
            )
          })}
        </div>
      )}

      {/* ——— 舰队 Tab ——— */}
      {tab === 'team' && <FleetPanel />}

      {/* ——— 我的 Tab ——— */}
      {tab === 'profile' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* 人格卡 */}
          <div style={{
            ...s.card, padding: 20, textAlign: 'center',
          }}>
            <div style={{ display: 'flex', justifyContent: 'center' }}>
              {personalityType?.emoji
                ? <span style={{ fontSize: 48 }}>{personalityType.emoji}</span>
                : <PlanetXIcon name="planet" size={48} color="var(--px-color-text-brand)" />}
            </div>
            <div style={{ fontSize: 'var(--lo-font-size-lg)', fontWeight: 800, color: 'var(--px-color-text-brand)', marginTop: 8 }}>
              {personalityType?.name ?? '未测试'}
            </div>
            <div style={{ fontSize: 12, color: 'var(--px-color-text-tertiary)', marginTop: 4 }}>
              {personalityType
                ? '初始假设 · 将随行为沉淀更新'
                : '完成人格冷启动测评，生成初始假设'}
            </div>
            {personalityType && (
              <div style={{ marginTop: 10, display: 'flex', gap: 10, justifyContent: 'center' }}>
                {[
                  { screen: 'timeline' as const, label: '查看时间线', color: '#C8FF50', borderColor: 'rgba(200,255,80,0.25)' },
                  { screen: 'trust' as const, label: '信任档案', color: '#C4B5FD', borderColor: 'rgba(139,130,255,0.35)' },
                ].map((btn) => (
                  <button
                    key={btn.screen}
                    type="button"
                    onClick={() => setScreen(btn.screen)}
                    style={{
                      padding: '6px 14px', borderRadius: 'var(--lo-radius-full)',
                      border: `1px solid ${btn.borderColor}`,
                      background: 'transparent', color: btn.color,
                      fontSize: 12, cursor: 'pointer',
                      display: 'inline-flex', alignItems: 'center', gap: 4,
                    }}
                  >
                    {btn.label}
                    <PlanetXIcon name="chevron-right" size={14} color="currentColor" />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* 统计面板 */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {[
              { v: missionsCompleted.length, l: '完成任务', icon: 'target' as PlanetXIconName },
              { v: teamSize, l: '舰队成员', icon: 'fleet' as PlanetXIconName },
              { v: spreadCount, l: '信号传播', icon: 'signal' as PlanetXIconName },
              { v: xp, l: '总能量', icon: 'crystal' as PlanetXIconName },
            ].map((stat, i) => (
              <div
                key={i}
                style={{ ...s.card, padding: '14px', textAlign: 'center' }}
              >
                <PlanetXIcon name={stat.icon} size={16} color="var(--px-color-text-tertiary)" />
                <div style={{
                  fontSize: 'var(--lo-font-size-3xl)', fontWeight: 'var(--lo-font-black)',
                  color: 'var(--px-color-text-brand)', marginTop: 4,
                }}>
                  {stat.v}
                </div>
                <div style={{ fontSize: 11, color: 'var(--px-color-text-tertiary)', marginTop: 2 }}>
                  {stat.l}
                </div>
              </div>
            ))}
          </div>

          {/* 登出 */}
          <button
            type="button"
            onClick={logout}
            style={{
              ...s.btnSubtle,
              width: '100%', padding: '8px 0',
              fontSize: 12, color: 'var(--px-color-text-tertiary)',
              background: 'transparent',
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6,
            }}
          >
            <PlanetXIcon name="logout" size={14} color="currentColor" />
            退出登录
          </button>
        </div>
      )}
    </div>
  )
}
