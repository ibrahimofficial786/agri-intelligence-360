import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { en, te } from './translations'

const dict = { en, te }
const Ctx = createContext(null)
export const useLang = () => useContext(Ctx)

export function translate(lang, key, vars) {
  let s = dict[lang]?.[key] ?? en[key] ?? key
  if (vars) Object.entries(vars).forEach(([k, v]) => { s = s.replaceAll(`{${k}}`, v) })
  return s
}

export function LanguageProvider({ children }) {
  const [lang, setLangState] = useState(() => localStorage.getItem('agri_lang') || 'en')
  const setLang = useCallback((l, persist = true) => {
    if (!dict[l]) return
    setLangState(l)
    localStorage.setItem('agri_lang', l)
  }, [])
  useEffect(() => { document.documentElement.lang = lang }, [lang])
  const t = useCallback((key, vars) => translate(lang, key, vars), [lang])
  const value = useMemo(() => ({ lang, setLang, t }), [lang, setLang, t])
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}
