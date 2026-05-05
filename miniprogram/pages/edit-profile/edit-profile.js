// pages/edit-profile/edit-profile.js
const app = getApp()
const api = require('../../utils/api')

Page({
  data: {
    form: {
      username: '',
      real_name: '',
      student_id: '',
      class_name: '',
      email: '',
      phone: ''
    },
    saving: false
  },

  onLoad() {
    this.loadProfile()
  },

  async loadProfile() {
    try {
      const res = await api.getProfile()
      if (res.code === 0) {
        this.setData({
          form: {
            username: res.data.username || '',
            real_name: res.data.real_name || '',
            student_id: res.data.student_id || '',
            class_name: res.data.class_name || '',
            email: res.data.email || '',
            phone: res.data.phone || ''
          }
        })
      }
    } catch (err) {
      console.error('加载个人资料失败', err)
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      })
    }
  },

  onInputChange(e) {
    const field = e.currentTarget.dataset.field
    this.setData({
      [`form.${field}`]: e.detail.value
    })
  },

  async saveProfile() {
    if (this.data.saving) return

    const { real_name, email, phone } = this.data.form

    // 简单验证
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      wx.showToast({
        title: '邮箱格式不正确',
        icon: 'none'
      })
      return
    }

    if (phone && !/^1\d{10}$/.test(phone)) {
      wx.showToast({
        title: '手机号格式不正确',
        icon: 'none'
      })
      return
    }

    this.setData({ saving: true })

    try {
      const res = await api.updateProfile({
        real_name,
        email,
        phone
      })

      if (res.code === 0) {
        // 更新全局用户信息
        app.globalData.userInfo = {
          ...app.globalData.userInfo,
          real_name: res.data.real_name,
          email: res.data.email,
          phone: res.data.phone
        }

        wx.showToast({
          title: '保存成功',
          icon: 'success'
        })

        setTimeout(() => {
          wx.navigateBack()
        }, 1500)
      } else {
        wx.showToast({
          title: res.message || '保存失败',
          icon: 'none'
        })
      }
    } catch (err) {
      console.error('保存个人资料失败', err)
      wx.showToast({
        title: '保存失败',
        icon: 'none'
      })
    } finally {
      this.setData({ saving: false })
    }
  },

  goBack() {
    wx.navigateBack()
  }
})
