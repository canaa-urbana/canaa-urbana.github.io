// "Direção da expansão": rosa polar por octante, com seletor de período mineral. Registra
// PolarComponent aqui mesmo — não faz parte do conjunto padrão de lib/charts.ts.
import { useMemo, useState } from 'react'
import * as echarts from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { PolarComponent } from 'echarts/components'
import Chart from '../Chart'
import { Figura, Segmentado, type Coluna } from '../ui'
import { baseOption, FONTE_SANS } from '../../lib/charts'
import { useTema } from '../../lib/theme'
import { fmtHa, fmtPct } from '../../lib/format'
import type { DirecaoItem } from './tipos'

echarts.use([BarChart, PolarComponent])

const OCTANTES = ['N', 'NE', 'L', 'SE', 'S', 'SO', 'O', 'NO'] as const

export default function GraficoDirecao({ dados }: { dados: DirecaoItem[] }) {
  const { viz } = useTema()
  const periodos = useMemo(() => {
    const vistos = new Set<string>()
    const out: { valor: string; rotulo: string }[] = []
    for (const d of dados) if (!vistos.has(d.periodo)) {
      vistos.add(d.periodo)
      out.push({ valor: d.periodo, rotulo: d.rotulo })
    }
    return out
  }, [dados])
  const [periodo, setPeriodo] = useState(periodos[0]?.valor ?? '')

  const linhas = dados.filter((d) => d.periodo === periodo)
  const porOctante = new Map(linhas.map((d) => [d.octante, d]))
  const valores = OCTANTES.map((o) => porOctante.get(o)?.area_ha ?? 0)

  const option = useMemo(
    () =>
      baseOption(viz, {
        polar: { radius: '68%' },
        angleAxis: {
          type: 'category',
          data: OCTANTES as unknown as string[],
          startAngle: 90,
          axisLine: { lineStyle: { color: viz.filete } },
          axisLabel: { color: viz.texto2, fontSize: 11, fontFamily: FONTE_SANS },
          splitLine: { lineStyle: { color: viz.grade } },
        },
        radiusAxis: {
          axisLabel: { color: viz.texto3, fontSize: 10, fontFamily: FONTE_SANS },
          splitLine: { lineStyle: { color: viz.grade } },
        },
        tooltip: { trigger: 'item', formatter: (p: { name: string; value: number }) => `${p.name}: ${fmtHa(p.value)}` },
        series: [
          {
            type: 'bar',
            coordinateSystem: 'polar',
            data: valores,
            itemStyle: { color: viz.enfase },
            emphasis: { itemStyle: { color: viz.cat[0] } },
          },
        ],
      }),
    [viz, valores],
  )

  const colunas: Coluna<DirecaoItem>[] = [
    { id: 'octante', rotulo: 'Octante' },
    { id: 'area_ha', rotulo: 'Área acrescida', num: true, fmt: (l) => fmtHa(l.area_ha) },
    { id: 'participacao_pct', rotulo: 'Participação no período', num: true, fmt: (l) => fmtPct(l.participacao_pct) },
    { id: 'dist_media_km', rotulo: 'Distância média ao núcleo', num: true, fmt: (l) => `${l.dist_media_km.toFixed(2)} km` },
  ]

  return (
    <Figura
      kicker="Direção"
      titulo="Para onde a sede cresceu em cada ciclo mineral"
      subtitulo="Área acrescida por octante em relação ao núcleo histórico, em hectares."
      fonte="Classificação própria (E3c) — expansao_direcao.json"
      controles={<Segmentado rotulo="Período" opcoes={periodos.map((p) => ({ valor: p.valor, rotulo: p.rotulo }))} valor={periodo} onChange={setPeriodo} />}
      tabela={{ colunas, linhas: OCTANTES.map((o) => porOctante.get(o)).filter((x): x is DirecaoItem => !!x) }}
    >
      <Chart option={option} height={320} ariaLabel={`Área acrescida por octante no período ${periodo}, em hectares.`} />
    </Figura>
  )
}
