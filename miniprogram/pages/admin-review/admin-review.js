// pages/admin-review/admin-review.js
const api = require('../../utils/api')

Page({
  data: {
    competitions: [],
    selectedCompetition: null,
    registrations: [],
    filter: 'pending'  // 默认显示待审核
  },

  onLoad(options) {
    if (options.competitionId) {
      this.loadCompetitionAndRegistrations(options.competitionId)
    } else {
      this.loadCompetitions()
    }
  },

  onShow() {
    if (this.data.selectedCompetition) {
      this.loadRegistrations(this.data.selectedCompetition.id)
    } else {
      this.loadCompetitions()
    }
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

  async loadCompetitionAndRegistrations(competitionId) {
    try {
      const compRes = await api.getCompetitionDetail(competitionId)
      if (compRes.code === 0) {
        this.setData({ selectedCompetition: compRes.data })
        this.loadRegistrations(competitionId)
      }
    } catch (err) {
      console.error('加载赛事详情失败', err)
    }
  },

  async loadRegistrations(competitionId) {
    try {
      wx.showLoading({ title: '加载中...' })
      const res = await api.getCompetitionRegistrations(competitionId, this.data.filter)
      if (res.code === 0) {
        this.setData({
          registrations: res.data.registrations || []
        })
      }
      wx.hideLoading()
    } catch (err) {
      wx.hideLoading()
      console.error('加载报名记录失败', err)
    }
  },

  selectCompetition(e) {
    const compId = e.currentTarget.dataset.id
    const comp = this.data.competitions.find(c => c.id == compId)
    this.setData({
      selectedCompetition: comp,
      filter: 'pending'
    })
    this.loadRegistrations(compId)
  },

  setFilter(e) {
    const filter = e.currentTarget.dataset.filter
    this.setData({ filter })
    this.loadRegistrations(this.data.selectedCompetition.id)
  },

  async approveRegistration(e) {
    const regId = e.currentTarget.dataset.id
    wx.showModal({
      title: '确认通过',
      content: '确定通过此报名申请？',
      success: async (res) => {
        if (res.confirm) {
          await this.updateRegistrationStatus(regId, 'approved')
        }
      }
    })
  },

  async rejectRegistration(e) {
    const regId = e.currentTarget.dataset.id
    wx.showModal({
      title: '确认拒绝',
      content: '确定拒绝此报名申请？',
      success: async (res) => {
        if (res.confirm) {
          await this.updateRegistrationStatus(regId, 'rejected')
        }
      }
    })
  },

  async updateRegistrationStatus(regId, status) {
    try {
      wx.showLoading({ title: '处理中...' })
      const res = await api.updateRegistrationStatus(regId, status)
      wx.hideLoading()
      if (res.code === 0) {
        wx.showToast({
          title: status === 'approved' ? '已通过' : '已拒绝',
          icon: 'success'
        })
        this.loadRegistrations(this.data.selectedCompetition.id)
      } else {
        wx.showToast({ title: res.message || '操作失败', icon: 'none' })
      }
    } catch (err) {
      wx.hideLoading()
      wx.showToast({ title: '操作失败', icon: 'none' })
    }
  },

  goBack() {
    this.setData({
      selectedCompetition: null,
      registrations: []
    })
    this.loadCompetitions()
  }
})
