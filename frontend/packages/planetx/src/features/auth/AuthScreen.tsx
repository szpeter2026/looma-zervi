import { useState } from 'react'
import { usePlanetXStore } from './planetxAuthStore'
import PlanetXButton from '../../brand/ui/PlanetXButton'
import PlanetXInput from '../../brand/ui/PlanetXInput'

/**
 * 认证屏幕 — 邮箱登录/注册/访客模式
 * 使用 PlanetX 品牌组件重构
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

  return (
    <div>
      <div style={{ textAlign: 'center', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 900, color: 'var(--px-color-accent)', letterSpacing: '2px', margin: 0 }}>
          Planet
          <span
            style={{
              color: 'var(--px-color-purple-deep)',
              display: 'inline-block',
              animation: 'xSpin 8s linear infinite',
            }}
          >
            X
          </span>
        </h1>
        <p style={{ fontSize: '12px', color: 'var(--px-color-text-muted)', letterSpacing: '0.2em', marginTop: '4px' }}>
          跃迁登录 · 登上你的飞船
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--px-spacing-md)' }}>
        <PlanetXInput
          label="📧 邮箱"
          value={email}
          onChange={setEmail}
          placeholder="你的星际邮箱"
          type="email"
        />
        
        <PlanetXInput
          label="🔐 密码"
          value={password}
          onChange={setPassword}
          placeholder="至少6位"
          type="password"
          helperText="密码至少6位字符"
        />
        
        <div style={{ display: 'flex', gap: 'var(--px-spacing-sm)' }}>
          <PlanetXButton
            variant="accent"
            fullWidth
            onClick={handleLogin}
            disabled={loading}
            loading={loading}
            leftIcon="🚀"
          >
            登录
          </PlanetXButton>
          
          <PlanetXButton
            variant="outline"
            fullWidth
            onClick={handleRegister}
            disabled={loading}
            loading={loading}
            leftIcon="✨"
          >
            注册
          </PlanetXButton>
        </div>
        
        <PlanetXButton
          variant="ghost"
          fullWidth
          onClick={() => setScreen('onboarding')}
          leftIcon="🌌"
        >
          先逛逛，稍后登录（访客模式）
        </PlanetXButton>
      </div>
    </div>
  )
}
