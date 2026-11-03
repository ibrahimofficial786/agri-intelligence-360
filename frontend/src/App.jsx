import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import { useLang } from './i18n'
import { Spinner } from './components/ui'
import AppLayout from './layouts/AppLayout'
import Landing from './pages/Landing'
import { Login, Register } from './pages/Auth'
import Dashboard from './pages/Dashboard'
import Crops from './pages/Crops'
import PestAlert from './pages/PestAlert'
import MandiMate from './pages/MandiMate'
import Notifications from './pages/Notifications'
import SmartIntercrop from './pages/SmartIntercrop'

function Protected({ children }) {
  const { user, loading } = useAuth()
  const { t } = useLang()
  if (loading) return <Spinner label={t('common.loading')} />
  return user ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/app" element={<Protected><AppLayout /></Protected>}>
        <Route index element={<Dashboard />} />
        <Route path="crops" element={<Crops />} />
        <Route path="pest-alert" element={<PestAlert />} />
        <Route path="mandi-mate" element={<MandiMate />} />
        <Route path="smart-intercrop" element={<SmartIntercrop />} />
        <Route path="notifications" element={<Notifications />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
