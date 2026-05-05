// pages/admin-draw/admin-draw.js
const api = require('../../utils/api')

Page({
  data: {
    competitions: [],
    selectedCompetition: null,
    approvedCount: 0,
    drawResult: []
  },

  onLoad() {
    this.loadCompetitions()
  },

  async loadCompetitions() {
    try {
      const res = await api.getCompetitions({ pageSize: 100 })
      if (res.code === 0) {
        this.setData({ competitions: res.data.competitions || [] })
      }
    } catch (err) {
      console.error('加载赛事失败', err)
    }
  },

  async onCompetitionChange(e) {
    const index = e.detail.value
    const comp = this.data.competitions[index]
    this.setData({ selectedCompetition: comp })
    await this.loadApprovedRegistrations(comp.id)
  },

  async loadApprovedRegistrations(competitionId) {
    try {
      const res = await api.getCompetitionRegistrations(competitionId, 'approved')
      if (res.code === 0) {
        const regs = res.data.registrations || []
        this.setData({ approvedCount: regs.length })
      }
    } catch (err) {
      console.error('加载报名记录失败', err)
    }
  },

  async performDraw() {
    wx.showModal({
      title: '确认抽签',
      content: '确定要进行随机抽签吗？',
      success: async (res) => {
        if (res.confirm) {
          // TODO: 调用后端抽签API
          wx.showToast({ title: '功能开发中', icon: 'none' })
        }
      }
    })
  }
})
