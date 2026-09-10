// "Dispersão entre setores": para os indicadores da tabela de desigualdade intraurbana (E5),
// uma faixa P10–P90 por ano com o P50 (traço) e a média ponderada (ponto), 2010 × 2022 lado a
// lado por indicador (pequenos múltiplos, sem eixo duplo — cada indicador tem sua própria escala).
import { useMemo } from 'react'
import Chart from '../Chart'
import { Figura } from '../ui'
import { baseOption, eixo, eixoValor, type Opcao } from '../../lib/charts'
import { fmtNum, fmtPct } from '../../lib/format'
import type { VizTokens } from '../../lib/theme'
import { idIndicadorDe } from './dados'
import type { DesigualdadeItem, IndicadoresSetores } from './tipos'

interface Props {
  desigualdade: DesigualdadeItem[] | undefined
  indicadores: IndicadoresSetores | undefined
  viz: VizTokens
}

const ANOS = [2010, 2022] as const

export default function GraficoDispersao({ desigualdade, indicadores, viz }: Props) {
  const ids = useMemo(() => {
    const vistos = new Set<string>()
    const ord: string[] = []
    for (const d of desigualdade ?? []) if (!vistos.has(d.indicador)) (vistos.add(d.indicador), ord.push(d.indicador))
    return ord
  }, [desigualdade])

  const meta = (idDes: string) => indicadores?.indicadores.find((i) => i.id === idIndicadorDe(idDes))
  const item = (idDes: string, ano: number) => desigualdade?.find((d) => d.indicador === idDes && d.ano === ano)

  // No gráfico, só os indicadores em % num eixo comum 0–100 (faixas com eixos próprios por
  // linha pareciam barras comparáveis e enganavam); os demais ficam na tabela.
  const idsPct = useMemo(() => ids.filter((d) => (meta(d)?.unidade ?? '').includes('%')), [ids, indicadores])

  const option = useMemo<Opcao | null>(() => {
    if (!idsPct.length) return null
    const linhas: { idDes: string; ano: number; rot: string }[] = []
    for (const idDes of idsPct) for (const ano of ANOS) if (item(idDes, ano)) linhas.push({ idDes, ano, rot: `${meta(idDes)?.rotulo ?? idDes} · ${ano}` })
    linhas.reverse()
    const cat = linhas.map((l) => l.rot)
    const faixa = linhas.map((l, k) => {
      const it = item(l.idDes, l.ano)!
      return { value: [it.p10, it.p90, k], itemStyle: { color: viz.censo[l.ano as 2010 | 2022] } }
    })
    return baseOption(viz, {
      grid: { left: 8, right: 24, top: 36, bottom: 8, containLabel: true },
      legend: {
        ...baseOption(viz, {}).legend,
        data: ['P10–P90 · 2010', 'P10–P90 · 2022', 'Mediana (P50)', 'Média ponderada'],
      },
      tooltip: {
        ...baseOption(viz, {}).tooltip,
        trigger: 'axis',
        axisPointer: { type: 'shadow', shadowStyle: { color: viz.grade, opacity: 0.4 } },
        formatter: (ps: { dataIndex: number }[]) => {
          const l = linhas[ps[0].dataIndex]
          const it = item(l.idDes, l.ano)!
          return `<b>${l.rot}</b><br/>P10 ${fmtPct(it.p10, 1)} · P50 ${fmtPct(it.p50, 1)} · P90 ${fmtPct(it.p90, 1)}<br/>média ponderada ${fmtPct(it.media_ponderada, 1)} · CV entre setores ${fmtNum(it.cv_entre_setores_pct, 0)} %`
        },
      },
      xAxis: { ...eixoValor(viz, { min: 0, max: 100, axisLabel: { color: viz.texto3, fontSize: 11, formatter: '{value} %' } }) },
      yAxis: eixo(viz, { type: 'category', data: cat, axisLabel: { color: viz.texto2, fontSize: 11 } }),
      series: [
        ...([2010, 2022] as const).map((ano) => ({
          name: `P10–P90 · ${ano}`,
          type: 'custom',
          itemStyle: { color: viz.censo[ano] },
          renderItem: (_: unknown, api: { value: (i: number) => number; coord: (v: number[]) => number[]; size: (v: number[]) => number[] }) => {
            const k = api.value(2)
            if (linhas[k].ano !== ano) return null
            const a = api.coord([api.value(0), k])
            const b = api.coord([api.value(1), k])
            const h = Math.min(10, api.size([0, 1])[1] * 0.45)
            return { type: 'rect', shape: { x: a[0], y: a[1] - h / 2, width: b[0] - a[0], height: h }, style: { fill: viz.censo[ano], opacity: 0.85 } }
          },
          encode: { x: [0, 1], y: 2 },
          data: faixa,
        })),
        {
          name: 'Mediana (P50)',
          type: 'scatter',
          symbol: 'diamond',
          symbolSize: 11,
          itemStyle: { color: viz.superficie, borderColor: viz.texto, borderWidth: 1.5 },
          data: linhas.map((l) => item(l.idDes, l.ano)!.p50),
          z: 3,
        },
        {
          name: 'Média ponderada',
          type: 'scatter',
          symbol: 'circle',
          symbolSize: 8,
          itemStyle: { color: viz.texto },
          data: linhas.map((l) => item(l.idDes, l.ano)!.media_ponderada),
          z: 4,
        },
      ],
    })
  }, [idsPct, viz, desigualdade, indicadores])

  if (!option) return null

  const linhasTabela = ids.flatMap((idDes) =>
    ANOS.map((ano) => {
      const it = item(idDes, ano)
      const m = meta(idDes)
      return { indicador: m?.rotulo ?? idDes, ano, cv: it?.cv_entre_setores_pct ?? null, razao: it?.razao_p90_p10 ?? null, p10: it?.p10 ?? null, p90: it?.p90 ?? null }
    }),
  )

  return (
    <Figura
      kicker="Dispersão entre setores"
      titulo="Água e esgoto melhoram em toda a faixa de setores entre 2010 e 2022; a coleta de lixo cai e fica mais desigual"
      subtitulo="% dos domicílios: faixa entre o 10º e o 90º percentil dos setores da sede, mediana (losango) e média ponderada por domicílios (ponto). Indicadores sem escala percentual estão na tabela."
      fonte="IBGE, Censos 2010 e 2022 (Universo); estimativas próprias (E5, `desigualdade_intraurbana`)"
      notas={<p>Malhas de setor diferentes entre os censos: a comparação é de dispersão (CV, faixa), não setor a setor.</p>}
      tabela={{
        colunas: [
          { id: 'indicador', rotulo: 'Indicador' },
          { id: 'ano', rotulo: 'Ano' },
          { id: 'p10', rotulo: 'P10', num: true, fmt: (l) => fmtNum(l.p10, 1) },
          { id: 'p90', rotulo: 'P90', num: true, fmt: (l) => fmtNum(l.p90, 1) },
          { id: 'razao', rotulo: 'Razão P90/P10', num: true, fmt: (l) => fmtNum(l.razao, 1) },
          { id: 'cv', rotulo: 'CV entre setores (%)', num: true, fmt: (l) => fmtNum(l.cv, 0) },
        ],
        linhas: linhasTabela,
      }}
    >
      <Chart option={option} height={Math.max(240, idsPct.length * 2 * 30 + 60)} ariaLabel="Faixas P10-P90 dos indicadores de infraestrutura e densidade entre os setores da sede, 2010 e 2022, com mediana e média ponderada marcadas." />
    </Figura>
  )
}
