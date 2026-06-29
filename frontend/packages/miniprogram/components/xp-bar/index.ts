/**
 * XP Bar Component
 * Shows level, rank, XP progress bar
 */
import { getRankName } from '../../types/index'

Component({
  properties: {
    level: { type: Number, value: 1 },
    xp: { type: Number, value: 0 },
    xpToNext: { type: Number, value: 100 },
  },

  data: {
    pct: 0,
    rankName: '星际新兵',
  },

  observers: {
    'level, xp, xpToNext': function (level: number, xp: number, xpToNext: number) {
      this.setData({
        pct: Math.min(100, (xp / xpToNext) * 100),
        rankName: getRankName(level),
      })
    },
  },
})
