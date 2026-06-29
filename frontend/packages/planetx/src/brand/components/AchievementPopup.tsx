import { usePlanetXStore } from '../../features/auth/planetxAuthStore'

/**
 * 成就弹窗
 */
export default function AchievementPopup() {
  const achievement = usePlanetXStore((s) => s.achievement)
  const visible = !!achievement

  return (
    <div
      style={{
        position: 'fixed',
        top: '50%',
        left: '50%',
        transform: visible ? 'translate(-50%, -50%) scale(1)' : 'translate(-50%, -50%) scale(0.8)',
        zIndex: 100,
        maxWidth: '300px',
        width: '90%',
        textAlign: 'center',
        background: 'rgba(13,13,26,0.97)',
        border: '1px solid #FFD700',
        borderRadius: '16px',
        padding: '24px',
        boxShadow: '0 0 60px rgba(255,215,0,0.3)',
        transition: 'all 0.4s ease',
        opacity: visible ? 1 : 0,
        pointerEvents: 'none',
      }}
    >
      <div style={{ fontSize: '48px', marginBottom: '8px' }}>🏆</div>
      <div style={{ fontSize: '18px', fontWeight: 900, color: '#FFD700' }}>{achievement?.title}</div>
      <div style={{ fontSize: '14px', color: '#B8B8C8', marginTop: '4px' }}>{achievement?.desc}</div>
    </div>
  )
}
