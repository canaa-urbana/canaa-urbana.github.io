// Aba "Anos censitários": 1991 (Parauapebas, inclui o atual Canaã), 2000, 2010, 2022 lado a lado.
// Lê só web/public/data (estimativas da E2, análise da E5, estatísticas da mancha da E3c).
import { useMemo, useState } from 'react'
import { Secao, Figura, Segmentado, Termo, Precisao, Esqueleto, Erro, type Coluna } from '../components/ui'
import Chart from '../components/Chart'
import { useTema } from '../lib/theme'
import { useEstimativas, useAnalise, useJSON, type Estimativa, type Classe } from '../lib/data'
import { useRotulos, rotulo } from '../lib/rotulos'
import { baseOption, eixoValor, decalPrecisao } from '../lib/charts'
import { fmtNum, fmtPct, fmtHa, fmtReais, TRACO } from '../lib/format'
import { busca, ic95, chaveEtaria, censoCor, censoMarcador, corCategoriaFixa, corSequencial, ordenarCategorias } from '../components/censos/estimativas'
import { serieDotIC, decalFusao } from '../components/censos/graficos'
import { MiniMapaMancha } from '../components/censos/MiniMapaMancha'
import '../styles/censos-migracao.css'

type Escopo = 'sede' | 'municipio'

interface DefCenso {
  censo: number
  label: string
  labelCurto: string
  manchaArquivo: string
}

const CENSOS: DefCenso[] = [
  { censo: 1991, label: 'Parauapebas 1991 (inclui o atual Canaã)', labelCurto: '1991', manchaArquivo: 'geo/mancha/mancha_propria_1991.json' },
  { censo: 2000, label: '2000', labelCurto: '2000', manchaArquivo: 'geo/mancha/mancha_propria_2000.json' },
  { censo: 2010, label: '2010', labelCurto: '2010', manchaArquivo: 'geo/mancha/mancha_propria_2010.json' },
  { censo: 2022, label: '2022', labelCurto: '2022', manchaArquivo: 'geo/mancha/mancha_propria_2022.json' },
]

function geoPara(censo: number, escopo: Escopo): string {
  return (censo === 1991 ? 'parauapebas' : 'canaa') + '_' + escopo
}

interface EstatMancha {
  ano: number
  pop_sede: number | null
  area_sede_ajustada_ha: number | null
  densidade_ajustada_hab_ha: number | null
}
interface EstatManchaJSON {
  censos: EstatMancha[]
}
interface SeriePopRow {
  ano: number
  valor: number | null
  recorte: string
}
interface ResumoAnalise {
  mancha_1990_1991: { ano: number; area_sede_ha: number }[]
}

const SETORES_ORDEM_FALLBACK = [
  'agropecuaria', 'extrativa_mineral', 'transformacao', 'construcao', 'comercio', 'servicos', 'adm_publica_educacao_saude', 'domestico', 'outras_atividades',
]
// Ordinal (sem instrução → superior); "não determinado" e fusões ficam fora do mapa e caem em
// viz.contexto com textura (corCategoriaFixa/corSequencial não os cobre, então entram por último).
const NIVEL_INSTRUCAO_ORDEM = ['sem_instrucao_fund_incompleto', 'fund_completo_medio_incompleto', 'medio_completo_sup_incompleto', 'superior_completo']
// Posição na ocupação: mapa fixo categoria → índice de viz.cat (nunca por posição na lista).
const POSICAO_COR: Record<string, number> = {
  empregado_com_carteira: 0,
  empregado_sem_carteira: 1,
  militar_estatutario: 2,
  conta_propria: 3,
  empregador: 4,
  nao_remunerado: 5,
}
const POSICAO_ORDEM = ['empregado_com_carteira', 'empregado_sem_carteira', 'militar_estatutario', 'conta_propria', 'empregador', 'nao_remunerado']

export default function Censos() {
  const { viz } = useTema()
  const rRotulos = useRotulos()
  const rEst = useEstimativas()
  const rSeriePop = useAnalise<SeriePopRow>('serie_populacao')
  const rMancha = useJSON<EstatManchaJSON>('estatisticas_mancha.json')
  const rResumo = useJSON<ResumoAnalise>('painel/resumo_analise.json')
  const [escopo, setEscopo] = useState<Escopo>('municipio')

  const carregando = rRotulos.loading || rEst.loading || rSeriePop.loading || rMancha.loading || rResumo.loading
  const erro = rRotulos.error || rEst.error || rSeriePop.error || rMancha.error || rResumo.error

  if (erro) return <div className="pagina"><Erro erro={erro} /></div>
  if (carregando || !rRotulos.data || !rEst.data || !rSeriePop.data || !rMancha.data || !rResumo.data) {
    return <div className="pagina"><Esqueleto altura={600} /></div>
  }

  return (
    <CensosConteudo
      viz={viz}
      R={rRotulos.data}
      linhas={rEst.data}
      seriePop={rSeriePop.data}
      mancha={rMancha.data}
      resumo={rResumo.data}
      escopo={escopo}
      setEscopo={setEscopo}
    />
  )
}

// -----------------------------------------------------------------------------------------------

function CensosConteudo({
  viz,
  R,
  linhas,
  seriePop,
  mancha,
  resumo,
  escopo,
  setEscopo,
}: {
  viz: ReturnType<typeof useTema>['viz']
  R: NonNullable<ReturnType<typeof useRotulos>['data']>
  linhas: Estimativa[]
  seriePop: SeriePopRow[]
  mancha: EstatManchaJSON
  resumo: ResumoAnalise
  escopo: Escopo
  setEscopo: (e: Escopo) => void
}) {
  const popMun2000 = seriePop.find((r) => r.ano === 2000 && r.recorte === 'município')?.valor
  const popMun2022 = seriePop.find((r) => r.ano === 2022 && r.recorte === 'município')?.valor
  const popUrb2022 = seriePop.find((r) => r.ano === 2022 && r.recorte === 'urbana')?.valor
  const pctUrb2022 = popMun2022 && popUrb2022 ? (popUrb2022 / popMun2022) * 100 : null

  return (
    <div className="pagina">
      <Secao
        kicker="Anos censitários"
        titulo={`De ${fmtNum(popMun2000)} a ${fmtNum(popMun2022)} habitantes em 22 anos: de assentamento rural a cidade ${fmtPct(pctUrb2022, 0)} urbana`}
      >
        <p>
          Os quatro levantamentos amostrais do IBGE com informação comparável para o município — 1991 (
          <strong>Parauapebas</strong>, que incluía o atual território de Canaã, emancipado em 1994), 2000, 2010 e
          2022 — mostram a transição de um povoado agropecuário do assentamento GETAT/CEDERE&nbsp;II para uma cidade
          predominantemente urbana, moldada pelas obras dos projetos Sossego (2002–04) e S11D (2013–16). Os painéis
          abaixo comparam a <Termo id="sede">sede</Termo> e o município nos quatro censos, com <Termo id="cv">CV</Termo>{' '}
          e classe de precisão sempre visíveis nas estimativas amostrais.
        </p>
      </Secao>

      <div className="figura__controles" style={{ marginBottom: 16 }}>
        <Segmentado
          rotulo="Geografia"
          valor={escopo}
          onChange={setEscopo}
          opcoes={[
            { valor: 'sede', rotulo: 'Sede' },
            { valor: 'municipio', rotulo: 'Município' },
          ]}
        />
      </div>

      <div className="censos-grade4">
        {CENSOS.map((c, i) => (
          <ColunaCenso
            key={c.censo}
            def={c}
            escopo={escopo}
            seriePop={seriePop}
            mancha={mancha}
            resumo={resumo}
            manchaContexto2022={c.censo !== 2022 ? CENSOS[3].manchaArquivo : undefined}
            primeiraColuna={i === 0}
          />
        ))}
      </div>

      <div className="bloco">
        <h3>Pirâmides etárias</h3>
        <Piramides viz={viz} R={R} linhas={linhas} escopo={escopo} />
      </div>

      <div className="bloco">
        <h3>Escolaridade e renda</h3>
        <div className="grade">
          <div className="c-6"><PainelEscolaridade viz={viz} R={R} linhas={linhas} escopo={escopo} /></div>
          <div className="c-6"><PainelRenda viz={viz} R={R} linhas={linhas} escopo={escopo} /></div>
        </div>
      </div>

      <div className="bloco">
        <h3>Inserção ocupacional</h3>
        <div className="grade">
          <div className="c-7"><PainelSetor viz={viz} R={R} linhas={linhas} escopo={escopo} /></div>
          <div className="c-5"><PainelPosicao viz={viz} R={R} linhas={linhas} escopo={escopo} /></div>
        </div>
      </div>

      <div className="bloco">
        <h3>Condições domiciliares</h3>
        <PainelDomicilios viz={viz} R={R} linhas={linhas} escopo={escopo} />
      </div>

      <div className="aviso-metodo aviso">
        <p>
          Todas as proporções, médias e contagens vêm de estimativas amostrais (bootstrap de domicílios, B = 200
          réplicas), publicadas com erro-padrão, <Termo id="cv">CV</Termo> e classe de precisão (boa ≤ 15&nbsp;%;
          cautela 15–30&nbsp;%, marcada com *; baixa &gt; 30&nbsp;%, marcada com **). Os microdados do Censo 2022 são
          de acesso controlado: só agregados aprovados pelo controle de revelação (regras R1–R8) chegam a este painel.
          Categorias suprimidas por sigilo aparecem fundidas como "Outros (…)", sem redistribuição.
        </p>
      </div>
    </div>
  )
}

// --------------------------------------------------------------------------- coluna por censo

function ColunaCenso({
  def,
  seriePop,
  mancha,
  resumo,
  manchaContexto2022,
  primeiraColuna,
}: {
  def: DefCenso
  escopo: Escopo
  seriePop: SeriePopRow[]
  mancha: EstatManchaJSON
  resumo: ResumoAnalise
  manchaContexto2022?: string
  primeiraColuna: boolean
}) {
  const { viz } = useTema()
  const [contexto, setContexto] = useState<GeoJSON.FeatureCollection | undefined>(undefined)
  useMemo(() => {
    if (!manchaContexto2022) return
    import('../lib/data').then(({ loadJSON }) => loadJSON<GeoJSON.FeatureCollection>(manchaContexto2022).then(setContexto).catch(() => {}))
  }, [manchaContexto2022])
  const corTopo = { borderTop: `3px solid ${censoCor(viz, def.censo)}` }

  if (def.censo === 1991) {
    const popMun = seriePop.find((r) => r.ano === 1991)?.valor ?? 53335
    const areaSede1991 = resumo.mancha_1990_1991.find((r) => r.ano === 1991)?.area_sede_ha ?? null
    return (
      <div className="censo-coluna" style={corTopo}>
        <div className="censo-coluna__mapa">
          <MiniMapaMancha ano={1991} arquivo={def.manchaArquivo} contexto={contexto} titulo="1991" />
        </div>
        <p style={{ font: '600 13px var(--ard-serif)', margin: '0 0 6px' }}>{def.label}</p>
        <div className="censo-coluna__kpis">
          <div className="censo-coluna__kpi">
            <span className="censo-coluna__kpi-r">População (Parauapebas)</span>
            <span className="censo-coluna__kpi-v">{fmtNum(popMun)}</span>
          </div>
          <div className="censo-coluna__kpi">
            <span className="censo-coluna__kpi-r">Mancha da sede (mapeada)</span>
            <span className="censo-coluna__kpi-v">{fmtHa(areaSede1991)}</span>
          </div>
        </div>
        <p className="censo-coluna__nota">
          Canaã ainda não existia como município (emancipada em 1994); os valores são de Parauapebas, que incluía o
          atual território de Canaã. Não há série oficial urbana/rural separada nem área ajustada pela acurácia para
          1991 neste projeto — a área acima é a mancha mapeada (Landsat/MSS), sem correção de comissão/omissão.
        </p>
      </div>
    )
  }

  const linhaMancha = mancha.censos.find((m) => m.ano === def.censo)
  const popMun = seriePop.find((r) => r.ano === def.censo && r.recorte === 'município')?.valor ?? null
  const popUrb = seriePop.find((r) => r.ano === def.censo && r.recorte === 'urbana')?.valor ?? null
  const pctUrb = popMun && popUrb ? (popUrb / popMun) * 100 : null

  return (
    <div className="censo-coluna" style={corTopo}>
      <div className="censo-coluna__mapa">
        <MiniMapaMancha ano={def.censo} arquivo={def.manchaArquivo} contexto={contexto} titulo={def.labelCurto} />
      </div>
      <p style={{ font: '600 13px var(--ard-serif)', margin: '0 0 6px' }}>{def.label}</p>
      <div className="censo-coluna__kpis">
        <div className="censo-coluna__kpi">
          <span className="censo-coluna__kpi-r">População (município)</span>
          <span className="censo-coluna__kpi-v">{fmtNum(popMun)}</span>
        </div>
        <div className="censo-coluna__kpi">
          <span className="censo-coluna__kpi-r">População urbana</span>
          <span className="censo-coluna__kpi-v">{fmtNum(popUrb)}</span>
        </div>
        <div className="censo-coluna__kpi">
          <span className="censo-coluna__kpi-r">% urbana</span>
          <span className="censo-coluna__kpi-v">{fmtPct(pctUrb, 0)}</span>
        </div>
        <div className="censo-coluna__kpi">
          <span className="censo-coluna__kpi-r">Área da sede (ajustada)</span>
          <span className="censo-coluna__kpi-v">{fmtHa(linhaMancha?.area_sede_ajustada_ha ?? null)}</span>
        </div>
        <div className="censo-coluna__kpi">
          <span className="censo-coluna__kpi-r">Densidade (ajustada)</span>
          <span className="censo-coluna__kpi-v">
            {linhaMancha?.densidade_ajustada_hab_ha ? fmtNum(linhaMancha.densidade_ajustada_hab_ha, 1) + ' hab/ha' : TRACO}
          </span>
        </div>
      </div>
      {primeiraColuna && <p className="censo-coluna__nota">Contorno fino = extensão da mancha em 2022 (referência de comparação).</p>}
    </div>
  )
}

// --------------------------------------------------------------------------- pirâmides etárias

interface PontoPiramide {
  cat2: string
  valor: number | null
  cv: number | null
  classe: Classe | null
}

/** Grade fixa de faixas das pirâmides — a mesma da figura 7 do artigo, para que os quatro
 *  painéis tenham as mesmas linhas, a mesma coluna de rótulos e o zero na mesma posição. */
const FAIXAS_PIRAMIDE = [
  '00_04', '05_09', '10_14', '15_19', '20_24', '25_29', '30_34', '35_39', '40_44',
  '45_49', '50_54', '55_59', '60_64', '65_69', '70_74', '75_79', '80_mais',
]

/** Faixa em que a categoria assenta na grade: a primeira que a compõe (fusões do gate incluídas). */
function faixaBase(cat: string): string {
  return cat.startsWith('outros:') ? cat.slice(7).split('+')[0] : cat
}

function extraiPiramide(linhas: Estimativa[], censo: number, geografia: string, sexo: 'M' | 'F'): PontoPiramide[] {
  const rows = busca(linhas, { censo, geografia, universo: 'pessoas', estatistica: 'proporcao', dim1: 'sexo', cat1: sexo, dim2: 'faixa_etaria' })
  return rows
    .map((r) => ({ cat2: r.cat2!, valor: r.valor, cv: r.cv, classe: r.classe }))
    .sort((a, b) => chaveEtaria(a.cat2) - chaveEtaria(b.cat2))
}

function Piramides({ viz, R, linhas, escopo }: { viz: ReturnType<typeof useTema>['viz']; R: ReturnType<typeof useRotulos>['data']; linhas: Estimativa[]; escopo: Escopo }) {
  if (!R) return null
  const dados = CENSOS.map((c) => {
    const geografia = geoPara(c.censo, escopo)
    return { def: c, homens: extraiPiramide(linhas, c.censo, geografia, 'M'), mulheres: extraiPiramide(linhas, c.censo, geografia, 'F') }
  })
  const maxAbs = Math.max(
    1,
    ...dados.flatMap((d) => [...d.homens, ...d.mulheres].map((p) => Math.abs(p.valor ?? 0))),
  )
  // extremo simétrico arredondado (múltiplo de 5 acima do máximo dos dados) — evita rótulos
  // não redondos nas pontas do eixo (ex. "17"/"15" espremidos); as pontas ficam sempre ocultas.
  const maxRedondo = Math.ceil(maxAbs / 5) * 5

  return (
    <Figura
      kicker="Estrutura etária"
      titulo="A pirâmide se estreita na base e ganha volume em idade adulta jovem — efeito direto da migração de trabalho"
      subtitulo="% da população total (pessoas), por sexo e faixa etária de 5 anos, em cada censo. Mesma escala horizontal nos quatro painéis."
      fonte="IBGE, Censos 1991–2022 — microdados da amostra; estimativas próprias aprovadas pelo controle de revelação."
      notas={
        <p className="nota-miuda">
          Faixas marcadas com <strong>+</strong> agregam categorias fundidas pelo controle de revelação (baixa
          contagem) e são posicionadas pela primeira faixa que as compõe; a composição exata aparece ao passar o
          cursor sobre a barra. Faixas sem barra tiveram sua população somada à faixa fundida mais próxima.
        </p>
      }
    >
      <div className="piramides-grade">
        {dados.map(({ def, homens, mulheres }) => {
          // homens e mulheres podem ter faixas "outros:" fundidas de forma diferente pelo controle
          // de revelação — assentar as duas séries na MESMA grade fixa (pela primeira faixa que
          // compõe a categoria) mantém cada sexo na linha certa e os painéis comparáveis entre si.
          const porCat = (arr: PontoPiramide[]) => new Map(arr.map((p) => [faixaBase(p.cat2), p]))
          const homensPorCat = porCat(homens)
          const mulheresPorCat = porCat(mulheres)
          const fundida = (f: string) =>
            (homensPorCat.get(f)?.cat2 ?? '').startsWith('outros:') || (mulheresPorCat.get(f)?.cat2 ?? '').startsWith('outros:')
          const categorias = FAIXAS_PIRAMIDE
          return (
          <div key={def.censo} className="piramide-item">
            <p className="piramide-item__titulo">{def.labelCurto}</p>
            {homens.length === 0 && mulheres.length === 0 ? (
              <p className="nota-miuda" style={{ textAlign: 'center' }}>não disponível</p>
            ) : (
              <Chart
                height={230}
                ariaLabel={`Pirâmide etária de ${def.labelCurto}, homens à esquerda e mulheres à direita, em percentual da população.`}
                option={baseOption(viz, {
                  legend: { show: false },
                  grid: { left: 4, right: 4, top: 4, bottom: 4, containLabel: true },
                  xAxis: eixoValor(viz, {
                    min: -maxRedondo,
                    max: maxRedondo,
                    interval: maxRedondo / 2,
                    axisLabel: { formatter: (v: number) => fmtNum(Math.abs(v), 0), showMaxLabel: false, showMinLabel: false },
                  }),
                  yAxis: {
                    type: 'category',
                    data: categorias.map((c) => rotulo(R, c, 'faixa_etaria') + (fundida(c) ? ' +' : '')),
                    axisLine: { show: false },
                    axisTick: { show: false },
                    axisLabel: { color: viz.texto3, fontSize: 9 },
                  },
                  tooltip: {
                    trigger: 'item',
                    formatter: (p: { seriesIndex: number; dataIndex: number; marker: string }) => {
                      const cat = categorias[p.dataIndex]
                      const d = (p.seriesIndex === 0 ? homensPorCat : mulheresPorCat).get(cat)
                      const nome = p.seriesIndex === 0 ? 'Homens' : 'Mulheres'
                      if (!d) return `${p.marker}${nome}, ${rotulo(R, cat, 'faixa_etaria')}<br/>não disponível`
                      return `${p.marker}${nome}, ${rotulo(R, d.cat2, 'faixa_etaria')}<br/>${fmtPct(Math.abs(d.valor ?? 0))} · CV ${fmtNum(d.cv, 1)}% (${d.classe ?? '—'})`
                    },
                  },
                  series: [
                    {
                      name: 'Homens',
                      type: 'bar',
                      data: categorias.map((c) => {
                        const v = homensPorCat.get(c)?.valor
                        return v == null ? null : -v
                      }),
                      itemStyle: { color: viz.cat[0], decal: undefined },
                      barMaxWidth: 10,
                      barCategoryGap: '22%',
                    },
                    {
                      name: 'Mulheres',
                      type: 'bar',
                      data: categorias.map((c) => mulheresPorCat.get(c)?.valor ?? null),
                      itemStyle: { color: viz.cat[1] },
                      barMaxWidth: 10,
                      // sem isto o ECharts agrupa as duas séries lado a lado e cada sexo cai em
                      // meia-linha diferente da faixa etária (mesmo defeito corrigido na figura 7).
                      barGap: '-100%',
                    },
                  ],
                })}
              />
            )}
          </div>
          )
        })}
      </div>
      <div className="legenda-dot">
        <span className="legenda-dot__item"><span className="legenda-dot__marca" style={{ background: viz.cat[0] }} />Homens</span>
        <span className="legenda-dot__item"><span className="legenda-dot__marca" style={{ background: viz.cat[1] }} />Mulheres</span>
      </div>
    </Figura>
  )
}

// --------------------------------------------------------------------------- escolaridade

function PainelEscolaridade({ viz, R, linhas, escopo }: { viz: ReturnType<typeof useTema>['viz']; R: ReturnType<typeof useRotulos>['data']; linhas: Estimativa[]; escopo: Escopo }) {
  if (!R) return null
  type Linha = { censo: number; label: string; itens: { cat: string; valor: number; cv: number | null; classe: Classe | null }[] }
  const porCenso: Linha[] = CENSOS.map((c) => {
    const rows = busca(linhas, { censo: c.censo, geografia: geoPara(c.censo, escopo), universo: 'pessoas_25mais', estatistica: 'proporcao', dim1: 'nivel_instrucao', dim2: null })
    const ordem = [...NIVEL_INSTRUCAO_ORDEM]
    const itens = ordem
      .map((cat) => rows.find((r) => r.cat1 === cat))
      .filter((r): r is Estimativa => !!r)
      .map((r) => ({ cat: r.cat1!, valor: r.valor ?? 0, cv: r.cv, classe: r.classe }))
    // categorias fundidas (outros:) não previstas na ordem fixa
    for (const r of rows) if (!ordem.includes(r.cat1!) && r.cat1) itens.push({ cat: r.cat1, valor: r.valor ?? 0, cv: r.cv, classe: r.classe })
    return { censo: c.censo, label: c.labelCurto, itens }
  })
  const categoriasUniao = ordenarCategorias(R.categorias, Array.from(new Set(porCenso.flatMap((l) => l.itens.map((i) => i.cat)))))

  const colunas: Coluna<{ censo: number; cat: string; valor: number; cv: number | null; classe: Classe | null }>[] = [
    { id: 'censo', rotulo: 'Censo' },
    { id: 'cat', rotulo: 'Nível de instrução', fmt: (l) => rotulo(R, l.cat, 'nivel_instrucao') },
    { id: 'valor', rotulo: '%', num: true, fmt: (l) => fmtPct(l.valor) },
    { id: 'cv', rotulo: 'CV', num: true, fmt: (l) => (l.cv !== null ? fmtPct(l.cv) : TRACO) },
    { id: 'classe', rotulo: 'Precisão', fmt: (l) => l.classe && l.classe !== 'boa' ? <Precisao classe={l.classe} cv={l.cv} /> : 'boa' },
  ]
  const linhasTabela = porCenso.flatMap((l) => l.itens.map((i) => ({ censo: l.censo, ...i })))

  return (
    <Figura
      kicker="Escolaridade"
      titulo="A escolaridade da população adulta sobe a cada censo, mas quase 30% ainda não completou o fundamental"
      subtitulo="% da população de 25 anos ou mais, por nível de instrução mais elevado concluído."
      fonte="IBGE, Censos 1991–2022 — microdados da amostra; estimativas próprias aprovadas pelo controle de revelação."
      tabela={{ colunas, linhas: linhasTabela }}
    >
      <Chart
        height={230}
        ariaLabel="Barras 100% empilhadas de nível de instrução da população 25+ por censo."
        option={baseOption(viz, {
          grid: { left: 8, right: 8, top: 64, bottom: 24, containLabel: true },
          legend: { top: 0, left: 0 },
          xAxis: eixoValor(viz, { max: 100, axisLabel: { formatter: (v: number) => fmtNum(v, 0) + '%' } }),
          yAxis: { type: 'category', data: porCenso.map((l) => l.label), axisLine: { show: false }, axisTick: { show: false } },
          tooltip: {
            trigger: 'item',
            formatter: (p: { seriesName: string; value: number; dataIndex: number; marker: string }) => {
              const l = porCenso[p.dataIndex]
              const item = l.itens.find((i) => rotulo(R, i.cat, 'nivel_instrucao') === p.seriesName)
              return `${p.marker}${p.seriesName}<br/>${fmtPct(p.value)}${item ? ' · CV ' + fmtNum(item.cv, 1) + '% (' + (item.classe ?? '—') + ')' : ''}`
            },
          },
          series: categoriasUniao.map((cat) => {
            const idxOrdinal = NIVEL_INSTRUCAO_ORDEM.indexOf(cat)
            const estilo = idxOrdinal >= 0 ? { color: corSequencial(idxOrdinal, NIVEL_INSTRUCAO_ORDEM.length, viz) } : { color: viz.contexto, decal: decalFusao(viz) }
            return {
              name: rotulo(R, cat, 'nivel_instrucao'),
              type: 'bar',
              stack: 'total',
              barMaxWidth: 34,
              data: porCenso.map((l) => l.itens.find((i) => i.cat === cat)?.valor ?? 0),
              itemStyle: estilo,
            }
          }),
        })}
      />
    </Figura>
  )
}

// --------------------------------------------------------------------------- renda média do trabalho

function PainelRenda({ viz, R, linhas, escopo }: { viz: ReturnType<typeof useTema>['viz']; R: ReturnType<typeof useRotulos>['data']; linhas: Estimativa[]; escopo: Escopo }) {
  if (!R) return null
  const dados = CENSOS.map((c) => {
    const row = busca(linhas, { censo: c.censo, geografia: geoPara(c.censo, escopo), universo: 'ocupados', estatistica: 'media', variavel: 'renda_trabalho_r2022', dim1: null })[0]
    return { censo: c.censo, label: c.labelCurto, valor: row?.valor ?? null, ic: row ? ic95(row.valor, row.ep) : null, cv: row?.cv ?? null, classe: row?.classe ?? null }
  })
  const colunas: Coluna<(typeof dados)[number]>[] = [
    { id: 'label', rotulo: 'Censo' },
    { id: 'valor', rotulo: 'Renda média (R$ jul/2022)', num: true, fmt: (l) => fmtReais(l.valor) },
    { id: 'ic', rotulo: 'IC 95%', num: true, fmt: (l) => (l.ic ? `${fmtReais(l.ic[0])} – ${fmtReais(l.ic[1])}` : TRACO) },
    { id: 'cv', rotulo: 'CV', num: true, fmt: (l) => (l.cv !== null ? fmtPct(l.cv) : TRACO) },
    { id: 'classe', rotulo: 'Precisão', fmt: (l) => (l.classe && l.classe !== 'boa' ? <Precisao classe={l.classe} cv={l.cv} /> : 'boa') },
  ]
  const maxV = Math.max(1, ...dados.map((d) => d.ic?.[1] ?? d.valor ?? 0))
  return (
    <Figura
      kicker="Renda"
      titulo="A renda média do trabalho quase dobra entre 2000 e 2022, mas estagna na última década"
      subtitulo="Renda média do trabalho principal (ocupados 10+), em R$ de julho de 2022 (deflator IPCA). Barra de erro = IC 95%."
      fonte="IBGE, Censos 2000–2022 — microdados da amostra; deflator IPCA (t/1737); estimativas próprias aprovadas pelo controle de revelação. 1991 sem série em R$ 2022 (só faixas de salário mínimo do próprio IBGE)."
      tabela={{ colunas, linhas: dados }}
    >
      <Chart
        height={230}
        ariaLabel="Barras horizontais de renda média do trabalho por censo com intervalo de confiança de 95%."
        option={baseOption(viz, {
          legend: { show: false },
          grid: { left: 8, right: 16, top: 8, bottom: 24, containLabel: true },
          xAxis: eixoValor(viz, { max: maxV * 1.15, axisLabel: { formatter: (v: number) => fmtNum(v, 0) } }),
          yAxis: { type: 'category', data: dados.map((d) => d.label), inverse: true, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: viz.texto3, fontSize: 11 } },
          tooltip: {
            trigger: 'item',
            formatter: (p: { dataIndex: number; marker: string }) => {
              const d = dados[p.dataIndex]
              return `${p.marker}${d.label}<br/>${fmtReais(d.valor)} (IC: ${d.ic ? fmtReais(d.ic[0]) + ' – ' + fmtReais(d.ic[1]) : TRACO})<br/>CV ${fmtNum(d.cv, 1)}% (${d.classe ?? '—'})`
            },
          },
          series: [
            {
              type: 'bar',
              barMaxWidth: 20,
              data: dados.map((d) => ({ value: d.valor ?? 0, itemStyle: { color: censoCor(viz, d.censo), decal: decalPrecisao(d.classe, viz) } })),
            },
            serieDotIC('IC 95%', viz.texto3, 0, 1, dados.map((d, i) => ({ cat: i, valor: d.valor, baixo: d.ic?.[0] ?? null, alto: d.ic?.[1] ?? null })), { ponto: false }),
          ],
        })}
      />
    </Figura>
  )
}

// --------------------------------------------------------------------------- setor de atividade

function PainelSetor({ viz, R, linhas, escopo }: { viz: ReturnType<typeof useTema>['viz']; R: ReturnType<typeof useRotulos>['data']; linhas: Estimativa[]; escopo: Escopo }) {
  if (!R) return null
  const setoresOrdem = R.setores_ordem?.length ? R.setores_ordem : SETORES_ORDEM_FALLBACK
  interface Ponto { setor: string; censo: number; valor: number | null; ic: [number, number] | null; cv: number | null; classe: Classe | null }
  const pontos: Ponto[] = []
  for (const s of setoresOrdem) {
    for (const c of CENSOS) {
      const row = busca(linhas, { censo: c.censo, geografia: geoPara(c.censo, escopo), universo: 'ocupados', estatistica: 'proporcao', dim1: 'setor', dim2: null, cat1: s })[0]
      pontos.push({ setor: s, censo: c.censo, valor: row?.valor ?? null, ic: row ? ic95(row.valor, row.ep) : null, cv: row?.cv ?? null, classe: row?.classe ?? null })
    }
  }
  const colunas: Coluna<Ponto>[] = [
    { id: 'setor', rotulo: 'Setor', fmt: (l) => rotulo(R, l.setor, 'setor') },
    { id: 'censo', rotulo: 'Censo' },
    { id: 'valor', rotulo: '%', num: true, fmt: (l) => fmtPct(l.valor) },
    { id: 'ic', rotulo: 'IC 95%', num: true, fmt: (l) => (l.ic ? `${fmtPct(l.ic[0])} – ${fmtPct(l.ic[1])}` : TRACO) },
    { id: 'cv', rotulo: 'CV', num: true, fmt: (l) => (l.cv !== null ? fmtPct(l.cv) : TRACO) },
  ]

  return (
    <Figura
      kicker="Setor de atividade"
      titulo="A base econômica migra da agropecuária (55% em 2000) para mineração, construção e serviços"
      subtitulo="% dos ocupados (10+) por setor de atividade, um ponto por censo, com IC 95%. Extrativa mineral em destaque."
      fonte="IBGE, Censos 1991–2022 — microdados da amostra (CNAE-Dom); estimativas próprias aprovadas pelo controle de revelação."
      tabela={{ colunas, linhas: pontos }}
    >
      <Chart
        height={setoresOrdem.length * 34 + 60}
        ariaLabel="Gráfico de pontos com intervalo de confiança: nove setores de atividade, um ponto por censo."
        option={baseOption(viz, {
          legend: { show: false },
          grid: { left: 8, right: 16, top: 8, bottom: 24, containLabel: true },
          xAxis: eixoValor(viz, { max: 100, axisLabel: { formatter: (v: number) => fmtNum(v, 0) + '%' } }),
          yAxis: {
            type: 'category',
            data: setoresOrdem.map((s) => rotulo(R, s, 'setor')),
            inverse: true,
            axisLine: { show: false },
            axisTick: { show: false },
            axisLabel: {
              color: viz.texto3,
              fontSize: 11,
              formatter: (v: string) => (v === rotulo(R, 'extrativa_mineral', 'setor') ? '{b|' + v + '}' : v),
              rich: { b: { color: viz.enfase, fontWeight: 700 } },
            },
          },
          tooltip: {
            trigger: 'item',
            formatter: (p: { seriesName: string; value: unknown[] }) => {
              const [catIdx, valor, baixo, alto] = p.value as number[]
              const setor = setoresOrdem[catIdx]
              const pt = pontos.find((x) => x.setor === setor && String(x.censo) === p.seriesName.replace('Censo ', ''))
              return `${p.seriesName} · ${rotulo(R, setor, 'setor')}<br/>${fmtPct(valor)} (IC ${fmtPct(baixo)} – ${fmtPct(alto)})${pt ? '<br/>CV ' + fmtNum(pt.cv, 1) + '% (' + (pt.classe ?? '—') + ')' : ''}`
            },
          },
          series: CENSOS.map((c, gi) =>
            serieDotIC(
              'Censo ' + c.censo,
              censoCor(viz, c.censo),
              gi,
              CENSOS.length,
              setoresOrdem.map((s, ci) => {
                const p = pontos.find((x) => x.setor === s && x.censo === c.censo)
                return { cat: ci, valor: p?.valor ?? null, baixo: p?.ic?.[0] ?? null, alto: p?.ic?.[1] ?? null }
              }),
              { marcador: censoMarcador(c.censo) },
            ),
          ),
        })}
      />
      <div className="legenda-dot">
        {CENSOS.map((c) => (
          <span key={c.censo} className="legenda-dot__item">
            <span className="legenda-dot__marca" style={{ background: censoCor(viz, c.censo) }} />
            {c.labelCurto}
          </span>
        ))}
      </div>
    </Figura>
  )
}

// --------------------------------------------------------------------------- posição na ocupação

function PainelPosicao({ viz, R, linhas, escopo }: { viz: ReturnType<typeof useTema>['viz']; R: ReturnType<typeof useRotulos>['data']; linhas: Estimativa[]; escopo: Escopo }) {
  if (!R) return null
  const porCenso = CENSOS.map((c) => {
    const rows = busca(linhas, { censo: c.censo, geografia: geoPara(c.censo, escopo), universo: 'ocupados', estatistica: 'proporcao', dim1: 'posicao', dim2: null })
    const formalRow = busca(linhas, { censo: c.censo, geografia: geoPara(c.censo, escopo), universo: 'ocupados', estatistica: 'proporcao', dim1: 'formal', dim2: null, cat1: 'sim' })[0]
    return { censo: c.censo, label: c.labelCurto, rows, formal: formalRow?.valor ?? null }
  })
  const categoriasUniao = Array.from(new Set(porCenso.flatMap((l) => l.rows.map((r) => r.cat1!))))
  const ordenadas = [...POSICAO_ORDEM.filter((c) => categoriasUniao.includes(c)), ...categoriasUniao.filter((c) => !POSICAO_ORDEM.includes(c))]

  const colunas: Coluna<{ censo: number; cat: string; valor: number | null; classe: Classe | null }>[] = [
    { id: 'censo', rotulo: 'Censo' },
    { id: 'cat', rotulo: 'Posição', fmt: (l) => rotulo(R, l.cat, 'posicao') },
    { id: 'valor', rotulo: '%', num: true, fmt: (l) => fmtPct(l.valor) },
  ]
  const linhasTabela = porCenso.flatMap((l) => l.rows.map((r) => ({ censo: l.censo, cat: r.cat1!, valor: r.valor, classe: r.classe })))

  return (
    <Figura
      kicker="Posição na ocupação"
      titulo={`Formalidade sobe de ${fmtPct(porCenso[1]?.formal, 0)} (2000) para ${fmtPct(porCenso[3]?.formal, 0)} (2022) dos ocupados`}
      subtitulo="% dos ocupados por posição na ocupação, um bloco 100% por censo."
      fonte="IBGE, Censos 1991–2022 — microdados da amostra; estimativas próprias aprovadas pelo controle de revelação."
      tabela={{ colunas, linhas: linhasTabela }}
    >
      <Chart
        height={230}
        ariaLabel="Barras 100% empilhadas de posição na ocupação por censo."
        option={baseOption(viz, {
          grid: { left: 8, right: 8, top: 64, bottom: 24, containLabel: true },
          legend: { top: 0, left: 0 },
          xAxis: eixoValor(viz, { max: 100, axisLabel: { formatter: (v: number) => fmtNum(v, 0) + '%' } }),
          yAxis: { type: 'category', data: porCenso.map((l) => l.label), axisLine: { show: false }, axisTick: { show: false } },
          tooltip: { trigger: 'item', formatter: (p: { seriesName: string; value: number; marker: string }) => `${p.marker}${p.seriesName}<br/>${fmtPct(p.value)}` },
          series: ordenadas.map((cat) => ({
            name: rotulo(R, cat, 'posicao'),
            type: 'bar',
            stack: 'total',
            barMaxWidth: 34,
            data: porCenso.map((l) => l.rows.find((r) => r.cat1 === cat)?.valor ?? 0),
            itemStyle: corCategoriaFixa(cat, POSICAO_COR, viz),
          })),
        })}
      />
    </Figura>
  )
}

// --------------------------------------------------------------------------- domicílios

interface IndicadorDom {
  id: string
  rotuloTxt: string
  dim1: string
  cat1: string
}
const INDICADORES_DOM: IndicadorDom[] = [
  { id: 'agua', rotuloTxt: 'Água da rede geral', dim1: 'agua_rede', cat1: 'sim' },
  { id: 'esgoto', rotuloTxt: 'Esgoto adequado', dim1: 'esgoto_adequado', cat1: 'sim' },
  { id: 'lixo', rotuloTxt: 'Lixo coletado', dim1: 'lixo_coletado', cat1: 'sim' },
  { id: 'energia', rotuloTxt: 'Energia elétrica', dim1: 'energia', cat1: 'sim' },
  { id: 'alugado', rotuloTxt: 'Domicílio alugado', dim1: 'condicao_ocupacao', cat1: 'alugado' },
]

function PainelDomicilios({ viz, R, linhas, escopo }: { viz: ReturnType<typeof useTema>['viz']; R: ReturnType<typeof useRotulos>['data']; linhas: Estimativa[]; escopo: Escopo }) {
  if (!R) return null
  interface Ponto { indicador: string; censo: number; valor: number | null; ic: [number, number] | null; cv: number | null; classe: Classe | null }
  const pontos: Ponto[] = []
  for (const ind of INDICADORES_DOM) {
    for (const c of CENSOS) {
      const row = busca(linhas, { censo: c.censo, geografia: geoPara(c.censo, escopo), universo: 'domicilios', estatistica: 'proporcao', dim1: ind.dim1, dim2: null, cat1: ind.cat1 })[0]
      pontos.push({ indicador: ind.id, censo: c.censo, valor: row?.valor ?? null, ic: row ? ic95(row.valor, row.ep) : null, cv: row?.cv ?? null, classe: row?.classe ?? null })
    }
  }
  const colunas: Coluna<Ponto>[] = [
    { id: 'indicador', rotulo: 'Indicador', fmt: (l) => INDICADORES_DOM.find((i) => i.id === l.indicador)?.rotuloTxt ?? l.indicador },
    { id: 'censo', rotulo: 'Censo' },
    { id: 'valor', rotulo: '%', num: true, fmt: (l) => fmtPct(l.valor) },
    { id: 'ic', rotulo: 'IC 95%', num: true, fmt: (l) => (l.ic ? `${fmtPct(l.ic[0])} – ${fmtPct(l.ic[1])}` : TRACO) },
    { id: 'cv', rotulo: 'CV', num: true, fmt: (l) => (l.cv !== null ? fmtPct(l.cv) : 'não disponível neste censo') },
  ]

  return (
    <Figura
      kicker="Domicílios"
      titulo="Água, esgoto e lixo se universalizam; o aluguel cresce junto com a chegada de migrantes"
      subtitulo="% dos domicílios com cada condição adequada (ou alugados), um ponto por censo, com IC 95%."
      fonte="IBGE, Censos 1991–2022 — microdados da amostra; estimativas próprias aprovadas pelo controle de revelação."
      notas={<p className="nota-miuda">Energia elétrica só foi levantada de forma comparável até 2010 (quase universal em 2022, não perguntada da mesma forma).</p>}
      tabela={{ colunas, linhas: pontos }}
    >
      <Chart
        height={260}
        ariaLabel="Gráfico de pontos com intervalo de confiança: cinco indicadores domiciliares, um ponto por censo."
        option={baseOption(viz, {
          legend: { show: false },
          grid: { left: 8, right: 16, top: 8, bottom: 24, containLabel: true },
          xAxis: eixoValor(viz, { max: 100, axisLabel: { formatter: (v: number) => fmtNum(v, 0) + '%' } }),
          yAxis: { type: 'category', data: INDICADORES_DOM.map((i) => i.rotuloTxt), inverse: true, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: viz.texto3, fontSize: 11 } },
          tooltip: {
            trigger: 'item',
            formatter: (p: { seriesName: string; value: unknown[] }) => {
              const [catIdx, valor, baixo, alto] = p.value as number[]
              const ind = INDICADORES_DOM[catIdx]
              const pt = pontos.find((x) => x.indicador === ind.id && String(x.censo) === p.seriesName.replace('Censo ', ''))
              return `${p.seriesName}<br/>${ind.rotuloTxt}: ${fmtPct(valor)} (IC ${fmtPct(baixo)} – ${fmtPct(alto)})${pt ? '<br/>CV ' + fmtNum(pt.cv, 1) + '% (' + (pt.classe ?? '—') + ')' : ''}`
            },
          },
          series: CENSOS.map((c, gi) =>
            serieDotIC(
              'Censo ' + c.censo,
              censoCor(viz, c.censo),
              gi,
              CENSOS.length,
              INDICADORES_DOM.map((ind, ci) => {
                const p = pontos.find((x) => x.indicador === ind.id && x.censo === c.censo)
                return { cat: ci, valor: p?.valor ?? null, baixo: p?.ic?.[0] ?? null, alto: p?.ic?.[1] ?? null }
              }),
              { marcador: censoMarcador(c.censo) },
            ),
          ),
        })}
      />
      <div className="legenda-dot">
        {CENSOS.map((c) => (
          <span key={c.censo} className="legenda-dot__item">
            <span className="legenda-dot__marca" style={{ background: censoCor(viz, c.censo) }} />
            {c.labelCurto}
          </span>
        ))}
      </div>
    </Figura>
  )
}
