// app.js
App({
  onLaunch() {
    // 检查登录状态
    this.checkLoginStatus()
  },

  globalData: {
    userInfo: null,
    token: null,
    baseUrl: 'http://192.168.1.99:5000/api'  // 本地测试地址，正式环境需要HTTPS
  },

  checkLoginStatus() {
    const token = wx.getStorageSync('token')
    if (token) {
      this.globalData.token = token
      // 验证token有效性
      this.validateToken(token)
    }
  },

  validateToken(token) {
    wx.request({
      url: this.globalData.baseUrl + '/auth/profile',
      method: 'GET',
      header: {
        'Authorization': 'Bearer ' + token
      },
      success: (res) => {
        if (res.statusCode === 200) {
          this.globalData.userInfo = res.data.data
        } else {
          // token无效，清除
          wx.removeStorageSync('token')
          this.globalData.token = null
          this.globalData.userInfo = null
        }
      },
      fail: () => {
        console.log('Token验证失败')
      }
    })
  }
})
