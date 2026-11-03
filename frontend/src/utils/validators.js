export const MAX_IMAGE_MB = 5
export const IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']

export function validateImageFile(file) {
  if (!file) return 'err.noFile'
  if (!IMAGE_TYPES.includes(file.type)) return 'err.imageType'
  if (file.size > MAX_IMAGE_MB * 1024 * 1024) return 'err.imageSize'
  return null
}

export function validateEmail(v) {
  return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test((v || '').trim()) ? null : 'err.email'
}

export function validatePassword(v) {
  if (!v || v.length < 8 || !/[A-Za-z]/.test(v) || !/\d/.test(v)) return 'err.password'
  return null
}

export function validatePositive(v) {
  const n = Number(v)
  return Number.isFinite(n) && n > 0 ? null : 'err.positive'
}

export function validateNonNegative(v) {
  if (v === '' || v == null) return null
  const n = Number(v)
  return Number.isFinite(n) && n >= 0 ? null : 'err.nonNegative'
}

export const inr = (n) => '₹' + Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })
export const fmtDate = (d, lang = 'en') =>
  d ? new Date(d + (String(d).length <= 10 ? 'T00:00:00' : '')).toLocaleDateString(lang === 'te' ? 'te-IN' : 'en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : ''
