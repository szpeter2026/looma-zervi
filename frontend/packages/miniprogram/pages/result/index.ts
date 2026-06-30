/**
 * Result Page - personality test result display
 */
import { store } from '../../utils/store'
import { getShareText } from '../../constants/quiz'
import type { PersonalityType } from '../../types/index'

Page({
  data: {
    emoji: '',
    name: '',
    tagline: '',
    desc: '',
    traits: [] as string[],
    hasResult: false,
  },

  onLoad() {
    const p = store.get('personalityType')
    if (p) {
      this.setData({
        emoji: p.emoji,
        name: p.name,
        tagline: p.tagline,
        desc: p.desc,
        traits: p.traits,
        hasResult: true,
      })
    }
  },

  onShareAppMessage() {
    const p = store.get('personalityType')
    if (!p) {
      return {
        title: 'PlanetX - 你的职业飞行器',
        path: '/pages/splash/index',
      }
    }
    return {
      title: `🪐 我的星际人格是「${p.name}」！测测你是什么星球身份？`,
      path: '/pages/splash/index',
      imageUrl: '',
    }
  },

  onShareTimeline() {
    const p = store.get('personalityType')
    if (!p) return { title: 'PlanetX - 你的职业飞行器' }
    return {
      title: `🪐 我的星际人格是「${p.name}」！${p.tagline}`,
    }
  },

  handleShare() {
    wx.showShareMenu({
      withShareTicket: true,
      menus: ['shareAppMessage', 'shareTimeline'],
    })
    wx.showToast({ title: '点击右上角分享给好友', icon: 'none' })
  },

  handleBack() {
    wx.switchTab({ url: '/pages/hub/index' })
  },
})
