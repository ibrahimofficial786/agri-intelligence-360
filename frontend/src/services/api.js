// Empty = same origin (Vite proxies /api to the backend, works on localhost and ngrok).
// Set VITE_API_URL only if the backend is hosted on another domain.
const BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')
const TOKEN_KEY = 'agri_token'

let token = typeof localStorage !== 'undefined' ? localStorage.getItem(TOKEN_KEY) : null
let onUnauthorized = () => {}

export const setToken = (t) => {
  token = t
  if (t) localStorage.setItem(TOKEN_KEY, t)
  else localStorage.removeItem(TOKEN_KEY)
}
export const hasToken = () => !!token
export const setUnauthorizedHandler = (fn) => { onUnauthorized = fn }

export class ApiError extends Error {
  constructor(message, status) { super(message); this.status = status }
}

function messageFrom(body, status) {
  const d = body && body.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) return d.map((e) => (e.msg || '').replace(/^Value error, /, '')).filter(Boolean).join('. ')
  return status >= 500 ? 'Server error. Please try again.' : `Request failed (${status})`
}

// Lightweight response validation: throws if the payload is not the expected shape.
export function expect(data, shape) {
  const ok = Object.entries(shape).every(([k, type]) => (type === 'array' ? Array.isArray(data?.[k]) : typeof data?.[k] === type))
  if (!ok) throw new ApiError('Unexpected response from the server', 502)
  return data
}

async function request(path, { method = 'GET', body, form, blob, params } = {}) {
  const url = new URL(BASE + path, window.location.origin)
  Object.entries(params || {}).forEach(([k, v]) => v !== undefined && v !== null && v !== '' && url.searchParams.set(k, v))
  const headers = { 'ngrok-skip-browser-warning': '1' }
  if (token) headers.Authorization = `Bearer ${token}`
  let payload
  if (form) payload = form
  else if (body !== undefined) { headers['Content-Type'] = 'application/json'; payload = JSON.stringify(body) }
  let res
  try {
    res = await fetch(url, { method, headers, body: payload })
  } catch {
    throw new ApiError('Cannot reach the server. Make sure the backend is running on port 8000.', 0)
  }
  if (res.status === 401 && token && !path.startsWith('/api/auth/login')) onUnauthorized()
  if (!res.ok) {
    let b = null
    try { b = await res.json() } catch { /* ignore */ }
    throw new ApiError(messageFrom(b, res.status), res.status)
  }
  if (res.status === 204) return null
  return blob ? res.blob() : res.json()
}

export const api = {
  get: (p, params) => request(p, { params }),
  post: (p, body) => request(p, { method: 'POST', body }),
  put: (p, body) => request(p, { method: 'PUT', body }),
  del: (p) => request(p, { method: 'DELETE' }),
  upload: (p, form) => request(p, { method: 'POST', form }),
  blob: (p) => request(p, { blob: true }),
}
