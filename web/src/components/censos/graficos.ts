// Séries ECharts `custom` reaproveitadas por Censos.tsx e Migracao.tsx: ponto com intervalo de
// confiança (dot plot) e linha conectora (dumbbell). Eixo y sempre `category`; eixo x `value`
// a partir de zero (eixoValor de lib/charts.ts). Cada ponto recebe [catIdx, valor, baixoIC, altoIC].
import type { Opcao } from '../../lib/charts'
import type { VizTokens } from '../../lib/theme'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type ApiCustom = any

export interface DadoCI {
  cat: number
  valor: number | null
  baixo?: number | null
  alto?: number | null
}

export type FormaMarcador = 'circle' | 'rect' | 'diamond' | 'triangle'

/** Desenha o marcador de uma forma (segundo sinal do censo, `MARCADOR_CENSO`) num ponto do
 *  `renderItem` de uma série `custom`. Nunca só a cor codifica a entidade. */
function formaMarcador(tipo: FormaMarcador, cx: number, cy: number, r: number, cor: string): ApiCustom {
  switch (tipo) {
    case 'rect':
      return { type: 'rect', shape: { x: cx - r * 0.85, y: cy - r * 0.85, width: r * 1.7, height: r * 1.7 }, style: { fill: cor } }
    case 'diamond':
      return {
        type: 'polygon',
        shape: { points: [[cx, cy - r * 1.2], [cx + r * 1.2, cy], [cx, cy + r * 1.2], [cx - r * 1.2, cy]] },
        style: { fill: cor },
      }
    case 'triangle':
      return {
        type: 'polygon',
        shape: { points: [[cx, cy - r * 1.25], [cx + r * 1.15, cy + r * 0.85], [cx - r * 1.15, cy + r * 0.85]] },
        style: { fill: cor },
      }
    default:
      return { type: 'circle', shape: { cx, cy, r }, style: { fill: cor } }
  }
}

/** Série de pontos com faixa de IC (traço horizontal ± marcador), deslocada verticalmente dentro
 *  da categoria conforme `idxGrupo`/`nGrupos` (pequenos múltiplos por censo, migrante × não etc.).
 *  `opcoes.marcador` = segundo sinal (ex.: `MARCADOR_CENSO[censo]`); `opcoes.ponto` = false só
 *  desenha as hastes de IC, sem o marcador central (útil sobre uma barra que já marca o valor). */
export function serieDotIC(
  nome: string,
  cor: string,
  idxGrupo: number,
  nGrupos: number,
  dados: DadoCI[],
  opcoes: { marcador?: FormaMarcador; ponto?: boolean } = {},
): Opcao {
  const marcador = opcoes.marcador ?? 'circle'
  const ponto = opcoes.ponto ?? true
  return {
    name: nome,
    type: 'custom',
    z: 3,
    itemStyle: { color: cor },
    data: dados.map((d) => [d.cat, d.valor, d.baixo ?? null, d.alto ?? null]),
    renderItem: (_p: unknown, api: ApiCustom) => {
      const catIdx = api.value(0) as number
      const valor = api.value(1) as number
      const baixo = api.value(2) as number
      const alto = api.value(3) as number
      if (valor === null || valor === undefined || Number.isNaN(valor)) return undefined as unknown as object
      const tam = api.size ? (api.size([0, 1]) as number[]) : [0, 20]
      const passo = tam[1] / (nGrupos + 1)
      const dy = (idxGrupo - (nGrupos - 1) / 2) * passo
      const pv = api.coord([valor, catIdx]) as number[]
      const y = pv[1] + dy
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const filhos: any[] = []
      if (baixo !== null && alto !== null && !Number.isNaN(baixo) && !Number.isNaN(alto)) {
        const pb = api.coord([baixo, catIdx]) as number[]
        const pa = api.coord([alto, catIdx]) as number[]
        filhos.push({ type: 'line', shape: { x1: pb[0], y1: y, x2: pa[0], y2: y }, style: { stroke: cor, lineWidth: 1.25, opacity: 0.55 } })
        filhos.push({ type: 'line', shape: { x1: pb[0], y1: y - 3, x2: pb[0], y2: y + 3 }, style: { stroke: cor, lineWidth: 1.25, opacity: 0.55 } })
        filhos.push({ type: 'line', shape: { x1: pa[0], y1: y - 3, x2: pa[0], y2: y + 3 }, style: { stroke: cor, lineWidth: 1.25, opacity: 0.55 } })
      }
      if (ponto) filhos.push(formaMarcador(marcador, pv[0], y, 4, cor))
      return { type: 'group', children: filhos }
    },
  }
}

export interface ParConectado {
  cat: number
  a: number | null
  b: number | null
}

/** Linha fina conectando dois valores da mesma categoria (dumbbell), sem marcador — desenhe
 *  antes (z menor) de duas `serieDotIC` nas extremidades. */
export function serieLinhaConectora(dados: ParConectado[], cor: string): Opcao {
  return {
    type: 'custom',
    silent: true,
    z: 2,
    data: dados.map((d) => [d.cat, d.a, d.b]),
    renderItem: (_p: unknown, api: ApiCustom) => {
      const catIdx = api.value(0) as number
      const a = api.value(1) as number
      const b = api.value(2) as number
      if (a === null || b === null || a === undefined || b === undefined || Number.isNaN(a) || Number.isNaN(b)) return undefined as unknown as object
      const pa = api.coord([a, catIdx]) as number[]
      const pb = api.coord([b, catIdx]) as number[]
      return { type: 'line', shape: { x1: pa[0], y1: pa[1], x2: pb[0], y2: pb[1] }, style: { stroke: cor, lineWidth: 1.5, opacity: 0.5 } }
    },
  }
}

/** Textura diagonal para categorias fundidas pelo controle de revelação (`outros:a+b`) em barras
 *  empilhadas ou pontos — segundo sinal além da cor de contexto (`viz.contexto`). Distinta de
 *  `decalPrecisao` (que marca CV alto): esta marca a fusão de categorias, não a precisão do ponto. */
export function decalFusao(t: VizTokens): Opcao {
  return {
    symbol: 'rect',
    symbolSize: 1,
    color: t.tema === 'dark' ? 'rgba(23,27,30,0.5)' : 'rgba(250,249,246,0.5)',
    dashArrayX: [2, 0],
    dashArrayY: [3, 4],
    rotation: Math.PI / 4,
  }
}
