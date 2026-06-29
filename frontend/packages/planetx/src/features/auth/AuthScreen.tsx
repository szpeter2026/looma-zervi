import { useState } from 'react'
import { usePlanetXStore } from './planetxAuthStore'

/**
 * 认证屏幕 — 邮箱登录/注册/访客模式
 */
export default function AuthScreen() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { login, register, setScreen, setToast } = usePlanetXStore()

  const handleLogin = async () => {
    if (!email || !password) { setToast('请填写邮箱和密码'); return }
    setLoading(true)
    await login(email, password)
    setLoading(false)
  }

  const handleRegister = async () => {
    if (!email || !password) { setToast('请填写邮箱和密码'); return }
    if (password.length < 6) { setToast('密码至少6位'); return }
    setLoading(true)
    await register(email, password)
    setLoading(false)
  }

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '12px',
    background: '#0D0D1A',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '12px',
    color: 'white',
    fontSize: '14px',
    outline: 'none',
    boxSizing: 'border-box',
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
          跃迁登录 · 登上你的飞船
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div>
          <label style={{ fontSize: '12px', color: '#B8B8C8', display: 'block', marginBottom: '4px' }}>📧 邮箱</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="你的星际邮箱"
            style={inputStyle}
          />
        </div>
        <div>
          <label style={{ fontSize: '12px', color: '#B8B8C8', display: 'block', marginBottom: '4px' }}>🔐 密码</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="至少6位"
            style={inputStyle}
          />
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={handleLogin}
            disabled={loading}
            style={{
              flex: 1,
              padding: '12px 0',
              borderRadius: '16px',
              fontWeight: 'bold',
              fontSize: '14px',
              color: 'white',
              background: 'linear-gradient(90deg, #6B3FA0, #8B5CF6)',
              border: 'none',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.5 : 1,
              transition: 'all 0.2s',
            }}
          >
            🚀 登录
          </button>
          <button
            onClick={handleRegister}
            disabled={loading}
            style={{
              flex: 1,
              padding: '12px 0',
              borderRadius: '16px',
              fontWeight: 'bold',
              fontSize: '14px',
              color: '#B8B8C8',
              border: '1px solid rgba(255,255,255,0.1)',
              background: 'transparent',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.5 : 1,
              transition: 'all 0.2s',
            }}
          >
            ✨ 注册
          </button>
        </div>
        <button
          onClick={() => setScreen('onboarding')}
          style={{
            width: '100%',
            padding: '8px 0',
            borderRadius: '16px',
            fontWeight: 'bold',
            fontSize: '12px',
            color: '#C8FF50',
            border: '1px solid rgba(200,255,80,0.2)',
            background: 'rgba(200,255,80,0.05)',
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
        >
          🌌 先逛逛，稍后登录（访客模式）
        </button>
      </div>
    </div>
  )
}
