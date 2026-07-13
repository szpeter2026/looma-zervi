import { useEffect, useRef, useState } from 'react'
import { usePlanetXStore } from './planetxAuthStore'
import PlanetXButton from '../../brand/ui/PlanetXButton'
import PlanetXInput from '../../brand/ui/PlanetXInput'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (cfg: Record<string, unknown>) => void
          renderButton: (el: HTMLElement, cfg: Record<string, unknown>) => void
          prompt: () => void
        }
      }
    }
  }
}

/**
 * 认证屏幕 — 邮箱登录/注册 + 海外 Google（配置了 VITE_GOOGLE_CLIENT_ID 时显示）
 */
export default function AuthScreen() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { login, register, loginWithGoogle, setScreen, setToast } = usePlanetXStore()
  const googleBtnRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID || !googleBtnRef.current) return

    const scriptId = 'gis-client'
    const mountButton = () => {
      if (!window.google?.accounts?.id || !googleBtnRef.current) return
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: async (resp: { credential?: string }) => {
          if (!resp?.credential) {
            setToast('Google credential missing')
            return
          }
          setLoading(true)
          await loginWithGoogle(resp.credential)
          setLoading(false)
        },
      })
      googleBtnRef.current.innerHTML = ''
      window.google.accounts.id.renderButton(googleBtnRef.current, {
        theme: 'outline',
        size: 'large',
        width: 320,
        text: 'continue_with',
        shape: 'pill',
      })
    }

    if (document.getElementById(scriptId)) {
      mountButton()
      return
    }
    const s = document.createElement('script')
    s.id = scriptId
    s.src = 'https://accounts.google.com/gsi/client'
    s.async = true
    s.onload = mountButton
    document.head.appendChild(s)
  }, [loginWithGoogle, setToast])

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
          Career growth partner · sign in
        </p>
      </div>

      {GOOGLE_CLIENT_ID && (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, marginBottom: 20 }}>
          <div ref={googleBtnRef} />
          <div style={{ fontSize: 11, color: 'var(--px-color-text-muted)' }}>or continue with email</div>
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--px-spacing-md)' }}>
        <PlanetXInput
          label="📧 Email"
          value={email}
          onChange={setEmail}
          placeholder="you@example.com"
          type="email"
        />

        <PlanetXInput
          label="🔐 Password"
          value={password}
          onChange={setPassword}
          placeholder="至少6位 / min 6 chars"
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
