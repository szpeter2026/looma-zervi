import { useEffect, useRef } from 'react'

/**
 * 星空动画背景 — 80 颗脉冲星星
 */
export default function StarBackground() {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const container = ref.current
    if (!container) return
    const stars: HTMLDivElement[] = []
    for (let i = 0; i < 80; i++) {
      const s = document.createElement('div')
      const size = Math.random() * 3 + 1
      s.style.cssText = `
        position:absolute; border-radius:50%;
        width:${size}px; height:${size}px;
        left:${Math.random() * 100}%; top:${Math.random() * 100}%;
        background:#C8FF50; pointer-events:none;
        animation: starPulse ${Math.random() * 3 + 2}s ease-in-out infinite;
        animation-delay: ${Math.random() * 4}s;
      `
      container.appendChild(s)
      stars.push(s)
    }
    return () => stars.forEach((s) => s.remove())
  }, [])

  return (
    <div
      ref={ref}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        overflow: 'hidden',
        pointerEvents: 'none',
        zIndex: 0,
      }}
    />
  )
}
