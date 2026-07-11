import { useEffect, useRef, useState } from 'react'
import { createGameApi } from '@looma/shared-core'
import type { FleetMatchResponse } from '@looma/shared-core'
import { usePlanetXStore, getApiClient } from '../auth/planetxAuthStore'

type Phase = 'scanning' | 'result' | 'error'

/**
 * 首次星际匹配 — 舰队内人格互补配对
 */
export default function MatchScreen() {
  const { setScreen, completeMission, missionsCompleted, setAchievement } = usePlanetXStore()
  const [phase, setPhase] = useState<Phase>('scanning')
  const [statusText, setStatusText] = useState('正在扫描舰队星轨…')
  const [errorMessage, setErrorMessage] = useState('')
  const [result, setResult] = useState<FleetMatchResponse | null>(null)
  const [completing, setCompleting] = useState(false)
  const started = useRef(false)

  useEffect(() => {
    if (started.current) return
    started.current = true
    void runMatch()
  }, [])

  async function runMatch() {
    setPhase('scanning')
    setStatusText('正在扫描舰队星轨…')
    setErrorMessage('')
    setResult(null)

    await new Promise((r) => setTimeout(r, 900))
    setStatusText('计算人格互补轨道…')

    try {
      const data = await createGameApi(getApiClient()).match()
      if (!data?.matched || !data?.match) {
        throw new Error('匹配失败')
      }
      setResult(data)
      setPhase('result')
    } catch (err: any) {
      setPhase('error')
      setErrorMessage(
        err?.body?.message || err?.message || err?.error || '匹配信号中断，请稍后重试',
      )
    }
  }

  async function onConfirm() {
    if (completing) return
    setCompleting(true)
    try {
      if (!missionsCompleted.includes('match')) {
        completeMission('match')
        setAchievement({
          title: '🎯 首次星际匹配！',
          desc: '你已与另一位星际公民完成匹配 · 匹配星图已解锁',
        })
      }
      setTimeout(() => setScreen('hub'), 600)
    } finally {
      setCompleting(false)
    }
  }

  return (
    <div>
      <div style={{ textAlign: 'center', marginBottom: '8px' }}>
        <div style={{ fontSize: '12px', color: 'var(--px-color-text-muted)', letterSpacing: '0.15em' }}>
          PLANET X · MATCH
        </div>
        <h2 style={{ margin: '8px 0 0', fontSize: '22px', fontWeight: 800, color: 'var(--px-color-accent)' }}>
          首次星际匹配
        </h2>
      </div>

      {phase === 'scanning' && (
        <div style={{ textAlign: 'center', padding: '48px 12px' }}>
          <div
            style={{
              width: 96,
              height: 96,
              margin: '0 auto 24px',
              borderRadius: '50%',
              border: '3px solid rgba(200,255,80,0.25)',
              borderTopColor: 'var(--px-color-accent)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 36,
              animation: 'xSpin 1.2s linear infinite',
            }}
          >
            🎯
          </div>
          <div style={{ color: 'var(--px-color-accent)', fontSize: 14, marginBottom: 8 }}>{statusText}</div>
          <div style={{ color: 'var(--px-color-text-muted)', fontSize: 12 }}>仅在舰队范围内寻找互补人格</div>
        </div>
      )}

      {phase === 'result' && result && (
        <div style={{ animation: 'fadeIn 0.35s ease' }}>
          {result.fleet_name && (
            <div
              style={{
                textAlign: 'center',
                fontSize: 12,
                color: 'var(--px-color-text-muted)',
                marginBottom: 16,
              }}
            >
              舰队 · {result.fleet_name}
            </div>
          )}

          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
            <PairCard
              emoji={result.self.personality_emoji}
              role="你"
              type={result.self.personality_type}
            />
            <div style={{ width: 72, textAlign: 'center', flexShrink: 0 }}>
              <div style={{ fontSize: 28, fontWeight: 900, color: 'var(--px-color-accent)', lineHeight: 1 }}>
                {result.match.match_score}
              </div>
              <div style={{ fontSize: 11, color: 'var(--px-color-text-muted)', marginTop: 4 }}>契合度</div>
            </div>
            <PairCard
              emoji={result.match.personality_emoji}
              role={result.match.name}
              type={result.match.personality_type}
            />
          </div>

          <div
            style={{
              background: 'rgba(107,63,160,0.2)',
              border: '1px solid rgba(200,255,80,0.2)',
              borderRadius: 12,
              padding: '14px 16px',
              textAlign: 'center',
              fontSize: 13,
              marginBottom: 20,
              lineHeight: 1.5,
            }}
          >
            {result.match.reason}
          </div>

          <button
            onClick={onConfirm}
            disabled={completing}
            style={{
              width: '100%',
              padding: '14px 0',
              borderRadius: 12,
              border: 'none',
              background: 'var(--px-color-accent)',
              color: '#0a0a1a',
              fontWeight: 700,
              fontSize: 14,
              cursor: completing ? 'default' : 'pointer',
              opacity: completing ? 0.7 : 1,
              marginBottom: 10,
            }}
          >
            {completing ? '同步中…' : '确认匹配 · 解锁星图 +40 XP'}
          </button>
          <button
            onClick={() => setScreen('hub')}
            style={{
              width: '100%',
              padding: '10px 0',
              borderRadius: 12,
              border: '1px solid rgba(255,255,255,0.1)',
              background: 'transparent',
              color: 'var(--px-color-text-muted)',
              fontSize: 13,
              cursor: 'pointer',
            }}
          >
            稍后再说
          </button>
        </div>
      )}

      {phase === 'error' && (
        <div style={{ textAlign: 'center', padding: '40px 12px' }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>📡</div>
          <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 8 }}>匹配信号中断</div>
          <div style={{ fontSize: 13, color: 'var(--px-color-text-muted)', marginBottom: 24, lineHeight: 1.5 }}>
            {errorMessage}
          </div>
          <button
            onClick={() => { started.current = true; void runMatch() }}
            style={{
              width: '100%',
              padding: '14px 0',
              borderRadius: 12,
              border: 'none',
              background: 'var(--px-color-accent)',
              color: '#0a0a1a',
              fontWeight: 700,
              fontSize: 14,
              cursor: 'pointer',
              marginBottom: 10,
            }}
          >
            重新扫描
          </button>
          <button
            onClick={() => setScreen('hub')}
            style={{
              width: '100%',
              padding: '10px 0',
              borderRadius: 12,
              border: '1px solid rgba(255,255,255,0.1)',
              background: 'transparent',
              color: 'var(--px-color-text-muted)',
              fontSize: 13,
              cursor: 'pointer',
            }}
          >
            返回母舰
          </button>
        </div>
      )}
    </div>
  )
}

function PairCard({ emoji, role, type }: { emoji: string; role: string; type: string }) {
  return (
    <div
      style={{
        flex: 1,
        background: 'var(--px-color-bg-card)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 12,
        padding: '16px 10px',
        textAlign: 'center',
        minWidth: 0,
      }}
    >
      <div style={{ fontSize: 32, marginBottom: 6 }}>{emoji}</div>
      <div
        style={{
          fontSize: 11,
          color: 'var(--px-color-text-muted)',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
      >
        {role}
      </div>
      <div style={{ fontSize: 13, fontWeight: 600, marginTop: 4 }}>{type}</div>
    </div>
  )
}
