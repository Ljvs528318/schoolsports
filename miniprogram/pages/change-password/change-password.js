// pages/change-password/change-password.js
const api = require('../../utils/api')

Page({
  data: {
    form: {
      old_password: '',
      new_password: '',
      confirm_password: ''
    },
    saving: false
  },

  onInputChange(e) {
    const field = e.currentTarget.dataset.field
    this.setData({
      [`form.${field}`]: e.detail.value
    })
  },

  async changePassword() {
    if (this.data.saving) return

    const { old_password, new_password, confirm_password } = this.data.form

    if (!old_password) {
      wx.showToast({ title: '请输入当前密码', icon: 'none' })
      return
    }

    if (!new_password || new_password.length < 6) {
      wx.showToast({ title: '新密码至少6位', icon: 'none' })
      return
    }

    if (new_password !== confirm_password) {
      wx.showToast({ title: '两次密码不一致', icon: 'none' })
      return
    }

    if (old_password === new_password) {
      wx.showToast({ title: '新密码不能与当前密码相同', icon: 'none' })
      return
    }

    this.setData({ saving: true })

    try {
      const res = await api.changePassword({
        old_password,
        new_password
      })

      if (res.code === 0) {
        wx.showToast({
          title: '密码修改成功',
          icon: 'success'
        })
        setTimeout(() => {
          wx.navigateBack()
        }, 1500)
      } else {
        wx.showToast({
          title: res.message || '修改失败',
          icon: 'none'
        })
      }
    } catch (err) {
      console.error('修改密码失败', err)
      wx.showToast({
        title: '修改失败',
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
