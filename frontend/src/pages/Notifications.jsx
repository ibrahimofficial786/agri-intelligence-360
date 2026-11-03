import { Bell, Bug, Sprout, Store, TriangleAlert } from 'lucide-react'
import { useLang } from '../i18n'
import { useGet } from '../hooks/useApi'
import { api } from '../services/api'
import { Button, Card, Empty, ErrorBox, Notice, PageHeader, Spinner } from '../components/ui'
import { fmtDate } from '../utils/validators'

const icons = { crop_activity: Sprout, crop_health: Bug, community_risk: TriangleAlert, market: Store }

export default function Notifications() {
  const { t, lang } = useLang()
  const { data, loading, error, reload, setData } = useGet('/api/notifications', { limit: 50 })
  const read = async (n) => {
    try { await api.put(`/api/notifications/${n.id}/read`); setData(data.map((x) => (x.id === n.id ? { ...x, is_read: true } : x))) } catch { reload() }
  }
  if (loading) return <Spinner label={t('common.loading')} />
  return (
    <div>
      <PageHeader title={t('nav.notifications')} subtitle={t('notif.sub')} />
      <ErrorBox message={error} onRetry={reload} />
      {data && data.length === 0 && <Empty title={t('notif.empty')} text={t('notif.emptyText')} />}
      <ul className="space-y-3">
        {(data || []).map((n) => { const Icon = icons[n.kind] || Bell; return (
          <li key={n.id}><Card className={`flex items-start gap-3 ${n.is_read ? 'opacity-70' : 'border-field-600'}`}>
            <Icon className="mt-1 h-5 w-5 shrink-0 text-field-600" aria-hidden />
            <div className="flex-1"><p className="font-semibold">{n.title}</p><p className="text-sm text-field-700">{n.body}</p><p className="mt-1 text-xs text-field-700/70">{fmtDate(n.created_at, lang)}</p></div>
            {!n.is_read && <Button variant="ghost" onClick={() => read(n)}>{t('notif.markRead')}</Button>}
          </Card></li>) })}
      </ul>
      <div className="mt-5"><Notice tone="info">{t('notif.inAppOnly')}</Notice></div>
    </div>
  )
}
