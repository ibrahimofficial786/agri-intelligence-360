import { useEffect, useRef, useState } from 'react'
import { ImageUp, ShieldAlert } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { useLang } from '../i18n'
import { useGet } from '../hooks/useApi'
import { api } from '../services/api'
import { Badge, Button, Card, Empty, ErrorBox, Field, inputCls, Notice, PageHeader, Spinner } from '../components/ui'
import { fmtDate, validateImageFile } from '../utils/validators'

const CROPS = ['Groundnut', 'Cotton', 'Paddy', 'Red gram']

function AuthImage({ id, className }) {
  const [src, setSrc] = useState(null)
  useEffect(() => {
    let url
    api.blob(`/api/health/reports/${id}/image`).then((b) => { url = URL.createObjectURL(b); setSrc(url) }).catch(() => {})
    return () => url && URL.revokeObjectURL(url)
  }, [id])
  return src ? <img src={src} alt="" className={className} /> : <div className={`${className} bg-field-100`} />
}

function Result({ r }) {
  const { t } = useLang()
  const res = r.result || {}
  const tone = r.status === 'analysed' ? 'ok' : r.status === 'uncertain' ? 'warn' : 'info'
  return (
    <Card>
      <div className="grid gap-4 sm:grid-cols-[180px_1fr]">
        {r.has_image && <AuthImage id={r.id} className="h-44 w-full rounded-md object-cover sm:w-44" />}
        <div>
          <Badge tone={tone}>{t('health.status.' + r.status)}</Badge>
          <h3 className="mt-2 text-xl font-bold">{res.info?.title || (r.status === 'model_unavailable' ? t('health.unavailableTitle') : t('health.noResult'))}</h3>
          {r.confidence != null && <p className="text-sm text-field-700">{t('health.confidence')}: {(r.confidence * 100).toFixed(0)}% <span className="text-xs">({t('health.notProof')})</span></p>}
          <p className="mt-2 text-sm">{res.message}</p>
          {res.info && <p className="mt-2 text-sm text-field-700">{res.info.description}</p>}
        </div>
      </div>
      {res.info && (
        <div className="mt-4 grid gap-4 md:grid-cols-2 text-sm">
          <div><h4 className="font-semibold">{t('health.monitoring')}</h4><ul className="list-disc pl-5">{res.info.monitoring.map((m) => <li key={m}>{m}</li>)}</ul></div>
          <div><h4 className="font-semibold">{t('health.prevention')}</h4><ul className="list-disc pl-5">{res.info.prevention.map((m) => <li key={m}>{m}</li>)}</ul></div>
        </div>
      )}
      {res.predictions?.length > 1 && <p className="mt-3 text-xs text-field-700">{t('health.others')}: {res.predictions.slice(1).map((p) => `${p.label.replace(/_/g, ' ')} ${(p.confidence * 100).toFixed(0)}%`).join(', ')}</p>}
      <p className="mt-3 flex gap-2 text-xs text-field-700"><ShieldAlert className="h-4 w-4 shrink-0" aria-hidden />{res.disclaimer || t('health.disclaimer')}</p>
    </Card>
  )
}

function Analyse() {
  const { t, lang } = useLang()
  const status = useGet('/api/health/status')
  const crops = useGet('/api/crops')
  const hist = useGet('/api/health/reports', { limit: 10 })
  const [cropKey, setCropKey] = useState('Groundnut')
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)
  const input = useRef()

  const pick = (e) => {
    const f = e.target.files[0]
    setResult(null)
    if (!f) return
    const v = validateImageFile(f)
    if (v) { setErr(t(v)); setFile(null); setPreview(null); return }
    setErr(''); setFile(f); setPreview(URL.createObjectURL(f))
  }
  useEffect(() => () => preview && URL.revokeObjectURL(preview), [preview])

  const run = async () => {
    if (!file) { setErr(t('err.noFile')); return }
    setBusy(true); setErr('')
    const fd = new FormData()
    fd.append('file', file)
    if (cropKey.startsWith('id:')) fd.append('crop_id', cropKey.slice(3)); else fd.append('crop_name', cropKey)
    try { const r = await api.upload('/api/health/analyse', fd); setResult(r); hist.reload() } catch (e) { setErr(e.message) } finally { setBusy(false) }
  }
  const unavailable = status.data && !status.data.model_available
  return (
    <div className="space-y-5">
      {unavailable && <Notice><strong>{t('health.unavailableTitle')}.</strong> {t('health.unavailableText')} <span className="block text-xs opacity-80">{status.data.message}</span></Notice>}
      <Card>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-4">
            <Field label={t('crops.crop')}>
              <select className={inputCls} value={cropKey} onChange={(e) => setCropKey(e.target.value)}>
                {(crops.data || []).map((c) => <option key={c.id} value={`id:${c.id}`}>{t('crop.' + c.crop_name)} – {c.location} ({fmtDate(c.sowing_date, lang)})</option>)}
                {CROPS.map((c) => <option key={c} value={c}>{t('crop.' + c)}</option>)}
              </select>
            </Field>
            <button type="button" onClick={() => input.current.click()} className="flex w-full flex-col items-center gap-2 rounded-lg border-2 border-dashed border-field-300 bg-field-50 p-6 text-sm text-field-700 hover:bg-field-100">
              <ImageUp className="h-8 w-8 text-field-600" aria-hidden />{file ? file.name : t('health.choose')}<span className="text-xs">{t('health.formats')}</span>
            </button>
            <input ref={input} type="file" accept="image/jpeg,image/png,image/webp" className="sr-only" onChange={pick} aria-label={t('health.choose')} />
            <ErrorBox message={err} />
            <Button onClick={run} loading={busy} disabled={unavailable || !file} className="w-full">{busy ? t('health.analysing') : t('health.analyse')}</Button>
          </div>
          <div>{preview ? <img src={preview} alt={t('health.preview')} className="max-h-72 w-full rounded-md object-contain" /> : <div className="flex h-full min-h-40 items-center justify-center rounded-md bg-field-50 text-sm text-field-700">{t('health.preview')}</div>}</div>
        </div>
      </Card>
      {result && <Result r={result} />}
      <h2 className="text-lg font-semibold">{t('health.history')}</h2>
      {hist.loading ? <Spinner label={t('common.loading')} /> : hist.data?.length === 0 ? <Empty title={t('health.noHistory')} text={t('health.noHistoryText')} /> : (
        <ul className="grid gap-3 sm:grid-cols-2">{hist.data?.map((r) => (
          <li key={r.id}><button onClick={() => setResult(r)} className="flex w-full items-center gap-3 rounded-lg border border-field-200 bg-white p-3 text-left hover:border-field-600">
            {r.has_image ? <AuthImage id={r.id} className="h-14 w-14 rounded object-cover" /> : <div className="h-14 w-14 rounded bg-field-100" />}
            <div className="text-sm"><p className="font-semibold">{t('crop.' + r.crop_name)} {r.is_demo && <Badge tone="sample">{t('common.demo')}</Badge>}</p><p className="text-field-700">{fmtDate(r.created_at, lang)} · {t('health.status.' + r.status)}</p></div></button></li>))}</ul>
      )}
    </div>
  )
}

function Community() {
  const { t, lang } = useLang()
  const { user } = useAuth()
  const alerts = useGet('/api/risk/alerts')
  const mine = useGet('/api/risk/reports/mine')
  const status = useGet('/api/health/status')
  const today = new Date().toISOString().slice(0, 10)
  const [f, setF] = useState({ crop_name: 'Groundnut', district: user.district, area: user.mandal || '', report_date: today, problem: 'Leaf spot', notes: '' })
  const [photo, setPhoto] = useState(null)
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setErr(''); setMsg('')
    if (!f.district.trim() || f.report_date > today) { setErr(t('err.required')); return }
    if (photo) { const v = validateImageFile(photo); if (v) { setErr(t(v)); return } }
    const fd = new FormData()
    Object.entries(f).forEach(([k, v]) => v && fd.append(k, v))
    if (photo) fd.append('photo', photo)
    setBusy(true)
    try { const r = await api.upload('/api/risk/reports', fd); setMsg(t('risk.saved') + (r.alert_triggered ? ' ' + t('risk.alertTriggered') : '')); alerts.reload(); mine.reload() } catch (x) { setErr(x.message) } finally { setBusy(false) }
  }
  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <div className="space-y-4">
        <h2 className="text-lg font-semibold">{t('risk.alerts')}</h2>
        {alerts.loading ? <Spinner label={t('common.loading')} /> : alerts.data?.alerts.length === 0 ? <Empty title={t('risk.noAlerts')} text={t('risk.noAlertsText')} /> :
          alerts.data.alerts.map((a) => (
            <Card key={a.key} className="border-turmeric-400">
              <div className="flex items-center justify-between"><h3 className="font-semibold">{t('crop.' + a.crop_name)}: {a.problem}</h3><Badge tone={a.level === 'elevated' ? 'warn' : 'sample'}>{t('risk.status.' + a.status)} · {t('risk.level.' + a.level)}</Badge></div>
              <dl className="mt-2 grid grid-cols-2 gap-1 text-sm"><dt className="text-field-700">{t('risk.count')}</dt><dd>{a.report_count}</dd><dt className="text-field-700">{t('risk.area')}</dt><dd>{a.district}{a.areas.length ? ` (${a.areas.join(', ')})` : ''}</dd><dt className="text-field-700">{t('risk.period')}</dt><dd>{fmtDate(a.period_start, lang)} – {fmtDate(a.period_end, lang)}</dd></dl>
              <p className="mt-2 text-sm text-field-700">{a.explanation}</p>{a.has_demo_reports && <div className="mt-2"><Badge tone="sample">{t('common.demo')}</Badge></div>}
            </Card>))}
        <Notice tone="info">{t('risk.suspectedNote')}</Notice>
        <h2 className="pt-2 text-lg font-semibold">{t('risk.mine')}</h2>
        {mine.data?.length === 0 ? <p className="text-sm text-field-700">{t('risk.noMine')}</p> : <ul className="space-y-1 text-sm">{mine.data?.map((r) => <li key={r.id}>{fmtDate(r.report_date, lang)} · {t('crop.' + r.crop_name)} · {r.problem} <Badge tone="info">{t('risk.suspected')}</Badge></li>)}</ul>}
      </div>
      <Card>
        <h2 className="mb-1 text-lg font-semibold">{t('risk.submit')}</h2>
        <p className="mb-4 text-sm text-field-700">{t('risk.privacy')}</p>
        <form onSubmit={submit} className="grid gap-3 sm:grid-cols-2" noValidate>
          <Field label={t('crops.crop')}><select className={inputCls} value={f.crop_name} onChange={set('crop_name')}>{CROPS.map((c) => <option key={c} value={c}>{t('crop.' + c)}</option>)}</select></Field>
          <Field label={t('risk.problem')}><select className={inputCls} value={f.problem} onChange={set('problem')}>{(status.data?.problem_options || ['Leaf spot']).map((p) => <option key={p}>{p}</option>)}</select></Field>
          <Field label={t('common.district')}><input className={inputCls} value={f.district} onChange={set('district')} /></Field>
          <Field label={t('common.mandal')}><input className={inputCls} value={f.area} onChange={set('area')} /></Field>
          <Field label={t('risk.date')}><input type="date" max={today} className={inputCls} value={f.report_date} onChange={set('report_date')} /></Field>
          <Field label={t('risk.photo')}><input type="file" accept="image/jpeg,image/png,image/webp" className={inputCls} onChange={(e) => setPhoto(e.target.files[0] || null)} /></Field>
          <Field label={t('risk.notes')} className="sm:col-span-2"><textarea maxLength={500} rows={3} className={inputCls} value={f.notes} onChange={set('notes')} /></Field>
          <div className="space-y-2 sm:col-span-2"><ErrorBox message={err} />{msg && <Notice tone="info">{msg}</Notice>}<Button type="submit" loading={busy}>{t('risk.send')}</Button></div>
        </form>
      </Card>
    </div>
  )
}

export default function PestAlert() {
  const { t } = useLang()
  const [tab, setTab] = useState('analyse')
  return (
    <div>
      <PageHeader title={t('mod.pest.name')} subtitle={t('mod.pest.desc')} />
      <div role="tablist" className="mb-5 inline-flex rounded-md border border-field-300 bg-white">
        {[['analyse', t('health.tab')], ['community', t('risk.tab')]].map(([k, label]) => (
          <button key={k} role="tab" aria-selected={tab === k} onClick={() => setTab(k)} className={`min-h-[44px] px-4 text-sm font-semibold ${tab === k ? 'bg-field-700 text-white' : 'text-field-700 hover:bg-field-100'}`}>{label}</button>))}
      </div>
      {tab === 'analyse' ? <Analyse /> : <Community />}
    </div>
  )
}
