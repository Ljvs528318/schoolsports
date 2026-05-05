// pages/schedule/schedule.js
const api = require('../../utils/api')

Page({
  data: {
    competitionId: null,
    schedule: [],
    loading: true
  },

  onLoad(options) {
    if (options.id) {
      this.setData({
        competitionId: options.id
      })
      this.loadSchedule()
    }
  },

  async loadSchedule() {
    this.setData({ loading: true })

    try {
      const res = await api.getSchedule(this.data.competitionId)
      if (res.code === 0) {
        this.setData({
          schedule: res.data.stages || []
        })
      }
    } catch (err) {
      console.error('加载赛程失败', err)
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      })
    } finally {
      this.setData({ loading: false })
    }
  }
})
