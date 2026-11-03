import { Link, useNavigate } from 'react-router-dom'
import { ArrowRight, Blend, Bug, Languages, MapPin, Sprout, Store, Wheat, BellRing, Scale } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { useLang } from '../i18n'
import LangSwitch from '../components/LangSwitch'
import { Button } from '../components/ui'
import { useState } from 'react'

export const DEMO = { email: 'demo@agri360.example', password: 'Demo@12345' }

const modules = [
  { icon: Sprout, k: 'krishi', to: '/app/crops' },
  { icon: Bug, k: 'pest', to: '/app/pest-alert' },
  { icon: Store, k: 'mandi', to: '/app/mandi-mate' },
  { icon: Blend, k: 'intercrop', to: '/app/smart-intercrop' },
]

export default function Landing() {
  const { t, lang } = useLang()
  const { user, login } = useAuth()
  const nav = useNavigate()
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const demo = async () => {
    setBusy(true); setErr('')
    try { await login(DEMO.email, DEMO.password); nav('/app') } catch (e) { setErr(e.message) } finally { setBusy(false) }
  }
  const stages = [['emergence', 'done'], ['vegetative', 'done'], ['flowering', 'now'], ['pod', ''], ['harvest', '']]

  return (
    <div>
      <header className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
        <Link to="/" className="flex items-center gap-2 font-display text-lg font-bold text-field-800"><Wheat className="h-6 w-6 text-turmeric-600" aria-hidden />AGRI INTELLIGENCE 360</Link>
        <div className="flex items-center gap-3"><LangSwitch />
          <Link to={user ? '/app' : '/login'} className="hidden text-sm font-semibold text-field-700 sm:inline">{user ? t('nav.dashboard') : t('auth.login')}</Link></div>
      </header>

      <section className="bg-field-900 text-white">
        <div className="mx-auto grid max-w-6xl gap-8 px-4 py-14 sm:px-6 lg:grid-cols-2 lg:py-20">
          <div>
            <p className="mb-3 flex items-center gap-2 text-sm text-field-300"><MapPin className="h-4 w-4" aria-hidden />{t('landing.region')}</p>
            <h1 className="text-4xl font-bold leading-tight sm:text-5xl">{t('landing.tagline')}</h1>
            <p className="mt-4 max-w-xl text-field-100">{t('landing.intro')}</p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link to="/register"><Button variant="accent">{t('landing.cta.start')}<ArrowRight className="h-4 w-4" aria-hidden /></Button></Link>
              <Button variant="secondary" onClick={demo} loading={busy}>{t('landing.cta.demo')}</Button>
            </div>
            {err && <p role="alert" className="mt-3 text-sm text-red-200">{err}</p>}
            <p className="mt-3 text-xs text-field-300">{t('landing.demoNote')}</p>
          </div>
          <div className="rounded-lg bg-field-800 p-5" aria-label={t('landing.ribbonTitle')}>
            <p className="font-display text-lg font-semibold">{t('landing.ribbonTitle')}</p>
            <p className="mb-4 text-sm text-field-300">{t('landing.ribbonText')}</p>
            <div className="flex h-14 overflow-hidden rounded-md">
              {stages.map(([k, s]) => (
                <div key={k} className={`flex flex-1 items-center justify-center px-1 text-center text-[11px] font-semibold sm:text-xs ${s === 'now' ? 'bg-turmeric-400 text-field-900' : s === 'done' ? 'bg-field-600 text-white' : 'bg-field-700 text-field-300'}`}>{t('landing.stage.' + k)}</div>
              ))}
            </div>
            <ul className="mt-4 space-y-1 text-sm text-field-100"><li>{t('landing.ribbon.a')}</li><li>{t('landing.ribbon.b')}</li></ul>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-14 sm:px-6">
        <h2 className="text-2xl font-bold sm:text-3xl">{t('landing.modules')}</h2>
        <div className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {modules.map(({ icon: Icon, k, to }) => (
            <Link key={k} to={user ? to : '/login'} className="group rounded-lg border border-field-200 bg-white p-5 hover:border-field-600">
              <Icon className="h-7 w-7 text-field-600" aria-hidden />
              <h3 className="mt-3 text-xl font-semibold">{t(`mod.${k}.name`)}</h3>
              <p className="text-sm font-medium text-turmeric-600">{t(`mod.${k}.role`)}</p>
              <p className="mt-2 text-sm text-field-700">{t(`mod.${k}.desc`)}</p>
              <span className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-field-700 group-hover:underline">{t('landing.open')}<ArrowRight className="h-4 w-4" aria-hidden /></span>
            </Link>
          ))}
        </div>
      </section>

      <section className="bg-field-100">
        <div className="mx-auto grid max-w-6xl gap-8 px-4 py-14 sm:px-6 lg:grid-cols-2">
          <div>
            <h2 className="text-2xl font-bold">{t('landing.benefits')}</h2>
            <ul className="mt-5 space-y-4">
              {[[Sprout, 'b1'], [Scale, 'b2'], [BellRing, 'b3'], [Languages, 'b4']].map(([Icon, k]) => (
                <li key={k} className="flex gap-3"><Icon className="mt-0.5 h-5 w-5 shrink-0 text-field-600" aria-hidden /><span className="text-sm">{t('landing.' + k)}</span></li>
              ))}
            </ul>
          </div>
          <div>
            <h2 className="text-2xl font-bold">{t('landing.how')}</h2>
            <ol className="mt-5 space-y-4">
              {['s1', 's2', 's3'].map((k, i) => (
                <li key={k} className="flex gap-3"><span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-field-700 text-sm font-bold text-white">{i + 1}</span><span className="text-sm">{t('landing.' + k)}</span></li>
              ))}
            </ol>
            <p className="mt-6 rounded-md bg-white p-3 text-sm"><strong>{t('landing.langs')}:</strong> English, తెలుగు</p>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-14 text-center sm:px-6">
        <h2 className="text-2xl font-bold sm:text-3xl">{t('landing.finalCta')}</h2>
        <div className="mt-5 flex flex-wrap justify-center gap-3">
          <Link to="/register"><Button>{t('auth.register')}</Button></Link>
          <Link to="/login"><Button variant="secondary">{t('auth.login')}</Button></Link>
        </div>
      </section>
      <footer className="border-t border-field-200 px-4 py-6 text-center text-xs text-field-700">{t('landing.footer')}</footer>
    </div>
  )
}
