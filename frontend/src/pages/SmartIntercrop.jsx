import { useMemo, useState } from 'react'
import { AlertTriangle, BadgeCheck, ChevronDown, Search } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { useLang } from '../i18n'
import { useGet } from '../hooks/useApi'
import { api } from '../services/api'
import { Badge, Button, Card, Empty, ErrorBox, Field, inputCls, Notice, PageHeader, Spinner } from '../components/ui'

const SEASONS = ['kharif', 'rabi', 'zaid']
const SOILS = ['Red soil', 'Black soil', 'Sandy loam', 'Clay loam', 'Alluvial']
const IRR = ['rainfed', 'drip', 'sprinkler', 'canal', 'borewell']
const A = '#1f5130', B = '#e8b32f'

/** Simple top-down sketches of the four planting arrangements. A = main crop, B = companion. */
export function PatternDiagram({ kind, active }) {
  const cells = []
  if (kind === 'row') for (let i = 0; i < 8; i++) cells.push(<rect key={i} x="4" y={4 + i * 11} width="92" height="7" rx="3" fill={i % 2 ? B : A} />)
  if (kind === 'strip') for (let i = 0; i < 4; i++) cells.push(<rect key={i} x={4 + i * 23} y="4" width="21" height="84" rx="3" fill={i % 2 ? B : A} />)
  if (kind === 'mixed') for (let r = 0; r < 7; r++) for (let c = 0; c < 9; c++) cells.push(<circle key={r * 9 + c} cx={10 + c * 10} cy={10 + r * 12} r="3.6" fill={(r * 7 + c * 3) % 3 === 0 ? B : A} />)
  if (kind === 'relay') cells.push(
    <g key="r"><rect x="4" y="18" width="62" height="14" rx="4" fill={A} /><rect x="40" y="48" width="56" height="14" rx="4" fill={B} />
      <line x1="40" y1="12" x2="40" y2="72" stroke="#6b7a6e" strokeDasharray="3 3" /><text x="4" y="84" fontSize="8" fill="#4a3a2c">time →</text></g>)
  return (
    <svg viewBox="0 0 100 92" className={`h-24 w-full rounded border ${active ? 'border-turmeric-400 bg-turmeric-100/40' : 'border-field-200 bg-white'}`} role="img" aria-label={kind}>{cells}</svg>
  )
}

function Combo({ r, primary, big, lang }) {
  const { t } = useLang()
  const [open, setOpen] = useState(!!big)
  const pct = r.score
  const tone = r.rating === 'highly_suitable' ? 'ok' : r.rating === 'suitable' ? 'info' : 'sample'
  const rec = r.patterns.recommended
  return (
    <Card className={big ? 'border-2 border-field-700' : ''}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          {big && <Badge tone="ok">{t('ic.best')}</Badge>}
          <h3 className={`mt-1 font-bold ${big ? 'text-2xl' : 'text-lg'}`}>{lang === 'te' ? primary.name_te : primary.name} <span className="text-field-500">+</span> {lang === 'te' ? r.companion.name_te : r.companion.name}</h3>
          <div className="mt-1 flex flex-wrap gap-2"><Badge tone={tone}>{t('ic.rating.' + r.rating)}</Badge>
            {r.known_system && <Badge tone="info"><BadgeCheck className="mr-1 inline h-3 w-3" aria-hidden />{t('ic.known')}</Badge>}</div>
        </div>
        <div className="w-28 text-right"><p className="font-display text-3xl font-bold">{pct}<span className="text-base text-field-700">/100</span></p>
          <div className="mt-1 h-2 rounded bg-field-100" role="img" aria-label={`${t('ic.score')} ${pct}`}><div className="h-2 rounded bg-field-700" style={{ width: `${pct}%` }} /></div>
          <p className="mt-1 text-xs text-field-700">{t('ic.score')}</p></div>
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
        <div><dt className="text-field-700">{t('ic.growSeason')}</dt><dd className="font-medium capitalize">{t('ic.season.' + r.season + '.short')}</dd></div>
        <div><dt className="text-field-700">{t('ic.waterNeed')}</dt><dd className="font-medium">{t('ic.water.' + r.water.primary)} / {t('ic.water.' + r.water.companion)}</dd></div>
        <div><dt className="text-field-700">{t('ic.duration')}</dt><dd className="font-medium">{r.duration_days.primary.join('–')} / {r.duration_days.companion.join('–')} {t('ic.days')}</dd></div>
        <div><dt className="text-field-700">{t('ic.recommended')}</dt><dd className="font-medium">{t('ic.pat.' + rec)}</dd></div>
      </dl>

      <div className="mt-4 grid gap-2 grid-cols-2 sm:grid-cols-4">
        {r.patterns.options.map((o) => (
          <div key={o.key} title={o.reason}>
            <PatternDiagram kind={o.key} active={o.key === rec} />
            <p className={`mt-1 text-xs ${o.suitable ? 'font-semibold text-field-800' : 'text-field-700/60'}`}>{t('ic.pat.' + o.key)} · {o.suitable ? t('ic.suitable') : t('ic.notSuitable')}</p>
          </div>))}
      </div>
      <p className="mt-2 text-xs text-field-700"><span className="mr-3"><span className="mr-1 inline-block h-2 w-2 rounded-full" style={{ background: A }} />{primary.name}</span><span><span className="mr-1 inline-block h-2 w-2 rounded-full" style={{ background: B }} />{r.companion.name}</span></p>
      <p className="mt-2 text-sm">{r.patterns.options.find((o) => o.key === rec)?.reason}</p>

      <div className="mt-4 grid gap-4 md:grid-cols-2 text-sm">
        <div><h4 className="font-semibold">{t('ic.benefits')}</h4><ul className="mt-1 list-disc space-y-1 pl-5">{r.benefits.map((b) => <li key={b}>{b}</li>)}</ul></div>
        <div><h4 className="font-semibold">{t('ic.limits')}</h4><ul className="mt-1 list-disc space-y-1 pl-5">{r.limitations.map((b) => <li key={b}>{b}</li>)}</ul></div>
      </div>
      {r.regional_note && <Notice tone="info"><strong>{r.regional_note.source}:</strong> {r.regional_note.note}</Notice>}

      <button onClick={() => setOpen(!open)} aria-expanded={open} className="mt-4 flex min-h-[44px] items-center gap-1 text-sm font-semibold text-field-700 underline">
        {t('ic.why')} ({r.points}/{r.points_possible})<ChevronDown className={`h-4 w-4 transition-transform ${open ? 'rotate-180' : ''}`} aria-hidden /></button>
      {open && (
        <ul className="mt-2 space-y-2 text-sm">{r.criteria.map((c) => (
          <li key={c.key} className="rounded bg-field-50 p-2"><div className="flex justify-between font-medium"><span>{c.label}</span><span>{c.evaluated ? `${c.points}/${c.max}` : '–'}</span></div>
            <p className="text-field-700">{c.note}</p></li>))}</ul>)}
    </Card>
  )
}

export default function SmartIntercrop() {
  const { user } = useAuth()
  const { t, lang } = useLang()
  const crops = useGet('/api/intercrop/crops')
  const mine = useGet('/api/crops')
  const meta = useGet('/api/intercrop/meta')
  const [f, setF] = useState({ primary: '', season: 'kharif', soil: '', ph: '', rain: '', temp: '', water: '', irrigation: '' })
  const [q, setQ] = useState('')
  const [errs, setErrs] = useState({})
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const [res, setRes] = useState(null)
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })

  const list = useMemo(() => {
    const s = q.trim().toLowerCase()
    return (crops.data?.crops || []).filter((c) => !s || c.name.toLowerCase().includes(s) || c.name_te.includes(s) || c.group.includes(s))
  }, [crops.data, q])
  const myCropKey = (name) => crops.data?.crops.find((c) => c.name.toLowerCase().startsWith(name.toLowerCase()))?.key

  const range = (v, lo, hi) => (v === '' ? null : Number(v) >= lo && Number(v) <= hi ? null : true)
  const submit = async (e) => {
    e.preventDefault()
    const v = { primary: f.primary ? null : 'ic.err.crop', ph: range(f.ph, 3.5, 9.5) && 'ic.err.ph', rain: range(f.rain, 0, 5000) && 'ic.err.rain', temp: range(f.temp, 5, 45) && 'ic.err.temp' }
    setErrs(v)
    if (Object.values(v).some(Boolean)) return
    setBusy(true); setErr('')
    const num = (x) => (x === '' ? null : Number(x))
    try {
      setRes(await api.post('/api/intercrop/recommend', { primary_crop: f.primary, season: f.season, soil_type: f.soil || null, soil_ph: num(f.ph),
        rainfall_mm: num(f.rain), temperature_c: num(f.temp), water_availability: f.water || null, irrigation: f.irrigation || null, region: user.district }))
    } catch (x) { setErr(x.message) } finally { setBusy(false) }
  }

  if (crops.loading) return <Spinner label={t('common.loading')} />
  if (crops.error) return <ErrorBox message={crops.error} onRetry={crops.reload} />
  const best = res?.recommendations?.[0]
  return (
    <div className="space-y-5">
      <PageHeader title={t('mod.intercrop.name')} subtitle={`${t('ic.tagline')} ${t('mod.intercrop.desc')}`} />
      <Card>
        <form onSubmit={submit} noValidate className="space-y-5">
          <div>
            <p className="mb-2 text-sm font-medium">{t('ic.primary')}</p>
            {mine.data?.length > 0 && (
              <div className="mb-2 flex flex-wrap items-center gap-2 text-xs"><span className="text-field-700">{t('ic.myCrops')}:</span>
                {mine.data.map((c) => { const k = myCropKey(c.crop_name); return k && (
                  <button type="button" key={c.id} onClick={() => setF({ ...f, primary: k, soil: c.soil_type && SOILS.includes(c.soil_type) ? c.soil_type : f.soil })} className="rounded-full border border-field-300 px-3 py-1.5 font-semibold text-field-700 hover:bg-field-100">{t('crop.' + c.crop_name)}</button>) })}</div>)}
            <div className="relative mb-2"><Search className="pointer-events-none absolute left-3 top-3.5 h-4 w-4 text-field-500" aria-hidden />
              <input className={`${inputCls} pl-9`} value={q} onChange={(e) => setQ(e.target.value)} placeholder={t('ic.search')} aria-label={t('ic.search')} /></div>
            {list.length === 0 ? <p className="text-sm text-field-700">{t('ic.noMatch')}</p> : (
              <div role="radiogroup" aria-label={t('ic.primary')} className="grid max-h-56 grid-cols-2 gap-2 overflow-y-auto sm:grid-cols-3 lg:grid-cols-4">
                {list.map((c) => (
                  <button type="button" role="radio" aria-checked={f.primary === c.key} key={c.key} onClick={() => setF({ ...f, primary: c.key })}
                    className={`min-h-[44px] rounded-md border p-2 text-left text-sm ${f.primary === c.key ? 'border-field-700 bg-field-100 font-semibold' : 'border-field-200 bg-white hover:bg-field-50'}`}>
                    {lang === 'te' ? c.name_te : c.name}<span className="block text-xs capitalize text-field-700">{c.group}</span></button>))}
              </div>)}
            {errs.primary && <p role="alert" className="mt-1 text-xs font-medium text-red-700">{t(errs.primary)}</p>}
          </div>

          <div>
            <p className="mb-2 text-sm font-medium">{t('ic.season')}</p>
            <div role="radiogroup" className="inline-flex overflow-hidden rounded-md border border-field-300">
              {SEASONS.map((s) => (<button type="button" role="radio" aria-checked={f.season === s} key={s} onClick={() => setF({ ...f, season: s })}
                className={`min-h-[44px] px-4 text-sm font-semibold ${f.season === s ? 'bg-field-700 text-white' : 'bg-white text-field-700 hover:bg-field-100'}`}>{t('ic.season.' + s)}</button>))}
            </div>
          </div>

          <div>
            <p className="mb-2 text-xs text-field-700">{t('ic.optional')}</p>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <Field label={t('crops.soil')}><select className={inputCls} value={f.soil} onChange={set('soil')}><option value="">{t('common.unknown')}</option>{SOILS.map((s) => <option key={s}>{s}</option>)}</select></Field>
              <Field label={t('ic.ph')} error={errs.ph}><input inputMode="decimal" className={inputCls} value={f.ph} onChange={set('ph')} placeholder="6.5" /></Field>
              <Field label={t('ic.temp')} error={errs.temp}><input inputMode="decimal" className={inputCls} value={f.temp} onChange={set('temp')} placeholder="28" /></Field>
              <Field label={t('ic.rain')} error={errs.rain}><input inputMode="decimal" className={inputCls} value={f.rain} onChange={set('rain')} placeholder="650" /></Field>
              <Field label={t('ic.water')}><select className={inputCls} value={f.water} onChange={set('water')}><option value="">{t('common.unknown')}</option>{['low', 'medium', 'high'].map((w) => <option key={w} value={w}>{t('ic.water.' + w)}</option>)}</select></Field>
              <Field label={t('ic.irrigation')}><select className={inputCls} value={f.irrigation} onChange={set('irrigation')}><option value="">{t('common.unknown')}</option>{IRR.map((w) => <option key={w} value={w}>{t('ic.irr.' + w)}</option>)}</select></Field>
            </div>
          </div>
          <ErrorBox message={err} />
          <Button type="submit" loading={busy}>{busy ? t('ic.finding') : t('ic.find')}</Button>
        </form>
      </Card>

      {busy && <Spinner label={t('ic.finding')} />}
      {res && !busy && (
        <div className="space-y-4">
          <Card className="flex flex-wrap items-center gap-3 !p-3 text-sm">
            <Badge tone={res.confidence === 'high' ? 'ok' : 'sample'}>{t('ic.confidence')}: {res.data_completeness}%</Badge>
            <span className="capitalize">{t('ic.season.' + res.season + '.short')}</span><span>·</span><span>{lang === 'te' ? res.primary_crop.name_te : res.primary_crop.name}</span>
            <span className="ml-auto text-xs text-field-700">{t('ic.dataNote')}</span>
          </Card>
          {res.warnings.map((w) => <div key={w} role="alert" className="flex gap-2 rounded-md border border-turmeric-400/50 bg-turmeric-100 p-3 text-sm text-soil-700"><AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />{w}</div>)}
          {res.assumptions.map((a) => <Notice key={a} tone="info">{a}</Notice>)}
          {res.recommendations.length === 0 ? <Empty title={t('ic.empty')} text={t('ic.emptyText')} /> : (
            <>
              <Combo r={best} primary={res.primary_crop} big lang={lang} />
              {res.recommendations.length > 1 && <h2 className="pt-2 text-lg font-semibold">{t('ic.alternatives')}</h2>}
              <div className="grid gap-4 lg:grid-cols-2">{res.recommendations.slice(1).map((r) => <Combo key={r.companion.key} r={r} primary={res.primary_crop} lang={lang} />)}</div>
            </>)}
          {res.excluded.length > 0 && (
            <details className="rounded-lg border border-field-200 bg-white p-4 text-sm"><summary className="cursor-pointer font-semibold">{t('ic.excluded')} ({res.excluded.length})</summary>
              <ul className="mt-2 space-y-1">{res.excluded.map((e) => <li key={e.key}><strong>{e.name}:</strong> {e.reason}</li>)}</ul></details>)}
          <Card>
            <h2 className="mb-2 text-lg font-semibold">{t('ic.precautions')}</h2>
            <ul className="list-disc space-y-1 pl-5 text-sm"><li>{t('ic.p1')}</li><li>{t('ic.p2')}</li><li>{t('ic.p3')}</li><li>{t('ic.p4')}</li></ul>
            <p className="mt-3 text-xs text-field-700">{res.disclaimer}</p>
            <p className="mt-2 text-xs text-field-700">{res.data_note}</p>
            <p className="mt-2 text-xs font-semibold">{t('ic.refs')}:</p>
            <ul className="text-xs text-field-700">{res.references_to_verify.map((r) => <li key={r.url}>{r.name}</li>)}</ul>
          </Card>
        </div>)}
    </div>
  )
}
