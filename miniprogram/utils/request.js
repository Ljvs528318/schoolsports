// utils/request.js - HTTP请求封装
const app = getApp()

function request(options) {
  return new Promise((resolve, reject) => {
    const token = wx.getStorageSync('token')

    wx.request({
      url: app.globalData.baseUrl + options.url,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
      },
      success: (res) => {
        if (res.statusCode === 401) {
          // Token过期，清除并跳转到登录页
          wx.removeStorageSync('token')
          app.globalData.token = null
          app.globalData.userInfo = null
          wx.redirectTo({
            url: '/pages/login/login'
          })
          reject({ code: 401, message: '登录已过期，请重新登录' })
        } else if (res.statusCode === 200) {
          resolve(res.data)
        } else {
          reject(res.data || { code: -1, message: '请求失败' })
        }
      },
      fail: (err) => {
        reject({ code: -1, message: '网络错误', error: err })
      }
    })
  })
}

module.exports = { request }
