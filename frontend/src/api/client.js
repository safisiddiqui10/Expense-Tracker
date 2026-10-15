const BASE = '/api'

async function apiFetch(path, options = {}) {
  const res = await fetch(BASE + path, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  const data = await res.json()
  if (!res.ok) throw data
  return data
}

export const api = {
  login: (email, password) =>
    apiFetch('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  register: (name, email, password) =>
    apiFetch('/auth/register', { method: 'POST', body: JSON.stringify({ name, email, password }) }),
  logout: () => apiFetch('/auth/logout', { method: 'POST' }),
  me: () => apiFetch('/auth/me'),

  getProfile: (params = {}) => {
    const cleaned = Object.fromEntries(Object.entries(params).filter(([, v]) => v))
    return apiFetch('/profile?' + new URLSearchParams(cleaned))
  },

  getExpense: (id) => apiFetch(`/expenses/${id}`),
  addExpense: (data) => apiFetch('/expenses', { method: 'POST', body: JSON.stringify(data) }),
  updateExpense: (id, data) => apiFetch(`/expenses/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteExpense: (id) => apiFetch(`/expenses/${id}`, { method: 'DELETE' }),
}
