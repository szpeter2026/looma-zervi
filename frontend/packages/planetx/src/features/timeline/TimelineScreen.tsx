import { useCallback, useEffect, useState, type CSSProperties } from 'react'
import { createTimelineApi, type TimelineEvent, type TimelineGrowthResponse } from '@looma/shared-core'
import { getApiClient, usePlanetXStore } from '../auth/planetxAuthStore'

const KIND_LABEL: Record<string, string> = {
  initial_hypothesis: '初始假设',
  quiz_completed: '完成测评',
  project_record: '项目记录',
  check_in: '每周签到',
  share_authorized: '授权分享',
  match_scan: '匹配扫描',
  resume_ingest: '简历沉淀',
  interaction_log: '对话摘要',
  mission_completed: '任务完成',
  learning_activity: '学习行为',
}

function kindLabel(kind: string) {
  return KIND_LABEL[kind] || kind
}

/**
 * 职业时间线 — 看见行为在长；人格仅为初始假设。
 */
export default function TimelineScreen() {
  const setScreen = usePlanetXStore((s) => s.setScreen)
  const setToast = usePlanetXStore((s) => s.setToast)
  const [items, setItems] = useState<TimelineEvent[]>([])
  const [growth, setGrowth] = useState<TimelineGrowthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [panel, setPanel] = useState<'none' | 'check_in' | 'project'>('none')
  const [mood, setMood] = useState('focused')
  const [focus, setFocus] = useState('')
  const [projectTitle, setProjectTitle] = useState('')
  const [projectSummary, setProjectSummary] = useState('')
  const [saving, setSaving] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState(false)

  const reload = useCallback(async () => {
    setLoading(true)
    try {
      const api = createTimelineApi(getApiClient())
      await api.backfill().catch(() => undefined)
      const [list, g] = await Promise.all([api.list({ limit: 50 }), api.growth()])
      setItems(list.items || [])
      setGrowth(g)
    } catch (e) {
      setToast('时间线加载失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }, [setToast])

  useEffect(() => {
    reload()
  }, [reload])

  const submitCheckIn = async () => {
    setSaving(true)
    try {
      const api = createTimelineApi(getApiClient())
      await api.createEvent({
        event_kind: 'check_in',
        title: '本周签到',
        summary: focus || '记录本周状态',
        payload: { mood, focus: focus || null, blocker: null },
      })
      setPanel('none')
      setFocus('')
      setToast('已记录签到，时间线又厚了一点')
      await reload()
    } catch {
      setToast('签到失败')
    } finally {
      setSaving(false)
    }
  }

  const submitProject = async () => {
    if (!projectTitle.trim()) {
      setToast('请填写项目标题')
      return
    }
    setSaving(true)
    try {
      const api = createTimelineApi(getApiClient())
      await api.createEvent({
        event_kind: 'project_record',
        title: projectTitle.trim(),
        summary: projectSummary.trim(),
        payload: {
          role: '',
          outcome: projectSummary.trim(),
          raw_text_chars: projectSummary.trim().length,
        },
      })
      setPanel('none')
      setProjectTitle('')
      setProjectSummary('')
      setToast('项目已写入时间线')
      await reload()
    } catch {
      setToast('保存失败')
    } finally {
      setSaving(false)
    }
  }

  const handleExport = useCallback(async () => {
    setSaving(true)
    try {
      const api = createTimelineApi(getApiClient())
      const data = await api.exportMyData()
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `planex-timeline-${data.user_id.slice(0, 8)}.json`
      a.click()
      URL.revokeObjectURL(url)
      setToast(`已导出 ${data.event_count} 条事件`)
    } catch {
      setToast('导出失败')
    } finally {
      setSaving(false)
    }
  }, [setToast])

  const handleDeleteAll = useCallback(async () => {
    setSaving(true)
    try {
      const api = createTimelineApi(getApiClient())
      const res = await api.deleteAllMyData()
      setToast(`已删除 ${res.deleted} 条事件`)
      setDeleteConfirm(false)
      await reload()
    } catch {
      setToast('删除失败')
    } finally {
      setSaving(false)
    }
  }, [setToast, reload])

  const handleDeleteEvent = useCallback(
    async (eventId: string) => {
      setSaving(true)
      try {
        const api = createTimelineApi(getApiClient())
        await api.deleteEvent(eventId)
        setToast('事件已删除')
        await reload()
      } catch {
        setToast('删除失败')
      } finally {
        setSaving(false)
      }
    },
    [setToast, reload],
  )

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <button
          type="button"
          onClick={() => setScreen('hub')}
          style={{
            background: 'transparent',
            border: '1px solid rgba(255,255,255,0.15)',
            color: 'var(--px-color-text-muted)',
            borderRadius: 10,
            padding: '6px 10px',
            cursor: 'pointer',
          }}
        >
          ← 返回
        </button>
        <div>
          <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--px-color-accent)' }}>职业时间线</div>
          <div style={{ fontSize: 12, color: 'var(--px-color-text-muted)' }}>行为沉淀让画像浮现</div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
        <button type="button" onClick={handleExport} disabled={saving} style={{ ...ctaStyle, flex: 1, fontSize: 12 }}>
          📥 导出数据
        </button>
        {!deleteConfirm ? (
          <button type="button" onClick={() => setDeleteConfirm(true)} style={{ ...ctaStyle, flex: 1, fontSize: 12, border: '1px solid rgba(255,80,80,0.35)', background: 'rgba(255,80,80,0.08)', color: 'rgba(255,100,100,0.9)' }}>
            🗑 清空时间线
          </button>
        ) : (
          <button type="button" onClick={handleDeleteAll} disabled={saving} style={{ ...ctaStyle, flex: 1, fontSize: 12, border: '1px solid rgba(255,80,80,0.7)', background: 'rgba(255,80,80,0.18)', color: '#f66' }}>
            {saving ? '删除中…' : '确认清空'}
          </button>
        )}
      </div>

      {growth && (
        <div
          style={{
            background: 'var(--px-color-bg-card)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 12,
            padding: 14,
            marginBottom: 14,
          }}
        >
          <div style={{ fontSize: 13, color: 'var(--px-color-text-muted)', marginBottom: 8 }}>{growth.message}</div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {growth.dimensions.map((d) => (
              <div
                key={d.id}
                style={{
                  flex: '1 1 90px',
                  background: 'rgba(255,255,255,0.04)',
                  borderRadius: 10,
                  padding: '10px 8px',
                  textAlign: 'center',
                }}
              >
                <div style={{ fontSize: 20, fontWeight: 900, color: 'var(--px-color-accent)' }}>{d.level}</div>
                <div style={{ fontSize: 11, color: 'var(--px-color-text-muted)' }}>{d.label}</div>
              </div>
            ))}
          </div>
          {growth.hypothesis_present && (
            <div style={{ marginTop: 10, fontSize: 12, color: 'rgba(200,255,80,0.75)' }}>
              人格测评权重上限 {Math.round(growth.hypothesis_weight_cap * 100)}% · 仅为初始假设
            </div>
          )}
        </div>
      )}

      <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
        <button
          type="button"
          onClick={() => setPanel(panel === 'check_in' ? 'none' : 'check_in')}
          style={ctaStyle}
        >
          每周签到
        </button>
        <button
          type="button"
          onClick={() => setPanel(panel === 'project' ? 'none' : 'project')}
          style={ctaStyle}
        >
          记项目
        </button>
      </div>

      {panel === 'check_in' && (
        <div style={formCard}>
          <div style={{ fontSize: 13, marginBottom: 8, color: 'var(--px-color-text-muted)' }}>本周状态</div>
          <select
            value={mood}
            onChange={(e) => setMood(e.target.value)}
            style={inputStyle}
          >
            <option value="focused">专注</option>
            <option value="exploring">探索中</option>
            <option value="stressed">有压力</option>
            <option value="hopeful">有期待</option>
          </select>
          <input
            value={focus}
            onChange={(e) => setFocus(e.target.value)}
            placeholder="本周关注什么？（可选）"
            style={{ ...inputStyle, marginTop: 8 }}
          />
          <button type="button" disabled={saving} onClick={submitCheckIn} style={{ ...ctaStyle, width: '100%', marginTop: 10 }}>
            {saving ? '保存中…' : '写入时间线'}
          </button>
        </div>
      )}

      {panel === 'project' && (
        <div style={formCard}>
          <input
            value={projectTitle}
            onChange={(e) => setProjectTitle(e.target.value)}
            placeholder="项目标题"
            style={inputStyle}
          />
          <textarea
            value={projectSummary}
            onChange={(e) => setProjectSummary(e.target.value)}
            placeholder="做了什么、结果如何（可选）"
            rows={3}
            style={{ ...inputStyle, marginTop: 8, resize: 'vertical' }}
          />
          <button type="button" disabled={saving} onClick={submitProject} style={{ ...ctaStyle, width: '100%', marginTop: 10 }}>
            {saving ? '保存中…' : '写入时间线'}
          </button>
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', color: 'var(--px-color-text-muted)', padding: 32 }}>加载中…</div>
      ) : items.length === 0 ? (
        <div style={{ textAlign: 'center', color: 'var(--px-color-text-muted)', padding: '36px 12px' }}>
          <div style={{ fontSize: 36, marginBottom: 8 }}>🌀</div>
          <div style={{ fontSize: 14, marginBottom: 6 }}>时间线还是空的</div>
          <div style={{ fontSize: 12, lineHeight: 1.6 }}>
            先完成人格测评作冷启动，或用上方「每周签到 / 记项目」开始沉淀行为。
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {items.map((ev) => (
            <div
              key={ev.id}
              style={{
                background: 'var(--px-color-bg-card)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 12,
                padding: 12,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                <span
                  style={{
                    fontSize: 11,
                    padding: '2px 8px',
                    borderRadius: 999,
                    background:
                      ev.weight_role === 'hypothesis'
                        ? 'rgba(255,180,80,0.15)'
                        : 'rgba(200,255,80,0.12)',
                    color:
                      ev.weight_role === 'hypothesis'
                        ? 'rgba(255,200,120,0.95)'
                        : 'var(--px-color-accent)',
                  }}
                >
                  {kindLabel(ev.event_kind)}
                  {ev.weight_role === 'hypothesis' ? ' · 假设' : ''}
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: 11, color: 'var(--px-color-text-muted)' }}>
                    {(ev.occurred_at || '').slice(0, 10)}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleDeleteEvent(ev.id)}
                    disabled={saving}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: 'rgba(255,255,255,0.25)',
                      cursor: 'pointer',
                      fontSize: 14,
                      padding: '0 2px',
                      lineHeight: 1,
                    }}
                    title="删除此事件"
                  >
                    ×
                  </button>
                </div>
              </div>
              <div style={{ fontSize: 14, fontWeight: 700, marginTop: 8 }}>{ev.title || kindLabel(ev.event_kind)}</div>
              {ev.summary ? (
                <div style={{ fontSize: 12, color: 'var(--px-color-text-muted)', marginTop: 4, lineHeight: 1.5 }}>
                  {ev.summary}
                </div>
              ) : null}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

const ctaStyle: CSSProperties = {
  flex: 1,
  padding: '10px 0',
  borderRadius: 12,
  border: '1px solid rgba(200,255,80,0.35)',
  background: 'rgba(200,255,80,0.1)',
  color: 'var(--px-color-accent)',
  fontWeight: 700,
  fontSize: 13,
  cursor: 'pointer',
}

const formCard: CSSProperties = {
  background: 'var(--px-color-bg-card)',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: 12,
  padding: 12,
  marginBottom: 14,
}

const inputStyle: CSSProperties = {
  width: '100%',
  boxSizing: 'border-box',
  background: 'rgba(0,0,0,0.25)',
  border: '1px solid rgba(255,255,255,0.12)',
  borderRadius: 10,
  padding: '10px 12px',
  color: 'var(--px-color-text-bright)',
  fontSize: 13,
}
