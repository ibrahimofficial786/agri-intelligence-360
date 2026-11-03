import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Bell, Bug, LayoutDashboard, LogOut, Sprout, Store, Wheat, Blend } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { useLang } from '../i18n'
import { api } from '../services/api'
import LangSwitch from '../components/LangSwitch'

const links = [
  { to: '/app', end: true, icon: LayoutDashboard, key: 'nav.dashboard' },
  { to: '/app/crops', icon: Sprout, key: 'nav.krishi' },
  { to: '/app/pest-alert', icon: Bug, key: 'nav.pest' },
  { to: '/app/mandi-mate', icon: Store, key: 'nav.mandi' },
  { to: '/app/smart-intercrop', icon: Blend, key: 'nav.intercrop' },
  { to: '/app/notifications', icon: Bell, key: 'nav.notifications' },
]

export default function AppLayout() {
  const { user, logout } = useAuth()
  const { t } = useLang()
  const nav = useNavigate()
  const loc = useLocation()
  const [unread, setUnread] = useState(0)

  useEffect(() => {
    api.get('/api/notifications', { limit: 50 }).then((n) => setUnread(n.filter((x) => !x.is_read).length)).catch(() => {})
  }, [loc.pathname])

  const item = (l, mobile) => (
    <NavLink key={l.to} to={l.to} end={l.end}
      className={({ isActive }) => mobile
        ? `flex flex-1 flex-col items-center gap-0.5 py-2 text-[11px] font-medium ${isActive ? 'text-field-700' : 'text-field-700/60'}`
        : `flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium ${isActive ? 'bg-turmeric-400 text-field-900' : 'text-field-100 hover:bg-field-800'}`}>
      <span className="relative"><l.icon className="h-5 w-5" aria-hidden />
        {l.key === 'nav.notifications' && unread > 0 && <span className="absolute -right-2 -top-2 rounded-full bg-red-600 px-1 text-[10px] text-white">{unread}</span>}
      </span>
      <span>{t(mobile ? l.key + '.short' : l.key)}</span>
    </NavLink>
  )

  return (
    <div className="min-h-screen lg:pl-64">
      <aside className="fixed inset-y-0 left-0 hidden w-64 flex-col bg-field-900 p-4 lg:flex">
        <NavLink to="/" className="mb-6 flex items-center gap-2 px-2 font-display text-lg font-bold text-white"><Wheat className="h-6 w-6 text-turmeric-400" aria-hidden />AGRI INTELLIGENCE 360</NavLink>
        <nav className="flex flex-col gap-1" aria-label="Main">{links.map((l) => item(l, false))}</nav>
        <div className="mt-auto space-y-3 border-t border-field-800 pt-4 text-sm text-field-100">
          <LangSwitch dark />
          <div className="truncate px-1">{user?.full_name}<div className="truncate text-xs text-field-300">{user?.district}</div></div>
          <button onClick={() => { logout(); nav('/') }} className="flex w-full items-center gap-2 rounded-md px-2 py-2 hover:bg-field-800"><LogOut className="h-4 w-4" aria-hidden />{t('nav.logout')}</button>
        </div>
      </aside>
      <header className="sticky top-0 z-20 flex items-center justify-between border-b border-field-200 bg-white px-4 py-2 lg:hidden">
        <span className="flex items-center gap-2 font-display font-bold text-field-800"><Wheat className="h-5 w-5 text-turmeric-600" aria-hidden />AGRI 360</span>
        <div className="flex items-center gap-2"><LangSwitch />
          <button onClick={() => { logout(); nav('/') }} aria-label={t('nav.logout')} className="rounded-md p-2 text-field-700 hover:bg-field-100"><LogOut className="h-5 w-5" /></button></div>
      </header>
      <main className="mx-auto max-w-6xl px-4 pb-24 pt-5 sm:px-6 lg:pb-10"><Outlet /></main>
      <nav className="fixed inset-x-0 bottom-0 z-20 flex border-t border-field-200 bg-white lg:hidden" aria-label="Main mobile">{links.map((l) => item(l, true))}</nav>
    </div>
  )
}
