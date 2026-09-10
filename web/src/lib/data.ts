// Carregamento dos JSON estáticos de public/data (só agregados aprovados pelo gate).
import { useEffect, useState } from 'react'

const BASE = import.meta.env.BASE_URL

/** URL absoluta de um arquivo em public/ (ex.: asset('data/painel/rotulos.json')). */
export function asset(caminho: string): string {
  return BASE + caminho.replace(/^\//, '')
}

/** URL de um arquivo em public/data. */
export function dataUrl(caminho: string): string {
  return asset('data/' + caminho.replace(/^\//, ''))
}

const cache = new Map<string, Promise<unknown>>()

/** Busca um JSON de public/data com cache por caminho (uma requisição por sessão). */
export function loadJSON<T>(caminho: string): Promise<T> {
  let p = cache.get(caminho)
  if (!p) {
    p = fetch(dataUrl(caminho)).then((r) => {
      if (!r.ok) throw new Error(`${caminho}: HTTP ${r.status}`)
      return r.json()
    })
    p.catch(() => cache.delete(caminho))
    cache.set(caminho, p)
  }
  return p as Promise<T>
}

export interface Carga<T> {
  data: T | undefined
  error: Error | undefined
  loading: boolean
}

/** Hook: carrega um JSON (null = não carregar ainda). */
export function useJSON<T>(caminho: string | null): Carga<T> {
  const [estado, setEstado] = useState<Carga<T>>({ data: undefined, error: undefined, loading: !!caminho })
  useEffect(() => {
    if (!caminho) return
    let vivo = true
    setEstado((e) => ({ ...e, loading: true, error: undefined }))
    loadJSON<T>(caminho)
      .then((data) => vivo && setEstado({ data, error: undefined, loading: false }))
      .catch((error: Error) => vivo && setEstado({ data: undefined, error, loading: false }))
    return () => {
      vivo = false
    }
  }, [caminho])
  return estado
}

/** Tabela analítica da E5: data/painel/analise/<nome>.json (lista de registros). */
export function useAnalise<T = Record<string, unknown>>(nome: string): Carga<T[]> {
  return useJSON<T[]>(`painel/analise/${nome}.json`)
}

// ---------------------------------------------------------------------------
// Estimativas da E2 (tabela longa em colunas com dicionário)
// ---------------------------------------------------------------------------

export type Classe = 'boa' | 'cautela' | 'baixa'

export interface Estimativa {
  censo: number
  geografia: string
  universo: string
  estatistica: 'contagem' | 'proporcao' | 'media' | 'mediana'
  variavel: string | null
  dim1: string | null
  cat1: string | null
  dim2: string | null
  cat2: string | null
  valor: number | null
  ep: number | null
  cv: number | null
  classe: Classe
  n_faixa: string | null
  n_dom_faixa: string | null
}

interface EstimativasBrutas {
  fonte: string
  n: number
  dic: Record<string, string[]>
  col: Record<string, (number | null)[]>
}

let estimativasCache: Promise<Estimativa[]> | null = null

export function loadEstimativas(): Promise<Estimativa[]> {
  if (!estimativasCache) {
    estimativasCache = loadJSON<EstimativasBrutas>('painel/estimativas.json').then((b) => {
      const dec = (c: string, i: number): string | null => {
        const v = b.dic[c][b.col[c][i] as number]
        return v === '' || v === undefined ? null : v
      }
      const out: Estimativa[] = new Array(b.n)
      for (let i = 0; i < b.n; i++) {
        out[i] = {
          censo: Number(dec('censo', i)),
          geografia: dec('geografia', i)!,
          universo: dec('universo', i)!,
          estatistica: dec('estatistica', i) as Estimativa['estatistica'],
          variavel: dec('variavel', i),
          dim1: dec('dim1', i),
          cat1: dec('cat1', i),
          dim2: dec('dim2', i),
          cat2: dec('cat2', i),
          valor: b.col.valor[i],
          ep: b.col.ep[i],
          cv: b.col.cv[i],
          classe: dec('classe_precisao', i) as Classe,
          n_faixa: dec('n_faixa', i),
          n_dom_faixa: dec('n_dom_faixa', i),
        }
      }
      return out
    })
  }
  return estimativasCache
}

export function useEstimativas(): Carga<Estimativa[]> {
  const [estado, setEstado] = useState<Carga<Estimativa[]>>({ data: undefined, error: undefined, loading: true })
  useEffect(() => {
    let vivo = true
    loadEstimativas()
      .then((data) => vivo && setEstado({ data, error: undefined, loading: false }))
      .catch((error: Error) => vivo && setEstado({ data: undefined, error, loading: false }))
    return () => {
      vivo = false
    }
  }, [])
  return estado
}

type Filtro = Partial<{ [K in keyof Estimativa]: Estimativa[K] | Estimativa[K][] }>

/** Filtra estimativas; valor em lista = qualquer um; `null` exige ausência (ex.: dim2: null). */
export function consulta(linhas: Estimativa[], filtro: Filtro): Estimativa[] {
  const chaves = Object.keys(filtro) as (keyof Estimativa)[]
  return linhas.filter((l) =>
    chaves.every((k) => {
      const f = filtro[k]
      return Array.isArray(f) ? (f as unknown[]).includes(l[k]) : l[k] === f
    }),
  )
}
