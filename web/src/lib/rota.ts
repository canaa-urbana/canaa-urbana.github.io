// Rota por hash (#/aba?chave=valor): funciona em GitHub Pages sem reescrita de URL.
import { useCallback, useEffect, useState } from 'react'

export interface Rota {
  aba: string
  params: URLSearchParams
}

function ler(): Rota {
  const h = window.location.hash.replace(/^#\/?/, '')
  const [aba, q] = h.split('?')
  return { aba: aba || 'inicio', params: new URLSearchParams(q ?? '') }
}

export function useRota(): [Rota, (aba: string, params?: Record<string, string | number | null>) => void] {
  const [rota, setRota] = useState<Rota>(ler)
  useEffect(() => {
    const f = () => setRota(ler())
    window.addEventListener('hashchange', f)
    return () => window.removeEventListener('hashchange', f)
  }, [])
  const ir = useCallback((aba: string, params?: Record<string, string | number | null>) => {
    const q = new URLSearchParams()
    for (const [k, v] of Object.entries(params ?? {})) if (v !== null && v !== undefined) q.set(k, String(v))
    const s = q.toString()
    window.location.hash = `/${aba}${s ? '?' + s : ''}`
  }, [])
  return [rota, ir]
}

/** Atualiza um parâmetro da rota atual sem criar entrada de histórico (ex.: ano do slider). */
export function trocarParam(chave: string, valor: string | number | null) {
  const h = window.location.hash.replace(/^#\/?/, '')
  const [aba, q] = h.split('?')
  const p = new URLSearchParams(q ?? '')
  if (valor === null) p.delete(chave)
  else p.set(chave, String(valor))
  const s = p.toString()
  history.replaceState(null, '', `#/${aba || 'inicio'}${s ? '?' + s : ''}`)
  window.dispatchEvent(new HashChangeEvent('hashchange'))
}
