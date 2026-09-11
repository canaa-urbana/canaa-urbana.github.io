// Aba "Migração": status migratório de data fixa, origens, coortes de chegada, seletividade
// migrante × não migrante, condições domiciliares e cadeia da mineração. Lê só web/public/data.
import { useState } from 'react'
import { Secao, Figura, Kpi, Segmentado, Selecao, Termo, Precisao, Esqueleto, Erro, type Coluna } from '../components/ui'
import Chart from '../components/Chart'
import { useTema } from '../lib/theme'
import { useEstimativas, useAnalise, useJSON, type Estimativa, type Classe } from '../lib/data'
import { useRotulos, rotulo } from '../lib/rotulos'
import { baseOption, eixoValor, decalPrecisao, marcosTempo } from '../lib/charts'
import { fmtNum, fmtPct, fmtReais, TRACO } from '../lib/format'
import { busca, ic95, censoCor, corCategoriaFixa, ordenarCategorias } from '../components/censos/estimativas'
import { serieDotIC, serieLinhaConectora } from '../components/censos/graficos'
import { FlowMap, type FluxoUF } from '../components/migracao/FlowMap'
import '../styles/censos-migracao.css'

type Geografia = 'canaa_sede' | 'canaa_municipio' | 'parauapebas_municipio' | 'pa'

const GEOGRAFIAS: { valor: Geografia; rotulo: string }[] = [
  { valor: 'canaa_sede', rotulo: 'Canaã (sede)' },
  { valor: 'canaa_municipio', rotulo: 'Canaã (município)' },
  { valor: 'parauapebas_municipio', rotulo: 'Parauapebas' },
  { valor: 'pa', rotulo: 'Pará' },
]

const CENSOS_MIG = [2000, 2010, 2022]

const TIPO_MIG_ORDEM = ['nao_migrante', 'intraestadual', 'interestadual', 'internacional', 'outros:interestadual+internacional']
// Status migratório: mapa fixo categoria → índice de viz.cat (internacional fica em cat[4], não
// cat[3], para reservar essa posição — fusões e categorias fora do mapa usam viz.contexto+decal).
const TIPO_MIG_COR: Record<string, number> = {
  nao_migrante: 0,
  intraestadual: 1,
  interestadual: 2,
  internacional: 4,
}
// 2017–2022: cohort do Censo 2022 (25.100 pessoas no município) cobre jan/2017 a 31/jul/2022 =
// 5,6 anos (jan/2017 a jul/2022; mesma duração usada na E5 — 40_analise_artigo.py) — não 6 anos cheios.
const ANOS_CICLO_2017_2022 = 5.6

interface PerfilRow {
  geografia: string
  censo: number
  universo: string
  dimensao: string
  categoria: string
  rotulo: string
  p_migrante: number | null
  ep_migrante: number | null
  classe_migrante: Classe | null
  p_nao_migrante: number | null
  ep_nao_migrante: number | null
  classe_nao_migrante: Classe | null
  razao_seletividade: number | null
  ep_razao: number | null
  diferenca_pp: number | null
  ep_diferenca: number | null
  significativo_95: boolean | null
}
interface CoorteAnualRow { censo: number; ano_chegada: string; valor: number; ep: number; cv: number; classe: Classe; n_faixa: string; ano_num: number | null }
interface CoorteRow { geografia: string; censo: number; estatistica: string; periodo: string; rotulo: string; valor: number; ep: number; cv: number; classe: Classe; n_faixa: string }
interface CondDomRow { geografia: string; censo: number; grupo: string; dimensao: string; categoria: string; rotulo: string; valor: number; ep: number; cv: number; classe: Classe; n_faixa: string }
interface CadeiaRow {
  geografia: string; censo: number; elo: string; rotulo: string
  p_migrante: number | null; ep_migrante: number | null; classe_migrante: Classe | null
  p_nao_migrante: number | null; ep_nao_migrante: number | null; classe_nao_migrante: Classe | null
  razao_seletividade: number | null; ep_razao: number | null; significativo_95: boolean | null
}
interface ResumoAnalise { chegados_2022_total: number; chegados_2022_pos_2013_pct: number }

export default function Migracao() {
  const { viz } = useTema()
  const rRotulos = useRotulos()
  const rEst = useEstimativas()
  const rPerfil = useAnalise<PerfilRow>('perfil_migrantes')
  const rCoorteAnual = useAnalise<CoorteAnualRow>('coortes_chegada_anual')
  const rCoorte = useAnalise<CoorteRow>('coortes_chegada')
  const rCondDom = useAnalise<CondDomRow>('condicoes_domiciliares')
  const rCadeia = useAnalise<CadeiaRow>('cadeia_mineral_migrantes')
  const rResumo = useJSON<ResumoAnalise>('painel/resumo_analise.json')

  const rs = [rRotulos, rEst, rPerfil, rCoorteAnual, rCoorte, rCondDom, rCadeia, rResumo]
  const carregando = rs.some((r) => r.loading)
  const erro = rs.find((r) => r.error)?.error

  if (erro) return <div className="pagina"><Erro erro={erro} /></div>
  if (carregando || !rRotulos.data || !rEst.data || !rPerfil.data || !rCoorteAnual.data || !rCoorte.data || !rCondDom.data || !rCadeia.data || !rResumo.data) {
    return <div className="pagina"><Esqueleto altura={600} /></div>
  }

  return (
    <MigracaoConteudo
      viz={viz}
      R={rRotulos.data}
      linhas={rEst.data}
      perfil={rPerfil.data}
      coorteAnual={rCoorteAnual.data}
      coorte={rCoorte.data}
      condDom={rCondDom.data}
      cadeia={rCadeia.data}
      resumo={rResumo.data}
    />
  )
}

// -----------------------------------------------------------------------------------------------

function MigracaoConteudo({
  viz, R, linhas, perfil, coorteAnual, coorte, condDom, cadeia, resumo,
}: {
  viz: ReturnType<typeof useTema>['viz']
  R: NonNullable<ReturnType<typeof useRotulos>['data']>
  linhas: Estimativa[]
  perfil: PerfilRow[]
  coorteAnual: CoorteAnualRow[]
  coorte: CoorteRow[]
  condDom: CondDomRow[]
  cadeia: CadeiaRow[]
  resumo: ResumoAnalise
}) {
  const migData2022 = busca(linhas, { censo: 2022, geografia: 'canaa_sede', universo: 'pessoas_5mais', estatistica: 'proporcao', dim1: 'migrante', cat1: 'migrante', dim2: null })[0]
  const ciclo2022 = coorte.find((c) => c.geografia === 'canaa_municipio' && c.censo === 2022 && c.periodo === '2017_2022')
  const ritmo = ciclo2022 ? ciclo2022.valor / ANOS_CICLO_2017_2022 : null
  const alugCom = condDom.find((c) => c.geografia === 'canaa_municipio' && c.censo === 2022 && c.grupo === 'com_migrante_recente' && c.dimensao === 'condicao_ocupacao' && c.categoria === 'alugado')
  const alugSem = condDom.find((c) => c.geografia === 'canaa_municipio' && c.censo === 2022 && c.grupo === 'sem_migrante_recente' && c.dimensao === 'condicao_ocupacao' && c.categoria === 'alugado')

  return (
    <div className="pagina">
      <Secao kicker="Migração" titulo="Seis em cada dez não naturais residentes em 2022 chegaram a Canaã depois de 2013, no ciclo do S11D">
        <p>
          A migração de <Termo id="data_fixa">data fixa</Termo> — quem morava em outro município cinco anos antes do
          censo — é o retrato mais direto de como os dois grandes projetos minerais, Sossego (2002–04) e S11D
          (2013–16), atraíram população. Os painéis abaixo cobrem o status migratório por censo e geografia, as
          origens declaradas, o ritmo de chegada ano a ano, o perfil de quem migra frente a quem já morava no
          município, as condições de moradia e a inserção na cadeia da mineração.
        </p>
      </Secao>

      <div className="kpis kpis-fluxo">
        <Kpi rotulo="Migrantes de data fixa (2022, sede)" valor={fmtPct(migData2022?.valor ?? null, 1)} nota={<Precisao classe={migData2022?.classe} cv={migData2022?.cv} />} />
        <Kpi rotulo="Chegados desde 2013 (% dos não naturais)" valor={fmtPct(resumo.chegados_2022_pos_2013_pct, 0)} nota={`de ${fmtNum(resumo.chegados_2022_total)} pessoas chegadas`} />
        <Kpi rotulo="Ritmo de chegada 2017–22" valor={fmtNum(ritmo, 0)} unidade="pessoas/ano" nota="jan/2017–jul/2022, ciclo de operação do S11D" />
        <Kpi
          rotulo="Alugado: domicílio com migrante recente"
          valor={fmtPct(alugCom?.valor ?? null, 0)}
          nota={`vs. ${fmtPct(alugSem?.valor ?? null, 0)} nos demais domicílios (2022, município)`}
        />
      </div>

      <div className="bloco">
        <PainelStatusMigratorio viz={viz} R={R} linhas={linhas} />
      </div>

      <div className="bloco">
        <h3>Origens</h3>
        <PainelOrigens R={R} linhas={linhas} />
      </div>

      <div className="bloco">
        <h3>Coortes de chegada</h3>
        <PainelCoortes viz={viz} coorteAnual={coorteAnual} coorte={coorte} R={R} />
      </div>

      <div className="bloco">
        <h3>Perfil: migrantes × não migrantes</h3>
        <PainelPerfil viz={viz} R={R} perfil={perfil} />
      </div>

      <div className="bloco">
        <h3>Condições domiciliares</h3>
        <PainelCondicoes viz={viz} condDom={condDom} />
      </div>

      <div className="bloco">
        <h3>Cadeia da mineração</h3>
        <PainelCadeia viz={viz} cadeia={cadeia} />
      </div>

      <div className="aviso-metodo aviso">
        <p>
          Estimativas amostrais com bootstrap de domicílios (B = 200 réplicas); <Termo id="cv">CV</Termo> e classe de
          precisão em toda linha. Categorias suprimidas pelo controle de revelação (R1–R8) aparecem fundidas como
          "Outros (…)"; o Censo 2022 é de acesso controlado — só agregados aprovados chegam a este painel.
        </p>
      </div>
    </div>
  )
}

// --------------------------------------------------------------------------- (a) status migratório

function PainelStatusMigratorio({ viz, R, linhas }: { viz: ReturnType<typeof useTema>['viz']; R: ReturnType<typeof useRotulos>['data']; linhas: Estimativa[] }) {
  const [geo, setGeo] = useState<Geografia>('canaa_municipio')
  if (!R) return null

  const censosMostrados = [1991, ...CENSOS_MIG]
  const porCenso = censosMostrados.map((censo) => {
    const geografia = censo === 1991 ? 'parauapebas_municipio' : geo
    const rows = busca(linhas, { censo, geografia, universo: 'pessoas_5mais', estatistica: 'proporcao', dim1: 'tipo_mig_5anos', dim2: null })
    return { censo, geografia, rows }
  })
  const categoriasUniao = Array.from(new Set(porCenso.flatMap((l) => l.rows.map((r) => r.cat1!))))
  const ordenadas = ordenarCategorias(R.categorias, [...TIPO_MIG_ORDEM.filter((c) => categoriasUniao.includes(c)), ...categoriasUniao.filter((c) => !TIPO_MIG_ORDEM.includes(c))])

  const colunas: Coluna<{ censo: number; cat: string; valor: number | null; cv: number | null; classe: Classe | null }>[] = [
    { id: 'censo', rotulo: 'Censo' },
    { id: 'cat', rotulo: 'Status migratório', fmt: (l) => rotulo(R, l.cat, 'tipo_mig_5anos') },
    { id: 'valor', rotulo: '%', num: true, fmt: (l) => fmtPct(l.valor) },
    { id: 'cv', rotulo: 'CV', num: true, fmt: (l) => (l.cv !== null ? fmtPct(l.cv) : TRACO) },
  ]
  const linhasTabela = porCenso.flatMap((l) => l.rows.map((r) => ({ censo: l.censo, cat: r.cat1!, valor: r.valor, cv: r.cv, classe: r.classe })))

  return (
    <Figura
      kicker="Status migratório de data fixa"
      titulo="A parcela de migrantes recentes dobra entre 2000 e 2010 e segue perto de um quarto da população em 2022"
      subtitulo="% da população de 5 anos ou mais, por status migratório de data fixa (5 anos antes do censo). Canaã (município): 16,1% em 2000 → 32,5% em 2010 (pico) → 27,8% em 2022."
      fonte="IBGE, Censos 1991–2022 — microdados da amostra; estimativas próprias aprovadas pelo controle de revelação."
      controles={<Segmentado rotulo="Geografia" valor={geo} onChange={setGeo} opcoes={GEOGRAFIAS} />}
      notas={<p className="nota-miuda">1991 é sempre Parauapebas (inclui o atual Canaã), já que o município ainda não existia.</p>}
      tabela={{ colunas, linhas: linhasTabela }}
    >
      <Chart
        height={230}
        ariaLabel="Barras 100% empilhadas do status migratório de data fixa por censo."
        option={baseOption(viz, {
          grid: { left: 8, right: 8, top: 64, bottom: 24, containLabel: true },
          legend: { top: 0, left: 0 },
          xAxis: eixoValor(viz, { max: 100, axisLabel: { formatter: (v: number) => fmtNum(v, 0) + '%' } }),
          yAxis: {
            type: 'category',
            data: porCenso.map((l) => (l.censo === 1991 ? '1991 (Parauapebas)' : String(l.censo))),
            axisLine: { show: false },
            axisTick: { show: false },
          },
          tooltip: {
            trigger: 'item',
            formatter: (p: { seriesName: string; value: number; dataIndex: number; marker: string }) => {
              const l = porCenso[p.dataIndex]
              const r = l.rows.find((x) => rotulo(R, x.cat1, 'tipo_mig_5anos') === p.seriesName)
              return `${p.marker}${p.seriesName}<br/>${fmtPct(p.value)}${r ? ' · CV ' + fmtNum(r.cv, 1) + '% (' + r.classe + ')' : ''}`
            },
          },
          series: ordenadas.map((cat) => ({
            name: rotulo(R, cat, 'tipo_mig_5anos'),
            type: 'bar',
            stack: 'total',
            barMaxWidth: 34,
            data: porCenso.map((l) => l.rows.find((r) => r.cat1 === cat)?.valor ?? 0),
            itemStyle: corCategoriaFixa(cat, TIPO_MIG_COR, viz),
          })),
        })}
      />
    </Figura>
  )
}

// --------------------------------------------------------------------------- (b) origens

function PainelOrigens({ R, linhas }: { R: ReturnType<typeof useRotulos>['data']; linhas: Estimativa[] }) {
  const [censo, setCenso] = useState(2022)
  if (!R) return null
  const rows = busca(linhas, { censo, geografia: 'canaa_municipio', universo: 'migrantes_internos', estatistica: 'proporcao', dim1: 'origem_uf', dim2: null })
  // contagem ponderada da mesma célula, para o tooltip do mapa mostrar volume além da participação
  const contagens = new Map(
    busca(linhas, { censo, geografia: 'canaa_municipio', universo: 'migrantes_internos', estatistica: 'contagem', dim1: 'origem_uf', dim2: null }).map(
      (r) => [r.cat1!, r.valor],
    ),
  )
  const publicadas: FluxoUF[] = rows
    .filter((r) => r.cat1 && !r.cat1.startsWith('outros:'))
    .map((r) => ({
      uf: R.ufs[r.cat1!] ?? r.cat1!,
      valor: r.valor ?? 0,
      cv: r.cv,
      classe: r.classe,
      pessoas: contagens.get(r.cat1!) ?? null,
    }))
    .sort((a, b) => b.valor - a.valor)
  const fundidas = rows.filter((r) => r.cat1?.startsWith('outros:'))

  const colunas: Coluna<Estimativa>[] = [
    { id: 'cat1', rotulo: 'Origem (UF)', fmt: (l) => rotulo(R, l.cat1, 'origem_uf') },
    { id: 'valor', rotulo: '%', num: true, fmt: (l) => fmtPct(l.valor) },
    { id: 'ic', rotulo: 'IC 95%', num: true, fmt: (l) => { const ic = ic95(l.valor, l.ep); return ic ? `${fmtPct(ic[0])} – ${fmtPct(ic[1])}` : TRACO } },
    { id: 'cv', rotulo: 'CV', num: true, fmt: (l) => fmtPct(l.cv) },
    { id: 'classe', rotulo: 'Precisão', fmt: (l) => (l.classe && l.classe !== 'boa' ? <Precisao classe={l.classe} cv={l.cv} /> : 'boa') },
    { id: 'n_faixa', rotulo: 'n (faixa)' },
  ]

  return (
    <Figura
      kicker="Origens declaradas"
      titulo="Pará (migração intraestadual) e Maranhão concentram a maior parte das origens dos migrantes internos"
      subtitulo="% dos migrantes internos (residência anterior no Brasil), por UF de origem. Espessura do arco ∝ estimativa; só células publicadas pelo controle de revelação são desenhadas."
      fonte="IBGE, Censos 2000–2022 — microdados da amostra; estimativas próprias aprovadas pelo controle de revelação. Coordenadas das capitais estaduais: IBGE (proxy do centroide da UF)."
      controles={<Selecao rotulo="Censo" valor={String(censo)} onChange={(v) => setCenso(Number(v))} opcoes={CENSOS_MIG.map((c) => ({ valor: String(c), rotulo: String(c) }))} />}
      notas={fundidas.length > 0 ? <p className="nota-miuda">Fundidas pelo sigilo: {fundidas.map((f) => rotulo(R, f.cat1, 'origem_uf')).join('; ')}.</p> : undefined}
      tabela={{ colunas, linhas: rows }}
    >
      <FlowMap dados={publicadas} />
    </Figura>
  )
}

// --------------------------------------------------------------------------- (c) coortes de chegada

function PainelCoortes({ viz, coorteAnual, coorte, R }: { viz: ReturnType<typeof useTema>['viz']; coorteAnual: CoorteAnualRow[]; coorte: CoorteRow[]; R: ReturnType<typeof useRotulos>['data'] }) {
  if (!R) return null
  const anual = coorteAnual.filter((r) => r.censo === 2022 && r.ano_num !== null).sort((a, b) => a.ano_num! - b.ano_num!)
  const janelas: [number, number, string][] = R.janelas_obras
  const marcos = R.marcos.filter((m) => m.tipo === 'mineral' && m.inicio === m.fim).map((m) => ({ ano: m.inicio, rotulo: m.rotulo }))

  const porCiclo = coorte.filter((r) => r.geografia === 'canaa_municipio' && r.estatistica === 'contagem')
  const ciclos = Object.keys(R.ciclos)
  const censosCiclo = CENSOS_MIG
  const dominioAnos: [number, number] = anual.length ? [anual[0].ano_num!, anual[anual.length - 1].ano_num!] : [1990, 2022]

  const colunasAnual: Coluna<CoorteAnualRow>[] = [
    { id: 'ano_chegada', rotulo: 'Ano de chegada' },
    { id: 'valor', rotulo: 'Pessoas (arred.)', num: true, fmt: (l) => fmtNum(l.valor) },
    { id: 'cv', rotulo: 'CV', num: true, fmt: (l) => fmtPct(l.cv) },
    { id: 'classe', rotulo: 'Precisão', fmt: (l) => (l.classe !== 'boa' ? <Precisao classe={l.classe} cv={l.cv} /> : 'boa') },
  ]

  return (
    <>
      <Figura
        kicker="Ano a ano"
        titulo="As chegadas sobreviventes até 2022 sobem de ~250/ano no assentamento para 4.482/ano depois de 2016"
        subtitulo="Pessoas chegadas a Canaã dos Carajás e ainda residentes em 2022, por ano de chegada (município). Janelas sombreadas = obras do Sossego e do S11D."
        fonte="IBGE, Censo 2022 — microdados da amostra; estimativas próprias aprovadas pelo controle de revelação."
        notas={<p className="nota-miuda">Anos anteriores a 2000 com baixa contagem foram fundidos pelo controle de revelação e não aparecem no gráfico (só na tabela).</p>}
        tabela={{ colunas: colunasAnual, linhas: anual }}
      >
        <Chart
          height={260}
          ariaLabel="Barras de pessoas chegadas por ano, ainda residentes em 2022, com janelas de obras do Sossego e do S11D sombreadas."
          option={baseOption(viz, {
            legend: { show: false },
            grid: { left: 8, right: 16, top: 24, bottom: 24, containLabel: true },
            xAxis: { type: 'category', data: anual.map((r) => String(r.ano_num)), axisLine: { lineStyle: { color: viz.filete } }, axisTick: { show: false }, axisLabel: { color: viz.texto3, fontSize: 10, interval: 2 } },
            yAxis: eixoValor(viz),
            tooltip: {
              trigger: 'axis',
              formatter: (ps: { dataIndex: number }[]) => {
                const r = anual[ps[0].dataIndex]
                return `${r.ano_chegada}<br/>${fmtNum(r.valor)} pessoas · CV ${fmtNum(r.cv, 1)}% (${r.classe})`
              },
            },
            series: [
              {
                type: 'bar',
                data: anual.map((r) => ({ value: r.valor, itemStyle: { color: censoCor(viz, 2022), decal: decalPrecisao(r.classe, viz) } })),
                barMaxWidth: 10,
                markArea: marcosTempo(viz, janelas, marcos, true, dominioAnos).markArea,
                markLine: marcosTempo(viz, janelas, marcos, true, dominioAnos).markLine,
              },
            ],
          })}
        />
      </Figura>

      <Figura
        kicker="Por ciclo"
        titulo="Comparado entre censos, o retrato dos ciclos de chegada muda: cada censo só enxerga quem sobreviveu até ele"
        subtitulo="Pessoas chegadas ao município (contagem), por ciclo histórico, segundo o censo em que foram captadas."
        fonte="IBGE, Censos 2000–2022 — microdados da amostra; estimativas próprias aprovadas pelo controle de revelação."
      >
        <Chart
          height={280}
          ariaLabel="Barras agrupadas por censo, de pessoas chegadas em cada ciclo histórico."
          option={baseOption(viz, {
            grid: { left: 8, right: 16, top: 64, bottom: 60, containLabel: true },
            legend: { top: 0, left: 0 },
            xAxis: {
              type: 'category',
              data: ciclos.map((c) => R.ciclos[c]),
              axisLine: { lineStyle: { color: viz.filete } },
              axisTick: { show: false },
              axisLabel: { color: viz.texto3, fontSize: 9, rotate: 28, interval: 0 },
            },
            yAxis: eixoValor(viz, { name: 'pessoas (arred.)' }),
            tooltip: {
              trigger: 'item',
              formatter: (p: { seriesName: string; dataIndex: number; value: number }) => {
                const r = porCiclo.find((x) => x.censo === Number(p.seriesName) && x.periodo === ciclos[p.dataIndex])
                return `Censo ${p.seriesName} · ${R.ciclos[ciclos[p.dataIndex]]}<br/>${fmtNum(p.value)} pessoas${r ? ' · CV ' + fmtNum(r.cv, 1) + '% (' + r.classe + ')' : ''}`
              },
            },
            series: censosCiclo.map((c) => ({
              name: String(c),
              type: 'bar',
              barMaxWidth: 18,
              data: ciclos.map((ci) => {
                const r = porCiclo.find((x) => x.censo === c && x.periodo === ci)
                return { value: r?.valor ?? 0, itemStyle: { decal: decalPrecisao(r?.classe, viz) } }
              }),
              itemStyle: { color: censoCor(viz, c) },
            })),
          })}
        />
      </Figura>
    </>
  )
}

// --------------------------------------------------------------------------- (d) perfil migrante × não migrante

const DIMENSOES_PERFIL: { id: string; rotulo: string; tipo: 'pct' | 'reais' | 'anos' }[] = [
  { id: 'sexo', rotulo: 'Sexo', tipo: 'pct' },
  { id: 'media_idade', rotulo: 'Idade', tipo: 'anos' },
  { id: 'nivel_instrucao', rotulo: 'Instrução (25+)', tipo: 'pct' },
  { id: 'posicao', rotulo: 'Posição na ocupação', tipo: 'pct' },
  { id: 'formal', rotulo: 'Vínculo formal', tipo: 'pct' },
  { id: 'setor', rotulo: 'Setor de atividade', tipo: 'pct' },
  { id: 'media_renda_trabalho_r2022', rotulo: 'Renda do trabalho', tipo: 'reais' },
]

function PainelPerfil({ viz, R, perfil }: { viz: ReturnType<typeof useTema>['viz']; R: ReturnType<typeof useRotulos>['data']; perfil: PerfilRow[] }) {
  const [censo, setCenso] = useState(2022)
  const [geo, setGeo] = useState<Exclude<Geografia, 'pa'> | 'pa'>('canaa_municipio')
  const [dim, setDim] = useState('nivel_instrucao')
  if (!R) return null

  const linhasBrutas = perfil.filter((r) => r.censo === censo && r.geografia === geo && r.dimensao === dim)
  // ordem natural das categorias = ordem de inserção em rotulos.json `categorias` (ex.: sem
  // instrução → superior); para "setor" usa `setores_ordem`; fusões sempre por último.
  const catsOrdenadas =
    dim === 'setor' && R.setores_ordem?.length
      ? [...R.setores_ordem.filter((c) => linhasBrutas.some((r) => r.categoria === c)), ...linhasBrutas.map((r) => r.categoria).filter((c) => !R.setores_ordem.includes(c))]
      : ordenarCategorias(R.categorias, linhasBrutas.map((r) => r.categoria))
  const linhas = catsOrdenadas.map((c) => linhasBrutas.find((r) => r.categoria === c)).filter((r): r is PerfilRow => !!r)
  const def = DIMENSOES_PERFIL.find((d) => d.id === dim)!
  const fmtV = def.tipo === 'pct' ? (v: number | null) => fmtPct(v) : def.tipo === 'reais' ? (v: number | null) => fmtReais(v) : (v: number | null) => fmtNum(v, 1) + ' anos'

  const colunas: Coluna<PerfilRow>[] = [
    { id: 'rotulo', rotulo: 'Categoria' },
    { id: 'p_migrante', rotulo: 'Migrantes', num: true, fmt: (l) => fmtV(l.p_migrante) },
    { id: 'p_nao_migrante', rotulo: 'Não migrantes', num: true, fmt: (l) => fmtV(l.p_nao_migrante) },
    { id: 'diferenca_pp', rotulo: 'Diferença', num: true, fmt: (l) => (l.diferenca_pp !== null ? fmtNum(l.diferenca_pp, 1) : TRACO) },
    { id: 'razao_seletividade', rotulo: 'Razão de seletividade', num: true, fmt: (l) => (l.razao_seletividade !== null ? fmtNum(l.razao_seletividade, 2) : TRACO) },
    { id: 'significativo_95', rotulo: 'Signif. 95%', fmt: (l) => (l.significativo_95 === null ? TRACO : l.significativo_95 ? 'sim' : 'não') },
  ]

  return (
    <Figura
      kicker="Seletividade migratória"
      titulo="Migrantes recentes são mais jovens, mais escolarizados e mais formalizados do que quem já morava no município"
      subtitulo="Dumbbell: migrantes (terracota) × não migrantes (cinza-azulado), com IC 95%. Razão de seletividade = migrantes ÷ não migrantes."
      fonte="IBGE, Censos 1991–2022 — microdados da amostra; estimativas próprias aprovadas pelo controle de revelação."
      controles={
        <>
          <Selecao rotulo="Censo" valor={String(censo)} onChange={(v) => setCenso(Number(v))} opcoes={[1991, 2000, 2010, 2022].map((c) => ({ valor: String(c), rotulo: String(c) }))} />
          <Selecao rotulo="Geografia" valor={geo} onChange={(v) => setGeo(v as typeof geo)} opcoes={GEOGRAFIAS.filter((g) => g.valor !== 'parauapebas_municipio' || censo === 1991)} />
          <Selecao rotulo="Dimensão" valor={dim} onChange={setDim} opcoes={DIMENSOES_PERFIL.map((d) => ({ valor: d.id, rotulo: d.rotulo }))} />
        </>
      }
      tabela={{ colunas, linhas }}
    >
      {linhas.length === 0 ? (
        <p className="nota-miuda">Não disponível para esta combinação de censo, geografia e dimensão (suprimida pelo controle de revelação ou variável não coletada).</p>
      ) : (
        <Chart
          height={Math.max(160, linhas.length * 34 + 60)}
          ariaLabel="Dumbbell comparando migrantes e não migrantes na dimensão selecionada, com intervalo de confiança."
          option={baseOption(viz, {
            legend: { show: false },
            grid: { left: 8, right: 16, top: 8, bottom: 24, containLabel: true },
            xAxis: eixoValor(viz, def.tipo === 'pct' ? { max: 100, axisLabel: { formatter: (v: number) => fmtNum(v, 0) + '%' } } : {}),
            yAxis: { type: 'category', data: linhas.map((l) => l.rotulo), inverse: true, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: viz.texto3, fontSize: 11 } },
            tooltip: {
              trigger: 'item',
              formatter: (p: { seriesName: string; value: unknown[] }) => {
                const catIdx = (p.value as number[])[0]
                const l = linhas[catIdx]
                return `${l.rotulo}<br/>Migrantes: ${fmtV(l.p_migrante)} · Não migrantes: ${fmtV(l.p_nao_migrante)}<br/>Razão: ${l.razao_seletividade !== null ? fmtNum(l.razao_seletividade, 2) : TRACO} ${l.significativo_95 ? '(signif. 95%)' : ''}`
              },
            },
            series: [
              serieLinhaConectora(linhas.map((l, i) => ({ cat: i, a: l.p_nao_migrante, b: l.p_migrante })), viz.texto3),
              serieDotIC('Não migrantes', viz.cat[0], 0, 2, linhas.map((l, i) => ({ cat: i, valor: l.p_nao_migrante, baixo: ic95(l.p_nao_migrante, l.ep_nao_migrante)?.[0], alto: ic95(l.p_nao_migrante, l.ep_nao_migrante)?.[1] }))),
              serieDotIC('Migrantes', viz.enfase, 1, 2, linhas.map((l, i) => ({ cat: i, valor: l.p_migrante, baixo: ic95(l.p_migrante, l.ep_migrante)?.[0], alto: ic95(l.p_migrante, l.ep_migrante)?.[1] }))),
            ],
          })}
        />
      )}
      <div className="legenda-dot">
        <span className="legenda-dot__item"><span className="legenda-dot__marca" style={{ background: viz.enfase }} />Migrantes de data fixa</span>
        <span className="legenda-dot__item"><span className="legenda-dot__marca" style={{ background: viz.cat[0] }} />Não migrantes</span>
      </div>
    </Figura>
  )
}

// --------------------------------------------------------------------------- (e) condições domiciliares

const INDICADORES_COND: { id: string; rotuloTxt: string; dimensao: string; categoria: string }[] = [
  { id: 'alugado', rotuloTxt: 'Domicílio alugado', dimensao: 'condicao_ocupacao', categoria: 'alugado' },
  { id: 'proprio', rotuloTxt: 'Domicílio próprio', dimensao: 'condicao_ocupacao', categoria: 'proprio' },
  { id: 'densidade_alta', rotuloTxt: 'Mais de 3 moradores/dormitório', dimensao: 'densidade_faixa', categoria: 'mais_de_3' },
  { id: 'agua', rotuloTxt: 'Água da rede geral', dimensao: 'agua_rede', categoria: 'sim' },
  { id: 'esgoto', rotuloTxt: 'Esgoto adequado', dimensao: 'esgoto_adequado', categoria: 'sim' },
]

function PainelCondicoes({ viz, condDom }: { viz: ReturnType<typeof useTema>['viz']; condDom: CondDomRow[] }) {
  const grupos: { id: string; nome: string; cor: string }[] = [
    { id: 'com_migrante_recente', nome: 'Com migrante recente', cor: viz.enfase },
    { id: 'sem_migrante_recente', nome: 'Sem migrante recente', cor: viz.cat[0] },
  ]
  const linhas = condDom.filter((r) => r.censo === 2022 && r.geografia === 'canaa_municipio')
  const colunas: Coluna<{ indicador: string; grupo: string; valor: number | null; cv: number | null; classe: Classe | null }>[] = [
    { id: 'indicador', rotulo: 'Indicador', fmt: (l) => INDICADORES_COND.find((i) => i.id === l.indicador)?.rotuloTxt ?? l.indicador },
    { id: 'grupo', rotulo: 'Domicílio', fmt: (l) => grupos.find((g) => g.id === l.grupo)?.nome ?? l.grupo },
    { id: 'valor', rotulo: '%', num: true, fmt: (l) => fmtPct(l.valor) },
    { id: 'cv', rotulo: 'CV', num: true, fmt: (l) => fmtPct(l.cv) },
  ]
  const tabela = INDICADORES_COND.flatMap((ind) =>
    grupos.map((g) => {
      const r = linhas.find((x) => x.grupo === g.id && x.dimensao === ind.dimensao && x.categoria === ind.categoria)
      return { indicador: ind.id, grupo: g.id, valor: r?.valor ?? null, cv: r?.cv ?? null, classe: r?.classe ?? null }
    }),
  )

  return (
    <Figura
      kicker="Domicílios com e sem migrante recente"
      titulo="Metade dos domicílios com migrante recente é alugada, contra um em cinco nos demais"
      subtitulo="% dos domicílios (2022, município), por presença de morador migrante de data fixa. IC 95% nas hastes."
      fonte="IBGE, Censo 2022 — microdados da amostra; estimativas próprias aprovadas pelo controle de revelação."
      tabela={{ colunas, linhas: tabela }}
    >
      <Chart
        height={260}
        ariaLabel="Gráfico de pontos com IC comparando domicílios com e sem migrante recente em cinco indicadores."
        option={baseOption(viz, {
          legend: { show: false },
          grid: { left: 8, right: 16, top: 8, bottom: 24, containLabel: true },
          xAxis: eixoValor(viz, { max: 100, axisLabel: { formatter: (v: number) => fmtNum(v, 0) + '%' } }),
          yAxis: { type: 'category', data: INDICADORES_COND.map((i) => i.rotuloTxt), inverse: true, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: viz.texto3, fontSize: 11 } },
          tooltip: {
            trigger: 'item',
            formatter: (p: { seriesName: string; value: unknown[] }) => {
              const [catIdx, valor, baixo, alto] = p.value as number[]
              const ind = INDICADORES_COND[catIdx]
              return `${p.seriesName}<br/>${ind.rotuloTxt}: ${fmtPct(valor)} (IC ${fmtPct(baixo)} – ${fmtPct(alto)})`
            },
          },
          series: grupos.map((g, gi) =>
            serieDotIC(
              g.nome,
              g.cor,
              gi,
              grupos.length,
              INDICADORES_COND.map((ind, ci) => {
                const r = linhas.find((x) => x.grupo === g.id && x.dimensao === ind.dimensao && x.categoria === ind.categoria)
                const ic = r ? ic95(r.valor, r.ep) : null
                return { cat: ci, valor: r?.valor ?? null, baixo: ic?.[0] ?? null, alto: ic?.[1] ?? null }
              }),
            ),
          ),
        })}
      />
      <div className="legenda-dot">
        {grupos.map((g) => (
          <span key={g.id} className="legenda-dot__item"><span className="legenda-dot__marca" style={{ background: g.cor }} />{g.nome}</span>
        ))}
      </div>
    </Figura>
  )
}

// --------------------------------------------------------------------------- (f) cadeia da mineração

function PainelCadeia({ viz, cadeia }: { viz: ReturnType<typeof useTema>['viz']; cadeia: CadeiaRow[] }) {
  const censos = [2010, 2022]
  const linhas = censos.map((c) => cadeia.find((r) => r.censo === c && r.geografia === 'canaa_municipio' && r.elo === 'cadeia_ampliada')).filter((r): r is CadeiaRow => !!r)
  const colunas: Coluna<CadeiaRow>[] = [
    { id: 'censo', rotulo: 'Censo' },
    { id: 'p_migrante', rotulo: 'Migrantes na cadeia (%)', num: true, fmt: (l) => fmtPct(l.p_migrante) },
    { id: 'p_nao_migrante', rotulo: 'Não migrantes na cadeia (%)', num: true, fmt: (l) => fmtPct(l.p_nao_migrante) },
    { id: 'razao_seletividade', rotulo: 'Razão de seletividade', num: true, fmt: (l) => (l.razao_seletividade !== null ? fmtNum(l.razao_seletividade, 2) : TRACO) },
    { id: 'significativo_95', rotulo: 'Signif. 95%', fmt: (l) => (l.significativo_95 === null ? TRACO : l.significativo_95 ? 'sim' : 'não') },
  ]

  return (
    <Figura
      kicker="Cadeia da mineração (extrativa + construção + transformação)"
      titulo="Migrantes têm mais chance de estar na cadeia da mineração do que não migrantes, e a seletividade era maior em 2010"
      subtitulo="% dos ocupados na cadeia ampliada (seções B, F e C do CNAE-Dom), migrantes de data fixa × não migrantes, por censo (município). Barra de erro = IC 95%."
      fonte="IBGE, Censos 2010 e 2022 — microdados da amostra; estimativas próprias aprovadas pelo controle de revelação."
      notas={<p className="nota-miuda">Limite inferior: o CNAE-Dom não identifica fornecedores da mina em serviços e transporte, que também integram a cadeia mineral de forma não mensurável nesta base.</p>}
      tabela={{ colunas, linhas }}
    >
      <Chart
        height={220}
        ariaLabel="Dumbbell comparando migrantes e não migrantes na cadeia da mineração, 2010 e 2022, com IC."
        option={baseOption(viz, {
          legend: { show: false },
          grid: { left: 8, right: 16, top: 8, bottom: 24, containLabel: true },
          xAxis: eixoValor(viz, { max: 40, axisLabel: { formatter: (v: number) => fmtNum(v, 0) + '%' } }),
          yAxis: { type: 'category', data: linhas.map((l) => String(l.censo)), inverse: true, axisLine: { show: false }, axisTick: { show: false } },
          tooltip: {
            trigger: 'item',
            formatter: (p: { seriesName: string; value: unknown[] }) => {
              const catIdx = (p.value as number[])[0]
              const l = linhas[catIdx]
              return `${l.censo}<br/>Migrantes: ${fmtPct(l.p_migrante)} · Não migrantes: ${fmtPct(l.p_nao_migrante)}<br/>Razão: ${l.razao_seletividade !== null ? fmtNum(l.razao_seletividade, 2) : TRACO}`
            },
          },
          series: [
            serieLinhaConectora(linhas.map((l, i) => ({ cat: i, a: l.p_nao_migrante, b: l.p_migrante })), viz.texto3),
            serieDotIC('Não migrantes', viz.cat[0], 0, 2, linhas.map((l, i) => ({ cat: i, valor: l.p_nao_migrante, baixo: ic95(l.p_nao_migrante, l.ep_nao_migrante)?.[0], alto: ic95(l.p_nao_migrante, l.ep_nao_migrante)?.[1] }))),
            serieDotIC('Migrantes', viz.enfase, 1, 2, linhas.map((l, i) => ({ cat: i, valor: l.p_migrante, baixo: ic95(l.p_migrante, l.ep_migrante)?.[0], alto: ic95(l.p_migrante, l.ep_migrante)?.[1] }))),
          ],
        })}
      />
      <div className="legenda-dot">
        <span className="legenda-dot__item"><span className="legenda-dot__marca" style={{ background: viz.enfase }} />Migrantes de data fixa</span>
        <span className="legenda-dot__item"><span className="legenda-dot__marca" style={{ background: viz.cat[0] }} />Não migrantes</span>
      </div>
    </Figura>
  )
}
