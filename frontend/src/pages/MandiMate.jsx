import { useEffect, useState } from 'react'
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Plus, Trash2 } from 'lucide-react'
import { useLang } from '../i18n'
import { useGet } from '../hooks/useApi'
import { api } from '../services/api'
import { Badge, Button, Card, Empty, ErrorBox, Field, inputCls, Notice, PageHeader, SampleBadge, Spinner } from '../components/ui'
import { fmtDate, inr, validateNonNegative, validatePositive } from '../utils/validators'

const CROPS = ['Groundnut', 'Cotton', 'Paddy', 'Red gram']
const COLORS = ['#1f5130', '#e8b32f', '#4d8a47', '#4a3a2c', '#b5810d']
const UNITS = ['quintal', 'kg', 'tonne']

function Results({ options, disclaimer }) {
  const { t, lang } = useLang()
  const best = options[0]
  return (
    <div className="space-y-3">
      {options.length > 1 && <Notice tone="info">{t('mandi.best', { market: best.market, net: inr(best.net_return) })}{options[1] && ` ${t('mandi.ahead', { diff: inr(best.net_return - options[1].net_return), market: options[1].market })}`}</Notice>}
      <ol className="space-y-3">
        {options.map((o) => (
          <li key={o.market}><Card className={o.rank === 1 ? 'border-field-700' : ''}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-lg font-semibold">#{o.rank} {o.market} {o.is_sample && <SampleBadge />}</h3>
              <p className="font-display text-2xl font-bold">{inr(o.net_return)}</p>
            </div>
            <dl className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-sm sm:grid-cols-4">
              <div><dt className="text-field-700">{t('mandi.price')}</dt><dd>{inr(o.price_per_quintal)}/{t('unit.quintal')}</dd></div>
              <div><dt className="text-field-700">{t('mandi.gross')}</dt><dd>{inr(o.gross_value)}</dd></div>
              <div><dt className="text-field-700">{t('mandi.transport')}</dt><dd>− {inr(o.transport_cost)}</dd></div>
              <div><dt className="text-field-700">{t('mandi.other')}</dt><dd>− {inr(o.other_expenses)}</dd></div>
            </dl>
            <p className="mt-2 rounded bg-field-50 p-2 font-mono text-xs">{o.formula}</p>
            {o.price_date && <p className="mt-1 text-xs text-field-700">{t('mandi.priceDate')}: {fmtDate(o.price_date, lang)} · {t('mandi.source')}: {o.source}</p>}
            {o.rank > 1 && <p className="mt-1 text-xs text-field-700">{t('mandi.diff')}: {inr(o.difference_vs_best)}</p>}
          </Card></li>))}
      </ol>
      <p className="text-xs text-field-700">{disclaimer}</p>
    </div>
  )
}

function Compare() {
  const { t, lang } = useLang()
  const [crop, setCrop] = useState('Groundnut')
  const prices = useGet('/api/markets/prices', { crop })
  const [f, setF] = useState({ quantity: '10', unit: 'quintal', other: '0', transport: '0' })
  const [perMarket, setPerMarket] = useState({})
  const [errs, setErrs] = useState({})
  const [res, setRes] = useState(null)
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  useEffect(() => { setRes(null) }, [crop])
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })

  const run = async (e) => {
    e.preventDefault()
    const v = { quantity: validatePositive(f.quantity), other: validateNonNegative(f.other), transport: validateNonNegative(f.transport) }
    setErrs(v)
    if (Object.values(v).some(Boolean)) return
    setBusy(true); setErr('')
    const tc = Object.fromEntries(Object.entries(perMarket).filter(([, x]) => x !== '' && Number(x) >= 0).map(([k, x]) => [k, Number(x)]))
    try { setRes(await api.post('/api/markets/compare', { crop, quantity: Number(f.quantity), quantity_unit: f.unit, other_expenses: Number(f.other || 0), default_transport_cost: Number(f.transport || 0), transport_costs: tc })) } catch (x) { setErr(x.message) } finally { setBusy(false) }
  }
  const markets = prices.data ? [...new Set(prices.data.latest.map((p) => p.market))] : []
  return (
    <div className="space-y-5">
      <Card>
        <form onSubmit={run} noValidate className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Field label={t('crops.crop')}><select className={inputCls} value={crop} onChange={(e) => setCrop(e.target.value)}>{CROPS.map((c) => <option key={c} value={c}>{t('crop.' + c)}</option>)}</select></Field>
          <Field label={t('mandi.quantity')} error={errs.quantity}><input inputMode="decimal" className={inputCls} value={f.quantity} onChange={set('quantity')} /></Field>
          <Field label={t('mandi.unit')}><select className={inputCls} value={f.unit} onChange={set('unit')}>{UNITS.map((u) => <option key={u} value={u}>{t('unit.' + u)}</option>)}</select></Field>
          <Field label={t('mandi.otherExp')} error={errs.other}><input inputMode="decimal" className={inputCls} value={f.other} onChange={set('other')} /></Field>
          <Field label={t('mandi.defaultTransport')} error={errs.transport} hint={t('mandi.transportHint')}><input inputMode="decimal" className={inputCls} value={f.transport} onChange={set('transport')} /></Field>
          {markets.map((m) => (
            <Field key={m} label={`${t('mandi.transport')}: ${m}`}><input inputMode="decimal" placeholder={f.transport} className={inputCls} value={perMarket[m] ?? ''} onChange={(e) => setPerMarket({ ...perMarket, [m]: e.target.value })} /></Field>))}
          <div className="flex items-end sm:col-span-2 lg:col-span-4"><Button type="submit" loading={busy}>{t('mandi.compare')}</Button></div>
        </form>
        <div className="mt-3"><ErrorBox message={err} /></div>
      </Card>
      {res && <Results options={res.options} disclaimer={res.disclaimer} />}

      <Card>
        <h2 className="mb-1 text-lg font-semibold">{t('mandi.latest')}</h2>
        {prices.loading ? <Spinner label={t('common.loading')} /> : prices.error ? <ErrorBox message={prices.error} onRetry={prices.reload} /> : (
          <>
            {prices.data.is_sample_data && <div className="mb-3"><Notice>{t('mandi.sampleNotice')}</Notice></div>}
            <div className="overflow-x-auto"><table className="w-full min-w-[520px] text-left text-sm">
              <thead className="text-field-700"><tr><th className="py-2">{t('mandi.market')}</th><th>{t('mandi.price')}</th><th>{t('mandi.priceDate')}</th><th>{t('mandi.source')}</th></tr></thead>
              <tbody>{prices.data.latest.map((p) => <tr key={p.market} className="border-t border-field-100"><td className="py-2 font-medium">{p.market}</td><td>{inr(p.price)}/{t('unit.' + p.unit)}</td><td>{fmtDate(p.price_date, lang)}</td><td className="text-xs">{p.is_sample ? <Badge tone="sample">{t('common.sample')}</Badge> : null} {p.source}</td></tr>)}</tbody>
            </table></div>
            <h3 className="mb-2 mt-5 font-semibold">{t('mandi.history')}</h3>
            {prices.data.history.length < 3 ? <Empty title={t('mandi.noHistory')} /> : (
              <div className="h-64 w-full"><ResponsiveContainer><LineChart data={prices.data.history} margin={{ left: 0, right: 8, top: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2ebde" /><XAxis dataKey="date" tickFormatter={(d) => d.slice(5)} fontSize={11} /><YAxis fontSize={11} domain={['auto', 'auto']} width={48} /><Tooltip formatter={(v) => inr(v)} /><Legend />
                {markets.map((m, i) => <Line key={m} type="monotone" dataKey={m} stroke={COLORS[i % COLORS.length]} dot={false} strokeWidth={2} connectNulls />)}
              </LineChart></ResponsiveContainer></div>)}
          </>)}
      </Card>
    </div>
  )
}

function Calculator() {
  const { t } = useLang()
  const blank = { market: '', price: '', price_unit: 'quintal', transport_cost: '0' }
  const [qty, setQty] = useState({ quantity: '', unit: 'quintal', other: '0' })
  const [opts, setOpts] = useState([{ ...blank }, { ...blank }])
  const [res, setRes] = useState(null)
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const example = () => { setQty({ quantity: '10', unit: 'quintal', other: '0' }); setOpts([{ market: 'Market A', price: '6000', price_unit: 'quintal', transport_cost: '1000' }, { market: 'Market B', price: '6300', price_unit: 'quintal', transport_cost: '2500' }]) }
  const upd = (i, k, v) => setOpts(opts.map((o, j) => (j === i ? { ...o, [k]: v } : o)))

  const run = async (e) => {
    e.preventDefault(); setErr('')
    if (validatePositive(qty.quantity) || validateNonNegative(qty.other)) { setErr(t('err.positive')); return }
    if (opts.some((o) => !o.market.trim() || validatePositive(o.price) || validateNonNegative(o.transport_cost))) { setErr(t('mandi.checkRows')); return }
    setBusy(true)
    try { setRes(await api.post('/api/markets/calculate', { quantity: Number(qty.quantity), quantity_unit: qty.unit, other_expenses: Number(qty.other || 0), options: opts.map((o) => ({ market: o.market.trim(), price: Number(o.price), price_unit: o.price_unit, transport_cost: Number(o.transport_cost || 0) })) })) } catch (x) { setErr(x.message) } finally { setBusy(false) }
  }
  return (
    <div className="space-y-5">
      <Card>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2"><p className="text-sm text-field-700">{t('mandi.calcIntro')}</p><Button variant="secondary" onClick={example}>{t('mandi.loadExample')}</Button></div>
        <form onSubmit={run} noValidate className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <Field label={t('mandi.quantity')}><input inputMode="decimal" className={inputCls} value={qty.quantity} onChange={(e) => setQty({ ...qty, quantity: e.target.value })} /></Field>
            <Field label={t('mandi.unit')}><select className={inputCls} value={qty.unit} onChange={(e) => setQty({ ...qty, unit: e.target.value })}>{UNITS.map((u) => <option key={u} value={u}>{t('unit.' + u)}</option>)}</select></Field>
            <Field label={t('mandi.otherExp')}><input inputMode="decimal" className={inputCls} value={qty.other} onChange={(e) => setQty({ ...qty, other: e.target.value })} /></Field>
          </div>
          {opts.map((o, i) => (
            <div key={i} className="grid items-end gap-3 rounded-md bg-field-50 p-3 sm:grid-cols-[1.3fr_1fr_1fr_1fr_auto]">
              <Field label={t('mandi.market')}><input className={inputCls} value={o.market} onChange={(e) => upd(i, 'market', e.target.value)} /></Field>
              <Field label={t('mandi.price')}><input inputMode="decimal" className={inputCls} value={o.price} onChange={(e) => upd(i, 'price', e.target.value)} /></Field>
              <Field label={t('mandi.priceUnit')}><select className={inputCls} value={o.price_unit} onChange={(e) => upd(i, 'price_unit', e.target.value)}>{UNITS.map((u) => <option key={u} value={u}>{t('unit.' + u)}</option>)}</select></Field>
              <Field label={t('mandi.transport')}><input inputMode="decimal" className={inputCls} value={o.transport_cost} onChange={(e) => upd(i, 'transport_cost', e.target.value)} /></Field>
              <Button type="button" variant="ghost" disabled={opts.length < 2} onClick={() => setOpts(opts.filter((_, j) => j !== i))} aria-label={t('common.delete')}><Trash2 className="h-4 w-4" /></Button>
            </div>))}
          <div className="flex flex-wrap gap-2"><Button type="button" variant="secondary" onClick={() => setOpts([...opts, { ...blank }])} disabled={opts.length >= 8}><Plus className="h-4 w-4" aria-hidden />{t('mandi.addMarket')}</Button><Button type="submit" loading={busy}>{t('mandi.calculate')}</Button></div>
          <ErrorBox message={err} />
        </form>
      </Card>
      {res && <><Notice>{t('mandi.exampleNote')}</Notice><Results options={res.options} disclaimer={res.disclaimer} /></>}
    </div>
  )
}

export default function MandiMate() {
  const { t } = useLang()
  const [tab, setTab] = useState('compare')
  return (
    <div>
      <PageHeader title={t('mod.mandi.name')} subtitle={t('mod.mandi.desc')} />
      <div role="tablist" className="mb-5 inline-flex rounded-md border border-field-300 bg-white">
        {[['compare', t('mandi.tabCompare')], ['calc', t('mandi.tabCalc')]].map(([k, label]) => (
          <button key={k} role="tab" aria-selected={tab === k} onClick={() => setTab(k)} className={`min-h-[44px] px-4 text-sm font-semibold ${tab === k ? 'bg-field-700 text-white' : 'text-field-700 hover:bg-field-100'}`}>{label}</button>))}
      </div>
      {tab === 'compare' ? <Compare /> : <Calculator />}
    </div>
  )
}
