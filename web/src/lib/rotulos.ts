// Rótulos, marcos e ciclos exportados de pipeline/lib/rotulos.py (data/painel/rotulos.json).
import { useJSON } from './data'

export interface Marco {
  inicio: number
  fim: number
  rotulo: string
  tipo: 'fundiario' | 'administrativo' | 'mineral'
}

export interface Rotulos {
  marcos: Marco[]
  censos: number[]
  contagens: number[]
  ciclos: Record<string, string>
  janelas_obras: [number, number, string][]
  geografias: Record<string, string>
  geografias_curtas: Record<string, string>
  dimensoes: Record<string, string>
  categorias: Record<string, string>
  ufs: Record<string, string>
  setores_ordem: string[]
}

export function useRotulos() {
  return useJSON<Rotulos>('painel/rotulos.json')
}

/** Rótulo em português de uma categoria (porta de `rotulo()` de pipeline/lib/rotulos.py).
 *  Fusões do gate `outros:a+b` viram "Outros (a, b)" — nunca escondem a fusão. */
export function rotulo(R: Rotulos, cat: string | null | undefined, dim?: string | null): string {
  if (cat === null || cat === undefined) return ''
  if (cat.startsWith('outros:')) {
    const partes = cat.slice(7).split('+')
    return 'Outros (' + partes.map((p) => rotulo(R, p, dim)).join(', ') + ')'
  }
  if (dim === 'origem_uf' && R.ufs[cat]) return R.ufs[cat]
  if (dim === 'faixa_etaria' && cat.includes('_') && /^\d/.test(cat)) {
    const [a, b] = cat.split('_')
    return /^\d+$/.test(b) ? `${Number(a)}–${Number(b)}` : `${Number(a)}+`
  }
  if (dim === 'densidade_faixa') {
    const d: Record<string, string> = { ate_1: 'Até 1', '1_a_2': '1 a 2', '2_a_3': '2 a 3', mais_de_3: 'Mais de 3' }
    if (d[cat]) return d[cat]
  }
  return R.categorias[cat] ?? cat
}

export function rotuloDim(R: Rotulos, dim: string | null | undefined): string {
  return dim ? R.dimensoes[dim] ?? dim : ''
}

export function rotuloGeo(R: Rotulos, geo: string, curto = false): string {
  return (curto ? R.geografias_curtas : R.geografias)[geo] ?? geo
}
