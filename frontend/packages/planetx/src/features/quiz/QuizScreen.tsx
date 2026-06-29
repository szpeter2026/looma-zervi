import { usePlanetXStore, QUIZ_QUESTIONS } from '../auth/planetxAuthStore'

/**
 * 测评屏幕 — 8 道人格测试题
 */
export default function QuizScreen() {
  const { quizStep, answerQuiz, setScreen } = usePlanetXStore()

  if (quizStep >= QUIZ_QUESTIONS.length) {
    setScreen('result')
    return null
  }

  const q = QUIZ_QUESTIONS[quizStep]

  const handleAnswer = (trait: typeof q.options[number]['trait'], idx: number) => {
    answerQuiz(trait, idx)
    if (quizStep + 1 >= QUIZ_QUESTIONS.length) {
      setTimeout(() => setScreen('result'), 300)
    }
  }

  return (
    <div>
      <div style={{ textAlign: 'center', marginBottom: '16px' }}>
        <div style={{ fontSize: '14px', color: '#B8B8C8' }}>
          第 {quizStep + 1}/{QUIZ_QUESTIONS.length} 题
        </div>
      </div>

      <div
        style={{
          background: '#0D0D1A',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: '16px',
          padding: '20px',
        }}
      >
        {/* 进度点 */}
        <div style={{ display: 'flex', gap: '4px', marginBottom: '16px' }}>
          {QUIZ_QUESTIONS.map((_, i) => (
            <div
              key={i}
              style={{
                flex: 1,
                height: '4px',
                borderRadius: '2px',
                background:
                  i < quizStep ? '#C8FF50' : i === quizStep ? '#6B3FA0' : '#1A1A2E',
                transition: 'background-color 0.3s',
              }}
            />
          ))}
        </div>

        <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '16px', lineHeight: 1.6 }}>
          {q.q}
        </h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {q.options.map((opt, i) => (
            <button
              key={i}
              onClick={() => handleAnswer(opt.trait, i)}
              style={{
                textAlign: 'left',
                padding: '14px 16px',
                borderRadius: '12px',
                border: '1px solid rgba(255,255,255,0.1)',
                background: '#1A1A2E',
                color: 'white',
                fontSize: '14px',
                cursor: 'pointer',
                transition: 'all 0.2s',
                width: '100%',
              }}
            >
              {String.fromCharCode(65 + i)}. {opt.text}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
