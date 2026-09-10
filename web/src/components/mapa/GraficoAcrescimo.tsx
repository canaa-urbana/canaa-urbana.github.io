// (b) "Acréscimo anual da área": barras (ha/ano, eixo do zero), ano selecionado em ênfase,
// janelas de obras sombreadas.
import { useMemo } from 'react'
import Chart from '../Chart'
import { Figura, type Coluna } from '../ui'
import { baseOption, eixo, eixoValor, marcosTempo } from '../../lib/charts'
import { useTema } from '../../lib/theme'
import { fmtDelta } from '../../lib/format'
import type { SerieAno } from './tipos'

export default function GraficoAcrescimo({ serie, ano, janelasObras }: { serie: SerieAno[]; ano: number; janelasObras: [number, number, string][] }) {
  const { viz } = useTema()
  const linhas = serie.filter((s) => s.area_sede_delta_ha !== null)

  const option = useMemo(
    () =>
      baseOption(viz, {
        xAxis: eixo(viz, { type: 'category', data: linhas.map((s) => String(s.ano)) }),
        yAxis: eixoValor(viz, { name: 'ha/ano' }, 0),
        tooltip: { trigger: 'axis' },
        series: [
          {
            type: 'bar',
            data: linhas.map((s) => ({ value: s.area_sede_delta_ha, itemStyle: { color: s.ano === ano ? viz.enfase : viz.cat[0] } })),
            markArea: marcosTempo(viz, janelasObras, [], true).markArea,
            barCategoryGap: '20%',
          },
        ],
      }),
    [viz, linhas, ano, janelasObras],
  )

  const colunas: Coluna<SerieAno>[] = [
    { id: 'ano', rotulo: 'Ano' },
    { id: 'area_sede_delta_ha', rotulo: 'Acréscimo', num: true, fmt: (l) => fmtDelta(l.area_sede_delta_ha, 0, ' ha') },
    { id: 'area_sede_var_pct', rotulo: 'Variação', num: true, fmt: (l) => fmtDelta(l.area_sede_var_pct, 1, ' %') },
  ]

  return (
    <Figura
      kicker="Ritmo"
      titulo="O ritmo de crescimento foi mais intenso entre o Sossego e o S11D"
      subtitulo="Acréscimo anual da área mapeada da sede (hectares por ano)."
      fonte="Classificação própria (E3c) — estatisticas_mancha.json"
      tabela={{ colunas, linhas }}
    >
      <Chart option={option} height={260} ariaLabel="Acréscimo anual da área da sede, em hectares por ano, de 1985 a 2026." />
    </Figura>
  )
}
