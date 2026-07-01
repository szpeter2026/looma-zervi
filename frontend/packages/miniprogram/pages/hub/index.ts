/**
 * Hub Page - TabBar home (index 0)
 * XP bar + mission list + fleet panel + profile stats
 */
import { eventBus } from '../../utils/event-bus'
import { store } from '../../utils/store'
import { IDENTITY_LABELS } from '../../types/index'
import type { MissionId, Identity } from '../../types/index'

Page({
  data: {
    // Game state
    level: 1,
    xp: 0,
    xpToNext: 100,
    identity: '' as string,
    identityLabel: '',
    personalityName: '',
    personalityEmoji: '',
    personalityTagline: '',
    missionsCompleted: [] as string[],
    teamSize: 0,

    // UI
    activeTab: 'missions',
    missions: [
      { id: 'personality', icon: '🔮', name: '星际人格测试', reward: '+50 XP · 解锁专属星球身份', xp: 50, requires: '' },
      { id: 'team', icon: '🤝', name: '组建3人舰队', reward: '+80 XP · 解锁隐藏星图', xp: 80, requires: 'personality' },
      { id: 'match', icon: '🎯', name: '首次星际匹配', reward: '+100 XP · 获得匹配星图', xp: 100, requires: 'team' },
      { id: 'share', icon: '📡', name: '发送星际信号', reward: '+30 XP · 邀请好友获得额外能量', xp: 30, requires: 'personality' },
    ],
  },

  _profileHandler: null as any,
  _profileLoaded: false,

  onLoad() {
    console.log('[Hub] onLoad')
    this._profileHandler = () => this.refreshFromStore()
    eventBus.on('profile:loaded', this._profileHandler)
  },

  onShow() {
    console.log('[Hub] onShow')

    // Update tab bar selected state (custom tab bar)
    const tabBar = (this as any).getTabBar?.()
    if (tabBar) tabBar.setData({ selected: 0 })

    this.refreshFromStore()

    // Lazy-load profile from backend (deferred from app.onLaunch for performance)
    if (!this._profileLoaded) {
      this._profileLoaded = true
      const app = getApp() as any
      if (app.loadProfile) {
        console.log('[Hub] Triggering loadProfile from hub page')
        app.loadProfile()
      }
    }
  },

  onUnload() {
    if (this._profileHandler) eventBus.off('profile:loaded', this._profileHandler)
  },

  refreshFromStore() {
    const s = store.getAll()
    this.setData({
      level: s.level,
      xp: s.xp,
      xpToNext: s.xpToNext,
      identity: s.identity || '',
      identityLabel: s.identity ? IDENTITY_LABELS[s.identity] : '',
      personalityName: s.personalityType?.name || '',
      personalityEmoji: s.personalityType?.emoji || '',
      personalityTagline: s.personalityType?.tagline || '',
      missionsCompleted: s.missionsCompleted,
      teamSize: s.teamSize,
    })
  },

  switchTab(e: any) {
    this.setData({ activeTab: e.currentTarget.dataset.tab })
  },

  onMissionTap(e: any) {
    const id = e.currentTarget.dataset.id as MissionId
    const mission = this.data.missions.find((m) => m.id === id)
    if (!mission) return

    // Check if locked
    if (mission.requires && !this.data.missionsCompleted.includes(mission.requires)) {
      wx.showToast({ title: '需先完成前置任务', icon: 'none' })
      return
    }

    // Check if already done
    if (this.data.missionsCompleted.includes(id)) {
      wx.showToast({ title: '已完成', icon: 'none' })
      return
    }

    // Route based on mission type
    if (id === 'personality') {
      wx.navigateTo({ url: '/pages/quiz/index' })
    } else if (id === 'team') {
      wx.showToast({ title: '舰队功能即将上线', icon: 'none' })
    } else if (id === 'match') {
      wx.showToast({ title: '匹配功能即将上线', icon: 'none' })
    } else if (id === 'share') {
      if (!this.data.personalityName && !this.data.missionsCompleted.includes('personality')) {
        wx.showToast({ title: '请先完成人格测试', icon: 'none' })
        return
      }
      wx.navigateTo({ url: '/pages/result/index' })
    }
  },
})
