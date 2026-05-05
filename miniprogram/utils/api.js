// utils/api.js - API服务层
const { request } = require('./request')

// 认证相关
function login(username, password) {
  return request({
    url: '/auth/login',
    method: 'POST',
    data: { username, password }
  })
}

function register(userData) {
  return request({
    url: '/auth/register',
    method: 'POST',
    data: userData
  })
}

function getProfile() {
  return request({
    url: '/auth/profile',
    method: 'GET'
  })
}

function updateProfile(data) {
  return request({
    url: '/auth/profile',
    method: 'PUT',
    data: data
  })
}

function changePassword(data) {
  return request({
    url: '/auth/change-password',
    method: 'POST',
    data: data
  })
}

// 赛事相关
function getCompetitions(params = {}) {
  const query = Object.keys(params)
    .filter(key => params[key]!=='' && params[key]!==undefined && params[key]!==null)
    .map(key => `${key}=${encodeURIComponent(params[key])}`)
    .join('&')

  return request({
    url: '/competitions' + (query? `?${query}` : ''),
    method: 'GET'
  })
}

function getCompetitionDetail(id) {
  return request({
    url: `/competitions/${id}`,
    method: 'GET'
  })
}

function registerCompetition(id, data = {}) {
  return request({
    url: `/competitions/${id}/register`,
    method: 'POST',
    data: data
  })
}

// 赛程相关
function getSchedule(competitionId) {
  return request({
    url: `/competitions/${competitionId}/schedule`,
    method: 'GET'
  })
}

function getStandings(competitionId) {
  return request({
    url: `/competitions/${competitionId}/standings`,
    method: 'GET'
  })
}

// 用户相关
function getMyRegistrations() {
  return request({
    url: '/user/registrations',
    method: 'GET'
  })
}

// 管理相关
function getCompetitionRegistrations(competitionId, status = '') {
  let url = `/competitions/${competitionId}/registrations`
  if (status) {
    url += `?status=${status}`
  }
  return request({
    url: url,
    method: 'GET'
  })
}

function updateRegistrationStatus(registrationId, status) {
  return request({
    url: `/registrations/${registrationId}/status`,
    method: 'PUT',
    data: { status }
  })
}

// 公告相关
function getAnnouncements() {
  return request({
    url: '/announcements',
    method: 'GET'
  })
}

function getCompetitionAnnouncements(competitionId) {
  return request({
    url: `/competitions/${competitionId}/announcements`,
    method: 'GET'
  })
}

module.exports = {
  login,
  register,
  getProfile,
  updateProfile,
  changePassword,
  getCompetitions,
  getCompetitionDetail,
  registerCompetition,
  getSchedule,
  getStandings,
  getMyRegistrations,
  getCompetitionRegistrations,
  updateRegistrationStatus,
  getAnnouncements,
  getCompetitionAnnouncements
}
