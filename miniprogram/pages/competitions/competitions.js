// pages/competitions/competitions.js
const api = require('../../utils/api')

Page({
  data: {
    competitions: [],
    loading: true,
    loadingMore: false,
    page: 1,
    perPage: 10,
    hasMore: true,
    statusOptions: [
      { label: '全部', value: '' },
      { label: '报名中', value: 'open' },
      { label: '进行中', value: 'ongoing' },
      { label: '已结束', value: 'finished' }
    ],
    statusIndex: 0,
    currentStatus: ''
  },

  onLoad() {
    this.loadCompetitions()
  },

  onShow() {
    // 刷新数据
  },

  async loadCompetitions() {
    this.setData({ loading: true })

    try {
      const res = await api.getCompetitions({
        status: this.data.currentStatus,
        page: this.data.page,
        per_page: this.data.perPage
      })

      if (res.code === 0) {
        const newData = res.data.competitions || []
        this.setData({
          competitions: newData,
          hasMore: newData.length >= this.data.perPage
        })
      }
    } catch (err) {
      console.error('加载赛事失败', err)
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      })
    } finally {
      this.setData({ loading: false })
    }
  },

  onStatusChange(e) {
    const index = e.detail.value
    this.setData({
      statusIndex: index,
      currentStatus: this.data.statusOptions[index].value,
      page: 1
    })
    this.loadCompetitions()
  },

  goToDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/competition-detail/competition-detail?id=${id}`
    })
  },

  loadMore() {
    if (this.data.loadingMore || !this.data.hasMore) return

    this.setData({
      loadingMore: true,
      page: this.data.page + 1
    })

    api.getCompetitions({
      status: this.data.currentStatus,
      page: this.data.page,
      per_page: this.data.perPage
    }).then(res => {
      if (res.code === 0) {
        const newData = res.data.competitions || []
        this.setData({
          competitions: [...this.data.competitions, ...newData],
          hasMore: newData.length >= this.data.perPage
        })
      }
    }).catch(err => {
      console.error('加载更多失败', err)
    }).finally(() => {
      this.setData({ loadingMore: false })
    })
  },

  onPullDownRefresh() {
    this.setData({ page: 1 })
    this.loadCompetitions()
    wx.stopPullDownRefresh()
  }
})
