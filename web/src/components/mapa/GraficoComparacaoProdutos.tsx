// (d) "Comparação com outros produtos": série própria (ajustada) contra MapBiomas, GHSL,
// WSF-Evolution e IBGE Áreas Urbanizadas — ≥ 4 séries, então traço/marcador distintos além
// da cor (ninguém depende só da cor para diferenciar).
import { useMemo } from 'react'
import Chart from '../Chart'
import { Figura, type Coluna } from '../ui'
import { baseOption, eixoValor, MARCADORES, TRACOS } from '../../lib/charts'
import { useTema } from '../../lib/theme'
import { fmtHa } from '../../lib/format'
import type { ComparacaoProdutoItem, SerieAno } from './tipos'

const PRODUTOS = ['MapBiomas Col.11', 'GHS-BUILT-S R2023A', 'WSF-Evolution', 'IBGE Áreas Urbanizadas 2022', 'IBGE Áreas Urbanizadas 2019_revisado']
const ROTULOS: Record<string, string> = {
  'MapBiomas Col.11': 'MapBiomas Col. 11 (classe 24)',
  'GHS-BUILT-S R2023A': 'GHSL (superfície construída)',
  'WSF-Evolution': 'WSF-Evolution (acumulado)',
  'IBGE Áreas Urbanizadas 2022': 'IBGE AU 2022',
  'IBGE Áreas Urbanizadas 2019_revisado': 'IBGE AU 2019 (revisado)',
}

export default function GraficoComparacaoProdutos({ serie, produtos }: { serie: SerieAno[]; produtos: ComparacaoProdutoItem[] }) {
  const { viz } = useTema()

  const option = useMemo(() => {
    const series: Record<string, unknown>[] = [
      {
        name: 'Série própria (ajustada)',
        type: 'line',
        data: serie.map((s) => [s.ano, s.area_sede_ajustada_ha]),
        showSymbol: false,
        lineStyle: { color: viz.enfase, width: 2.5 },
      },
    ]
    // cor, traço e marcador FIXOS por produto (a cor segue a entidade); a série própria é a ênfase
    const estilo: Record<string, { cor: string; traco: string | number[]; simbolo: string }> = {
      'MapBiomas Col.11': { cor: viz.cat[0], traco: TRACOS[1] as string, simbolo: MARCADORES[1] },
      'GHS-BUILT-S R2023A': { cor: viz.cat[2], traco: TRACOS[2] as string, simbolo: MARCADORES[2] },
      'WSF-Evolution': { cor: viz.cat[3], traco: [...TRACOS[3]] as number[], simbolo: MARCADORES[3] },
      'IBGE Áreas Urbanizadas 2022': { cor: viz.texto2, traco: 'solid', simbolo: 'pin' },
      'IBGE Áreas Urbanizadas 2019_revisado': { cor: viz.texto2, traco: 'solid', simbolo: 'roundRect' },
    }
    PRODUTOS.forEach((p) => {
      const linhas = produtos.filter((d) => d.produto === p).sort((a, b) => a.ano - b.ano)
      if (!linhas.length) return
      const e = estilo[p]
      series.push({
        name: ROTULOS[p] ?? p,
        type: linhas.length > 1 ? 'line' : 'scatter',
        data: linhas.map((d) => [d.ano, d.area_ha]),
        showSymbol: true,
        symbol: e.simbolo,
        symbolSize: linhas.length > 1 ? 6 : 12,
        itemStyle: { color: e.cor },
        lineStyle: { color: e.cor, width: 1.5, type: e.traco },
      })
    })
    return baseOption(viz, {
      xAxis: { type: 'value', min: 1975, max: 2026, ...eixoValor(viz, { axisLabel: { formatter: (v: number) => String(v) } }, 0) },
      yAxis: eixoValor(viz, { name: 'ha' }, 0),
      grid: { left: 8, right: 16, top: 28, bottom: 64, containLabel: true },
      legend: { ...baseOption(viz, {}).legend, top: undefined, bottom: 0, left: 0, right: 0, type: 'plain', itemWidth: 24 },
      series,
    })
  }, [viz, serie, produtos])

  const colunas: Coluna<ComparacaoProdutoItem>[] = [
    { id: 'produto', rotulo: 'Produto', fmt: (l) => ROTULOS[l.produto] ?? l.produto },
    { id: 'ano', rotulo: 'Ano', num: true },
    { id: 'area_ha', rotulo: 'Área', num: true, fmt: (l) => fmtHa(l.area_ha) },
  ]

  return (
    <Figura
      kicker="Comparação"
      titulo="A série própria fica entre os produtos globais e bem abaixo do MapBiomas"
      subtitulo="Área construída/urbanizada segundo diferentes produtos de sensoriamento remoto na janela da sede."
      fonte="MapBiomas Col. 11; JRC GHS-BUILT-S; DLR WSF-Evolution; IBGE Áreas Urbanizadas — painel/geo/comparacao_produtos.json"
      notas="O MapBiomas superestima a mancha em cerca de 4× (classe 24 mistura outros usos construídos e de solo exposto na janela; ver E3a/E3c). Cada produto mede um recorte metodológico diferente — não é uma validação direta."
      tabela={{ colunas, linhas: produtos }}
    >
      <Chart option={option} height={340} ariaLabel="Comparação da área da sede entre a série própria e MapBiomas, GHSL, WSF-Evolution e IBGE Áreas Urbanizadas." />
    </Figura>
  )
}
