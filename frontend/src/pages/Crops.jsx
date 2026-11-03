import { useEffect, useState } from 'react'
import { Droplets, FlaskConical, Pencil, Plus, Search, Trash2 } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { useLang } from '../i18n'
import { useGet } from '../hooks/useApi'
import { api } from '../services/api'
import { Badge, Button, Card, Empty, ErrorBox, Field, inputCls, Notice, PageHeader, Spinner, StageRibbon, stageName } from '../components/ui'
import { fmtDate } from '../utils/validators'

const SOILS = ['Red soil', 'Black soil', 'Sandy loam', 'Clay loam', 'Alluvial']
const IRRIG = ['Rainfed', 'Drip', 'Sprinkler', 'Canal', 'Borewell']

function CropForm({ initial, catalog, onSaved, onCancel }) {
  const { user } = useAuth()
  const { t } = useLang()
  const [f, setF] = useState(initial || { crop_name: catalog[0] || '', variety: '', sowing_date: '', location: user.district, land_area_acres: '', soil_type: '', irrigation_method: '' })
  const [errs, setErrs] = useState({})
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    const v = {
      sowing_date: f.sowing_date ? null : 'err.required', location: f.location.trim().length >= 2 ? null : 'err.required',
      land_area_acres: f.land_area_acres === '' || Number(f.land_area_acres) > 0 ? null : 'err.positive',
    }
    setErrs(v)
    if (Object.values(v).some(Boolean)) return
    setBusy(true); setError('')
    const body = { ...f, variety: f.variety || null, soil_type: f.soil_type || null, irrigation_method: f.irrigation_method || null,
      land_area_acres: f.land_area_acres === '' ? null : Number(f.land_area_acres) }
    try { onSaved(initial?.id ? await api.put(`/api/crops/${initial.id}`, body) : await api.post('/api/crops', body)) } catch (err) { setError(err.message) } finally { setBusy(false) }
  }
  return (
    <Card>
      <h2 className="mb-4 text-lg font-semibold">{initial?.id ? t('crops.edit') : t('crops.add')}</h2>
      <form onSubmit={submit} noValidate className="grid gap-4 sm:grid-cols-2">
        <Field label={t('crops.crop')}><select className={inputCls} value={f.crop_name} onChange={set('crop_name')}>{catalog.map((c) => <option key={c} value={c}>{t('crop.' + c)}</option>)}</select></Field>
        <Field label={t('crops.variety')}><input className={inputCls} value={f.variety || ''} onChange={set('variety')} /></Field>
        <Field label={t('crops.sowingDate')} error={errs.sowing_date}><input type="date" className={inputCls} value={f.sowing_date} onChange={set('sowing_date')} /></Field>
        <Field label={t('common.location')} error={errs.location}><input className={inputCls} value={f.location} onChange={set('location')} /></Field>
        <Field label={t('crops.area')} error={errs.land_area_acres}><input type="number" step="0.1" min="0" className={inputCls} value={f.land_area_acres ?? ''} onChange={set('land_area_acres')} /></Field>
        <Field label={t('crops.soil')}><select className={inputCls} value={f.soil_type || ''} onChange={set('soil_type')}><option value="">{t('common.unknown')}</option>{SOILS.map((s) => <option key={s}>{s}</option>)}</select></Field>
        <Field label={t('crops.irrigation')}><select className={inputCls} value={f.irrigation_method || ''} onChange={set('irrigation_method')}><option value="">{t('common.unknown')}</option>{IRRIG.map((s) => <option key={s}>{s}</option>)}</select></Field>
        <div className="sm:col-span-2"><ErrorBox message={error} /></div>
        <div className="flex gap-2 sm:col-span-2"><Button type="submit" loading={busy}>{t('common.save')}</Button><Button type="button" variant="secondary" onClick={onCancel}>{t('common.cancel')}</Button></div>
      </form>
    </Card>
  )
}

function Guidance({ crop, onEdit, onDelete }) {
  const { t, lang } = useLang()
  const { data: g, loading, error, reload } = useGet(`/api/guidance/${crop.id}`)
  if (loading) return <Spinner label={t('common.loading')} />
  if (error) return <ErrorBox message={error} onRetry={reload} />
  const cur = g.current_stage
  return (
    <div className="space-y-4">
      <Card>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold">{t('crop.' + crop.crop_name)}{crop.variety ? ` · ${crop.variety}` : ''} {crop.is_demo && <Badge tone="sample">{t('common.demo')}</Badge>}</h2>
            <p className="text-sm text-field-700">{crop.location} · {t('crops.sown')} {fmtDate(crop.sowing_date, lang)} · {t('crops.day', { n: g.days_since_sowing })}{crop.land_area_acres ? ` · ${crop.land_area_acres} ${t('crops.acres')}` : ''}</p>
          </div>
          <div className="flex gap-2"><Button variant="secondary" onClick={onEdit}><Pencil className="h-4 w-4" aria-hidden />{t('common.edit')}</Button>
            <Button variant="danger" onClick={onDelete}><Trash2 className="h-4 w-4" aria-hidden />{t('common.delete')}</Button></div>
        </div>
        <div className="mt-4"><StageRibbon calendar={g.calendar} lang={lang} /></div>
        <p className="mt-2 text-xs text-field-700">{t('crops.ribbonLegend')}</p>
      </Card>

      <Card className="border-turmeric-400">
        <p className="text-sm text-field-700">{t('crops.currentStage')}</p>
        <h3 className="text-2xl font-bold">{cur ? stageName(cur, lang) : t('phase.' + g.phase)}</h3>
        {cur && <p className="text-sm text-field-700">{fmtDate(cur.start_date, lang)} – {fmtDate(cur.end_date, lang)} ({t('crops.estimated')})</p>}
        {cur && (
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <div><h4 className="mb-1 font-semibold">{t('crops.activities')}</h4><ul className="list-disc space-y-1 pl-5 text-sm">{cur.activities.map((a) => <li key={a}>{a}</li>)}</ul></div>
            <div className="space-y-3 text-sm">
              <p className="flex gap-2"><Droplets className="mt-0.5 h-4 w-4 shrink-0 text-field-600" aria-hidden /><span><strong>{t('crops.irrigationGuide')}:</strong> {cur.irrigation}</span></p>
              <p className="flex gap-2"><FlaskConical className="mt-0.5 h-4 w-4 shrink-0 text-field-600" aria-hidden /><span><strong>{t('crops.nutrients')}:</strong> {cur.nutrients}</span></p>
              <p className="flex gap-2"><Search className="mt-0.5 h-4 w-4 shrink-0 text-field-600" aria-hidden /><span><strong>{t('crops.monitoring')}:</strong> {cur.monitoring}</span></p>
            </div>
          </div>
        )}
        {g.reminders.length > 0 && <div className="mt-4 rounded-md bg-field-100 p-3 text-sm"><p className="font-semibold">{t('crops.reminders')}</p><ul className="mt-1 list-disc pl-5">{g.reminders.map((r) => <li key={r}>{r}</li>)}</ul></div>}
      </Card>

      <Card>
        <h3 className="mb-3 text-lg font-semibold">{t('crops.calendar')}</h3>
        <div className="overflow-x-auto"><table className="w-full min-w-[480px] text-left text-sm">
          <thead className="text-field-700"><tr><th className="py-2 pr-3">{t('crops.stage')}</th><th className="pr-3">{t('crops.from')}</th><th className="pr-3">{t('crops.to')}</th><th>{t('crops.status')}</th></tr></thead>
          <tbody>{g.calendar.map((s) => (
            <tr key={s.key} className={`border-t border-field-100 ${s.status === 'current' ? 'bg-turmeric-100/60 font-semibold' : ''}`}>
              <td className="py-2 pr-3">{stageName(s, lang)}</td><td className="pr-3">{fmtDate(s.start_date, lang)}</td><td className="pr-3">{fmtDate(s.end_date, lang)}</td><td>{t('stage.' + s.status)}</td></tr>))}</tbody>
        </table></div>
      </Card>
      <Notice tone="info">{t('crops.disclaimer')}</Notice>
    </div>
  )
}

export default function Crops() {
  const { t } = useLang()
  const list = useGet('/api/crops')
  const cat = useGet('/api/crops/catalog')
  const [sel, setSel] = useState(null)
  const [mode, setMode] = useState(null) // 'add' | 'edit'
  const [delErr, setDelErr] = useState('')
  const crops = list.data || []
  useEffect(() => { if (crops.length && !crops.find((c) => c.id === sel)) setSel(crops[0].id) }, [crops, sel])
  const current = crops.find((c) => c.id === sel)

  if (list.loading || cat.loading) return <Spinner label={t('common.loading')} />
  if (list.error || cat.error) return <ErrorBox message={list.error || cat.error} onRetry={() => { list.reload(); cat.reload() }} />

  const saved = (c) => { setMode(null); setSel(c.id); list.reload() }
  const remove = async () => {
    if (!window.confirm(t('crops.confirmDelete'))) return
    try { await api.del(`/api/crops/${current.id}`); setSel(null); list.reload() } catch (e) { setDelErr(e.message) }
  }
  return (
    <div>
      <PageHeader title={t('mod.krishi.name')} subtitle={t('mod.krishi.desc')}>
        <Button onClick={() => setMode('add')}><Plus className="h-4 w-4" aria-hidden />{t('crops.add')}</Button>
      </PageHeader>
      {mode && <div className="mb-5"><CropForm initial={mode === 'edit' ? { ...current, variety: current.variety || '' } : null} catalog={cat.data.crops} onSaved={saved} onCancel={() => setMode(null)} /></div>}
      {crops.length === 0 && !mode ? (
        <Empty title={t('crops.empty')} text={t('crops.emptyText')} action={<Button onClick={() => setMode('add')}>{t('crops.add')}</Button>} />
      ) : (
        <div className="grid gap-5 lg:grid-cols-[250px_1fr]">
          <ul className="flex gap-2 overflow-x-auto lg:flex-col" aria-label={t('dash.myCrops')}>
            {crops.map((c) => (
              <li key={c.id} className="shrink-0 lg:shrink">
                <button onClick={() => { setSel(c.id); setMode(null) }} aria-current={c.id === sel}
                  className={`w-full rounded-lg border p-3 text-left ${c.id === sel ? 'border-field-700 bg-white' : 'border-field-200 bg-field-50 hover:bg-white'}`}>
                  <p className="font-semibold">{t('crop.' + c.crop_name)}</p>
                  <p className="text-xs text-field-700">{c.location} · {t('crops.day', { n: c.summary.days_since_sowing })}</p>
                </button>
              </li>
            ))}
          </ul>
          <div>{delErr && <ErrorBox message={delErr} />}{current && <Guidance key={current.id + current.updated_at} crop={current} onEdit={() => setMode('edit')} onDelete={remove} />}</div>
        </div>
      )}
    </div>
  )
}
