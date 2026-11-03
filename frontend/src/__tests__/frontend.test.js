import { describe, expect, it } from 'vitest'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { en, te } from '../i18n/translations'
import { inr, validateEmail, validateImageFile, validateNonNegative, validatePassword, validatePositive } from '../utils/validators'

describe('translations', () => {
  it('Telugu has every English key and vice versa', () => {
    expect(Object.keys(en).filter((k) => !(k in te))).toEqual([])
    expect(Object.keys(te).filter((k) => !(k in en))).toEqual([])
  })
  it('no empty strings and placeholders match', () => {
    for (const k of Object.keys(en)) {
      expect(te[k].trim(), k).not.toBe('')
      expect((en[k].match(/\{\w+\}/g) || []).sort(), k).toEqual((te[k].match(/\{\w+\}/g) || []).sort())
    }
  })
  it('every static t(...) key used in the source exists', () => {
    const files = []
    const walk = (d) => readdirSync(d).forEach((f) => { const p = join(d, f); statSync(p).isDirectory() ? (f !== '__tests__' && walk(p)) : /\.jsx?$/.test(f) && files.push(p) })
    walk(join(__dirname, '..'))
    const missing = []
    for (const f of files) {
      for (const m of readFileSync(f, 'utf8').matchAll(/\bt\(\s*'([\w.]+)'\s*[,)]/g)) if (!(m[1] in en)) missing.push(`${f}: ${m[1]}`)
    }
    expect(missing).toEqual([])
  })
})

describe('validators', () => {
  it('validates image files', () => {
    expect(validateImageFile(null)).toBe('err.noFile')
    expect(validateImageFile({ type: 'application/pdf', size: 10 })).toBe('err.imageType')
    expect(validateImageFile({ type: 'image/png', size: 6 * 1024 * 1024 })).toBe('err.imageSize')
    expect(validateImageFile({ type: 'image/webp', size: 1000 })).toBeNull()
  })
  it('validates email, password and numbers', () => {
    expect(validateEmail('a@b.co')).toBeNull(); expect(validateEmail('nope')).toBe('err.email')
    expect(validatePassword('abc12345')).toBeNull(); expect(validatePassword('abcdefgh')).toBe('err.password')
    expect(validatePositive('0')).toBe('err.positive'); expect(validatePositive('2.5')).toBeNull()
    expect(validateNonNegative('')).toBeNull(); expect(validateNonNegative('-1')).toBe('err.nonNegative')
  })
  it('formats rupees', () => { expect(inr(59000)).toBe('₹59,000') })
})
