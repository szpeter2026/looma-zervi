import { useState, useCallback } from 'react'
import { usePlanetXStore, getShareText } from '../../features/auth/planetxAuthStore'

type SharePlatform = 'wechat' | 'xiaohongshu' | 'weibo' | 'copy'

const PLATFORMS: { id: SharePlatform; icon: string; name: string; tag: string }[] = [
  { id: 'wechat', icon: '💬', name: '微信', tag: '朋友圈/群聊' },
  { id: 'xiaohongshu', icon: '📕', name: '小红书', tag: '带话题标签' },
  { id: 'weibo', icon: '📢', name: '微博', tag: '超话扩散' },
  { id: 'copy', icon: '📋', name: '复制文案', tag: '通用版本' },
]

/**
 * 多平台分享面板
 */
export default function SharePanel() {
  const [show, setShow] = useState(false)
  const [activePlatform, setActivePlatform] = useState<SharePlatform>('wechat')
  const { personalityType, setToast, getInviteUrl, completeMission, addXP } = usePlanetXStore()

  const p = personalityType ?? { name: '未知', emoji: '🌌', tagline: '', desc: '', traits: [] }
  const shareText = getShareText(activePlatform, p, getInviteUrl())

  const handlePlatformSelect = useCallback((platform: SharePlatform) => {
    setActivePlatform(platform)
    const text = getShareText(platform, p, getInviteUrl())
    navigator.clipboard?.writeText(text).then(() => {
      setToast(`📋 ${PLATFORMS.find((fp) => fp.id === platform)?.name}文案已复制！`)
      completeMission('share')
      addXP(30)
    }).catch(() => {})
  }, [p, getInviteUrl, setToast, completeMission, addXP])

  if (!show) {
    return (
      <div style={{ textAlign: 'center', marginTop: '12px' }}>
        <button
          onClick={() => setShow(true)}
          style={{
            padding: '10px 24px',
            borderRadius: '16px',
            fontWeight: 'bold',
            fontSize: '14px',
            color: '#C8FF50',
            border: '1px solid rgba(200,255,80,0.3)',
            background: 'rgba(200,255,80,0.05)',
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
        >
          📡 分享到星际频道
        </button>
      </div>
    )
  }

  return (
    <div
      style={{
        background: '#0D0D1A',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: '16px',
        padding: '16px',
        marginTop: '12px',
        animation: 'fadeIn 0.3s ease',
      }}
    >
      <h3 style={{ fontSize: '14px', color: '#B8B8C8', textAlign: 'center', marginBottom: '12px', letterSpacing: '1px' }}>
        📡 选择星际频道发送信号
      </h3>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginBottom: '12px' }}>
        {PLATFORMS.map((pf) => (
          <button
            key={pf.id}
            onClick={() => handlePlatformSelect(pf.id)}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '4px',
              padding: '12px',
              borderRadius: '12px',
              transition: 'all 0.2s',
              fontSize: '12px',
              border: `1px solid ${activePlatform === pf.id ? '#C8FF50' : 'rgba(255,255,255,0.1)'}`,
              background: activePlatform === pf.id ? 'rgba(200,255,80,0.05)' : '#1A1A2E',
              cursor: 'pointer',
              color: '#B8B8C8',
            }}
          >
            <span style={{ fontSize: '24px' }}>{pf.icon}</span>
            <span>{pf.name}</span>
            <span style={{ color: 'rgba(200,255,80,0.7)', fontSize: '9px' }}>{pf.tag}</span>
          </button>
        ))}
      </div>

      <div
        style={{
          background: '#1A1A2E',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: '8px',
          padding: '12px',
          maxHeight: '112px',
          overflowY: 'auto',
        }}
      >
        <pre style={{
          fontSize: '12px',
          color: '#B8B8C8',
          lineHeight: 1.6,
          whiteSpace: 'pre-wrap',
          fontFamily: 'system-ui, sans-serif',
          margin: 0,
        }}>
          {shareText.split('\n').map((line, i) => (
            <span key={i}>
              {line.startsWith('#')
                ? <span style={{ color: '#C8FF50', fontWeight: 600 }}>{line}</span>
                : line}
              {i < shareText.split('\n').length - 1 && '\n'}
            </span>
          ))}
        </pre>
      </div>
    </div>
  )
}
