// Base comum dos gráficos ECharts no sistema Ardósia: eixos recessivos, grade horizontal
// fina, tooltip em superfície chapada, fontes sans 11 px, numerais pt-BR. Cada gráfico
// monta o próprio `option` e passa por `baseOption()`.
import * as echarts from 'echarts/core'
import { BarChart, CustomChart, LineChart, ScatterChart } from 'echarts/charts'
import {
  AriaComponent,
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  MarkAreaComponent,
  MarkLineComponent,
  MarkPointComponent,
  TitleComponent,
  TooltipComponent,
} from 'echarts/components'
import { SVGRenderer } from 'echarts/renderers'
import type { VizTokens } from './theme'
import type { Classe } from './data'
import { fmtNum } from './format'

echarts.use([
  BarChart,
  LineChart,
  ScatterChart,
  CustomChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  MarkLineComponent,
  MarkAreaComponent,
  MarkPointComponent,
  TitleComponent,
  DataZoomComponent,
  AriaComponent,
  SVGRenderer,
])

export { echarts }

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type Opcao = Record<string, any>

export const FONTE_SANS = "'Source Sans 3', 'Segoe UI', system-ui, -apple-system, sans-serif"
export const FONTE_SERIF = "'Source Serif 4', 'Iowan Old Style', Georgia, serif"

/** Eixo de categoria/valor com o estilo recessivo Ardósia. */
export function eixo(t: VizTokens, extra: Opcao = {}): Opcao {
  return {
    axisLine: { lineStyle: { color: t.filete } },
    axisTick: { show: false },
    axisLabel: { color: t.texto3, fontSize: 11, fontFamily: FONTE_SANS },
    splitLine: { show: false },
    nameTextStyle: { color: t.texto3, fontSize: 11, fontFamily: FONTE_SANS },
    ...extra,
  }
}

/** Eixo de valor: grade horizontal 1 px, sem linha de eixo; rótulos pt-BR. */
export function eixoValor(t: VizTokens, extra: Opcao = {}, casas = 0): Opcao {
  return eixo(t, {
    type: 'value',
    axisLine: { show: false },
    splitLine: { show: true, lineStyle: { color: t.grade, width: 1 } },
    axisLabel: {
      color: t.texto3,
      fontSize: 11,
      fontFamily: FONTE_SANS,
      formatter: (v: number) => fmtNum(v, casas),
    },
    ...extra,
  })
}

/** Opção base: aplica tema, tooltip e legenda Ardósia sob o `option` do gráfico. */
export function baseOption(t: VizTokens, op: Opcao): Opcao {
  return {
    animationDuration: 300,
    color: t.cat,
    backgroundColor: 'transparent',
    textStyle: { fontFamily: FONTE_SANS, color: t.texto2, fontSize: 11 },
    grid: { left: 8, right: 16, top: 28, bottom: 8, containLabel: true },
    tooltip: {
      trigger: 'axis',
      confine: true,
      backgroundColor: t.superficie,
      borderColor: t.filete,
      borderWidth: 1,
      padding: [8, 10],
      textStyle: { color: t.texto, fontSize: 12, fontFamily: FONTE_SANS },
      extraCssText: 'box-shadow:none;border-radius:6px;',
      axisPointer: { type: 'line', lineStyle: { color: t.texto3, width: 1, type: 'dashed' } },
    },
    legend: {
      top: 0,
      left: 0,
      itemWidth: 18,
      itemHeight: 10,
      textStyle: { color: t.texto2, fontSize: 11, fontFamily: FONTE_SANS },
      inactiveColor: t.contexto,
    },
    aria: { enabled: true },
    ...op,
  }
}

/** Traços para o segundo sinal das séries (a identidade nunca depende só da cor). */
export const TRACOS = ['solid', 'dashed', 'dotted', [8, 3, 2, 3], [2, 2], [12, 4]] as const
export const MARCADORES = ['circle', 'rect', 'triangle', 'diamond', 'pin', 'roundRect'] as const

/** Textura das classes de precisão (CV 15–30 % cautela; > 30 % baixa), além da cor. */
export function decalPrecisao(classe: Classe | null | undefined, t: VizTokens): Opcao | undefined {
  if (!classe || classe === 'boa') return undefined
  return {
    symbol: 'rect',
    symbolSize: 1,
    color: t.tema === 'dark' ? 'rgba(23,27,30,0.55)' : 'rgba(250,249,246,0.6)',
    dashArrayX: [1, 0],
    dashArrayY: classe === 'baixa' ? [2, 3] : [3, 5],
    rotation: Math.PI / 4,
  }
}

export interface MarcoTempo {
  ano: number
  rotulo: string
}

/** Janelas de obras (markArea) e marcos (markLine tracejada) para um eixo x de anos.
 *  Use em UMA série do gráfico (normalmente a primeira). Eixo x `category` ou `value`.
 *  `dominio` [primeiro, último ano do eixo] recorta janelas e marcos fora do eixo (num eixo
 *  de categorias, um ano ausente vira coordenada NaN). */
export function marcosTempo(
  t: VizTokens,
  janelas: [number, number, string][],
  marcos: MarcoTempo[] = [],
  categoria = false,
  dominio?: [number, number],
): Opcao {
  const x = (a: number) => (categoria ? String(a) : a)
  if (dominio) {
    const [d0, d1] = dominio
    janelas = janelas.filter(([a, b]) => b >= d0 && a <= d1).map(([a, b, r]) => [Math.max(a, d0), Math.min(b, d1), r])
    marcos = marcos.filter((m) => m.ano >= d0 && m.ano <= d1)
  }
  return {
    markArea: {
      silent: true,
      itemStyle: { color: t.obras, opacity: t.tema === 'dark' ? 0.6 : 0.9 },
      label: { color: t.texto3, fontSize: 10, fontFamily: FONTE_SANS, position: 'insideTop' },
      data: janelas.map(([a, b, r]) => [{ xAxis: x(a), name: `obras ${r}` }, { xAxis: x(b) }]),
    },
    markLine: {
      silent: true,
      symbol: 'none',
      lineStyle: { color: t.marco, type: 'dashed', width: 1 },
      label: { color: t.texto3, fontSize: 10, fontFamily: FONTE_SANS, formatter: '{b}', position: 'insideEndTop' },
      data: marcos.map((m) => ({ xAxis: x(m.ano), name: m.rotulo })),
    },
  }
}
