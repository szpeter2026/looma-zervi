/**
 * Match Page — 首次星际匹配
 * 等待动画 → POST /v1/game/match → 展示匹配星图 → mission-complete → 成就
 */
import { store } from '../../utils/store'
import { gameApi } from '../../utils/api'
import { MISSION_XP } from '../../utils/config'

Page({
  data: {
    phase: 'scanning' as 'scanning' | 'result' | 'error',
    statusText: '正在扫描舰队星轨…',
    errorMessage: '',
    selfEmoji: '🪐',
    selfType: '',
    matchEmoji: '🪐',
    matchName: '',
    matchType: '',
    matchScore: 0,
    matchReason: '',
    fleetName: '',
    completing: false,
    completed: false,
  },

  onLoad() {
    const completed = store.get('missionsCompleted') || []
    if (!completed.includes('team')) {
      wx.showToast({ title: '需先完成组建舰队', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 800)
      return
    }
    void this.startMatch()
  },

  async startMatch() {
    this.setData({
      phase: 'scanning',
      statusText: '正在扫描舰队星轨…',
      errorMessage: '',
    })

    // Brief wait for atmosphere, then call API
    await new Promise((r) => setTimeout(r, 900))
    this.setData({ statusText: '计算人格互补轨道…' })

    try {
      const data: any = await gameApi.match()
      if (!data?.matched || !data?.match) {
        throw new Error(data?.message || '匹配失败')
      }

      this.setData({
        phase: 'result',
        selfEmoji: data.self?.personality_emoji || '🪐',
        selfType: data.self?.personality_type || '',
        matchEmoji: data.match.personality_emoji || '🪐',
        matchName: data.match.name || '神秘星际公民',
        matchType: data.match.personality_type || '',
        matchScore: data.match.match_score || 0,
        matchReason: data.match.reason || '',
        fleetName: data.fleet_name || '',
      })
    } catch (err: any) {
      const msg =
        err?.body?.message ||
        err?.details?.message ||
        err?.message ||
        err?.error ||
        (typeof err === 'string' ? err : '匹配信号中断，请稍后重试')
      // MiniApiClient 常用 "HTTP 400" 作 message，优先取业务文案
      const friendly =
        typeof msg === 'string' && msg.startsWith('HTTP ')
          ? err?.details?.message || err?.body?.message || msg
          : msg
      this.setData({
        phase: 'error',
        errorMessage: friendly,
        statusText: '匹配未完成',
      })
    }
  },

  async onConfirmMatch() {
    if (this.data.completing || this.data.completed) return
    this.setData({ completing: true })

    const xpReward = MISSION_XP.match
    const alreadyDone = (store.get('missionsCompleted') || []).includes('match')

    try {
      if (!alreadyDone) {
        const data: any = await gameApi.completeMission('match', xpReward)
        store.completeMission('match')
        if (data?.total_xp != null) {
          store.applyGameProfile({
            xp: data.total_xp,
            level: data.level,
            missions_completed: store.get('missionsCompleted'),
          })
        }
        store.setAchievement({
          title: '🎯 首次星际匹配！',
          desc: '你已与另一位星际公民完成匹配 · 匹配星图已解锁',
        })
      }
      this.setData({ completed: true })
      wx.showToast({ title: '匹配星图已解锁', icon: 'success' })
      setTimeout(() => {
        wx.navigateBack()
      }, 900)
    } catch (err: any) {
      // 409 already completed — still treat as success locally
      const status = err?.status || err?.statusCode
      if (status === 409) {
        store.completeMission('match')
        store.setAchievement({
          title: '🎯 首次星际匹配！',
          desc: '你已与另一位星际公民完成匹配 · 匹配星图已解锁',
        })
        this.setData({ completed: true })
        wx.navigateBack()
        return
      }
      wx.showToast({
        title: err?.message || '回写任务失败',
        icon: 'none',
      })
    } finally {
      this.setData({ completing: false })
    }
  },

  onRetry() {
    void this.startMatch()
  },

  onBack() {
    wx.navigateBack()
  },
})
