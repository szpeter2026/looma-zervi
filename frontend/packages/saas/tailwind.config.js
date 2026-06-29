/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{ts,tsx,js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        // T 空间品牌色 —— 从 styles/tokens.css 对齐
        't-primary': 'var(--color-primary)',
        't-primary-dark': 'var(--color-primary-dark)',
        't-bg': 'var(--color-bg-primary)',
        't-bg-secondary': 'var(--color-bg-secondary)',
        't-text': 'var(--color-text-primary)',
        't-text-secondary': 'var(--color-text-secondary)',
        't-border': 'var(--color-border)',
        't-accent': 'var(--color-accent)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
