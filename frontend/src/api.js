const BASE = '/api'

const req = (path, opts = {}) =>
  fetch(BASE + path, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  })

export const login = (username, password) =>
  req('/login', { method: 'POST', body: JSON.stringify({ username, password }) })

export const register = (username, password, confirm_password) =>
  req('/register', { method: 'POST', body: JSON.stringify({ username, password, confirm_password }) })

export const logout = () => req('/logout', { method: 'POST' })

export const plan = (tasks) =>
  req('/plan', { method: 'POST', body: JSON.stringify({ tasks }) })

export const record = (tasks, completion_rate) =>
  req('/record', { method: 'POST', body: JSON.stringify({ tasks, completion_rate }) })

export const onboarding = (payload) =>
  req('/onboarding', { method: 'POST', body: JSON.stringify(payload) })

export const commitPlan = (tasks, analysis) =>
  req('/plan/commit', { method: 'POST', body: JSON.stringify({ tasks, analysis }) })

export const getTodayPlan = () => req('/plan/today')

export const getHistory = () => req('/history')

export const getStatus = () => req('/status')
