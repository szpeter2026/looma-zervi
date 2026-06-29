import { useEffect, useState } from 'react'

/**
 * 加载屏幕 — 跃迁引擎预热动画
 */
export default function LoadingScreen() {
  const [dots, setDots] = useState('')

  useEffect(() => {
    let count = 0
    const timer = setInterval(() => {
      count = (count + 1) % 4
      setDots('.'.repeat(count))
    }, 400)
    return () => clearInterval(timer)
  }, [])

  return (
    <div style={{ textAlign: 'center', padding: '64px 0' }}>
      <div
        style={{
          fontSize: '48px',
          display: 'inline-block',
          animation: 'xSpin 4s linear infinite',
        }}
      >
        🪐
      </div>
      <div style={{ fontSize: '18px', fontWeight: 'bold', marginTop: '16px', color: '#C8FF50' }}>
        跃迁引擎预热中{dots}
      </div>
      <div style={{ fontSize: '12px', color: '#B8B8C8', marginTop: '8px' }}>
        正在校准星际坐标
      </div>
    </div>
  )
}
