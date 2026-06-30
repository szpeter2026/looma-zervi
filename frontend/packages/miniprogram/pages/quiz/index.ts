/**
 * Quiz Page - 8 question personality test
 * After completion, computes personality and navigates to result.
 */
import { QUIZ_QUESTIONS, computePersonality } from '../../constants/quiz'
import { store } from '../../utils/store'
import { gameApi } from '../../utils/api'
import type { TraitKey } from '../../types/index'

Page({
  data: {
    step: 0,
    total: QUIZ_QUESTIONS.length,
    currentQuestion: QUIZ_QUESTIONS[0],
    progress: [] as boolean[],
  },

  traitCounts: {} as Partial<Record<TraitKey, number>>,

  onLoad() {
    // Initialize progress array
    this.setData({
      progress: new Array(QUIZ_QUESTIONS.length).fill(false),
    })
    // Reset quiz state
    this.traitCounts = {}
    store.set('quizStep', 0)
    store.set('quizTraitCounts', {})
  },

  onAnswer(e: any) {
    const idx = e.currentTarget.dataset.index
    const option = this.data.currentQuestion.options[idx]
    const trait = option.trait as TraitKey

    // Record trait count
    this.traitCounts[trait] = (this.traitCounts[trait] || 0) + 1

    // Update progress
    const progress = [...this.data.progress]
    progress[this.data.step] = true
    this.setData({ progress })

    // Move to next question or finish
    const nextStep = this.data.step + 1
    if (nextStep >= QUIZ_QUESTIONS.length) {
      // Quiz complete
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

    // Update store
    store.set('personalityType', personality)
    store.set('quizTraitCounts', this.traitCounts)
    store.completeMission('personality')
    store.addXP(50)
    store.setAchievement({
      title: '🔮 星际人格觉醒！',
      desc: `你被认证为「${personality.name}」`,
    })

    // Sync to backend (best-effort)
    gameApi.syncProfile({
      personality_type: personality,
    }).catch(() => {})

    gameApi.completeMission('personality').catch(() => {})

    // Navigate to result page
    setTimeout(() => {
      wx.redirectTo({ url: '/pages/result/index' })
    }, 500)
  },
})
