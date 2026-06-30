import { usePlanetXStore, IDENTITY_LABELS } from '../auth/planetxAuthStore'
import type { Identity } from '../auth/planetxAuthStore'

/**
 * 身份选择屏幕 — 星际身份三选一 + T空间入口
 */
export default function OnboardingScreen() {
  const { setIdentity, setScreen } = usePlanetXStore()

  const handleEnterTSpace = () => {
    const saasUrl = import.meta.env.VITE_SAAS_URL || 'http://localhost:5174/'
    window.location.href = saasUrl
  }

  const handleSelect = (type: Identity) => {
    setIdentity(type)
    setScreen('hub')
  }

  const cards: { type: Identity; emoji: string; desc: string; tag: { text: string; bg: string; color: string } }[] = [
    {
      type: 'explorer', emoji: '🚀',
      desc: '正在寻找新的职业星球 · 渴望找到属于自己的轨道',
      tag: { text: '🔥 最多人选择', bg: 'rgba(255,45,149,0.15)', color: '#FF2D95' },
    },
    {
      type: 'captain', emoji: '👨‍✈️',
      desc: '组建你的3人舰队 · 带领船员探索未知星域',
      tag: { text: '👥 组队模式', bg: 'rgba(0,229,255,0.15)', color: '#00E5FF' },
    },
    {
      type: 'wanderer', emoji: '🌌',
      desc: '不着急着陆 · 先在各个星球间随意漂流看看',
      tag: { text: '✨ 佛系模式', bg: 'rgba(255,45,149,0.15)', color: '#FF2D95' },
    },
  ]

  const cardBaseStyle: React.CSSProperties = {
    width: '100%',
    textAlign: 'left',
    background: '#0D0D1A',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '16px',
    padding: '16px',
    marginBottom: '12px',
    cursor: 'pointer',
    transition: 'all 0.2s',
    position: 'relative',
    overflow: 'hidden',
  }

  return (
    <div>
      <div style={{ textAlign: 'center', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 900, color: '#C8FF50', letterSpacing: '2px', margin: 0 }}>
          Planet
          <span
            style={{
              color: '#6B3FA0',
              display: 'inline-block',
              animation: 'xSpin 8s linear infinite',
            }}
          >
            X
          </span>
        </h1>
        <p style={{ fontSize: '12px', color: '#B8B8C8', letterSpacing: '0.2em', marginTop: '4px' }}>
          选择你的星际身份
        </p>
      </div>

      <p style={{ textAlign: 'center', fontSize: '18px', fontWeight: 'bold', marginBottom: '16px' }}>
        你正在寻找什么？
      </p>

      {cards.map((c) => (
        <button key={c.type} onClick={() => handleSelect(c.type)} style={cardBaseStyle}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>{c.emoji}</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{IDENTITY_LABELS[c.type].split('·')[0]}</div>
          <div style={{ fontSize: '12px', color: '#B8B8C8', marginTop: '4px' }}>{c.desc}</div>
          <span
            style={{
              display: 'inline-block',
              marginTop: '8px',
              padding: '4px 12px',
              borderRadius: '12px',
              fontSize: '12px',
              fontWeight: 600,
              background: c.tag.bg,
              color: c.tag.color,
            }}
          >
            {c.tag.text}
          </span>
        </button>
      ))}

      {/* T空间入口 */}
      <div style={{ textAlign: 'center', marginTop: '16px', paddingTop: '16px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
        <button
          onClick={handleEnterTSpace}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 24px',
            borderRadius: '24px',
            fontSize: '14px',
            fontWeight: 600,
            background: 'linear-gradient(90deg, rgba(107,63,160,0.3), rgba(200,255,80,0.08))',
            border: '1px solid rgba(200,255,80,0.2)',
            color: '#C8FF50',
            cursor: 'pointer',
          }}
        >
          🪐 进入 T 空间 · Navigator 叙事体验
        </button>
        <p style={{ fontSize: '12px', color: '#B8B8C8', marginTop: '8px', opacity: 0.6 }}>
          与 AI 向导对话 · 探索六域 · 10分钟叙事体验
        </p>
      </div>
    </div>
  )
}
