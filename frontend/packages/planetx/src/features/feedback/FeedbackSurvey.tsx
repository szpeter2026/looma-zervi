/**
 * FeedbackSurvey — Phase 0 收敛点反馈收集组件
 * Ownership: Jason
 *
 * 在 Navigator 叙事体验的收敛点展示，收集：
 *   1. 打动率 — "Navigator 让你有感觉吗？"
 *   2. 台词复述 — "还记得 Navigator 说过哪句话吗？"
 *   3. 重玩意愿 — "想换一个域再来一次吗？"
 *   4. 分享行为 — "分享给朋友"
 *   5. 开放反馈 — "还有什么想说的？"
 *
 * 使用示例:
 *   <FeedbackSurvey
 *     sessionId={sessionId}
 *     domain="职业域"
 *     onDismiss={() => navigate('/')}
 *   />
 */
import { useState } from 'react'
import { createApiClient, createNarrativeApi } from '@looma/shared-core'

const API_BASE = import.meta.env.VITE_API_BASE ?? ''

interface Props {
  sessionId: string
  domain: string
  onDismiss: () => void
}

/** Navigator 共情锚点 — 每个域对应的价值张力提示 */
const DOMAIN_HOOKS: Record<string, string> = {
  '职业域': '我们追求「好工作」时，究竟在追求什么？',
  '诗域': '有些说不出的话，诗替你说了。',
  '自我域': '标签可以是镜子，但镜子不是你。',
  '身份域': '你展示的，是你想成为的——还是别人想看到的？',
  '信任域': '在这里，你可以选择被看见多少。',
  '迷雾域': '有些问题没有答案。Navigator 知道这一点。',
  'career': '我们追求「好工作」时，究竟在追求什么？',
  'poetry': '有些说不出的话，诗替你说了。',
  'self': '标签可以是镜子，但镜子不是你。',
  'identity': '你展示的，是你想成为的——还是别人想看到的？',
  'trust': '在这里，你可以选择被看见多少。',
  'unknown': '有些问题没有答案。Navigator 知道这一点。',
}

export default function FeedbackSurvey({ sessionId, domain, onDismiss }: Props) {
  const [step, setStep] = useState(0)
  const [resonated, setResonated] = useState<boolean | null>(null)
  const [navigatorQuote, setNavigatorQuote] = useState('')
  const [wouldReplay, setWouldReplay] = useState<number | null>(null)
  const [shared, setShared] = useState(false)
  const [openFeedback, setOpenFeedback] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)

  const api = createApiClient({ baseURL: API_BASE })
  const narrativeApi = createNarrativeApi(api)

  const submit = async () => {
    setSubmitting(true)
    try {
      await narrativeApi.feedback({
        session_id: sessionId,
        resonated: !!resonated,
        navigator_quote: navigatorQuote || undefined,
        would_replay: wouldReplay ?? undefined,
        shared,
        share_channel: shared ? 'link' : undefined,
        open_feedback: openFeedback || undefined,
      })
    } catch {
      // Submit silently fails — don't block the user
    } finally {
      setSubmitting(false)
      setDone(true)
    }
  }

  const handleShare = () => {
    setShared(true)
    // Native share API if available
    const shareData = {
      title: 'PlanetX · Navigator 叙事体验',
      text: `我在 PlanetX 遇到了 Navigator。${DOMAIN_HOOKS[domain] || ''}`,
      url: window.location.origin,
    }
    if (navigator.share) {
      navigator.share(shareData).catch(() => {})
    } else {
      navigator.clipboard.writeText(`${shareData.text}\n${shareData.url}`).catch(() => {})
    }
  }

  if (done) {
    return (
      <div style={containerStyle}>
        <p style={doneTextStyle}>✨ 感谢你的反馈</p>
        <p style={subTextStyle}>你的感受会帮助 Navigator 变得更好</p>
        <button onClick={onDismiss} style={primaryBtnStyle}>
          完成
        </button>
      </div>
    )
  }

  return (
    <div style={containerStyle}>
      {/* Step 0: Resonated */}
      {step === 0 && (
        <>
          <h2 style={questionStyle}>Navigator 让你有感觉吗？</h2>
          <p style={hookStyle}>{DOMAIN_HOOKS[domain] || ''}</p>
          <div style={btnRowStyle}>
            <button
              onClick={() => { setResonated(true); setStep(1) }}
              style={{ ...choiceBtnStyle, borderColor: resonated === true ? 'var(--color-primary)' : '#333' }}
            >
              ✨ 有，触动了我
            </button>
            <button
              onClick={() => { setResonated(false); setStep(1) }}
              style={{ ...choiceBtnStyle, borderColor: resonated === false ? 'var(--color-text-muted)' : '#333' }}
            >
              还好，没什么感觉
            </button>
          </div>
        </>
      )}

      {/* Step 1: Navigator quote recall */}
      {step === 1 && (
        <>
          <h2 style={questionStyle}>
            {resonated ? '还记得 Navigator 对你说过哪句话吗？' : 'Navigator 有哪句话让你有点印象？'}
          </h2>
          <textarea
            value={navigatorQuote}
            onChange={(e) => setNavigatorQuote(e.target.value)}
            placeholder="写下你记得的那句话，哪怕只是大意..."
            rows={3}
            style={textareaStyle}
          />
          <div style={btnRowStyle}>
            <button onClick={() => setStep(0)} style={ghostBtnStyle}>返回</button>
            <button onClick={() => setStep(2)} style={primaryBtnStyle}>继续</button>
          </div>
        </>
      )}

      {/* Step 2: Would replay */}
      {step === 2 && (
        <>
          <h2 style={questionStyle}>想换一个域，再来一次吗？</h2>
          <p style={subTextStyle}>六域对应六种不同的价值取向。每次体验都不一样。</p>
          <div style={columnBtnStyle}>
            {[
              { val: 2, label: '🔄 想来，换个域试试' },
              { val: 1, label: '🤔 也许会，以后再说' },
              { val: 0, label: '不太想，一次就够了' },
            ].map((opt) => (
              <button
                key={opt.val}
                onClick={() => { setWouldReplay(opt.val); setStep(3) }}
                style={{
                  ...choiceBtnStyle,
                  borderColor: wouldReplay === opt.val ? 'var(--color-primary)' : '#333',
                }}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <button onClick={() => setStep(1)} style={{ ...ghostBtnStyle, marginTop: 12 }}>返回</button>
        </>
      )}

      {/* Step 3: Share + open feedback */}
      {step === 3 && (
        <>
          <h2 style={questionStyle}>最后一步</h2>

          {/* Share CTA */}
          <div style={shareBoxStyle}>
            <p style={subTextStyle}>觉得朋友也会喜欢 Navigator？</p>
            <button onClick={handleShare} style={shareBtnStyle}>
              📤 分享给朋友
            </button>
            {shared && <p style={{ ...subTextStyle, marginTop: 8 }}>已分享 ✨</p>}
          </div>

          {/* Open feedback */}
          <div style={{ marginTop: 20 }}>
            <p style={subTextStyle}>还有什么想说的？（选填）</p>
            <textarea
              value={openFeedback}
              onChange={(e) => setOpenFeedback(e.target.value)}
              placeholder="任何感受、建议、吐槽……"
              rows={3}
              style={textareaStyle}
            />
          </div>

          <div style={{ ...btnRowStyle, marginTop: 20 }}>
            <button onClick={() => setStep(2)} style={ghostBtnStyle}>返回</button>
            <button onClick={submit} disabled={submitting} style={primaryBtnStyle}>
              {submitting ? '提交中...' : '提交反馈'}
            </button>
          </div>
        </>
      )}
    </div>
  )
}

// ── inline styles (matching PlanetX dark sci-fi theme) ──

const containerStyle: React.CSSProperties = {
  maxWidth: 400,
  margin: '0 auto',
  padding: '32px 24px',
  backgroundColor: 'var(--color-bg-card, #1a1a2e)',
  borderRadius: 16,
  border: '1px solid rgba(255,255,255,0.08)',
}

const questionStyle: React.CSSProperties = {
  fontSize: 20,
  fontWeight: 600,
  color: 'var(--color-text-primary, #e0e0e0)',
  marginBottom: 12,
  lineHeight: 1.5,
}

const hookStyle: React.CSSProperties = {
  fontSize: 14,
  color: 'var(--color-primary, #7c6ff7)',
  marginBottom: 24,
  fontStyle: 'italic',
}

const subTextStyle: React.CSSProperties = {
  fontSize: 14,
  color: 'var(--color-text-muted, #888)',
  marginBottom: 12,
}

const doneTextStyle: React.CSSProperties = {
  fontSize: 22,
  fontWeight: 600,
  color: 'var(--color-text-primary, #e0e0e0)',
  textAlign: 'center',
  marginBottom: 8,
}

const btnRowStyle: React.CSSProperties = {
  display: 'flex',
  gap: 12,
  justifyContent: 'center',
}

const columnBtnStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: 10,
}

const choiceBtnStyle: React.CSSProperties = {
  flex: 1,
  padding: '14px 20px',
  fontSize: 15,
  color: 'var(--color-text-primary, #e0e0e0)',
  backgroundColor: 'transparent',
  border: '1.5px solid #333',
  borderRadius: 12,
  cursor: 'pointer',
  transition: 'border-color 0.2s, background 0.2s',
}

const primaryBtnStyle: React.CSSProperties = {
  padding: '12px 28px',
  fontSize: 15,
  fontWeight: 500,
  color: '#fff',
  backgroundColor: 'var(--color-primary, #7c6ff7)',
  border: 'none',
  borderRadius: 12,
  cursor: 'pointer',
}

const ghostBtnStyle: React.CSSProperties = {
  padding: '12px 20px',
  fontSize: 14,
  color: 'var(--color-text-muted, #888)',
  backgroundColor: 'transparent',
  border: '1px solid #333',
  borderRadius: 12,
  cursor: 'pointer',
}

const textareaStyle: React.CSSProperties = {
  width: '100%',
  padding: 12,
  fontSize: 14,
  color: 'var(--color-text-primary, #e0e0e0)',
  backgroundColor: 'var(--color-bg-surface, #0f0f23)',
  border: '1px solid #333',
  borderRadius: 10,
  resize: 'vertical',
  outline: 'none',
  boxSizing: 'border-box',
  fontFamily: 'inherit',
}

const shareBoxStyle: React.CSSProperties = {
  padding: '16px 20px',
  backgroundColor: 'var(--color-bg-surface, #0f0f23)',
  borderRadius: 12,
  border: '1px solid rgba(124,111,247,0.2)',
  textAlign: 'center',
}

const shareBtnStyle: React.CSSProperties = {
  padding: '10px 24px',
  fontSize: 14,
  color: 'var(--color-primary, #7c6ff7)',
  backgroundColor: 'rgba(124,111,247,0.1)',
  border: '1px solid rgba(124,111,247,0.3)',
  borderRadius: 10,
  cursor: 'pointer',
}
