import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { Wheat } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { useLang } from '../i18n'
import { Button, ErrorBox, Field, inputCls, Notice } from '../components/ui'
import LangSwitch from '../components/LangSwitch'
import { validateEmail, validatePassword } from '../utils/validators'
import { DEMO } from './Landing'

const DISTRICTS = ['Kurnool', 'Nandyal', 'Anantapur', 'Kadapa', 'Chittoor', 'Guntur', 'Krishna']

function Shell({ title, children }) {
  const { t } = useLang()
  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        <div className="mb-5 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 font-display font-bold text-field-800"><Wheat className="h-6 w-6 text-turmeric-600" aria-hidden />AGRI 360</Link>
          <LangSwitch />
        </div>
        <div className="rounded-lg border border-field-200 bg-white p-6">
          <h1 className="mb-4 text-2xl font-bold">{title}</h1>
          {children}
        </div>
      </div>
    </div>
  )
}

export function Login() {
  const { user, login } = useAuth()
  const { t } = useLang()
  const nav = useNavigate()
  const [f, setF] = useState({ email: '', password: '' })
  const [errs, setErrs] = useState({})
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  if (user) return <Navigate to="/app" replace />

  const submit = async (e) => {
    e.preventDefault()
    const v = { email: validateEmail(f.email), password: f.password ? null : 'err.required' }
    setErrs(v)
    if (v.email || v.password) return
    setBusy(true); setError('')
    try { await login(f.email.trim(), f.password); nav('/app') } catch (err) { setError(err.message) } finally { setBusy(false) }
  }
  return (
    <Shell title={t('auth.login')}>
      <form onSubmit={submit} className="space-y-4" noValidate>
        <Field label={t('auth.email')} error={errs.email}><input className={inputCls} type="email" autoComplete="email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} /></Field>
        <Field label={t('auth.password')} error={errs.password}><input className={inputCls} type="password" autoComplete="current-password" value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} /></Field>
        <ErrorBox message={error} />
        <Button type="submit" loading={busy} className="w-full">{t('auth.login')}</Button>
      </form>
      <div className="mt-4 space-y-2">
        <Notice tone="info">{t('auth.demoHint', { email: DEMO.email, password: DEMO.password })}
          <button type="button" className="ml-1 font-semibold underline" onClick={() => setF(DEMO)}>{t('auth.fillDemo')}</button></Notice>
        <p className="text-center text-sm">{t('auth.noAccount')} <Link className="font-semibold text-field-700 underline" to="/register">{t('auth.register')}</Link></p>
      </div>
    </Shell>
  )
}

export function Register() {
  const { user, register } = useAuth()
  const { t, lang } = useLang()
  const nav = useNavigate()
  const [f, setF] = useState({ full_name: '', email: '', password: '', district: 'Kurnool', mandal: '' })
  const [errs, setErrs] = useState({})
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  if (user) return <Navigate to="/app" replace />
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    const v = { full_name: f.full_name.trim().length >= 2 ? null : 'err.required', email: validateEmail(f.email), password: validatePassword(f.password) }
    setErrs(v)
    if (Object.values(v).some(Boolean)) return
    setBusy(true); setError('')
    try { await register({ ...f, email: f.email.trim(), mandal: f.mandal || null, language: lang }); nav('/app') } catch (err) { setError(err.message) } finally { setBusy(false) }
  }
  return (
    <Shell title={t('auth.register')}>
      <form onSubmit={submit} className="space-y-4" noValidate>
        <Field label={t('auth.name')} error={errs.full_name}><input className={inputCls} autoComplete="name" value={f.full_name} onChange={set('full_name')} /></Field>
        <Field label={t('auth.email')} error={errs.email}><input className={inputCls} type="email" autoComplete="email" value={f.email} onChange={set('email')} /></Field>
        <Field label={t('auth.password')} error={errs.password} hint={t('auth.passwordHint')}><input className={inputCls} type="password" autoComplete="new-password" value={f.password} onChange={set('password')} /></Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label={t('common.district')}><select className={inputCls} value={f.district} onChange={set('district')}>{DISTRICTS.map((d) => <option key={d}>{d}</option>)}</select></Field>
          <Field label={t('common.mandal')}><input className={inputCls} value={f.mandal} onChange={set('mandal')} /></Field>
        </div>
        <ErrorBox message={error} />
        <Button type="submit" loading={busy} className="w-full">{t('auth.register')}</Button>
      </form>
      <p className="mt-4 text-center text-sm">{t('auth.haveAccount')} <Link className="font-semibold text-field-700 underline" to="/login">{t('auth.login')}</Link></p>
    </Shell>
  )
}
