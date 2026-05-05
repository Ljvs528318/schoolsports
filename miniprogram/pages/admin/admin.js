// pages/admin/admin.js
const api = require('../../utils/api')

Page({
  data: {
    competitions: []
  },

  onLoad() {
    this.loadCompetitions()
  },

  onShow() {
    this.loadCompetitions()
  },

  async loadCompetitions() {
    try {
      const res = await api.getCompetitions({ pageSize: 100 })
      if (res.code === 0) {
        this.setData({
          competitions: res.data.competitions || []
        })
      }
    } catch (err) {
      console.error('加载赛事失败', err)
    }
  },

  goToReview() {
    wx.navigateTo({ url: '/pages/admin-review/admin-review' })
  },

  goToGroup() {
    wx.navigateTo({ url: '/pages/admin-group/admin-group' })
  },

  goToDraw() {
    wx.navigateTo({ url: '/pages/admin-draw/admin-draw' })
  },

  goToScores() {
    wx.navigateTo({ url: '/pages/admin-scores/admin-scores' })
  },

  selectCompetition(e) {
    const compId = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/admin-review/admin-review?competitionId=${compId}` })
  }
})
