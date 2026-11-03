import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { api, expect, hasToken, setToken, setUnauthorizedHandler } from '../services/api'
import { useLang } from '../i18n'

const Ctx = createContext(null)
export const useAuth = () => useContext(Ctx)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(hasToken())
  const { setLang } = useLang()

  const logout = useCallback(() => { setToken(null); setUser(null) }, [])

  useEffect(() => {
    setUnauthorizedHandler(logout)
    if (!hasToken()) return
    api.get('/api/auth/me').then((u) => { setUser(u); setLang(u.language, false) }).catch(logout).finally(() => setLoading(false))
  }, [logout, setLang])

  const accept = (res) => {
    expect(res, { access_token: 'string' })
    setToken(res.access_token)
    setUser(res.user)
    setLang(res.user.language, false)
    return res.user
  }
  const login = async (email, password) => accept(await api.post('/api/auth/login', { email, password }))
  const register = async (data) => accept(await api.post('/api/auth/register', data))
  const updateProfile = async (data) => setUser(await api.put('/api/auth/me', data))

  return <Ctx.Provider value={{ user, loading, login, register, logout, updateProfile }}>{children}</Ctx.Provider>
}
