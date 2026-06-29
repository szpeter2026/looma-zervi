import { useState } from 'react'
import { usePlanetXStore, getRankName, IDENTITY_LABELS } from '../auth/planetxAuthStore'
import type { MissionId } from '../auth/planetxAuthStore'
import XPBar from '../../brand/components/XPBar'
import FleetPanel from '../../brand/components/FleetPanel'

/**
 * 主中心屏幕 — XP条 + 任务Tab + 舰队Tab + 我的Tab
 */
export default function HubScreen() {
  const [tab, setTab] = useState<'missions' | 'team' | 'profile'>('missions')
  const {
    identity, level, xp, xpToNext, missionsCompleted,
    personalityType, setScreen, logout, teamSize,
  } = usePlanetXStore()

  const missions: {
    id: MissionId; icon: string; name: string; reward: string; xp: number; requires?: MissionId
  }[] = [
    { id: 'personality', icon: '🔮', name: '星际人格测试', reward: '+50 XP · 解锁专属星球身份', xp: 50 },
    { id: 'team', icon: '🤝', name: '组建3人舰队', reward: '+80 XP · 解锁隐藏星图', xp: 80, requires: 'personality' },
    { id: 'match', icon: '🎯', name: '首次星际匹配', reward: '+100 XP · 获得匹配星图', xp: 100, requires: 'team' },
    { id: 'share', icon: '📡', name: '发送星际信号', reward: '+30 XP · 邀请好友获得额外能量', xp: 30, requires: 'personality' },
  ]

  const isMissionUnlocked = (m: typeof missions[number]) => {
    if (!m.requires) return true
    return missionsCompleted.includes(m.requires)
  }

  const isMissionDone = (id: MissionId) => missionsCompleted.includes(id)

  return (
    <div>
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: '16px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 900, color: '#C8FF50', letterSpacing: '2px', margin: 0 }}>
          Planet
          <span style={{ color: '#6B3FA0', display: 'inline-block', animation: 'xSpin 8s linear infinite' }}>X</span>
        </h1>
        <p style={{ fontSize: '12px', color: '#B8B8C8', letterSpacing: '0.2em', marginTop: '4px' }}>
          {identity ? IDENTITY_LABELS[identity] : ''}
        </p>
      </div>

      {/* XP Bar */}
      <XPBar level={level} xp={xp} xpToNext={xpToNext} />

      {/* Nav Tabs */}
      <div style={{ display: 'flex', gap: '4px', background: '#0D0D1A', borderRadius: '12px', padding: '4px', marginBottom: '16px' }}>
        {(['missions', 'team', 'profile'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              flex: 1,
              padding: '10px 0',
              borderRadius: '12px',
              fontSize: '12px',
              fontWeight: 600,
              border: 'none',
              background: tab === t ? 'rgba(200,255,80,0.1)' : 'transparent',
              color: tab === t ? '#C8FF50' : '#B8B8C8',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            {{ missions: '🎯 任务', team: '👥 舰队', profile: '🪪 我的' }[t]}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {tab === 'missions' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {missions.map((m) => {
            const locked = !isMissionUnlocked(m)
            const done = isMissionDone(m.id)
            return (
              <button
                key={m.id}
                onClick={() => { if (!locked && m.id === 'personality') setScreen('quiz') }}
                disabled={locked}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '14px',
                  borderRadius: '12px',
                  border: '1px solid rgba(255,255,255,0.1)',
                  background: '#0D0D1A',
                  textAlign: 'left',
                  cursor: locked ? 'default' : 'pointer',
                  opacity: locked ? 0.4 : 1,
                  color: 'white',
                  width: '100%',
                }}
              >
                <span style={{ fontSize: '24px', width: '44px', height: '44px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  {m.icon}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: '14px', fontWeight: 'bold' }}>{m.name}</div>
                  <div style={{ fontSize: '12px', color: '#C8FF50', marginTop: '2px' }}>🎁 {m.reward}</div>
                </div>
                <span
                  style={{
                    fontSize: '12px',
                    padding: '4px 10px',
                    borderRadius: '12px',
                    flexShrink: 0,
                    background: done ? 'rgba(200,255,80,0.15)' : 'rgba(255,255,255,0.05)',
                    color: done ? '#C8FF50' : '#B8B8C8',
                  }}
                >
                  {done ? '已完成' : locked ? `🔒 需先完成${m.requires === 'personality' ? '人格测试' : '组队'}` : '待完成'}
                </span>
              </button>
            )
          })}
        </div>
      )}

      {tab === 'team' && <FleetPanel />}

      {tab === 'profile' && (
        <div>
          <div style={{ textAlign: 'center', padding: '16px 0' }}>
            <div style={{ fontSize: '48px' }}>{personalityType?.emoji ?? '🌌'}</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#C8FF50', marginTop: '8px' }}>
              {personalityType?.name ?? '未测试'}
            </div>
            <div style={{ fontSize: '12px', color: '#B8B8C8' }}>
              {personalityType?.tagline ?? '完成人格测试获取你的星际身份'}
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
            {[
              { v: missionsCompleted.length, l: '完成任务' },
              { v: teamSize, l: '舰队成员' },
              { v: 0, l: '信号传播' },
              { v: xp, l: '总能量' },
            ].map((s, i) => (
              <div
                key={i}
                style={{
                  background: '#0D0D1A',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '12px',
                  padding: '14px',
                  textAlign: 'center',
                }}
              >
                <div style={{ fontSize: '24px', fontWeight: 900, color: '#C8FF50' }}>{s.v}</div>
                <div style={{ fontSize: '12px', color: '#B8B8C8', marginTop: '4px' }}>{s.l}</div>
              </div>
            ))}
          </div>
          <button
            onClick={logout}
            style={{
              width: '100%',
              marginTop: '16px',
              padding: '8px 0',
              borderRadius: '12px',
              fontSize: '12px',
              color: '#B8B8C8',
              border: '1px solid rgba(255,255,255,0.1)',
              background: 'transparent',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            🚪 退出登录
          </button>
        </div>
      )}
    </div>
  )
}
