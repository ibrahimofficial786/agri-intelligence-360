import { useAuth } from '../hooks/useAuth'
import { useLang } from '../i18n'

export default function LangSwitch({ dark = false }) {
  const { lang, setLang } = useLang()
  const { user, updateProfile } = useAuth()
  const choose = (l) => {
    setLang(l)
    if (user) updateProfile({ language: l }).catch(() => {})
  }
  const base = 'min-h-[36px] px-3 text-sm font-semibold'
  return (
    <div role="group" aria-label="Language" className={`inline-flex overflow-hidden rounded-md border ${dark ? 'border-field-700' : 'border-field-300'}`}>
      {[['en', 'English'], ['te', 'తెలుగు']].map(([code, label]) => (
        <button key={code} onClick={() => choose(code)} aria-pressed={lang === code}
          className={`${base} ${lang === code ? 'bg-turmeric-400 text-field-900' : dark ? 'text-field-100 hover:bg-field-800' : 'text-field-700 hover:bg-field-100'}`}>{label}</button>
      ))}
    </div>
  )
}
