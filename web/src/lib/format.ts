// Formatação no padrão brasileiro (milhar com ponto, decimal com vírgula).

const cacheFmt = new Map<number, Intl.NumberFormat>()
function nf(casas: number): Intl.NumberFormat {
  let f = cacheFmt.get(casas)
  if (!f) {
    f = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: casas, maximumFractionDigits: casas })
    cacheFmt.set(casas, f)
  }
  return f
}

export const TRACO = '—'

export function vazio(v: unknown): v is null | undefined {
  return v === null || v === undefined || (typeof v === 'number' && !Number.isFinite(v))
}

export function fmtNum(v: number | null | undefined, casas = 0): string {
  return vazio(v) ? TRACO : nf(casas).format(v)
}

/** Percentual já em 0–100. */
export function fmtPct(v: number | null | undefined, casas = 1): string {
  return vazio(v) ? TRACO : `${nf(casas).format(v)} %`
}

/** Proporção 0–1 exibida como percentual. */
export function fmtProp(v: number | null | undefined, casas = 1): string {
  return vazio(v) ? TRACO : `${nf(casas).format(v * 100)} %`
}

export function fmtHa(v: number | null | undefined, casas = 0): string {
  return vazio(v) ? TRACO : `${nf(casas).format(v)} ha`
}

/** Variação com sinal explícito (+/−, com o sinal de menos tipográfico). */
export function fmtDelta(v: number | null | undefined, casas = 0, sufixo = ''): string {
  if (vazio(v)) return TRACO
  const s = nf(casas).format(Math.abs(v))
  return `${v > 0 ? '+' : v < 0 ? '−' : ''}${s}${sufixo}`
}

export function fmtReais(v: number | null | undefined, casas = 0): string {
  return vazio(v) ? TRACO : `R$ ${nf(casas).format(v)}`
}

/** Valores grandes em mil / mi / bi (rótulo curto de eixo e KPI). */
export function fmtCompacto(v: number | null | undefined, casas = 1): string {
  if (vazio(v)) return TRACO
  const a = Math.abs(v)
  if (a >= 1e9) return `${nf(casas).format(v / 1e9)} bi`
  if (a >= 1e6) return `${nf(casas).format(v / 1e6)} mi`
  if (a >= 1e4) return `${nf(casas).format(v / 1e3)} mil`
  return nf(0).format(v)
}
