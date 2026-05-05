// pages/index/index.js
const app = getApp()
const api = require('../../utils/api')

Page({
  data: {
    announcements: [],
    recentCompetitions: [],
    loading: true,
    isLoggedIn: false
  },

  onLoad() {
    this.checkLoginStatus()
    this.loadData()
  },

  onShow() {
    this.checkLoginStatus()
  },

  checkLoginStatus() {
    const token = wx.getStorageSync('token')
    this.setData({
      isLoggedIn: !!token
    })
  },

  async loadData() {
    this.setData({ loading: true })

    try {
      // 获取公告
      const annRes = await api.getAnnouncements()
      if (annRes.code === 0) {
        this.setData({
          announcements: annRes.data.announcements || []
        })
      }

      // 获取近期赛事
      const compRes = await api.getCompetitions({ per_page: 5 })
      if (compRes.code === 0) {
        this.setData({
          recentCompetitions: compRes.data.competitions || []
        })
      }
    } catch (err) {
      console.error('加载数据失败', err)
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      })
    } finally {
      this.setData({ loading: false })
    }
  },

  goToCompetitions() {
    wx.switchTab({
      url: '/pages/competitions/competitions'
    })
  },

  goToMyRegistrations() {
    wx.navigateTo({
      url: '/pages/my-registrations/my-registrations'
    })
  },

  goToProfile() {
    wx.switchTab({
      url: '/pages/profile/profile'
    })
  },

  goToCompetitionDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/competition-detail/competition-detail?id=${id}`
    })
  },

  onPullDownRefresh() {
    this.loadData()
    wx.stopPullDownRefresh()
  }
})
