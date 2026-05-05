// pages/login/login.js
const app = getApp()
const api = require('../../utils/api')

Page({
  data: {
    // 登录表单
    username: '',
    password: '',
    loading: false,

    // 注册表单
    showRegisterForm: false,
    regUsername: '',
    regPassword: '',
    regConfirmPassword: '',
    regRealName: '',
    regStudentId: '',
    regClassName: '',
    regLoading: false
  },

  onLoad(options) {
    // 检查是否已登录
    const token = wx.getStorageSync('token')
    if (token) {
      // 已登录，跳转首页
      wx.switchTab({
        url: '/pages/index/index'
      })
    }
  },

  // 输入框事件
  onUsernameInput(e) {
    this.setData({ username: e.detail.value })
  },

  onPasswordInput(e) {
    this.setData({ password: e.detail.value })
  },

  onRegUsernameInput(e) {
    this.setData({ regUsername: e.detail.value })
  },

  onRegPasswordInput(e) {
    this.setData({ regPassword: e.detail.value })
  },

  onRegConfirmPasswordInput(e) {
    this.setData({ regConfirmPassword: e.detail.value })
  },

  onRegRealNameInput(e) {
    this.setData({ regRealName: e.detail.value })
  },

  onRegStudentIdInput(e) {
    this.setData({ regStudentId: e.detail.value })
  },

  onRegClassNameInput(e) {
    this.setData({ regClassName: e.detail.value })
  },

  // 切换登录/注册表单
  toggleRegisterForm() {
    this.setData({
      showRegisterForm: !this.data.showRegisterForm
    })
  },

  // 登录
  async handleLogin() {
    const { username, password } = this.data

    if (!username || !password) {
      wx.showToast({
        title: '请输入用户名和密码',
        icon: 'none'
      })
      return
    }

    this.setData({ loading: true })

    try {
      const res = await api.login(username, password)
      if (res.code === 0) {
        // 保存token和用户信息
        wx.setStorageSync('token', res.data.token)
        app.globalData.token = res.data.token
        app.globalData.userInfo = res.data.user

        wx.showToast({
          title: '登录成功',
          icon: 'success'
        })

        setTimeout(() => {
          wx.switchTab({
            url: '/pages/index/index'
          })
        }, 1000)
      } else {
        wx.showToast({
          title: res.message || '登录失败',
          icon: 'none'
        })
      }
    } catch (err) {
      wx.showToast({
        title: err.message || '网络错误',
        icon: 'none'
      })
    } finally {
      this.setData({ loading: false })
    }
  },

  // 注册
  async handleRegister() {
    const {
      regUsername, regPassword, regConfirmPassword,
      regRealName, regStudentId, regClassName
    } = this.data

    // 验证
    if (!regUsername || !regPassword) {
      wx.showToast({ title: '用户名和密码必填', icon: 'none' })
      return
    }

    if (regPassword.length < 6) {
      wx.showToast({ title: '密码至少6位', icon: 'none' })
      return
    }

    if (regPassword !== regConfirmPassword) {
      wx.showToast({ title: '两次密码不一致', icon: 'none' })
      return
    }

    this.setData({ regLoading: true })

    try {
      const res = await api.register({
        username: regUsername,
        password: regPassword,
        real_name: regRealName,
        student_id: regStudentId,
        class_name: regClassName
      })

      if (res.code === 0) {
        wx.showToast({
          title: '注册成功',
          icon: 'success'
        })

        // 自动登录
        wx.setStorageSync('token', res.data.token)
        app.globalData.token = res.data.token
        app.globalData.userInfo = res.data.user

        setTimeout(() => {
          wx.switchTab({
            url: '/pages/index/index'
          })
        }, 1000)
      } else {
        wx.showToast({
          title: res.message || '注册失败',
          icon: 'none'
        })
      }
    } catch (err) {
      wx.showToast({
        title: err.message || '网络错误',
        icon: 'none'
      })
    } finally {
      this.setData({ regLoading: false })
    }
  }
})
