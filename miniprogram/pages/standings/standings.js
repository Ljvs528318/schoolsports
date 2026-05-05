// pages/standings/standings.js
const api = require('../../utils/api')

Page({
  data: {
    competitionId: null,
    groups: [],
    loading: true
  },

  onLoad(options) {
    if (options.id) {
      this.setData({
        competitionId: options.id
      })
      this.loadStandings()
    }
  },

  async loadStandings() {
    this.setData({ loading: true })

    try {
      const res = await api.getStandings(this.data.competitionId)
      if (res.code === 0) {
        this.setData({
          groups: res.data.groups || []
        })
      }
    } catch (err) {
      console.error('加载积分榜失败', err)
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      })
    } finally {
      this.setData({ loading: false })
    }
  }
})
