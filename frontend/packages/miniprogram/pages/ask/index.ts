/**
 * Ask Page - TabBar AI Q&A (index 1)
 * Basic chat interface for AI career questions.
 */
import { eventBus } from '../../utils/event-bus'
import { store } from '../../utils/store'
import { askApi } from '../../utils/api'
import type { ChatMessage } from '../../types/index'

Page({
  data: {
    messages: [
      {
        role: 'assistant',
        content: '你好，探索者！我是你的星际导航员。关于求职、职业规划、简历优化，有什么想问的？',
      },
    ] as ChatMessage[],
    inputText: '',
    loading: false,
    scrollIntoView: '',
  },

  sessionHistory: [] as ChatMessage[],

  onShow() {
    const tabBar = (this as any).getTabBar?.()
    if (tabBar) tabBar.setData({ selected: 1 })
  },

  onInput(e: any) {
    this.setData({ inputText: e.detail.value })
  },

  async onSend() {
    const text = this.data.inputText.trim()
    if (!text || this.data.loading) return

    // Check auth
    const token = store.get('token')
    if (!token) {
      wx.showToast({ title: '请先登录', icon: 'none' })
      return
    }

    // Add user message
    const userMsg: ChatMessage = { role: 'user', content: text, timestamp: Date.now().toString() }
    const messages = [...this.data.messages, userMsg]
    this.setData({
      messages,
      inputText: '',
      loading: true,
    })
    this.scrollToBottom()

    try {
      const resp = await askApi.ask(text, this.sessionHistory)
      const aiMsg: ChatMessage = {
        role: 'assistant',
        content: resp.answer || '抱歉，我没能理解你的问题。',
        sources: resp.sources,
        timestamp: Date.now().toString(),
      }
      this.sessionHistory = [...this.sessionHistory, userMsg, aiMsg]
      this.setData({
        messages: [...this.data.messages, aiMsg],
        loading: false,
      })
      this.scrollToBottom()
    } catch (err: any) {
      const errMsg: ChatMessage = {
        role: 'assistant',
        content: '网络波动，请稍后重试。',
        timestamp: Date.now().toString(),
      }
      this.setData({
        messages: [...this.data.messages, errMsg],
        loading: false,
      })
      this.scrollToBottom()
    }
  },

  scrollToBottom() {
    setTimeout(() => {
      this.setData({ scrollIntoView: 'msg-bottom' })
    }, 100)
  },

  onShareAppMessage() {
    return {
      title: 'PlanetX - AI 星际问答，你的职业导航员',
      path: '/pages/splash/index',
    }
  },
})
