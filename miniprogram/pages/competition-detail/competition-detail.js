// pages/competition-detail/competition-detail.js
const api = require('../../utils/api')

Page({
  data: {
    competitionId: null,
    competition: {},
    userRegistration: null,
    canRegister: false,
    hasRegistered: false,
    loading: true,
    finalResult: null
  },

  onLoad(options) {
    if (options.id) {
      this.setData({
        competitionId: options.id
      })
      this.loadCompetitionDetail()
    }
  },

  onShow() {
    if (this.data.competitionId) {
      this.checkRegistrationStatus()
    }
  },

  async loadCompetitionDetail() {
    this.setData({ loading: true })

    try {
      const res = await api.getCompetitionDetail(this.data.competitionId)
      if (res.code === 0) {
        const comp = res.data
        this.setData({
          competition: comp,
          canRegister: comp.status === 'open' && !comp.user_registration
        })

        // 检查用户是否已报名
        if (comp.user_registration) {
          this.setData({
            hasRegistered: true,
            userRegistration: comp.user_registration
          })
        }

        // 如果比赛已结束，加载最终结果
        if (comp.status === 'finished') {
          this.loadFinalResult()
        }
      }
    } catch (err) {
      console.error('加载详情失败', err)
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      })
    } finally {
      this.setData({ loading: false })
    }
  },

  async loadFinalResult() {
    try {
      // 获取赛程数据来分析最终结果
      const res = await api.getSchedule(this.data.competitionId)
      if (res.code === 0) {
        const stages = res.data.stages || []
        const comp = this.data.competition
        let finalResult = null

        if (comp.format === 'knockout') {
          // 淘汰赛：查找决赛
          const finalStage = stages.find(s => s.stage === 'final')
          if (finalStage && finalStage.matches.length > 0) {
            const finalMatch = finalStage.matches[0]
            if (finalMatch.status === 'finished' && finalMatch.home_score !== null) {
              const isHomeWin = finalMatch.home_score > finalMatch.away_score
              finalResult = {
                champion: isHomeWin ? finalMatch.home_team : finalMatch.away_team,
                runner_up: isHomeWin ? finalMatch.away_team : finalMatch.home_team,
                final_score: `${finalMatch.home_score} : ${finalMatch.away_score}`
              }
            }
          }

          // 如果没有决赛但有半决赛结果
          if (!finalResult) {
            const semiStage = stages.find(s => s.stage === 'sf')
            if (semiStage && semiStage.matches.length > 0) {
              const finishedSemis = semiStage.matches.filter(m => m.status === 'finished')
              if (finishedSemis.length > 0) {
                finalResult = {
                  semifinal_results: finishedSemis.map(m => {
                    const isHomeWin = m.home_score > m.away_score
                    return {
                      winner: isHomeWin ? m.home_team : m.away_team,
                      score: `${m.home_score} : ${m.away_score}`
                    }
                  })
                }
              }
            }
          }
        } else {
          // 循环赛/联赛：从积分榜获取前三名
          const standingsRes = await api.getStandings(this.data.competitionId)
          if (standingsRes.code === 0 && standingsRes.data.groups) {
            const groups = standingsRes.data.groups
            finalResult = {
              groups: groups.map(group => ({
                group_name: group.group_name,
                top3: (group.standings || []).slice(0, 3).map((s, i) => ({
                  rank: i + 1,
                  team_name: s.team_name,
                  points: s.points
                }))
              }))
            }
          }
        }

        this.setData({ finalResult })
      }
    } catch (err) {
      console.error('加载最终结果失败', err)
    }
  },

  async checkRegistrationStatus() {
    try {
      const res = await api.getMyRegistrations()
      if (res.code === 0) {
        const registrations = res.data.registrations || []
        const myReg = registrations.find(r => r.competition_id == this.data.competitionId)
        if (myReg) {
          this.setData({
            hasRegistered: true,
            userRegistration: myReg,
            canRegister: false
          })
        }
      }
    } catch (err) {
      console.error('检查报名状态失败', err)
    }
  },

  handleRegister() {
    // 检查登录状态
    const token = wx.getStorageSync('token')
    if (!token) {
      wx.showToast({
        title: '请先登录',
        icon: 'none'
      })
      setTimeout(() => {
        wx.navigateTo({
          url: '/pages/login/login'
        })
      }, 1000)
      return
    }
    // 跳转到报名页面
    wx.navigateTo({
      url: `/pages/register/register?id=${this.data.competitionId}`
    })
  },

  viewMyRegistration() {
    wx.showToast({
      title: `报名状态: ${this.data.userRegistration.status === 'pending' ? '待审核' : (this.data.userRegistration.status === 'approved' ? '已通过' : '已拒绝')}`,
      icon: 'none'
    })
  },

  viewSchedule() {
    wx.navigateTo({
      url: `/pages/schedule/schedule?id=${this.data.competitionId}`
    })
  },

  viewStandings() {
    wx.navigateTo({
      url: `/pages/standings/standings?id=${this.data.competitionId}`
    })
  }
})
