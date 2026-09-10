// (a) "Área da sede, 1984–2026": linha ajustada com banda de IC, área mapeada tracejada fina,
// MapBiomas classe 24 pontilhada (opcional), marcos/obras e marcador do ano selecionado.
// Clicar/passar o mouse num ano do gráfico manda o ano para o mapa; o ano do mapa também marca
// o gráfico (sincronização nos dois sentidos).
import { useCallback, useMemo, useState } from 'react'
import Chart from '../Chart'
import { Figura, type Coluna } from '../ui'
import { baseOption, eixoValor, marcosTempo } from '../../lib/charts'
import { useTema } from '../../lib/theme'
import { fmtHa } from '../../lib/format'
import type { Marco } from '../../lib/rotulos'
import type { SerieAno } from './tipos'

interface Props {
  serie: SerieAno[]
  ano: number
  onAno: (a: number) => void
  censos: number[]
  marcos: Marco[]
  janelasObras: [number, number, string][]
}

export default function GraficoAreaSede({ serie, ano, onAno, censos, janelasObras }: Props) {
  const { viz } = useTema()
  const [comMapbiomas, setComMapbiomas] = useState(false)

  const anos = serie.map((s) => s.ano)
  const ajustada = serie.map((s) => s.area_sede_ajustada_ha)
  const icBaixo = serie.map((s) => s.area_sede_ajustada_ha - s.area_sede_ajustada_ic95_ha)
  const icDelta = serie.map((s) => 2 * s.area_sede_ajustada_ic95_ha)
  const mapeada = serie.map((s) => s.area_sede_ha)
  const mapbiomas = serie.map((s) => s.mapbiomas24_janela_ha)

  const option = useMemo(() => {
    // só os censos como linhas rotuladas (horizontais, no topo); as obras das minas já são as
    // janelas sombreadas — rótulos verticais de cada marco poluíam o gráfico
    const marcosCenso: { ano: number; rotulo: string }[] = censos.map((c) => ({ ano: c, rotulo: `Censo ${c}` }))
    const { markArea } = marcosTempo(viz, janelasObras, [])
    const markLine = {
      silent: true,
      symbol: 'none',
      lineStyle: { color: viz.marco, type: 'dashed', width: 1 },
      label: { color: viz.texto3, fontSize: 10, formatter: '{b}', position: 'end', distance: 4 },
      data: [
        ...marcosCenso.map((m) => ({ xAxis: m.ano, name: m.rotulo })),
        { xAxis: ano, name: '', lineStyle: { color: viz.enfase, type: 'solid', width: 1.5 }, label: { show: false } },
      ],
    }
    return baseOption(viz, {
      xAxis: { type: 'value', min: 1984, max: 2026, ...eixoValor(viz, { axisLabel: { formatter: (v: number) => String(v) } }, 0) },
      grid: { left: 8, right: 16, top: 44, bottom: 8, containLabel: true },
      yAxis: eixoValor(viz, { name: 'ha' }, 0),
      legend: { top: 0, right: 0, data: comMapbiomas ? ['Área ajustada', 'Área mapeada', 'MapBiomas (classe 24)'] : ['Área ajustada', 'Área mapeada'] },
      series: [
        {
          name: 'IC inferior',
          type: 'line',
          data: anos.map((a, i) => [a, icBaixo[i]]),
          stack: 'ic',
          symbol: 'none',
          lineStyle: { opacity: 0 },
          areaStyle: { opacity: 0 },
          silent: true,
          tooltip: { show: false },
        },
        {
          name: 'IC 95 %',
          type: 'line',
          data: anos.map((a, i) => [a, icDelta[i]]),
          stack: 'ic',
          symbol: 'none',
          lineStyle: { opacity: 0 },
          areaStyle: { color: viz.cat[0], opacity: 0.12 },
          silent: true,
          tooltip: { show: false },
        },
        {
          name: 'Área ajustada',
          type: 'line',
          data: anos.map((a, i) => [a, ajustada[i]]),
          showSymbol: true,
          symbol: 'circle',
          symbolSize: 4,
          itemStyle: { color: viz.cat[0], opacity: 0 },
          emphasis: { itemStyle: { opacity: 1 } },
          lineStyle: { color: viz.cat[0], width: 2 },
          markArea,
          markLine,
        },
        {
          name: 'Área mapeada',
          type: 'line',
          data: anos.map((a, i) => [a, mapeada[i]]),
          showSymbol: false,
          lineStyle: { color: viz.texto3, width: 1, type: 'dashed' },
        },
        ...(comMapbiomas
          ? [
              {
                name: 'MapBiomas (classe 24)',
                type: 'line',
                data: anos.map((a, i) => [a, mapbiomas[i]]),
                showSymbol: false,
                lineStyle: { color: viz.contexto, width: 1.5, type: 'dotted' },
              },
            ]
          : []),
      ],
    })
  }, [viz, anos, ajustada, icBaixo, icDelta, mapeada, mapbiomas, comMapbiomas, ano, censos, janelasObras])

  const a1990 = serie.find((s) => s.ano === 1990)?.area_sede_ajustada_ha
  const aFim = serie[serie.length - 1]
  const titulo =
    a1990 && aFim
      ? `De ${fmtHa(a1990)} em 1990 a cerca de ${fmtHa(Math.round(aFim.area_sede_ajustada_ha / 100) * 100)} em ${aFim.ano}: a sede cresce em saltos, nas obras das minas e depois de 2022`
      : 'Área da sede, 1984–2026'

  const clicar = useCallback((x: number) => onAno(Math.min(2026, Math.max(1984, Math.round(x)))), [onAno])

  const colunas: Coluna<SerieAno>[] = [
    { id: 'ano', rotulo: 'Ano' },
    { id: 'area_sede_ha', rotulo: 'Área mapeada', num: true, fmt: (l) => fmtHa(l.area_sede_ha) },
    { id: 'area_sede_ajustada_ha', rotulo: 'Área ajustada', num: true, fmt: (l) => fmtHa(l.area_sede_ajustada_ha) },
    { id: 'ajuste_origem', rotulo: 'Origem do ajuste' },
  ]

  return (
    <Figura
      kicker="Trajetória"
      titulo={titulo}
      subtitulo="Área contígua da sede (hectares), mapeada e ajustada pelo erro de classificação, com intervalo de confiança de 95 %."
      fonte="Classificação própria (E3c) — estatisticas_mancha.json"
      notas="Janelas sombreadas: obras do Sossego (2002–04) e do S11D (2013–16). Linha terracota: ano mostrado no mapa — clique num ponto para levar o mapa a esse ano. O valor de 2026 é provisório."
      controles={
        <button type="button" className={'botao-texto' + (comMapbiomas ? ' ativo' : '')} aria-pressed={comMapbiomas} onClick={() => setComMapbiomas((v) => !v)}>
          {comMapbiomas ? 'Ocultar MapBiomas' : 'Comparar com MapBiomas'}
        </button>
      }
      tabela={{ colunas, linhas: serie }}
    >
      <Chart
        option={option}
        height={340}
        ariaLabel="Área da sede mapeada e ajustada, 1984 a 2026, com marcos do assentamento, emancipação, Sossego e S11D."
        aoClicarEixoX={clicar}
      />
    </Figura>
  )
}
