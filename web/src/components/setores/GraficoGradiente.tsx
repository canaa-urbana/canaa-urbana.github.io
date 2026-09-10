// "Gradiente centro-periferia": o indicador escolhido contra a distância ao núcleo histórico
// (ou a idade do tecido urbano), 2010 × 2022, com o tamanho do ponto proporcional à população.
import { useMemo, useState } from 'react'
import Chart from '../Chart'
import { Figura, Segmentado } from '../ui'
import { baseOption, eixo, eixoValor, type Opcao } from '../../lib/charts'
import { fmtNum } from '../../lib/format'
import type { VizTokens } from '../../lib/theme'
import { fmtIndicador, ID_DESIGUALDADE } from './dados'
import type { DesigualdadeItem, IndicadorMeta, SetorFC } from './tipos'

interface Ponto {
  cod: string
  x: number
  y: number
  pop: number
}

interface Props {
  fc2010: SetorFC | undefined
  fc2022: SetorFC | undefined
  indicador: IndicadorMeta
  desigualdade: DesigualdadeItem[] | undefined
  viz: VizTokens
}

type EixoX = 'distancia' | 'idade'

function pontos(fc: SetorFC | undefined, indicadorId: string, campoX: string): Ponto[] {
  if (!fc) return []
  const out: Ponto[] = []
  for (const f of fc.features) {
    const p = f.properties as unknown as Record<string, number | string | null>
    if (p.pertence !== 'sede') continue
    const x = p[campoX]
    const y = p[indicadorId]
    if (typeof x !== 'number' || !Number.isFinite(x) || typeof y !== 'number' || !Number.isFinite(y)) continue
    out.push({ cod: String(p.cod_setor), x, y, pop: typeof p.pop === 'number' ? p.pop : 0 })
  }
  return out
}

export default function GraficoGradiente({ fc2010, fc2022, indicador, desigualdade, viz }: Props) {
  const [eixoX, setEixoX] = useState<EixoX>('distancia')
  const campoX = eixoX === 'distancia' ? 'dist_nucleo_km' : 'ano_urbanizacao'
  const rotuloX = eixoX === 'distancia' ? 'Distância ao núcleo histórico (km)' : 'Ano mediano de urbanização do setor'

  const p2010 = useMemo(() => pontos(fc2010, indicador.id, campoX), [fc2010, indicador.id, campoX])
  const p2022 = useMemo(() => pontos(fc2022, indicador.id, campoX), [fc2022, indicador.id, campoX])
  const popMax = useMemo(() => Math.max(1, ...p2010.map((p) => p.pop), ...p2022.map((p) => p.pop)), [p2010, p2022])
  const tamanho = (pop: number) => 5 + Math.sqrt(Math.max(0, pop) / popMax) * 24

  const idDes = ID_DESIGUALDADE[indicador.id] ?? indicador.id
  const rho = (ano: number) => desigualdade?.find((d) => d.ano === ano && d.indicador === idDes)?.spearman_distancia ?? null
  const rho2010 = eixoX === 'distancia' ? rho(2010) : null
  const rho2022 = eixoX === 'distancia' ? rho(2022) : null

  const option = useMemo<Opcao>(
    () =>
      baseOption(viz, {
        grid: { left: 8, right: 16, top: 32, bottom: 8, containLabel: true },
        legend: { top: 0, right: 0, left: 'auto' },
        xAxis: eixo(viz, { type: 'value', name: rotuloX, nameLocation: 'middle', nameGap: 30, scale: true }),
        yAxis: eixoValor(viz, { name: `${indicador.rotulo} (${indicador.unidade})`, nameLocation: 'middle', nameGap: 52, scale: true }, indicador.casas),
        tooltip: {
          ...baseOption(viz, {}).tooltip,
          trigger: 'item',
          formatter: (p: { seriesName: string; value: [number, number, number]; data: { cod: string } }) =>
            `${p.seriesName} · setor ${p.data.cod}<br/>${rotuloX}: ${fmtNum(p.value[0], eixoX === 'distancia' ? 2 : 0)}<br/>${indicador.rotulo}: ${fmtIndicador(p.value[1], indicador)}<br/>população: ${fmtNum(p.value[2])}`,
        },
        series: [
          {
            name: '2010',
            type: 'scatter',
            symbol: 'circle',
            data: p2010.map((p) => ({ value: [p.x, p.y, p.pop], cod: p.cod, symbolSize: tamanho(p.pop) })),
            itemStyle: { color: viz.cat[0], opacity: 0.75 },
          },
          {
            name: '2022',
            type: 'scatter',
            symbol: 'rect',
            data: p2022.map((p) => ({ value: [p.x, p.y, p.pop], cod: p.cod, symbolSize: tamanho(p.pop) })),
            itemStyle: { color: viz.cat[1], opacity: 0.75 },
          },
        ],
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [viz, p2010, p2022, indicador, rotuloX, eixoX],
  )

  const linhas = [...p2010.map((p) => ({ ...p, ano: 2010 })), ...p2022.map((p) => ({ ...p, ano: 2022 }))]

  return (
    <Figura
      kicker="Gradiente centro–periferia"
      titulo={`${indicador.rotulo}: setores mais distantes do núcleo tinham menos cobertura em 2010`}
      subtitulo={
        <>
          Cada ponto é um setor da sede; tamanho ∝ população.{' '}
          {rho2010 !== null && <>ρ de Spearman com a distância: 2010 = {fmtNum(rho2010, 2)}{rho2022 !== null && <>, 2022 = {fmtNum(rho2022, 2)}</>}.</>}
        </>
      }
      fonte="IBGE, Censos 2010 e 2022 (Universo); distância e ano de urbanização da E5"
      notas={<p>Malhas de setor diferentes entre 2010 e 2022: compare o padrão do gradiente, não setores individuais.</p>}
      controles={
        <Segmentado
          rotulo="Eixo horizontal"
          valor={eixoX}
          onChange={setEixoX}
          opcoes={[
            { valor: 'distancia', rotulo: 'Distância ao núcleo' },
            { valor: 'idade', rotulo: 'Idade do tecido urbano' },
          ]}
        />
      }
      tabela={{
        colunas: [
          { id: 'ano', rotulo: 'Ano' },
          { id: 'cod', rotulo: 'Setor' },
          { id: 'x', rotulo: rotuloX, num: true, fmt: (l) => fmtNum(l.x, eixoX === 'distancia' ? 2 : 0) },
          { id: 'y', rotulo: indicador.rotulo, num: true, fmt: (l) => fmtIndicador(l.y, indicador) },
          { id: 'pop', rotulo: 'População', num: true, fmt: (l) => fmtNum(l.pop) },
        ],
        linhas,
      }}
    >
      <Chart
        option={option}
        height={360}
        ariaLabel={`Dispersão de ${indicador.rotulo} contra ${rotuloX.toLowerCase()}, setores da sede em 2010 e 2022.`}
      />
    </Figura>
  )
}
