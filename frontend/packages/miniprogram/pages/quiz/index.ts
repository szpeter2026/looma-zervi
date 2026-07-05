/**
 * Quiz Page - 8 question personality test
 * After completion, computes personality and navigates to result.
 */
import { QUIZ_QUESTIONS, computePersonality } from '../../constants/quiz'
import { store } from '../../utils/store'
import { gameApi } from '../../utils/api'
import { MISSION_XP } from '../../utils/config'
import type { PlanetXTraitKey, PlanetXPersonalityType } from '../../types/index'

Page({
  data: {
    step: 0,
    total: QUIZ_QUESTIONS.length,
    currentQuestion: QUIZ_QUESTIONS[0],
    progress: [] as boolean[],
  },

  traitCounts: {} as Partial<Record<PlanetXTraitKey, number>>,

  onLoad() {
    this.setData({
      progress: new Array(QUIZ_QUESTIONS.length).fill(false),
    })
    this.traitCounts = {}
    store.set('quizStep', 0)
    store.set('quizTraitCounts', {})
  },

  onAnswer(e: any) {
    const idx = e.currentTarget.dataset.index
    const option = this.data.currentQuestion.options[idx]
    const trait = option.trait as PlanetXTraitKey

    this.traitCounts[trait] = (this.traitCounts[trait] || 0) + 1

    const progress = [...this.data.progress]
    progress[this.data.step] = true
    this.setData({ progress })

    const nextStep = this.data.step + 1
    if (nextStep >= QUIZ_QUESTIONS.length) {
      this.finishQuiz()
    } else {
      setTimeout(() => {
        this.setData({
          step: nextStep,
          currentQuestion: QUIZ_QUESTIONS[nextStep],
        })
      }, 300)
    }
  },

  finishQuiz() {
    const personality = computePersonality(this.traitCounts)

    store.set('personalityType', personality as any)
    store.set('quizTraitCounts', this.traitCounts)
    store.completeMission('personality')
    store.setAchievement({
      title: '🔮 星际人格觉醒！',
      desc: `你被认证为「${personality.name}」`,
    })

    const xpReward = MISSION_XP.personality

    gameApi.syncProfile({
      personality_type: personality.name,
      personality_detail: JSON.stringify(personality),
    }).catch(() => {})

    gameApi.completeMission('personality', xpReward).then((data: any) => {
      if (data?.total_xp != null) {
        // 使用完整的 profile 更新，包括 xp 和 level
        store.applyGameProfile({ xp: data.total_xp, level: data.level })
      }
    }).catch(() => {})

    setTimeout(() => {
      wx.redirectTo({ url: '/pages/result/index' })
    }, 500)
  },
})
