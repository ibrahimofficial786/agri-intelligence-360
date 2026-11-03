import { AlertTriangle, Inbox, Loader2 } from 'lucide-react'
import { useLang } from '../i18n'

export const Card = ({ className = '', children, as: As = 'section' }) => (
  <As className={`rounded-lg border border-field-200 bg-white p-4 sm:p-5 ${className}`}>{children}</As>
)

const variants = {
  primary: 'bg-field-700 text-white hover:bg-field-800 disabled:bg-field-300',
  secondary: 'border border-field-300 bg-white text-field-800 hover:bg-field-100 disabled:opacity-50',
  accent: 'bg-turmeric-400 text-field-900 hover:bg-turmeric-600 hover:text-white disabled:opacity-50',
  danger: 'border border-red-300 bg-white text-red-700 hover:bg-red-50 disabled:opacity-50',
  ghost: 'text-field-700 hover:bg-field-100',
}
export function Button({ variant = 'primary', loading, className = '', children, ...p }) {
  return (
    <button {...p} disabled={p.disabled || loading}
      className={`inline-flex min-h-[44px] items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-semibold transition-colors disabled:cursor-not-allowed ${variants[variant]} ${className}`}>
      {loading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden />}
      {children}
    </button>
  )
}

export function Field({ label, error, hint, className = '', children }) {
  const { t } = useLang()
  return (
    <label className={`block text-sm ${className}`}>
      <span className="mb-1 block font-medium text-field-800">{label}</span>
      {children}
      {hint && !error && <span className="mt-1 block text-xs text-field-700/70">{hint}</span>}
      {error && <span role="alert" className="mt-1 block text-xs font-medium text-red-700">{t(error)}</span>}
    </label>
  )
}
export const inputCls = 'w-full min-h-[44px] rounded-md border border-field-300 bg-white px-3 py-2 text-field-900 placeholder:text-field-700/40'

export const Spinner = ({ label }) => (
  <div role="status" className="flex items-center justify-center gap-2 py-10 text-field-700">
    <Loader2 className="h-5 w-5 animate-spin" aria-hidden /> <span>{label}</span>
  </div>
)

export const ErrorBox = ({ message, onRetry }) => {
  const { t } = useLang()
  if (!message) return null
  return (
    <div role="alert" className="flex items-start gap-3 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
      <div className="flex-1">{message}</div>
      {onRetry && <button onClick={onRetry} className="font-semibold underline">{t('common.retry')}</button>}
    </div>
  )
}

export const Empty = ({ title, text, action }) => (
  <div className="rounded-lg border border-dashed border-field-300 bg-field-50 p-8 text-center">
    <Inbox className="mx-auto h-8 w-8 text-field-500" aria-hidden />
    <p className="mt-2 font-display text-lg font-semibold">{title}</p>
    {text && <p className="mx-auto mt-1 max-w-md text-sm text-field-700">{text}</p>}
    {action && <div className="mt-4">{action}</div>}
  </div>
)

const tones = {
  sample: 'bg-turmeric-100 text-turmeric-600', ok: 'bg-field-100 text-field-700', warn: 'bg-red-100 text-red-800', info: 'bg-soil-100 text-soil-700',
}
export const Badge = ({ tone = 'ok', children }) => (
  <span className={`inline-block rounded px-2 py-0.5 text-xs font-semibold ${tones[tone]}`}>{children}</span>
)
export const SampleBadge = () => { const { t } = useLang(); return <Badge tone="sample">{t('common.sample')}</Badge> }

export const Notice = ({ tone = 'sample', children }) => (
  <div className={`rounded-md border p-3 text-sm ${tone === 'sample' ? 'border-turmeric-400/50 bg-turmeric-100 text-soil-700' : 'border-field-200 bg-field-100 text-field-800'}`}>{children}</div>
)

export const PageHeader = ({ title, subtitle, children }) => (
  <header className="mb-5 flex flex-wrap items-end justify-between gap-3">
    <div>
      <h1 className="text-2xl font-bold sm:text-3xl">{title}</h1>
      {subtitle && <p className="mt-1 max-w-2xl text-sm text-field-700">{subtitle}</p>}
    </div>
    {children}
  </header>
)

/** Crop stage ribbon: one segment per stage, widths proportional to duration. */
export function StageRibbon({ calendar, lang }) {
  const total = calendar.reduce((s, c) => s + (c.end_day - c.start_day), 0) || 1
  return (
    <div className="flex h-12 w-full overflow-hidden rounded-md border border-field-300" role="img"
      aria-label={calendar.map((c) => `${lang === 'te' && c.name_te ? c.name_te : c.name_en}: ${c.status}`).join(', ')}>
      {calendar.map((c) => (
        <div key={c.key} style={{ width: `${((c.end_day - c.start_day) / total) * 100}%` }}
          className={`flex items-center justify-center border-r border-white/60 px-1 text-center text-[11px] font-semibold leading-tight last:border-r-0
          ${c.status === 'current' ? 'bg-turmeric-400 text-field-900' : c.status === 'completed' ? 'bg-field-700 text-white' : 'bg-field-100 text-field-700'}`}>
          <span className="hidden sm:inline">{(lang === 'te' && c.name_te ? c.name_te : c.name_en).split(' ')[0]}</span>
        </div>
      ))}
    </div>
  )
}

export const stageName = (s, lang) => (s ? (lang === 'te' && s.name_te ? s.name_te : s.name_en) : '')
