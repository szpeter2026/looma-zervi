/**
 * Result Page - personality test result + share (裂变 / HR 链接)
 */
import { store } from '../../utils/store'
import { gameApi, referralApi } from '../../utils/api'
import { getShareText } from '../../constants/quiz'
import { SAAS_BASE } from '../../utils/config'
import { trackMiniEvent } from '../../utils/analytics'
import type { PersonalityType } from '../../types/index'

Page({
  data: {
    emoji: '',
    name: '',
    tagline: '',
    desc: '',
    traits: [] as string[],
    hasResult: false,
    referralCode: '',
    profileShareCode: '',
    hrShareUrl: '',
    loading: true,
  },

  onLoad() {
    void this.loadResult()
  },

  async loadResult() {
    const local = store.get('personalityType')
    if (local) {
      this.applyPersonality(local)
      await this.ensureShareCodes()
      this.setData({ loading: false })
      return
    }

    try {
      const data = await gameApi.getProfile()
      store.applyGameProfile(data)
      const hydrated = store.get('personalityType')
      if (hydrated) {
        this.applyPersonality(hydrated)
        await this.ensureShareCodes()
      }
    } catch {
      /* no backend profile */
    }
    this.setData({ loading: false })
  },

  applyPersonality(p: PersonalityType) {
    this.setData({
      emoji: p.emoji,
      name: p.name,
      tagline: p.tagline,
      desc: p.desc,
      traits: p.traits,
      hasResult: true,
    })
  },

  async ensureShareCodes() {
    const token = store.get('token')
    if (!token || token === 'dev-mode-token') return

    try {
      const [refResp, profileResp] = await Promise.all([
        referralApi.create('referral'),
        referralApi.create('profile_share'),
      ])
      const referralCode = refResp.code
      const profileShareCode = profileResp.code
      const hrShareUrl = `${SAAS_BASE.replace(/\/$/, '')}/candidate/share/${profileShareCode}`
      this.setData({ referralCode, profileShareCode, hrShareUrl })
    } catch {
      /* best-effort */
    }
  },

  onShareAppMessage() {
    const p = store.get('personalityType')
    const ref = this.data.referralCode
    const path = ref ? `/pages/splash/index?ref=${ref}` : '/pages/splash/index'
    if (!p) {
      return { title: 'PlanetX - 你的职业飞行器', path }
    }
    return {
      title: `🪐 我的星际人格是「${p.name}」！测测你是什么星球身份？`,
      path,
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
    const p = store.get('personalityType')
    if (!p) return
    const ref = this.data.referralCode
    const inviteUrl = ref ? `pages/splash/index?ref=${ref}` : 'pages/splash/index'
    const text = getShareText(p, inviteUrl)
    wx.setClipboardData({
      data: text,
      success: () => {
        wx.showToast({ title: '分享文案已复制', icon: 'success' })
        store.completeMission('share')
        gameApi.completeMission('share', 30).catch(() => {})
      },
    })
  },

  handleCopyHrLink() {
    const url = this.data.hrShareUrl
    if (!url) {
      wx.showToast({ title: '链接生成中，请稍候', icon: 'none' })
      void this.ensureShareCodes()
      return
    }
    wx.setClipboardData({
      data: url,
      success: () => {
        wx.showToast({ title: 'HR 画像链接已复制', icon: 'success' })
        trackMiniEvent('share_link_copied', {
          share_code: this.data.profileShareCode,
          properties: { channel: 'hr_link' },
        })
      },
    })
  },

  handleBack() {
    wx.switchTab({ url: '/pages/hub/index' })
  },
})
