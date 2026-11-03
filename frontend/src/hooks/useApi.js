import { useCallback, useEffect, useState } from 'react'
import { api } from '../services/api'

/** GET helper with loading/error state. `params` should be stable or memoised. */
export function useGet(path, params, enabled = true) {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(enabled)
  const key = JSON.stringify(params || {})
  const load = useCallback(() => {
    if (!enabled || !path) return
    setLoading(true); setError('')
    api.get(path, params).then(setData).catch((e) => setError(e.message)).finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, key, enabled])
  useEffect(load, [load])
  return { data, error, loading, reload: load, setData }
}
