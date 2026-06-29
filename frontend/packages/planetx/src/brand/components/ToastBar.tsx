import { useEffect, useState } from 'react'
import { usePlanetXStore } from '../../features/auth/planetxAuthStore'

/**
 * 游戏化 Toast 提示条
 */
export default function ToastBar() {
  const toast = usePlanetXStore((s) => s.toast)
  const [visible, setVisible] = useState(false)
  const [text, setText] = useState('')

  useEffect(() => {
    if (toast) {
      setText(toast)
      setVisible(true)
      const t = setTimeout(() => setVisible(false), 2000)
      return () => clearTimeout(t)
    }
  }, [toast])

  if (!visible) return null

  return (
    <div
      style={{
        position: 'fixed',
        top: '20px',
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 200,
        padding: '12px 24px',
        borderRadius: '9999px',
        fontSize: '14px',
        fontWeight: 'bold',
        color: '#C8FF50',
        background: 'rgba(13,13,26,0.95)',
        border: '1px solid rgba(200,255,80,0.5)',
        boxShadow: '0 0 20px rgba(200,255,80,0.15)',
        animation: 'fadeIn 0.3s ease',
      }}
    >
      {text}
    </div>
  )
}
