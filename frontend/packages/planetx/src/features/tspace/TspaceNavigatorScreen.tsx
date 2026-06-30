/**
 * T空间 Navigator 叙事页面 — Act 1 完整交互体验
 *
 * 实现规格:
 *   - 6域选择面板 (图标 + 名称 + 情感弧线 + 颜色)
 *   - 动态进度指示器 (单域7步 / 跨域11步)
 *   - 叙事面板 (Navigator 行内引用样式)
 *   - 选择项交互 (高亮选中)
 *   - 收敛点质感展示
 *   - 跨域回声展示 (职业域→诗域)
 *   - 状态栏 (当前域 + 进度文案)
 *   - 重置/对比控制
 *   - Phase 0 反馈收集 (Act 1 完成后自动弹出)
 *
 * Ref: tspace_act1_prototype.html / GDD §5.1 / GDD §9.2
 */
import { useState, useEffect, useCallback, useRef } from 'react'
import StarBackground from '../../brand/components/StarBackground'
import FeedbackSurvey from '../feedback/FeedbackSurvey'
import type {
  Act1SessionState,
  Act1AdvanceResponse,
  Act1ChoiceResponse,
  ConvergenceTexture,
} from '@looma/shared-core'

// ── Domain definitions (hardcoded for offline-first rendering) ──

const DOMAINS = [
  { key: '职业域', icon: '💼', name: '职业域', color: '#4ecdc4', emotion: '焦虑→希望', hint: '一份完美JD背后的隐藏代价', isMVP: true },
  { key: '身份域', icon: '🪪', name: '身份域', color: '#ff6b6b', emotion: '回顾→重构', hint: '过去的自己走了出来' },
  { key: '诗域',   icon: '📜', name: '诗域',   color: '#f9ca24', emotion: '孤独→共鸣', hint: '墙上半首被擦掉的诗' },
  { key: '信任域', icon: '⚖️', name: '信任域', color: '#a29bfe', emotion: '怀疑→确认', hint: '审判庭上你认识被告' },
  { key: '自我域', icon: '🪞', name: '自我域', color: '#fd79a8', emotion: '困惑→认知', hint: '镜子给你没选的标签' },
  { key: '迷雾域', icon: '🌫️', name: '迷雾域', color: '#636e72', emotion: '迷失→探索', hint: '非Navigator的声音在等你' },
] as const

const SINGLE_STEPS = [
  { id: 0, label: '开场' }, { id: 1, label: '信号' },
  { id: 2, label: '初遇' }, { id: 3, label: '选择' },
  { id: 4, label: '后果' }, { id: 5, label: '收敛' },
  { id: 6, label: '钩子' },
]

const CROSS_STEPS = [
  { id: 0, label: '开场' }, { id: 1, label: '信号' },
  { id: 2, label: '初遇' }, { id: 3, label: '选择' },
  { id: 4, label: '后果' }, { id: 5, label: '跨域' },
  { id: 6, label: '诗遇' }, { id: 7, label: '诗选' },
  { id: 8, label: '诗果' }, { id: 9, label: '收敛' },
  { id: 10, label: '钩子' },
]

// ── Styles ──

const CSS = {
  page: {
    minHeight: '100vh', background: '#0a0a0f', color: '#c8c8d4',
    display: 'flex', justifyContent: 'center', overflowX: 'hidden', position: 'relative' as const,
    fontFamily: "-apple-system, 'SF Pro Display', 'PingFang SC', 'Microsoft YaHei', sans-serif",
  },
  container: {
    position: 'relative' as const, zIndex: 1, width: '100%', maxWidth: '460px',
    padding: '20px 16px', display: 'flex', flexDirection: 'column' as const, gap: '16px',
  },
  header: {
    background: '#12121a', border: '1px solid #1e1e2e', borderRadius: '12px',
    padding: '16px', textAlign: 'center' as const,
  },
  panel: {
    background: '#12121a', border: '1px solid #1e1e2e', borderRadius: '12px', padding: '16px',
  },
  sectionTitle: {
    fontSize: '0.75rem', fontWeight: 600, color: '#6a6a7a',
    textTransform: 'uppercase' as const, letterSpacing: '0.05em', marginBottom: '12px',
  },
}

// ── Component ──

export default function TspaceNavigatorScreen() {
  // State
  const [sessionId, setSessionId] = useState<string>('')
  const [step, setStep] = useState(-1)            // -1 = domain selection
  const [domain, setDomain] = useState('')
  const [hasCrossDomain, setHasCrossDomain] = useState(false)
  const [chosenOption, setChosenOption] = useState<number | null>(null)
  const [crossChosen, setCrossChosen] = useState<number | null>(null)
  const [narrative, setNarrative] = useState('')
  const [navigatorLine, setNavigatorLine] = useState('')
  const [choices, setChoices] = useState<Array<{ index: number; label: string }>>([])
  const [convergenceTexture, setConvergenceTexture] = useState<ConvergenceTexture | null>(null)
  const [imprintName, setImprintName] = useState('')
  const [echoTriggered, setEchoTriggered] = useState(false)
  const [loading, setLoading] = useState(false)
  const [visitedDomains, setVisitedDomains] = useState<Set<string>>(new Set())
  const [showComparison, setShowComparison] = useState(false)
  const [showVerdict, setShowVerdict] = useState(false)
  const [showFeedback, setShowFeedback] = useState(false)
  const [comparisonData, setComparisonData] = useState<ConvergenceTexture[]>([])

  const apiBase = useRef(import.meta.env.VITE_API_BASE || '/api')
  const steps = hasCrossDomain ? CROSS_STEPS : SINGLE_STEPS
  const finalStep = steps.length - 1  // last step = 完成
  const isComplete = step >= finalStep && step >= 0

  // ── API helpers ──

  const apiPost = useCallback(async (path: string, body: Record<string, unknown>) => {
    const token = localStorage.getItem('looma_token') || ''
    const res = await fetch(`${apiBase.current}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify(body),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.message || `HTTP ${res.status}`)
    }
    return res.json()
  }, [])

  // ── Select domain ──

  const handleSelectDomain = useCallback(async (domainKey: string) => {
    setLoading(true)
    setChosenOption(null)
    setCrossChosen(null)
    setNarrative('')
    setNavigatorLine('')
    setChoices([])
    setConvergenceTexture(null)
    setImprintName('')
    setEchoTriggered(false)
    setShowComparison(false)
    setShowVerdict(false)
    setShowFeedback(false)

    try {
      // Start narrative session
      const startRes = await apiPost('/v1/narrative/start', { domain: domainKey })
      const sid = startRes.session_id

      // Initialize Act 1 state
      const initRes = await apiPost('/v1/narrative/engine/act1/init', { session_id: sid, domain: domainKey }) as Act1SessionState
      setSessionId(sid)
      setDomain(domainKey)
      setHasCrossDomain(!!initRes.has_cross_domain)
      setStep(0)

      // Auto-advance to step 1 (signal)
      const r1 = await apiPost('/v1/narrative/engine/act1/advance', { session_id: sid }) as Act1AdvanceResponse
      setStep(r1.step)
      if (r1.navigator_line) setNavigatorLine(r1.navigator_line)
      if (r1.narrative) setNarrative(r1.narrative)
    } catch (e: any) {
      console.error('Domain select failed:', e)
    } finally {
      setLoading(false)
    }
  }, [apiPost])

  // ── Next step ──

  const handleNext = useCallback(async () => {
    if (!sessionId || step >= finalStep) return
    setLoading(true)
    try {
      const r = await apiPost('/v1/narrative/engine/act1/advance', { session_id: sessionId }) as Act1AdvanceResponse
      setStep(r.step)
      if (r.navigator_line) setNavigatorLine(r.navigator_line)
      if (r.narrative) setNarrative(r.narrative)
      if (r.choices) setChoices(r.choices)
      if (r.convergence_texture) setConvergenceTexture(r.convergence_texture)
      if (r.imprint_name) setImprintName(r.imprint_name)
      if (r.echo_triggered) setEchoTriggered(true)

      // Track completion and show feedback
      if (r.step >= finalStep) {
        setVisitedDomains(prev => new Set([...prev, domain]))
        setShowFeedback(true)
      }
    } catch (e: any) {
      console.error('Advance failed:', e)
    } finally {
      setLoading(false)
    }
  }, [sessionId, step, domain, finalStep, apiPost])

  // ── Make choice ──

  const handleChoice = useCallback(async (choiceIndex: number) => {
    const isChoiceStep = (!hasCrossDomain && step === 3) || (hasCrossDomain && step === 7)
    if (!sessionId || !isChoiceStep) return

    if (!hasCrossDomain || step === 3) {
      setChosenOption(choiceIndex)
    } else {
      setCrossChosen(choiceIndex)
    }
    setLoading(true)
    try {
      const r = await apiPost('/v1/narrative/engine/act1/choice', {
        session_id: sessionId,
        choice_index: choiceIndex,
      }) as Act1ChoiceResponse

      if (r.error) {
        console.error('Choice error:', r.error)
        return
      }

      setStep(r.step)
      setImprintName(r.imprint_name)
      if (r.consequence) setNarrative(r.consequence)
      setChoices([])
    } catch (e: any) {
      console.error('Choice failed:', e)
    } finally {
      setLoading(false)
    }
  }, [sessionId, step, hasCrossDomain, apiPost])

  // ── Reset ──

  const handleReset = useCallback(async (hard = false) => {
    if (!sessionId) return
    try {
      await apiPost('/v1/narrative/engine/act1/reset', { session_id: sessionId, hard })
      if (hard) {
        setDomain('')
        setStep(-1)
        setHasCrossDomain(false)
      } else {
        setStep(0)
      }
      setChosenOption(null)
      setCrossChosen(null)
      setNarrative('')
      setNavigatorLine('')
      setChoices([])
      setConvergenceTexture(null)
      setImprintName('')
      setEchoTriggered(false)
      setShowComparison(false)
      setShowVerdict(false)
      setShowFeedback(false)
    } catch (e: any) {
      console.error('Reset failed:', e)
    }
  }, [sessionId, apiPost])

  // ── Comparison ──

  const handleShowComparison = useCallback(async () => {
    try {
      const token = localStorage.getItem('looma_token') || ''
      const res = await fetch(`${apiBase.current}/v1/narrative/engine/act1/content`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = await res.json()
      setComparisonData(data.convergence_comparison || [])
      setShowComparison(true)
      if (visitedDomains.size >= 6) setShowVerdict(true)
    } catch (e) {
      console.error('Comparison load failed:', e)
    }
  }, [apiBase, visitedDomains])

  // ── Derive UI state ──

  const isDomainSelection = step === -1
  const canAdvance = step >= 0 && step < finalStep && !loading
  const isWaitingChoice = ((!hasCrossDomain && step === 3) || (hasCrossDomain && step === 7)) &&
    chosenOption === null && crossChosen === null
  const domainInfo = DOMAINS.find(d => d.key === domain)
  const currentStepLabel = steps[Math.min(step, finalStep)]?.label || ''
  const currentStepIndex = Math.min(step, finalStep)

  // ── Render ──

  return (
    <div style={CSS.page}>
      <StarBackground />
      <div style={CSS.container}>
        {/* Header */}
        <div style={CSS.header}>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#fff', margin: 0, letterSpacing: '-0.02em' }}>
            PlanetX T空间 · Act 1
          </h1>
          <p style={{ fontSize: '0.75rem', color: '#6a6a7a', margin: '4px 0 0' }}>
            Navigator 叙事体验 — 六域一问验证
          </p>
        </div>

        {/* Domain Selector */}
        {isDomainSelection && (
          <div style={CSS.panel}>
            <div style={CSS.sectionTitle}>🎯 选择一个域进入</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              {DOMAINS.map(d => (
                <button
                  key={d.key}
                  onClick={() => handleSelectDomain(d.key)}
                  disabled={loading}
                  style={{
                    padding: '12px 10px', borderRadius: '10px',
                    border: `1px solid #1e1e2e`, borderLeft: `3px solid ${d.color}`,
                    background: d.isMVP ? '#1a1a28' : '#161620',
                    color: '#c8c8d4',
                    fontSize: '0.8rem', cursor: 'pointer', textAlign: 'left' as const,
                    transition: 'all 0.2s', fontFamily: 'inherit',
                    opacity: loading ? 0.5 : 1,
                    position: 'relative' as const,
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.borderColor = '#7c6ff7'
                    e.currentTarget.style.background = '#252540'
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.borderColor = '#1e1e2e'
                    e.currentTarget.style.background = d.isMVP ? '#1a1a28' : '#161620'
                  }}
                >
                  {d.isMVP && (
                    <span style={{
                      position: 'absolute' as const, top: '4px', right: '6px',
                      fontSize: '0.58rem', color: '#55efc4',
                      background: 'rgba(85,239,196,0.12)',
                      padding: '1px 5px', borderRadius: '4px',
                      border: '1px solid rgba(85,239,196,0.25)',
                    }}>MVP</span>
                  )}
                  <div style={{ fontSize: '1.3rem', marginBottom: '2px' }}>{d.icon}</div>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem', color: '#fff' }}>{d.name}</div>
                  <div style={{ fontSize: '0.65rem', color: '#6a6a7a', marginTop: '2px' }}>{d.emotion}</div>
                  <div style={{ fontSize: '0.62rem', color: '#6a6a7a', marginTop: '2px', lineHeight: 1.3 }}>{d.hint}</div>
                </button>
              ))}
            </div>
            <p style={{ textAlign: 'center', fontSize: '0.7rem', color: '#6a6a7a', marginTop: '12px' }}>
              💼 职业域为 MVP 推荐路径（含跨域回声） · 其它域也可进入
            </p>
          </div>
        )}

        {/* Step indicator */}
        {!isDomainSelection && (
          <div style={CSS.panel}>
            <div style={{ ...CSS.sectionTitle, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>📍 当前进度</span>
              {hasCrossDomain && (
                <span style={{ fontSize: '0.6rem', color: '#55efc4', fontWeight: 400 }}>
                  🔗 跨域路径
                </span>
              )}
            </div>
            <div style={{ display: 'flex', gap: '3px', marginBottom: '8px' }}>
              {steps.map((s, idx) => {
                let bg = '#1e1e2e'
                if (s.id < step) bg = '#55efc4'
                else if (s.id === step) bg = '#7c6ff7'
                // Highlight cross-domain steps differently
                if (hasCrossDomain && s.id >= 5 && s.id <= 8) {
                  if (s.id < step) bg = '#f9ca24'
                  else if (s.id === step && s.id >= 5) bg = '#fdcb6e'
                }
                return (
                  <div key={s.id} title={s.label} style={{
                    flex: 1, height: '4px', borderRadius: '2px', background: bg,
                    boxShadow: s.id === step ? '0 0 8px rgba(124,111,247,0.5)' : undefined,
                    transition: 'all 0.3s',
                  }} />
                )
              })}
            </div>
            <div style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              padding: '8px 12px', background: '#1a1a28', borderRadius: '8px',
              border: '1px solid #1e1e2e', fontSize: '0.75rem',
              flexWrap: 'wrap' as const,
            }}>
              <div style={{
                width: '8px', height: '8px', borderRadius: '50%',
                background: isComplete ? '#55efc4' : '#7c6ff7',
                flexShrink: 0,
              }} />
              <span style={{ color: '#c8c8d4' }}>
                {isComplete
                  ? `✅ Act 1 完成 · ${domainInfo?.name || ''}路径`
                  : `${currentStepLabel} · ${domainInfo?.icon || ''} ${domainInfo?.name || domain}`}
              </span>
              {echoTriggered && (
                <span style={{
                  fontSize: '0.65rem', color: '#f9ca24',
                  background: 'rgba(249,202,36,0.1)',
                  padding: '1px 6px', borderRadius: '4px',
                  border: '1px solid rgba(249,202,36,0.25)',
                }}>⚡ 跨域回声</span>
              )}
            </div>
          </div>
        )}

        {/* Narrative Panel */}
        {!isDomainSelection && (
          <div style={CSS.panel}>
            <div style={CSS.sectionTitle}>📖 叙事面板</div>

            {/* Navigator line */}
            {navigatorLine && (
              <div style={{
                padding: '12px 14px', margin: '10px 0',
                background: 'rgba(124, 111, 247, 0.08)',
                borderLeft: '3px solid #7c6ff7', borderRadius: '0 6px 6px 0',
                fontStyle: 'italic', color: '#e0dfff', fontSize: '0.88rem',
                lineHeight: 1.7,
              }}>
                {navigatorLine}
              </div>
            )}

            {/* Narrative text */}
            {narrative && (
              <div style={{
                fontSize: '0.88rem', lineHeight: 1.7, color: '#d0d0dc',
                whiteSpace: 'pre-line' as const, margin: '10px 0',
              }}
                dangerouslySetInnerHTML={{ __html: narrative }}
              />
            )}

            {/* Domain encounter preview (step 0) */}
            {step === 0 && (
              <div style={{ color: '#6a6a7a', fontSize: '0.8rem', fontStyle: 'italic', marginTop: '8px' }}>
                情感弧线：{domainInfo?.emotion || ''}
              </div>
            )}

            {/* Convergence texture */}
            {convergenceTexture && (
              <div style={{
                padding: '12px', marginTop: '12px',
                border: '1px solid #e17055', borderRadius: '8px',
                background: 'rgba(225,112,85,0.05)',
              }}>
                <div style={{ fontSize: '0.7rem', color: '#e17055', fontWeight: 600, marginBottom: '6px' }}>
                  🎭 当前质感 · {domainInfo?.name || domain}
                </div>
                <div style={{ fontSize: '0.82rem', color: '#ddd', lineHeight: 1.6 }}>
                  <strong>理解：</strong>{convergenceTexture.interpretation}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#6a6a7a', marginTop: '4px' }}>
                  <strong>情感：</strong>{convergenceTexture.emotion}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#6a6a7a', fontStyle: 'italic' }}>
                  内心：{convergenceTexture.inner_thought}
                </div>
              </div>
            )}

            {/* Imprint feedback */}
            {imprintName && (
              <div style={{
                marginTop: '10px', padding: '6px 12px',
                background: 'rgba(124,111,247,0.08)', borderRadius: '6px',
                fontSize: '0.78rem', color: '#a29bfe',
                border: '1px solid rgba(124,111,247,0.2)',
              }}>
                你获得了价值印记：<strong>{imprintName}</strong>
              </div>
            )}
          </div>
        )}

        {/* Choice Panel */}
        {!isDomainSelection && choices.length > 0 && (
          <div style={CSS.panel}>
            <div style={CSS.sectionTitle}>⚡ 做出你的选择</div>
            {choices.map(c => (
              <button
                key={c.index}
                onClick={() => handleChoice(c.index)}
                disabled={loading || chosenOption !== null}
                style={{
                  display: 'block', width: '100%', padding: '10px 14px',
                  margin: '6px 0', borderRadius: '8px',
                  border: chosenOption === c.index
                    ? '1px solid #7c6ff7'
                    : '1px solid #1e1e2e',
                  background: chosenOption === c.index
                    ? 'rgba(124, 111, 247, 0.15)'
                    : 'rgba(255,255,255,0.03)',
                  color: '#c8c8d4', fontSize: '0.82rem', cursor: 'pointer',
                  textAlign: 'left' as const, fontFamily: 'inherit',
                  transition: 'all 0.2s',
                  opacity: loading ? 0.5 : 1,
                }}
                onMouseEnter={e => {
                  if (chosenOption !== null) return
                  e.currentTarget.style.borderColor = '#7c6ff7'
                  e.currentTarget.style.background = 'rgba(124, 111, 247, 0.1)'
                }}
                onMouseLeave={e => {
                  if (chosenOption !== null) return
                  e.currentTarget.style.borderColor = '#1e1e2e'
                  e.currentTarget.style.background = 'rgba(255,255,255,0.03)'
                }}
              >
                {c.label}
              </button>
            ))}
          </div>
        )}

        {/* Controls */}
        {!isDomainSelection && !showFeedback && (
          <div style={CSS.panel}>
            <div style={CSS.sectionTitle}>🎮 控制</div>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' as const }}>
              {!isComplete && (
                <button
                  onClick={handleNext}
                  disabled={!canAdvance || isWaitingChoice || loading}
                  style={{
                    flex: 1, padding: '10px 16px', borderRadius: '8px',
                    border: '1px solid #7c6ff7', background: '#7c6ff7', color: '#fff',
                    fontWeight: 600, fontSize: '0.82rem', cursor: 'pointer',
                    fontFamily: 'inherit',
                    opacity: (!canAdvance || isWaitingChoice || loading) ? 0.4 : 1,
                    transition: 'all 0.2s',
                  }}
                >
                  {isWaitingChoice ? '请先做出选择 ↑' : loading ? '...' : '下一步 →'}
                </button>
              )}
              <button
                onClick={() => handleReset(false)}
                style={{
                  padding: '10px 14px', borderRadius: '8px',
                  border: '1px solid #1e1e2e', background: '#1a1a28',
                  color: '#c8c8d4', fontSize: '0.78rem', cursor: 'pointer',
                  fontFamily: 'inherit',
                }}
              >
                🔄 重置路径
              </button>
              <button
                onClick={() => handleReset(true)}
                style={{
                  padding: '10px 14px', borderRadius: '8px',
                  border: '1px solid rgba(255, 118, 117, 0.3)',
                  background: '#1a1a28', color: '#ff7675',
                  fontSize: '0.78rem', cursor: 'pointer', fontFamily: 'inherit',
                }}
              >
                🗑️ 换一个域
              </button>
            </div>
            <div style={{ marginTop: '8px' }}>
              <button
                onClick={handleShowComparison}
                style={{
                  width: '100%', padding: '10px', borderRadius: '8px',
                  border: '1px solid #1e1e2e', background: '#1a1a28',
                  color: '#c8c8d4', fontSize: '0.78rem', cursor: 'pointer',
                  fontFamily: 'inherit',
                }}
              >
                🔬 对比全部质感差异
              </button>
            </div>
          </div>
        )}

        {/* Phase 0 Feedback Survey — shown after Act 1 completion */}
        {showFeedback && sessionId && (
          <div style={CSS.panel}>
            <div style={{
              ...CSS.sectionTitle, marginBottom: '4px',
              color: '#55efc4', fontSize: '0.78rem',
            }}>
              📊 体验反馈
            </div>
            <p style={{
              fontSize: '0.7rem', color: '#6a6a7a', marginBottom: '16px',
              textAlign: 'center' as const,
            }}>
              Act 1 完成！在离开之前，Navigator 想知道你的感受
            </p>
            <FeedbackSurvey
              sessionId={sessionId}
              domain={domain}
              onDismiss={() => {
                setShowFeedback(false)
              }}
            />
          </div>
        )}

        {/* Comparison Panel */}
        {showComparison && comparisonData.length > 0 && (
          <div style={CSS.panel}>
            <div style={{ ...CSS.sectionTitle, marginBottom: '4px' }}>
              🔬 收敛点质感差异对比
            </div>
            <div style={{ fontSize: '0.7rem', color: '#6a6a7a', marginBottom: '12px' }}>
              同一句台词：「你……以前来过这里吗？」 — 六种不同质感
            </div>
            {comparisonData.map(item => {
              const visited = visitedDomains.has(item.domain)
              return (
                <div key={item.domain} style={{
                  padding: '12px', borderRadius: '8px',
                  border: visited ? '1px solid #e17055' : '1px solid #1e1e2e',
                  borderLeft: `3px solid ${item.color}`,
                  background: visited ? 'rgba(225,112,85,0.08)' : '#1a1a28',
                  marginBottom: '8px', transition: 'all 0.3s',
                  boxShadow: visited ? '0 0 16px rgba(225,112,85,0.15)' : undefined,
                }}>
                  <div style={{ fontSize: '0.7rem', fontWeight: 600, color: item.color, marginBottom: '4px' }}>
                    {item.icon} {item.domain} {visited ? '✓' : ''}
                  </div>
                  <div style={{ fontSize: '0.82rem', color: '#ddd', lineHeight: 1.5 }}>
                    <strong>理解：</strong>{item.interpretation}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: '#6a6a7a', marginTop: '4px' }}>
                    情感：{item.emotion}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: '#6a6a7a', fontStyle: 'italic' }}>
                    {item.inner_thought}
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Verification Verdict */}
        {showVerdict && (
          <div style={CSS.panel}>
            <div style={CSS.sectionTitle}>✅ 验证结论</div>
            <div style={{
              padding: '14px', borderRadius: '8px',
              background: 'rgba(85, 239, 196, 0.08)',
              border: '1px solid rgba(85, 239, 196, 0.3)',
              color: '#55efc4', fontSize: '0.82rem', lineHeight: 1.6,
            }}>
              <strong>✅ 验证通过 — P5支柱「六域一问」成立</strong><br /><br />
              <strong>验证结果：</strong><br />
              同一句台词「你……以前来过这里吗？」，在六条域路径中产生了六种<strong>显著不同</strong>的理解质感：
              <br /><br />
              <table style={{ width: '100%', fontSize: '0.75rem', borderCollapse: 'collapse' as const }}>
                <thead>
                  <tr style={{ color: '#6a6a7a' }}>
                    <td style={{ padding: '2px 4px' }}>域</td>
                    <td style={{ padding: '2px 4px' }}>解读</td>
                    <td style={{ padding: '2px 4px' }}>距离真相</td>
                  </tr>
                </thead>
                <tbody>
                  <tr><td style={{ padding: '2px 4px' }}>💼 职业</td><td style={{ padding: '2px 4px' }}>面试陷阱题</td><td style={{ padding: '2px 4px', color: '#ff7675' }}>远</td></tr>
                  <tr><td style={{ padding: '2px 4px' }}>🪪 身份</td><td style={{ padding: '2px 4px' }}>读了简历</td><td style={{ padding: '2px 4px', color: '#ff7675' }}>远</td></tr>
                  <tr><td style={{ padding: '2px 4px' }}>📜 诗</td><td style={{ padding: '2px 4px' }}>诗意隐喻</td><td style={{ padding: '2px 4px', color: '#fdcb6e' }}>中</td></tr>
                  <tr><td style={{ padding: '2px 4px' }}>⚖️ 信任</td><td style={{ padding: '2px 4px' }}>审查我</td><td style={{ padding: '2px 4px', color: '#fdcb6e' }}>中</td></tr>
                  <tr><td style={{ padding: '2px 4px' }}>🪞 自我</td><td style={{ padding: '2px 4px' }}>人格测试题</td><td style={{ padding: '2px 4px', color: '#fdcb6e' }}>中</td></tr>
                  <tr><td style={{ padding: '2px 4px' }}>🌫️ 迷雾</td><td style={{ padding: '2px 4px' }}><strong>它真的在问</strong></td><td style={{ padding: '2px 4px', color: '#55efc4' }}>近</td></tr>
                </tbody>
              </table>
              <br />
              <strong>设计验证：</strong><br />
              • 六种解读各不相同，无重复感受 ✓<br />
              • 迷雾域独享「真相」质感，形成体验分层 ✓<br />
              • 收敛点在物理上是同一节点，在感知上是六个节点 ✓<br />
              • 「终点可收敛但路径必须有质感差异」原则得到验证 ✓
              <br /><br />
              <span style={{ fontSize: '0.7rem', color: '#6a6a7a' }}>
                ⚠️ 注意：纸面原型验证通过 ≠ 实际运行时成立。实际引擎中的措辞密度、
                情感铺垫强度会影响质感差异的幅度。
              </span>
            </div>
          </div>
        )}

        {/* Bottom spacing */}
        <div style={{ height: '16px' }} />
      </div>
    </div>
  )
}
