// Helpers compartilhados por Censos.tsx e Migracao.tsx sobre painel/estimativas.json
// (dedupe de totais marginais repetidos, consulta tipada, intervalo de confiança 95 %,
// ordenação de faixa etária, coordenadas de capitais estaduais para o mapa de fluxos, cor por
// censo/categoria fixa).
import { consulta, type Estimativa } from '../../lib/data'
import { MARCADOR_CENSO, type VizTokens } from '../../lib/theme'
import type { Opcao } from '../../lib/charts'
import { decalFusao, type FormaMarcador } from './graficos'

/** Deduplica por (censo, geografia, universo, estatistica, variavel, dim1, cat1, dim2, cat2):
 *  `estimativas.json` repete totais marginais em mais de uma linha (E7_briefing). */
export function dedupe(linhas: Estimativa[]): Estimativa[] {
  const vistos = new Set<string>()
  const out: Estimativa[] = []
  for (const l of linhas) {
    const chave = [l.censo, l.geografia, l.universo, l.estatistica, l.variavel, l.dim1, l.cat1, l.dim2, l.cat2].join('|')
    if (!vistos.has(chave)) {
      vistos.add(chave)
      out.push(l)
    }
  }
  return out
}

type Filtro = Parameters<typeof consulta>[1]

/** `consulta()` de lib/data.ts já deduplicada. */
export function busca(linhas: Estimativa[], filtro: Filtro): Estimativa[] {
  return dedupe(consulta(linhas, filtro))
}

/** IC 95 % = valor ± 1,96·ep (mesma unidade do valor). */
export function ic95(valor: number | null, ep: number | null): [number, number] | null {
  if (valor === null || valor === undefined || ep === null || ep === undefined) return null
  return [valor - 1.96 * ep, valor + 1.96 * ep]
}

/** Chave de ordenação de uma categoria de faixa etária ("00_04", "outros:20_24+…" → 20). */
export function chaveEtaria(cat: string): number {
  const primeira = cat.startsWith('outros:') ? cat.slice(7).split('+')[0] : cat
  const m = primeira.match(/^(\d+)/)
  return m ? Number(m[1]) : 999
}

type CensoValido = 1991 | 2000 | 2010 | 2022

function censoValido(censo: number): CensoValido {
  return (censo === 1991 || censo === 2000 || censo === 2010 || censo === 2022 ? censo : 2022) as CensoValido
}

/** Censo → cor fixa validada para CVD (`viz.censo`), usada em todos os gráficos das abas Censos
 *  e Migração (barras, pontos, linhas, KPIs). Mantém a identidade do ano estável entre painéis. */
export function censoCor(viz: VizTokens, censo: number): string {
  return viz.censo[censoValido(censo)]
}

/** Segundo sinal do censo (forma do marcador em pontos/linhas) — a cor nunca é o único código. */
export function censoMarcador(censo: number): FormaMarcador {
  const m = MARCADOR_CENSO[censoValido(censo)]
  return (m === 'diamond' || m === 'triangle' || m === 'rect' ? m : 'circle') as FormaMarcador
}

/** Cor + textura de uma categoria a partir de um mapa fixo categoria → índice de `viz.cat`
 *  (nunca por posição/índice na lista de categorias do gráfico). Categorias fundidas pelo
 *  controle de revelação (`outros:a+b`) e categorias fora do mapa (ex.: "não determinado")
 *  caem em `viz.contexto` com textura diagonal (`decalFusao`). */
export function corCategoriaFixa(cat: string, mapa: Record<string, number>, viz: VizTokens): { color: string; decal?: Opcao } {
  if (cat.startsWith('outros:') || !(cat in mapa)) return { color: viz.contexto, decal: decalFusao(viz) }
  return { color: viz.cat[mapa[cat]] }
}

/** Cor sequencial (ordinal, clara → escura) de uma categoria pela sua posição entre `total`
 *  categorias ordenadas — usado na escolaridade (sem instrução → superior). */
export function corSequencial(idx: number, total: number, viz: VizTokens): string {
  const seq = viz.seq
  if (total <= 1) return seq[0]
  const pos = Math.round((idx / (total - 1)) * (seq.length - 1))
  return seq[pos]
}

/** Ordena a união de categorias de uma dimensão pela ordem de inserção de `rotulos.json`
 *  (`categorias`, que reflete a ordem natural: ex. sem instrução → superior); fusões
 *  (`outros:a+b`) sempre por último. */
export function ordenarCategorias(categorias: Record<string, string>, cats: string[]): string[] {
  const ordem = Object.keys(categorias)
  const rank = (c: string) => (c.startsWith('outros:') ? Infinity : ordem.indexOf(c))
  return [...cats].sort((a, b) => {
    const ra = rank(a)
    const rb = rank(b)
    if (ra === Infinity || ra === -1) return rb === Infinity || rb === -1 ? 0 : 1
    if (rb === Infinity || rb === -1) return -1
    return ra - rb
  })
}

/** Coordenadas das capitais estaduais [lon, lat] — fonte: IBGE, Malha Municipal 2022 /
 *  IBGE Cidades (sedes municipais das capitais), usadas como proxy do centroide da UF de
 *  origem no mapa de fluxos migratórios (a UF é a menor granularidade publicável pelo gate). */
export const CAPITAIS_UF: Record<string, [number, number]> = {
  RO: [-63.9004, -8.76077],
  AC: [-67.8243, -9.97499],
  AM: [-60.025, -3.10194],
  RR: [-60.67582, 2.82384],
  PA: [-48.50239, -1.45502],
  AP: [-51.06639, 0.03889],
  TO: [-48.33635, -10.18398],
  MA: [-44.30278, -2.52972],
  PI: [-42.80194, -5.08917],
  CE: [-38.54306, -3.71722],
  RN: [-35.211, -5.79448],
  PB: [-34.86306, -7.11509],
  PE: [-34.88111, -8.05389],
  AL: [-35.735, -9.66599],
  SE: [-37.07167, -10.9091],
  BA: [-38.51083, -12.97111],
  MG: [-43.93778, -19.92083],
  ES: [-40.33778, -20.31944],
  RJ: [-43.18223, -22.90642],
  SP: [-46.63331, -23.55052],
  PR: [-49.27306, -25.42778],
  SC: [-48.54917, -27.59667],
  RS: [-51.23, -30.03306],
  MS: [-54.64639, -20.44278],
  MT: [-56.09667, -15.601],
  GO: [-49.25389, -16.67861],
  DF: [-47.88278, -15.79389],
}

/** Coordenadas de Canaã dos Carajás (sede). */
export const CANAA: [number, number] = [-49.87, -6.5]
