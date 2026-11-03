import { Link } from 'react-router-dom'
import { Bell, Blend, Bug, MapPin, Sprout, Store, TriangleAlert } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { useLang } from '../i18n'
import { useGet } from '../hooks/useApi'
import { Badge, Button, Card, Empty, ErrorBox, Notice, PageHeader, SampleBadge, Spinner, stageName } from '../components/ui'
import { fmtDate, inr } from '../utils/validators'

export default function Dashboard() {
  const { user } = useAuth()
  const { t, lang } = useLang()
  const { data, error, loading, reload } = useGet('/api/dashboard/summary')
  if (loading) return <Spinner label={t('common.loading')} />
  if (error) return <ErrorBox message={error} onRetry={reload} />
  const d = data

  const stats = [
    [t('dash.crops'), d.crops.length, Sprout], [t('dash.upcoming'), d.upcoming_activities.length, Bell],
    [t('dash.alerts'), d.alerts.length, TriangleAlert], [t('dash.unread'), d.unread_notifications, Bell],
  ]
  return (
    <div className="space-y-5">
      <PageHeader title={t('dash.welcome', { name: user.full_name })} subtitle={undefined}>
        <span className="flex items-center gap-1 text-sm text-field-700"><MapPin className="h-4 w-4" aria-hidden />{d.user.district}{d.user.mandal ? `, ${d.user.mandal}` : ''}</span>
      </PageHeader>
      {d.has_demo_data && <Notice>{t('dash.demoNotice')}</Notice>}

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {stats.map(([label, n, Icon]) => (
          <Card key={label} className="!p-4"><Icon className="h-5 w-5 text-field-600" aria-hidden /><p className="mt-2 font-display text-3xl font-bold">{n}</p><p className="text-sm text-field-700">{label}</p></Card>
        ))}
      </div>

      <div className="grid gap-5 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <div className="mb-3 flex items-center justify-between"><h2 className="text-lg font-semibold">{t('dash.myCrops')}</h2><Link className="text-sm font-semibold text-field-700 underline" to="/app/crops">{t('dash.manage')}</Link></div>
          {d.crops.length === 0 ? (
            <Empty title={t('dash.noCrops')} text={t('dash.noCropsText')} action={<Link to="/app/crops"><Button>{t('crops.add')}</Button></Link>} />
          ) : (
            <ul className="divide-y divide-field-100">
              {d.crops.map((c) => (
                <li key={c.id} className="flex flex-wrap items-center justify-between gap-2 py-3">
                  <div><p className="font-semibold">{t('crop.' + c.crop_name)} {c.is_demo && <Badge tone="sample">{t('common.demo')}</Badge>}</p>
                    <p className="text-sm text-field-700">{c.location} · {t('crops.sown')} {fmtDate(c.sowing_date, lang)} · {t('crops.day', { n: c.days_since_sowing })}</p></div>
                  <div className="text-right text-sm">{c.current_stage ? <Badge>{stageName(c.current_stage, lang)}</Badge> : <Badge tone="info">{t('phase.' + c.phase)}</Badge>}</div>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card>
          <h2 className="mb-3 text-lg font-semibold">{t('dash.activities')}</h2>
          {d.upcoming_activities.length === 0 ? <p className="text-sm text-field-700">{t('dash.noActivities')}</p> : (
            <ul className="space-y-3 text-sm">
              {d.upcoming_activities.map((a, i) => (
                <li key={i}><p className="font-semibold">{t('crop.' + a.crop_name)}: {lang === 'te' && a.stage_te ? a.stage_te : a.stage}</p>
                  <p className="text-field-700">{a.status === 'current' ? t('dash.now') : fmtDate(a.start_date, lang)} · {a.activity}</p></li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <div className="grid gap-5 lg:grid-cols-3">
        <Card>
          <h2 className="mb-3 text-lg font-semibold">{t('dash.alertsTitle')}</h2>
          {d.alerts.length === 0 ? <p className="text-sm text-field-700">{t('dash.noAlerts')}</p> : d.alerts.map((a) => (
            <div key={a.key} className="mb-3 rounded-md bg-turmeric-100 p-3 text-sm"><p className="font-semibold">{t('crop.' + a.crop_name)}: {a.problem} ({a.district})</p>
              <p>{t('risk.reports', { n: a.report_count })} · {a.areas.join(', ')}</p>{a.has_demo_reports && <Badge tone="sample">{t('common.demo')}</Badge>}</div>
          ))}
        </Card>
        <Card>
          <h2 className="mb-3 text-lg font-semibold">{t('dash.health')}</h2>
          {d.recent_health_reports.length === 0 ? <p className="text-sm text-field-700">{t('dash.noHealth')}</p> : (
            <ul className="space-y-2 text-sm">{d.recent_health_reports.map((r) => (
              <li key={r.id} className="flex items-center justify-between gap-2"><span>{t('crop.' + r.crop_name)} · {fmtDate(r.created_at, lang)}</span>
                <span>{r.is_demo ? <Badge tone="sample">{t('common.demo')}</Badge> : <Badge tone={r.status === 'analysed' ? 'ok' : 'info'}>{t('health.status.' + r.status)}</Badge>}</span></li>))}</ul>
          )}
        </Card>
        <Card>
          <div className="mb-3 flex items-center justify-between"><h2 className="text-lg font-semibold">{t('dash.prices')}</h2><Link className="text-sm font-semibold text-field-700 underline" to="/app/mandi-mate">{t('nav.mandi')}</Link></div>
          {d.latest_prices.length === 0 ? <p className="text-sm text-field-700">{t('dash.noPrices')}</p> : (
            <ul className="space-y-2 text-sm">{d.latest_prices.map((p, i) => (
              <li key={i} className="flex items-center justify-between gap-2"><span>{t('crop.' + p.crop_name)} · {p.market}</span>
                <span className="text-right font-semibold">{inr(p.price)}/{t('unit.quintal')} {p.is_sample && <SampleBadge />}</span></li>))}</ul>
          )}
        </Card>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[['krishi', '/app/crops', Sprout], ['pest', '/app/pest-alert', Bug], ['mandi', '/app/mandi-mate', Store], ['intercrop', '/app/smart-intercrop', Blend]].map(([k, to, Icon]) => (
          <Link key={k} to={to} className="flex items-center gap-3 rounded-lg bg-field-800 p-4 text-white hover:bg-field-700"><Icon className="h-6 w-6 text-turmeric-400" aria-hidden /><div><p className="font-semibold">{t(`mod.${k}.name`)}</p><p className="text-xs text-field-200">{t(`mod.${k}.role`)}</p></div></Link>
        ))}
      </div>
    </div>
  )
}
