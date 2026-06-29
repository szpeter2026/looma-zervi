/**
 * Star Background Component
 * Renders 60 animated stars using CSS pulse animation.
 * In miniprogram, we can't create DOM elements dynamically,
 * so we generate star data in the component and use wx:for.
 */

Component({
  data: {
    stars: [] as Array<{ left: number; top: number; size: number; delay: number; duration: number }>,
  },

  lifetimes: {
    attached() {
      const stars = []
      for (let i = 0; i < 60; i++) {
        stars.push({
          left: Math.random() * 100,
          top: Math.random() * 100,
          size: Math.random() * 4 + 2,
          delay: Math.random() * 4,
          duration: Math.random() * 3 + 2,
        })
      }
      this.setData({ stars })
    },
  },
})
