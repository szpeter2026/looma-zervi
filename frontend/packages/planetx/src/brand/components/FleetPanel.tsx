import { usePlanetXStore } from '../../features/auth/planetxAuthStore'
import { useRef, useCallback } from 'react'

const MEMBER_EMOJIS = ['', '🦊', '🐱', '🐼', '🐨', '🦄']
const MEMBER_NAMES = ['', '星际猫猫', '宇宙熊猫', '银河狐狸', '深空考拉']

/**
 * 舰队面板 — 创建/加入/管理 3 人舰队
 */
export default function FleetPanel() {
  const { fleet, teamSize, createFleet, joinFleet, setToast, token } = usePlanetXStore()
  const joinInputRef = useRef<HTMLInputElement>(null)

  const handleJoin = useCallback(() => {
    const code = joinInputRef.current?.value?.trim()
    if (!code) { setToast('请输入邀请码'); return }
    joinFleet(code)
  }, [joinFleet, setToast])

  const handleCreateOrCopy = useCallback(() => {
    if (!token) { setToast('请先登录'); return }
    if (fleet) {
      const link = `${window.location.origin}${window.location.pathname}?join=${fleet.invite_code}`
      navigator.clipboard?.writeText(link).then(() => setToast('📋 邀请链接已复制！'))
        .catch(() => setToast('📋 邀请码: ' + fleet.invite_code))
    } else {
      createFleet()
    }
  }, [fleet, token, createFleet, setToast])

  const btnStyle: React.CSSProperties = {
    width: '100%',
    padding: '10px 0',
    borderRadius: '12px',
    fontSize: '14px',
    fontWeight: 600,
    color: '#C8FF50',
    border: '1px solid rgba(200,255,80,0.3)',
    background: 'rgba(200,255,80,0.05)',
    cursor: 'pointer',
    transition: 'all 0.2s',
  }

  return (
    <div>
      {!fleet && (
        <div style={{ textAlign: 'center', fontSize: '14px', color: '#B8B8C8', marginBottom: '16px' }}>
          完成人格测试后解锁舰队功能
        </div>
      )}

      {fleet && (
        <>
          <div style={{ textAlign: 'center', marginBottom: '12px' }}>
            <div style={{ fontSize: '18px', fontWeight: 900, color: '#00E5FF' }}>{fleet.name}</div>
            <div
              style={{
                display: 'inline-block',
                marginTop: '6px',
                padding: '6px 16px',
                background: 'rgba(0,229,255,0.1)',
                border: '1px dashed rgba(0,229,255,0.3)',
                borderRadius: '8px',
                fontSize: '14px',
                color: '#00E5FF',
                letterSpacing: '1px',
                cursor: 'pointer',
              }}
              onClick={() => {
                navigator.clipboard?.writeText(fleet.invite_code)
                setToast('📋 邀请码已复制！')
              }}
            >
              邀请码：{fleet.invite_code}
            </div>
          </div>

          {/* 成员 */}
          <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', flexWrap: 'wrap', marginBottom: '16px' }}>
            {/* 自己 */}
            <div style={{ textAlign: 'center', width: '80px' }}>
              <div style={{
                width: '56px', height: '56px', borderRadius: '50%', background: '#1A1A2E',
                border: '2px solid #C8FF50', display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '24px', margin: '0 auto 4px',
              }}>
                🧑‍🚀
              </div>
              <div style={{ fontSize: '12px', color: '#B8B8C8' }}>我</div>
            </div>
            {/* 队员 */}
            {[2, 3].map((slot) => {
              const filled = teamSize >= slot
              const idx = slot
              return (
                <div key={slot} style={{ textAlign: 'center', width: '80px' }}>
                  <div style={{
                    width: '56px', height: '56px', borderRadius: '50%', background: '#1A1A2E',
                    border: `2px solid ${filled ? '#C8FF50' : 'rgba(255,255,255,0.1)'}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '24px', margin: '0 auto 4px',
                    opacity: filled ? 1 : 0.5,
                  }}>
                    {filled ? (MEMBER_EMOJIS[idx] ?? '👾') : '❓'}
                  </div>
                  <div style={{ fontSize: '12px', color: '#B8B8C8' }}>
                    {filled ? (MEMBER_NAMES[idx] ?? '船员') : '虚位以待'}
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}

      {/* 操作 */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <button onClick={handleCreateOrCopy} style={btnStyle}>
          {fleet ? '📋 复制邀请链接' : '🚀 创建舰队'}
        </button>

        <div style={{ display: 'flex', gap: '8px' }}>
          <input
            ref={joinInputRef}
            placeholder="输入邀请码加入舰队"
            style={{
              flex: 1,
              padding: '10px 12px',
              background: '#0D0D1A',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '12px',
              color: 'white',
              fontSize: '12px',
              outline: 'none',
            }}
          />
          <button
            onClick={handleJoin}
            style={{
              padding: '10px 16px',
              borderRadius: '12px',
              fontSize: '12px',
              fontWeight: 600,
              color: '#00E5FF',
              border: '1px solid rgba(0,229,255,0.3)',
              background: 'rgba(0,229,255,0.05)',
              cursor: 'pointer',
            }}
          >
            加入
          </button>
        </div>
      </div>
    </div>
  )
}
