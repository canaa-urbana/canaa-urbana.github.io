// Mineração e economia: o ritmo das obras (área acrescida) contra o dos royalties (CFEM) e do
// PIB, a composição do valor adicionado, o emprego formal e a comparação regional.
import { useMemo, useState } from 'react'
import { useAnalise, useJSON } from '../lib/data'
import { fmtCompacto, fmtNum, fmtPct, fmtReais } from '../lib/format'
import { useTema } from '../lib/theme'
import { useRotulos } from '../lib/rotulos'
import { baseOption, eixo, eixoValor, FONTE_SANS, marcosTempo, MARCADORES, TRACOS, type Opcao } from '../lib/charts'
import Chart from '../components/Chart'
import { Esqueleto, Figura, Kpi, Secao, Segmentado, Selecao, Tabela } from '../components/ui'

interface Eco {
  ano: number
  pib_part_pa_pct: number | null
  pib_mil_r: number | null
  va_agro_pct: number | null
  va_industria_pct: number | null
  va_servicos_pct: number | null
  va_adm_publica_pct: number | null
  cempre_assalariados: number | null
  cempre_empresas: number | null
  cempre_assalariados_construcao: number | null
  cfem_r2022: number | null
  cfem_nominal_r: number | null
  cfem_per_capita_r2022: number | null
  pop_municipio: number | null
  area_sede_delta_ha: number | null
  pib_per_capita_r: number | null
}
interface PeriodoCfem {
  periodo: string
  rotulo: string
  area_acrescida_ha: number
  ha_por_ano: number
  cfem_acumulada_r2022: number
  cfem_media_anual_r2022: number
}
interface Corr {
  variavel: string
  defasagem_anos: number
  n: number
  pearson: number
  spearman: number
}
interface Grupo {
  grupo: string
  censo: number
  n_municipios_amc: number
  [k: string]: number | string | null
}
interface DifDif {
  indicador: string
  periodo: string
  comparacao: string
  delta_canaa: number
  delta_comparacao: number
  dif_em_dif: number
  ep_dif_em_dif: number
  significativo_95: boolean
}

const INDICADORES_PAINEL = [
  { id: 'pct_imigrante_5anos', rotulo: 'Migrantes de data fixa (% da população 5+)', casas: 1 },
  { id: 'pct_ocupado_extrativo', rotulo: 'Ocupados na extrativa mineral (%)', casas: 1 },
  { id: 'pct_sem_esgoto_adequado', rotulo: 'Domicílios sem esgoto adequado (%)', casas: 1 },
  { id: 'pct_alugado', rotulo: 'Domicílios alugados (%)', casas: 1 },
  { id: 'renda_trabalho_media_r2022', rotulo: 'Renda média do trabalho (R$ de jul/2022)', casas: 0 },
  { id: 'pop_var_pct_vs_2000', rotulo: 'Variação da população desde 2000 (%)', casas: 0 },
]

const JANELAS_PADRAO: [number, number, string][] = [
  [2002, 2004, 'Sossego'],
  [2013, 2016, 'S11D'],
]

export default function Economia() {
  const { viz } = useTema()
  const { data: R } = useRotulos()
  const { data: eco } = useAnalise<Eco>('economia_anual')
  const { data: periodos } = useAnalise<PeriodoCfem>('mancha_cfem_periodos')
  const { data: corr } = useAnalise<Corr>('mancha_cfem_correlacao')
  const { data: painel } = useAnalise<Grupo>('painel_amc_grupos')
  const { data: dd } = useAnalise<DifDif>('dif_em_dif_descritiva')
  const { data: resumo } = useJSON<{ cfem_pico: { ano: number; nominal: number }; pib_part_pa_2023?: number }>('painel/resumo_analise.json')

  const [indicador, setIndicador] = useState(INDICADORES_PAINEL[0].id)
  const [periodoDD, setPeriodoDD] = useState('2000–2022')

  const janelas = R?.janelas_obras ?? JANELAS_PADRAO
  const anos = useMemo(() => (eco ?? []).map((e) => e.ano), [eco])

  // --- três painéis empilhados com o mesmo eixo x (obras × royalties × PIB), sem eixo duplo
  const opTres = useMemo<Opcao | null>(() => {
    if (!eco) return null
    const cat = anos.map(String)
    const grids = [
      { left: 64, right: 16, top: 34, height: '22%' },
      { left: 64, right: 16, top: '38%', height: '22%' },
      { left: 64, right: 16, top: '71%', height: '22%' },
    ]
    const titulo = (t: string, top: number | string) => ({
      text: t,
      left: 64,
      top,
      textStyle: { fontSize: 12, fontFamily: FONTE_SANS, color: viz.texto2, fontWeight: 600 },
    })
    const mt = marcosTempo(viz, janelas, [], true, [anos[0], anos[anos.length - 1]])
    return baseOption(viz, {
      grid: grids,
      title: [titulo('Área acrescida à sede (ha/ano)', 8), titulo('CFEM distribuída ao município (R$ de 2022)', '33%'), titulo('PIB per capita (R$ correntes)', '66%')],
      legend: { show: false },
      tooltip: {
        ...baseOption(viz, {}).tooltip,
        trigger: 'axis',
        axisPointer: { type: 'line', link: [{ xAxisIndex: 'all' }], lineStyle: { color: viz.texto3, type: 'dashed' } },
        valueFormatter: undefined,
        formatter: (ps: { axisValue: string; seriesName: string; value: number | null; marker: string }[]) =>
          `<b>${ps[0]?.axisValue}</b><br/>` +
          ps
            .map((p) => {
              const v = p.value
              const txt = p.seriesName.startsWith('CFEM') ? fmtReais(v === null ? null : v) : p.seriesName.startsWith('PIB') ? fmtReais(v) : `${fmtNum(v)} ha`
              return `${p.marker} ${p.seriesName}: ${txt}`
            })
            .join('<br/>'),
      },
      xAxis: [0, 1, 2].map((i) => eixo(viz, { type: 'category', data: cat, gridIndex: i, axisLabel: { show: i === 2, color: viz.texto3, fontSize: 11 } })),
      yAxis: [0, 1, 2].map((i) =>
        eixoValor(viz, {
          gridIndex: i,
          splitNumber: 3,
          axisLabel: { color: viz.texto3, fontSize: 11, formatter: (v: number) => fmtCompacto(v, 0) },
        }),
      ),
      series: [
        { name: 'Área acrescida', type: 'bar', xAxisIndex: 0, yAxisIndex: 0, data: eco.map((e) => e.area_sede_delta_ha), itemStyle: { color: viz.cat[0] }, barMaxWidth: 14, ...mt },
        { name: 'CFEM (R$ 2022)', type: 'bar', xAxisIndex: 1, yAxisIndex: 1, data: eco.map((e) => e.cfem_r2022), itemStyle: { color: viz.enfase }, barMaxWidth: 14, markArea: mt.markArea },
        {
          name: 'PIB per capita',
          type: 'line',
          xAxisIndex: 2,
          yAxisIndex: 2,
          data: eco.map((e) => e.pib_per_capita_r),
          lineStyle: { color: viz.cat[2] === viz.cat[0] ? viz.texto2 : viz.cat[0], width: 2 },
          itemStyle: { color: viz.cat[0] },
          symbol: 'circle',
          symbolSize: 5,
          connectNulls: false,
          markArea: mt.markArea,
        },
      ],
    })
  }, [eco, anos, viz, janelas])

  // --- composição do valor adicionado (barras 100 % empilhadas)
  const opVA = useMemo<Opcao | null>(() => {
    if (!eco) return null
    const linhas = eco.filter((e) => e.va_industria_pct !== null)
    const series = [
      ['va_industria_pct', 'Indústria (inclui extrativa)'],
      ['va_servicos_pct', 'Serviços'],
      ['va_adm_publica_pct', 'Adm. pública'],
      ['va_agro_pct', 'Agropecuária'],
    ] as const
    return baseOption(viz, {
      grid: { left: 8, right: 16, top: 36, bottom: 8, containLabel: true },
      tooltip: { ...baseOption(viz, {}).tooltip, valueFormatter: (v: number) => fmtPct(v, 1) },
      xAxis: eixo(viz, { type: 'category', data: linhas.map((e) => String(e.ano)) }),
      yAxis: eixoValor(viz, { max: 100, axisLabel: { color: viz.texto3, fontSize: 11, formatter: '{value} %' } }),
      series: series.map(([k, n], i) => ({
        name: n,
        type: 'bar',
        stack: 'va',
        barMaxWidth: 22,
        data: linhas.map((e) => e[k]),
        itemStyle: { color: viz.cat[i], borderColor: viz.superficie, borderWidth: 1, decal: i >= 3 ? { symbol: 'rect', dashArrayX: [1, 0], dashArrayY: [2, 3], rotation: Math.PI / 4, color: viz.superficie } : undefined },
      })),
    })
  }, [eco, viz])

  // --- emprego formal (CEMPRE)
  const opCempre = useMemo<Opcao | null>(() => {
    if (!eco) return null
    const linhas = eco.filter((e) => e.cempre_assalariados !== null)
    return baseOption(viz, {
      grid: { left: 8, right: 76, top: 36, bottom: 8, containLabel: true },
      tooltip: { ...baseOption(viz, {}).tooltip, valueFormatter: (v: number) => fmtNum(v) },
      xAxis: eixo(viz, { type: 'category', data: linhas.map((e) => String(e.ano)) }),
      yAxis: eixoValor(viz),
      series: [
        { name: 'Assalariados (total)', type: 'line', data: linhas.map((e) => e.cempre_assalariados), lineStyle: { width: 2, color: viz.cat[0] }, itemStyle: { color: viz.cat[0] }, symbol: MARCADORES[0], symbolSize: 6, ...marcosTempo(viz, janelas, [], true, [linhas[0].ano, linhas[linhas.length - 1].ano]), endLabel: { show: true, formatter: 'total', color: viz.texto2, fontSize: 11 } },
        { name: 'Assalariados na construção', type: 'line', data: linhas.map((e) => e.cempre_assalariados_construcao), lineStyle: { width: 2, color: viz.cat[1], type: TRACOS[1] }, itemStyle: { color: viz.cat[1] }, symbol: MARCADORES[1], symbolSize: 6, endLabel: { show: true, formatter: 'construção', color: viz.texto2, fontSize: 11 } },
      ],
    })
  }, [eco, viz, janelas])

  // --- correlação CFEM × área com defasagem
  const opCorr = useMemo<Opcao | null>(() => {
    if (!corr) return null
    return baseOption(viz, {
      grid: { left: 8, right: 24, top: 16, bottom: 8, containLabel: true },
      tooltip: { ...baseOption(viz, {}).tooltip, trigger: 'item', formatter: (p: { name: string; value: number; dataIndex: number }) => `CFEM defasada ${p.name}<br/>Pearson ${fmtNum(p.value, 2)} · Spearman ${fmtNum(corr[p.dataIndex].spearman, 2)} · n = ${corr[p.dataIndex].n}` },
      xAxis: eixo(viz, { type: 'category', data: corr.map((c) => `${c.defasagem_anos} ano${c.defasagem_anos === 1 ? '' : 's'}`), name: 'defasagem da CFEM', nameLocation: 'middle', nameGap: 28 }),
      yAxis: eixoValor(viz, { min: -1, max: 1, interval: 0.5, axisLabel: { color: viz.texto3, fontSize: 11, formatter: (v: number) => fmtNum(v, 1) } }, 1),
      series: [
        {
          type: 'bar',
          barMaxWidth: 24,
          data: corr.map((c) => ({ value: c.pearson, itemStyle: { color: c.pearson < 0 ? viz.div[1] : viz.div[5] } })),
          label: { show: true, position: 'top', formatter: (p: { value: number }) => fmtNum(p.value, 2), color: viz.texto2, fontSize: 11 },
          markLine: { silent: true, symbol: 'none', lineStyle: { color: viz.filete, type: 'solid' }, data: [{ yAxis: 0 }], label: { show: false } },
        },
      ],
    })
  }, [corr, viz])

  // --- comparação regional (ênfase em Canaã, demais em cinza)
  const ind = INDICADORES_PAINEL.find((i) => i.id === indicador)!
  const opPainel = useMemo<Opcao | null>(() => {
    if (!painel) return null
    const grupos = [...new Set(painel.map((g) => g.grupo))]
    const censos = [2000, 2010, 2022]
    const contexto = grupos.filter((g) => !g.startsWith('Canaã') && g !== 'Parauapebas')
    const simbCtx = ['emptyCircle', 'emptyTriangle', 'emptyDiamond', 'emptyRect']
    const tracoCtx = ['solid', 'dotted', [6, 3], [2, 4]]
    return baseOption(viz, {
      grid: { left: 8, right: 140, top: 16, bottom: 64, containLabel: true },
      legend: {
        ...baseOption(viz, {}).legend,
        top: undefined,
        bottom: 0,
        data: contexto.map((g, i) => ({ name: g, icon: simbCtx[i % 4] })),
        formatter: (g: string) => `${g} (${painel.find((p) => p.grupo === g)?.n_municipios_amc ?? ''})`,
        itemWidth: 22,
      },
      tooltip: { ...baseOption(viz, {}).tooltip, valueFormatter: (v: number) => fmtNum(v, ind.casas) },
      xAxis: eixo(viz, { type: 'category', data: censos.map(String), boundaryGap: false }),
      yAxis: eixoValor(viz, { scale: false }),
      series: grupos.map((g) => {
        const canaa = g.startsWith('Canaã')
        const parau = g === 'Parauapebas'
        const k = contexto.indexOf(g)
        const cor = canaa ? viz.enfase : parau ? viz.cat[0] : viz.contexto
        const pts = censos.map((c) => painel.find((p) => p.grupo === g && p.censo === c)?.[indicador] ?? null)
        return {
          name: g,
          type: 'line',
          data: pts,
          z: canaa ? 5 : parau ? 4 : 2,
          lineStyle: { color: cor, width: canaa || parau ? 2.5 : 1.5, type: canaa ? 'solid' : parau ? 'dashed' : tracoCtx[k % 4] },
          itemStyle: { color: cor },
          symbol: canaa ? 'circle' : parau ? 'rect' : simbCtx[k % 4],
          symbolSize: canaa || parau ? 8 : 6,
          endLabel: canaa || parau ? { show: true, formatter: canaa ? 'Canaã' : 'Parauapebas', color: viz.texto, fontSize: 12, fontWeight: canaa ? 600 : 400 } : undefined,
        }
      }),
    })
  }, [painel, indicador, ind, viz])

  if (!eco) return <div className="pagina"><Esqueleto altura={480} /></div>

  const u = (a: number) => eco.find((e) => e.ano === a)
  const pibUlt = [...eco].reverse().find((e) => e.pib_part_pa_pct !== null)
  const cfemTot = eco.reduce((s, e) => s + (e.cfem_r2022 ?? 0), 0)
  const ddLinhas = (dd ?? []).filter((d) => d.periodo === periodoDD)
  const ddInd = [...new Set(ddLinhas.map((d) => d.indicador))]

  return (
    <div className="pagina">
      <Secao kicker="Mineração e economia" titulo="A cidade cresce nas obras; os royalties chegam depois">
        <p>
          O maior ritmo de expansão da sede coincide com a construção das minas (Sossego, 2002–04; S11D, 2013–16), quando a CFEM
          ainda era pequena. Os royalties só explodem a partir de 2018, com o S11D em operação plena — sobre uma cidade já
          construída. Valores monetários da CFEM deflacionados pelo IPCA (R$ de julho de 2022).
        </p>
      </Secao>

      <div className="kpis">
        <Kpi rotulo={`Participação no PIB do Pará, ${pibUlt?.ano}`} valor={fmtPct(pibUlt?.pib_part_pa_pct, 1)} delta={`${fmtPct(u(2021)?.pib_part_pa_pct, 1)} no pico (2021); ${fmtPct(u(2002)?.pib_part_pa_pct, 2)} em 2002`} serie={eco.map((e) => e.pib_part_pa_pct)} destaque={eco.indexOf(pibUlt!)} nota="IBGE, PIB dos Municípios" />
        <Kpi rotulo={`CFEM no pico, ${resumo?.cfem_pico.ano ?? 2021}`} valor={fmtCompacto(resumo?.cfem_pico.nominal ?? u(2021)?.cfem_nominal_r, 2)} unidade="R$ correntes" delta={`${fmtCompacto(cfemTot, 1)} acumulados 2004–2026 (R$ 2022)`} serie={eco.map((e) => e.cfem_r2022)} destaque={eco.findIndex((e) => e.ano === (resumo?.cfem_pico.ano ?? 2021))} nota="ANM; distribuída ao município" />
        <Kpi rotulo="Assalariados formais, 2021" valor={fmtNum(u(2021)?.cempre_assalariados)} delta={`${fmtNum(u(2006)?.cempre_assalariados)} em 2006; pico de ${fmtNum(u(2015)?.cempre_assalariados)} nas obras do S11D (2015)`} serie={eco.map((e) => e.cempre_assalariados)} destaque={eco.findIndex((e) => e.ano === 2021)} nota="IBGE, CEMPRE (unidades locais)" />
        <Kpi rotulo="Área acrescida à sede, 2022–2026" valor={fmtNum(periodos?.find((p) => p.periodo === '2022–2026')?.area_acrescida_ha)} unidade="ha" delta={`${fmtNum(periodos?.find((p) => p.periodo === '2016–2022')?.area_acrescida_ha)} ha em 2016–2022`} nota="área mapeada; 2026 provisório" />
      </div>

      <div className="grade" style={{ marginTop: 24 }}>
        <div className="c-8">
          {opTres && (
            <Figura
              kicker="Obras × royalties"
              titulo="A área cresce nas janelas de obras; a CFEM, depois da operação do S11D"
              subtitulo="Três painéis com o mesmo eixo de tempo e escalas próprias (não é eixo duplo). Faixas: construção do Sossego (2002–04) e do S11D (2013–16)."
              fonte="classificação própria (área mapeada da sede); ANM (CFEM, deflacionada pelo IPCA de julho); IBGE (PIB dos Municípios, estimativas de população)"
              notas={<p>O PIB per capita de 2022 cai porque o Censo corrigiu a população (77 mil contra 39 mil estimados para 2021); os anos 2011–2021 usam estimativas do IBGE que subcontaram Canaã.</p>}
              tabela={{
                colunas: [
                  { id: 'ano', rotulo: 'Ano' },
                  { id: 'a', rotulo: 'Área acrescida (ha)', num: true, fmt: (e: Eco) => fmtNum(e.area_sede_delta_ha, 1) },
                  { id: 'c', rotulo: 'CFEM (R$ 2022)', num: true, fmt: (e: Eco) => fmtNum(e.cfem_r2022) },
                  { id: 'p', rotulo: 'PIB per capita (R$)', num: true, fmt: (e: Eco) => fmtNum(e.pib_per_capita_r) },
                  { id: 'pop', rotulo: 'População usada', num: true, fmt: (e: Eco) => fmtNum(e.pop_municipio) },
                ],
                linhas: eco,
              }}
            >
              <Chart option={opTres} height={520} ariaLabel="Três painéis de 2002 a 2026: a área acrescida à sede tem picos em 2003, 2011 e 2014–15, nas obras; a CFEM fica abaixo de R$ 60 milhões até 2017 e passa de R$ 1 bilhão em 2021; o PIB per capita acompanha a CFEM." />
            </Figura>
          )}
        </div>
        <div className="c-4">
          {opCorr && (
            <Figura
              kicker="Defasagem"
              titulo="A correlação só fica positiva com três anos de defasagem"
              subtitulo="Correlação de Pearson entre a CFEM de t − k e a área acrescida em t (2004–2026)"
              fonte="elaboração própria (E5)"
              notas={<p>Série curta (19–22 anos): leitura descritiva, não causal.</p>}
              tabela={{
                colunas: [
                  { id: 'defasagem_anos', rotulo: 'Defasagem (anos)', num: true },
                  { id: 'n', rotulo: 'n', num: true },
                  { id: 'pearson', rotulo: 'Pearson', num: true, fmt: (c: Corr) => fmtNum(c.pearson, 2) },
                  { id: 'spearman', rotulo: 'Spearman', num: true, fmt: (c: Corr) => fmtNum(c.spearman, 2) },
                ],
                linhas: corr ?? [],
              }}
            >
              <Chart option={opCorr} height={240} ariaLabel="Correlação entre CFEM defasada e área acrescida: −0,20 sem defasagem, −0,11 com um ano, −0,01 com dois e +0,24 com três anos." />
            </Figura>
          )}
          {periodos && (
            <div style={{ marginTop: 24 }}>
              <Figura
                kicker="Por período"
                titulo="Nas obras, pouca CFEM por hectare construído"
                fonte="classificação própria; ANM"
              >
                <Tabela
                  legenda="Área acrescida e CFEM por período"
                  colunas={[
                    { id: 'rotulo', rotulo: 'Período' },
                    { id: 'ha', rotulo: 'ha/ano', num: true, fmt: (p: PeriodoCfem) => fmtNum(p.ha_por_ano, 0) },
                    { id: 'cfem', rotulo: 'CFEM média/ano (R$ 2022)', num: true, fmt: (p: PeriodoCfem) => fmtCompacto(p.cfem_media_anual_r2022, 1) },
                  ]}
                  linhas={periodos.filter((p) => !p.periodo.startsWith('2004–2016') && !p.periodo.startsWith('2016–2026'))}
                />
              </Figura>
            </div>
          )}
        </div>

        <div className="c-6">
          {opVA && (
            <Figura
              kicker="Estrutura produtiva"
              titulo="A indústria extrativa passa a responder por quase 90 % do valor adicionado"
              subtitulo="Composição do valor adicionado bruto a preços correntes (%), 2002–2021"
              fonte="IBGE, PIB dos Municípios (SIDRA t/5938); 2022–2023 sem abertura setorial divulgada"
              tabela={{
                colunas: [
                  { id: 'ano', rotulo: 'Ano' },
                  { id: 'i', rotulo: 'Indústria', num: true, fmt: (e: Eco) => fmtPct(e.va_industria_pct) },
                  { id: 's', rotulo: 'Serviços', num: true, fmt: (e: Eco) => fmtPct(e.va_servicos_pct) },
                  { id: 'ap', rotulo: 'Adm. pública', num: true, fmt: (e: Eco) => fmtPct(e.va_adm_publica_pct) },
                  { id: 'ag', rotulo: 'Agropecuária', num: true, fmt: (e: Eco) => fmtPct(e.va_agro_pct) },
                ],
                linhas: eco.filter((e) => e.va_industria_pct !== null),
              }}
            >
              <Chart option={opVA} height={320} ariaLabel="A indústria vai de 38 % do valor adicionado em 2002 para 90 % em 2021; a agropecuária cai de 26 % para menos de 1 %." />
            </Figura>
          )}
        </div>
        <div className="c-6">
          {opCempre && (
            <Figura
              kicker="Emprego formal"
              titulo="O emprego formal sobe nas obras do S11D e se estabiliza em patamar mais alto"
              subtitulo="Assalariados em unidades locais sediadas no município (CEMPRE), 2006–2021"
              fonte="IBGE, Cadastro Central de Empresas (SIDRA t/6449); a seção B (extrativa) é suprimida pelo IBGE na maior parte dos anos"
              tabela={{
                colunas: [
                  { id: 'ano', rotulo: 'Ano' },
                  { id: 'e', rotulo: 'Empresas', num: true, fmt: (e: Eco) => fmtNum(e.cempre_empresas) },
                  { id: 'a', rotulo: 'Assalariados', num: true, fmt: (e: Eco) => fmtNum(e.cempre_assalariados) },
                  { id: 'c', rotulo: 'na construção', num: true, fmt: (e: Eco) => fmtNum(e.cempre_assalariados_construcao) },
                ],
                linhas: eco.filter((e) => e.cempre_assalariados !== null),
              }}
            >
              <Chart option={opCempre} height={320} ariaLabel="Assalariados formais passam de cerca de 2,4 mil (2006) a 9 mil (2015) e 8 mil (2021); a construção tem picos em 2011, 2013 e 2015." />
            </Figura>
          )}
        </div>
      </div>

      <section className="bloco">
        <p className="ard-kicker">Comparação regional</p>
        <h3>Canaã se descola dos municípios comparáveis a partir de 2010</h3>
        <div className="grade">
          <div className="c-7">
            {opPainel && (
              <Figura
                titulo={ind.rotulo}
                subtitulo="Média dos municípios de cada grupo (áreas mínimas comparáveis 2000–2022). Canaã em destaque, Parauapebas tracejado; em cinza, os demais grupos (legenda abaixo, com o número de municípios)."
                fonte="IBGE, microdados da amostra 2000, 2010 e 2022, painel de áreas mínimas comparáveis (projeto migracoes-mineracao); estimativas próprias"
                controles={<Selecao rotulo="Indicador" valor={indicador} onChange={setIndicador} opcoes={INDICADORES_PAINEL.map((i) => ({ valor: i.id, rotulo: i.rotulo }))} />}
                tabela={{
                  colunas: [
                    { id: 'grupo', rotulo: 'Grupo' },
                    { id: 'n_municipios_amc', rotulo: 'Municípios', num: true },
                    { id: 'censo', rotulo: 'Censo', num: true },
                    { id: 'v', rotulo: ind.rotulo, num: true, fmt: (g: Grupo) => fmtNum(g[indicador] as number, ind.casas) },
                  ],
                  linhas: painel ?? [],
                }}
              >
                <Chart option={opPainel} height={360} ariaLabel={`${ind.rotulo}: Canaã comparada a Parauapebas e aos grupos de municípios do Pará, 2000, 2010 e 2022.`} />
              </Figura>
            )}
          </div>
          <div className="c-5">
            <Figura
              titulo="Diferença-em-diferenças descritiva"
              subtitulo="Variação em Canaã menos a variação no comparador (pontos percentuais ou unidade do indicador), com erro-padrão pelo método delta"
              fonte="estimativas próprias a partir dos microdados da amostra (E5); não é estimativa causal"
              controles={
                <Segmentado
                  rotulo="Período"
                  valor={periodoDD}
                  onChange={setPeriodoDD}
                  opcoes={['2000–2010', '2010–2022', '2000–2022'].map((p) => ({ valor: p, rotulo: p }))}
                />
              }
            >
              <Tabela
                legenda="Diferença-em-diferenças descritiva"
                colunas={[
                  { id: 'indicador', rotulo: 'Indicador' },
                  { id: 'p', rotulo: 'vs Parauapebas', num: true, fmt: (i: { indicador: string }) => celulaDD(ddLinhas.find((d) => d.indicador === i.indicador && d.comparacao === 'parauapebas_municipio')) },
                  { id: 'pa', rotulo: 'vs Pará', num: true, fmt: (i: { indicador: string }) => celulaDD(ddLinhas.find((d) => d.indicador === i.indicador && d.comparacao === 'pa')) },
                ]}
                linhas={ddInd.map((indicador) => ({ indicador }))}
              />
              <p className="nota-miuda">* significativo a 95 %. Erro-padrão entre parênteses.</p>
            </Figura>
          </div>
        </div>
      </section>
    </div>
  )
}

function celulaDD(d: DifDif | undefined) {
  if (!d) return '—'
  const casas = Math.abs(d.dif_em_dif) >= 100 ? 0 : 1
  return (
    <span title={`Canaã ${fmtNum(d.delta_canaa, 1)} · comparador ${fmtNum(d.delta_comparacao, 1)}`}>
      {d.dif_em_dif > 0 ? '+' : d.dif_em_dif < 0 ? '−' : ''}
      {fmtNum(Math.abs(d.dif_em_dif), casas)} <span className="nota-miuda">({fmtNum(d.ep_dif_em_dif, casas)})</span>
      {d.significativo_95 ? '*' : ''}
    </span>
  )
}
