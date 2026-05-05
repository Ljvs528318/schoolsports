// pages/admin-group/admin-group.js
const api = require('../../utils/api')

Page({
  data: {
    competitions: [],
    selectedCompetition: null,
    groupCount: 4,
    groups: [],
    pendingRegistrations: [],
    groupOptions: []
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

  onCompetitionChange(e) {
    const index = e.detail.value
    const comp = this.data.competitions[index]
    this.setData({ selectedCompetition: comp })
    this.loadGroups(comp.id)
    this.loadPendingRegistrations(comp.id)
  },

  onGroupCountChange(e) {
    this.setData({ groupCount: parseInt(e.detail.value) || 4 })
  },

  async createGroups() {
    if (!this.data.selectedCompetition) {
      wx.showToast({ title: '请先选择赛事', icon: 'none' })
      return
    }

    wx.showModal({
      title: '确认生成分组',
      content: `将创建 ${this.data.groupCount} 个小组，是否继续？`,
      success: async (res) => {
        if (res.confirm) {
          await this.performCreateGroups()
        }
      }
    })
  },

  async performCreateGroups() {
    // TODO: 调用后端API创建分组
    wx.showToast({ title: '功能开发中', icon: 'none' })
  },

  async loadGroups(competitionId) {
    // TODO: 加载分组数据
    this.setData({ groups: [] })
  },

  async loadPendingRegistrations(competitionId) {
    try {
      const res = await api.getCompetitionRegistrations(competitionId, 'approved')
      if (res.code === 0) {
        this.setData({
          pendingRegistrations: res.data.registrations || []
        })
      }
    } catch (err) {
      console.error('加载报名记录失败', err)
    }
  },

  onAssignGroup(e) {
    // TODO: 分配队伍到分组
    wx.showToast({ title: '功能开发中', icon: 'none' })
  }
})
