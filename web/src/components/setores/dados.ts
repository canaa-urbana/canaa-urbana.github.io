// Funções puras da aba Setores: classes de quantil (comparáveis entre 2010 e 2022), bbox de
// uma FeatureCollection e exportação CSV.
import { fmtNum } from '../../lib/format'
import type { IndicadorMeta, SetorFC, SetorProps } from './tipos'

export const N_CLASSES = 5

/** `desigualdade_intraurbana.json` usa ids próprios (E5), diferentes dos ids de
 *  `indicadores_setores.json`/`setores_{ano}.json` (E7) para o mesmo indicador. */
export const ID_DESIGUALDADE: Record<string, string> = {
  agua_pct: 'agua_pct',
  esgoto_pct: 'esgoto_pct',
  lixo_pct: 'lixo_pct',
  energia_pct: 'energia_pct',
  renda_resp: 'renda_media_responsavel',
  moradores_dom: 'moradores_por_dom',
  densidade_liquida: 'densidade_liquida_hab_ha',
  pretos_pardos_pct: 'pct_pretos_pardos',
}

/** Id do indicador (`indicadores_setores.json`) a partir do id usado em `desigualdade_intraurbana.json`. */
export function idIndicadorDe(idDesigualdade: string): string {
  for (const [k, v] of Object.entries(ID_DESIGUALDADE)) if (v === idDesigualdade) return k
  return idDesigualdade
}

/** Quantis (4 pontos de corte) de uma lista de valores, com pequenos ajustes para garantir
 *  cortes estritamente crescentes (exigido pela expressão `step` do MapLibre). */
export function quebrasQuantil(valores: number[], classes = N_CLASSES): number[] | null {
  const v = valores.filter((x) => Number.isFinite(x)).sort((a, b) => a - b)
  if (v.length < 2) return null
  const cortes: number[] = []
  for (let i = 1; i < classes; i++) {
    const p = (i / classes) * (v.length - 1)
    const lo = Math.floor(p)
    const hi = Math.ceil(p)
    const q = v[lo] + (v[hi] - v[lo]) * (p - lo)
    cortes.push(q)
  }
  // garante estritamente crescente (empurra corte seguinte se empatar)
  for (let i = 1; i < cortes.length; i++) {
    if (cortes[i] <= cortes[i - 1]) cortes[i] = cortes[i - 1] + Math.max(1e-9, Math.abs(cortes[i - 1]) * 1e-6)
  }
  return cortes
}

/** Valores não nulos de um indicador em uma FeatureCollection. */
export function valoresIndicador(fc: SetorFC | undefined, indicador: string): number[] {
  if (!fc) return []
  const out: number[] = []
  for (const f of fc.features) {
    const v = (f.properties as unknown as Record<string, unknown>)[indicador]
    if (typeof v === 'number' && Number.isFinite(v)) out.push(v)
  }
  return out
}

/** Bounding box [[oeste,sul],[leste,norte]] de uma FeatureCollection (EPSG:4326). */
export function bboxFC(fc: SetorFC): [[number, number], [number, number]] | null {
  let minX = Infinity,
    minY = Infinity,
    maxX = -Infinity,
    maxY = -Infinity
  const visit = (coords: unknown): void => {
    if (typeof (coords as number[])[0] === 'number') {
      const [x, y] = coords as [number, number]
      if (x < minX) minX = x
      if (y < minY) minY = y
      if (x > maxX) maxX = x
      if (y > maxY) maxY = y
    } else {
      for (const c of coords as unknown[]) visit(c)
    }
  }
  for (const f of fc.features) if (f.geometry) visit(f.geometry.coordinates)
  if (!Number.isFinite(minX)) return null
  return [
    [minX, minY],
    [maxX, maxY],
  ]
}

/** Formata o valor de um indicador com as casas/unidade do dicionário. */
export function fmtIndicador(v: number | null | undefined, meta: IndicadorMeta | undefined): string {
  if (v === null || v === undefined || !Number.isFinite(v)) return '—'
  const casas = meta?.casas ?? 1
  const un = meta?.unidade ?? ''
  const numero = fmtNum(v, casas)
  return un && un !== '%' ? `${numero} ${un}` : un === '%' ? `${numero} %` : numero
}

/** Baixa uma tabela como CSV (ponto e vírgula, UTF-8 com BOM, decimal vírgula). */
export function baixarCsv(nomeArquivo: string, colunas: { rotulo: string; valor: (l: SetorProps) => string | number | null }[], linhas: SetorProps[]) {
  const esc = (s: string) => (/[;"\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s)
  const linhaTxt = (vals: (string | number | null)[]) =>
    vals
      .map((v) => (v === null || v === undefined ? '' : typeof v === 'number' ? String(v).replace('.', ',') : esc(String(v))))
      .join(';')
  const cab = linhaTxt(colunas.map((c) => c.rotulo))
  const corpo = linhas.map((l) => linhaTxt(colunas.map((c) => c.valor(l))))
  const csv = '﻿' + [cab, ...corpo].join('\r\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = nomeArquivo
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
