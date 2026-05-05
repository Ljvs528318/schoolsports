// pages/register/register.js
const api = require('../../utils/api')

Page({
  data: {
    competitionId: null,
    competition: {},
    isTeam: false,
    team_name: '',
    maxMembers: 0,
    captain: {
      student_id: '',
      class_name: '',
      name: ''
    },
    members: [],
    submitting: false
  },

  onLoad(options) {
    if (options.id) {
      this.setData({ competitionId: options.id })
      this.loadCompetitionDetail()
      this.loadUserProfile()
    }
  },

  async loadCompetitionDetail() {
    try {
      const res = await api.getCompetitionDetail(this.data.competitionId)
      if (res.code === 0) {
        const comp = res.data
        const isTeam = comp.comp_type === 'team'
        const maxMembers = isTeam ? (comp.team_size ? comp.team_size - 1 : 4) : 0
        this.setData({
          competition: comp,
          isTeam: isTeam,
          maxMembers: maxMembers
        })
      }
    } catch (err) {
      console.error('加载赛事详情失败', err)
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  async loadUserProfile() {
    try {
      const res = await api.getProfile()
      if (res.code === 0) {
        const user = res.data
        this.setData({
          'captain.student_id': user.student_id || '',
          'captain.class_name': user.class_name || '',
          'captain.name': user.real_name || ''
        })
      }
    } catch (err) {
      console.error('加载用户资料失败', err)
    }
  },

  onTeamNameInput(e) {
    this.setData({ team_name: e.detail.value })
  },

  onCaptainInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [`captain.${field}`]: e.detail.value })
  },

  onMemberInput(e) {
    const index = e.currentTarget.dataset.index
    const field = e.currentTarget.dataset.field
    this.setData({ [`members[${index}].${field}`]: e.detail.value })
  },

  addMember() {
    const { members, maxMembers } = this.data
    if (members.length >= maxMembers) {
      wx.showToast({ title: `最多添加${maxMembers}名队员`, icon: 'none' })
      return
    }
    members.push({ student_id: '', class_name: '', name: '' })
    this.setData({ members })
  },

  removeMember(e) {
    const index = e.currentTarget.dataset.index
    const members = this.data.members
    members.splice(index, 1)
    this.setData({ members })
  },

  validate() {
    const { isTeam, team_name, captain, members } = this.data

    if (isTeam) {
      if (!team_name.trim()) {
        wx.showToast({ title: '请输入队名', icon: 'none' })
        return false
      }
      if (!captain.student_id.trim() || !captain.class_name.trim() || !captain.name.trim()) {
        wx.showToast({ title: '请填写队长完整信息', icon: 'none' })
        return false
      }
      for (let i = 0; i < members.length; i++) {
        const m = members[i]
        if (!m.student_id || !m.class_name || !m.name) {
          wx.showToast({ title: `请填写队员${i + 1}的完整信息`, icon: 'none' })
          return false
        }
      }
    }

    return true
  },

  async submit() {
    if (!this.validate()) return

    this.setData({ submitting: true })

    try {
      const { competitionId, isTeam, team_name, captain, members } = this.data

      let data = {}

      if (isTeam) {
        const team_members = [
          { ...captain, is_captain: true },
          ...members.map(m => ({ ...m, is_captain: false }))
        ]
        data = { team_name, team_members }
      }

      const res = await api.registerCompetition(competitionId, data)
      if (res.code === 0) {
        wx.showToast({ title: '报名成功', icon: 'success' })
        setTimeout(() => {
          wx.navigateBack()
        }, 1500)
      } else {
        wx.showToast({ title: res.message || '报名失败', icon: 'none' })
      }
    } catch (err) {
      wx.showToast({ title: err.message || '网络错误', icon: 'none' })
    } finally {
      this.setData({ submitting: false })
    }
  }
})
