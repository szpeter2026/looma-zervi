import { getRankName } from '../../features/auth/planetxAuthStore'

interface Props {
  level: number
  xp: number
  xpToNext: number
  /** 紧凑模式：不含外框 padding，适合嵌入 HubScreen Hero */
  compact?: boolean
  /** 是否显示等级徽章 */
  showBadge?: boolean
}

/**
 * XPBar — 经验条 + 等级徽章
 *
 * 联动 PlanetX 主题：
 *   - 底色 → var(--px-color-surface-card)
 *   - 边框 → var(--px-color-border-subtle)
 *   - 进度填充 → var(--px-gradient-primary)
 *   - 文本色 → 二级/三级
 *
 * compact 模式下内嵌于 Hero，无需外框。
 */
export default function XPBar({ level, xp, xpToNext, compact = false, showBadge = true }: Props) {
  const pct = Math.min(100, (xp / xpToNext) * 100)
  const rankName = getRankName(level)

  return (
    <div
      style={{
        background: compact ? 'transparent' : 'var(--px-color-surface-card)',
        border: compact ? 'none' : '1px solid var(--px-color-border-subtle)',
        borderRadius: 'var(--lo-radius-lg)',
        padding: compact ? '0' : '12px',
        marginBottom: compact ? '0' : '16px',
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
        <span style={{ fontSize: 'var(--lo-font-size-xs)', color: 'var(--px-color-text-secondary)', letterSpacing: '0.5px' }}>
          {!compact && '⚡ '}星际能量
        </span>

        {showBadge && (
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 4,
              background: 'var(--px-gradient-streak)',
              borderRadius: 'var(--lo-radius-full)',
              padding: '3px 10px',
              fontSize: 11,
              color: '#fff',
              fontWeight: 700,
            }}
          >
            🪐 Lv.{level} {rankName ? `· ${rankName}` : ''}
          </span>
        )}

        <span style={{ fontSize: 'var(--lo-font-size-xs)', color: 'var(--px-color-text-brand)', fontWeight: 700 }}>
          {xp} / {xpToNext} XP
        </span>
      </div>

      {/* Progress track */}
      <div
        style={{
          height: 6,
          background: compact ? 'rgba(255,255,255,0.08)' : 'var(--px-color-surface-root)',
          borderRadius: 'var(--lo-radius-full)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            height: '100%',
            borderRadius: 'var(--lo-radius-full)',
            background: 'var(--px-gradient-primary)',
            transition: 'width 0.8s ease',
            width: `${pct}%`,
            boxShadow: '0 0 8px rgba(108,99,255,0.4)',
          }}
        />
      </div>
    </div>
  )
}
