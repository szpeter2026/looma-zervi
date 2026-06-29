import { getRankName } from '../../features/auth/planetxAuthStore'

interface Props {
  level: number
  xp: number
  xpToNext: number
}

/**
 * XP 经验条 + 等级徽章
 */
export default function XPBar({ level, xp, xpToNext }: Props) {
  const pct = Math.min(100, (xp / xpToNext) * 100)

  return (
    <div
      style={{
        background: '#0D0D1A',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: '12px',
        padding: '12px',
        marginBottom: '16px',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '8px',
        }}
      >
        <span style={{ fontSize: '12px', color: '#B8B8C8', letterSpacing: '1px' }}>⚡ 星际能量</span>
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            background: 'linear-gradient(135deg, rgba(107,63,160,0.5), rgba(200,255,80,0.15))',
            border: '1px solid rgba(200,255,80,0.25)',
            borderRadius: '16px',
            padding: '4px 12px',
            fontSize: '12px',
            color: '#C8FF50',
            fontWeight: 'bold',
          }}
        >
          🪐 Lv.{level} · {getRankName(level)}
        </span>
        <span style={{ fontSize: '12px', color: '#C8FF50', fontWeight: 'bold' }}>
          {xp} / {xpToNext} XP
        </span>
      </div>
      <div
        style={{
          height: '6px',
          background: '#1A1A2E',
          borderRadius: '9999px',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            height: '100%',
            borderRadius: '9999px',
            background: 'linear-gradient(90deg, #6B3FA0, #C8FF50)',
            transition: 'width 0.8s ease',
            width: `${pct}%`,
          }}
        />
      </div>
    </div>
  )
}
