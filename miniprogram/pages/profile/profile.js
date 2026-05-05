// pages/profile/profile.js
const app = getApp()
const api = require('../../utils/api')

Page({
  data: {
    userInfo: null,
    registrations: [],
    showRegistrations: false
  },

  onLoad() {
    this.checkLoginStatus()
  },

  onShow() {
    this.checkLoginStatus()
    if (this.data.userInfo) {
      this.loadRegistrations()
      this.refreshProfile()
    }
  },

  checkLoginStatus() {
    const userInfo = app.globalData.userInfo
    this.setData({
      userInfo: userInfo || null
    })
  },

  async refreshProfile() {
    try {
      const res = await api.getProfile()
      if (res.code === 0) {
        const userInfo = res.data
        app.globalData.userInfo = userInfo
        this.setData({ userInfo })
      }
    } catch (err) {
      console.error('刷新个人资料失败', err)
    }
  },

  async loadRegistrations() {
    try {
      const res = await api.getMyRegistrations()
      if (res.code === 0) {
        this.setData({
          registrations: res.data.registrations || []
        })
      }
    } catch (err) {
      console.error('加载报名记录失败', err)
    }
  },

  goToLogin() {
    wx.navigateTo({
      url: '/pages/login/login'
    })
  },

  viewMyRegistrations() {
    this.setData({
      showRegistrations: !this.data.showRegistrations
    })
    if (this.data.showRegistrations && this.data.registrations.length === 0) {
      this.loadRegistrations()
    }
  },

  viewProfile() {
    wx.navigateTo({
      url: '/pages/edit-profile/edit-profile'
    })
  },

  changePassword() {
    wx.navigateTo({
      url: '/pages/change-password/change-password'
    })
  },

  goToAdmin() {
    wx.navigateTo({
      url: '/pages/admin/admin'
    })
  },

  handleLogout() {
    wx.showModal({
      title: '确认退出',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          // 清除登录信息
          wx.removeStorageSync('token')
          app.globalData.token = null
          app.globalData.userInfo = null

          this.setData({
            userInfo: null,
            registrations: [],
            showRegistrations: false
          })

          wx.showToast({
            title: '已退出登录',
            icon: 'success'
          })
        }
      }
    })
  }
})
