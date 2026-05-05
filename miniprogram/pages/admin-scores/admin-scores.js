// pages/admin-scores/admin-scores.js
const api = require('../../utils/api')

Page({
  data: {
    competitions: [],
    selectedCompetition: null,
    matches: [],
    filter: 'all',
    scoreChanges: {}
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

  async onCompetitionChange(e) {
    const index = e.detail.value
    const comp = this.data.competitions[index]
    this.setData({
      selectedCompetition: comp,
      filter: 'all',
      scoreChanges: {}
    })
    await this.loadMatches(comp.id)
  },

  setFilter(e) {
    const filter = e.currentTarget.dataset.filter
    this.setData({ filter })
    if (this.data.selectedCompetition) {
      this.loadMatches(this.data.selectedCompetition.id)
    }
  },

  async loadMatches(competitionId) {
    try {
      wx.showLoading({ title: '加载中...' })
      const res = await api.getSchedule(competitionId)
      wx.hideLoading()

      if (res.code === 0) {
        let matches = []
        const stages = res.data.stages || []

        stages.forEach(stage => {
          (stage.matches || []).forEach(match => {
            matches.push({
              ...match,
              stage_label: stage.stage_label
            })
          })
        })

        // 根据筛选条件过滤
        if (this.data.filter !== 'all') {
          matches = matches.filter(m => m.status === this.data.filter)
        }

        this.setData({ matches })
      }
    } catch (err) {
      wx.hideLoading()
      console.error('加载赛程失败', err)
    }
  },

  onScoreInput(e) {
    const { matchId, team } = e.currentTarget.dataset
    const value = e.detail.value

    const key = `${matchId}_${team}`
    const scoreChanges = { ...this.data.scoreChanges }
    scoreChanges[key] = value
    this.setData({ scoreChanges })
  },

  async saveScore(e) {
    const matchId = e.currentTarget.dataset.matchId
    const match = this.data.matches.find(m => m.id == matchId)
    if (!match) return

    const homeScore = this.data.scoreChanges[`${matchId}_home`] !== undefined
      ? this.data.scoreChanges[`${matchId}_home`]
      : match.home_score
    const awayScore = this.data.scoreChanges[`${matchId}_away`] !== undefined
      ? this.data.scoreChanges[`${matchId}_away`]
      : match.away_score

    // TODO: 调用后端API保存成绩
    wx.showToast({ title: '功能开发中', icon: 'none' })
  }
})
