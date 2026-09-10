// Página inicial: a história em cinco números e uma narrativa guiada (assentamento →
// emancipação → Sossego → S11D → hoje) que comanda um mapa fixo com a mancha de cada ano.
import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { useAnalise, useJSON } from '../lib/data'
import { fmtDelta, fmtHa, fmtNum, fmtPct } from '../lib/format'
import { citacaoCurta, useReferencias, type Referencia } from '../lib/referencias'
import { Citacao, Kpi, Termo } from '../components/ui'
import MapaNarrativa, { type EstadoMapa } from '../components/inicio/MapaNarrativa'
import '../styles/inicio.css'

interface AnoMancha {
  ano: number
  area_sede_ha: number | null
  area_sede_ajustada_ha: number | null
  area_sede_ajustada_ic95_ha: number | null
  pop_urbana: number | null
}
interface EstMancha {
  serie: AnoMancha[]
}
interface PontoPop {
  ano: number
  valor: number | null
  tipo_fonte: string
  recorte: string
}
interface Resumo {
  chegados_2022_total: number
  chegados_2022_pos_2013_pct: number
  setor_extrativa_canaa: Record<string, number>
}

interface Passo {
  id: string
  periodo: string
  titulo: string
  mapa: EstadoMapa
  texto: (d: Dados) => ReactNode
  refs: string[]
}

interface Dados {
  area: (ano: number) => AnoMancha | undefined
  pop: (ano: number, recorte?: string) => number | null
}

const PASSOS: Passo[] = [
  {
    id: 'assentamento',
    periodo: '1982–1985',
    titulo: 'Um núcleo de colonização aberto na floresta',
    // 1984, primeira imagem TM: as MSS de 1973/1982 (80 m, Tier 2 com erro de posição de até ~1 km e,
    // em out/1982, cheia de cúmulos) não coincidem com a série e não distinguem o núcleo (QA E7)
    mapa: {
      ano: 1984,
      imagem: 'landsat_cor',
      vetor: 'mancha_propria',
      pb: true,
      // ±2,5 km em torno do núcleo histórico (centroide da sede de 1990, estatisticas_mancha.json): a vila de ~6 ha some na janela inteira
      limites: [
        [-49.8498 - 0.023, -6.531 - 0.023],
        [-49.8498 + 0.023, -6.531 + 0.023],
      ],
    },
    texto: (d) => (
      <>
        <p>
          Em 1982 o GETAT abriu o CEDERE II, núcleo do Projeto de Assentamento Carajás, entre Marabá e a Serra dos Carajás.
          Nos três anos seguintes, 1.551 famílias receberam lotes de cerca de 50 ha nos núcleos da região; até 1985, 816 tinham
          título definitivo.
        </p>
        <p>
          A primeira imagem Landsat TM que distingue o núcleo é de 1984: em tons de cinza, com a mancha em vermelho, a vila
          ocupa cerca de {fmtHa(d.area(1984)?.area_sede_ajustada_ha, 0)}. Ainda não é cidade: é uma vila de colonos, parte do
          distrito-sede de Marabá. As imagens MSS de 1982 (80 m, com nuvens e georreferenciamento aproximado) não permitem
          delimitar o núcleo.
        </p>
      </>
    ),
    refs: ['silva2006arranjos', 'carmo2023mineracao'],
  },
  {
    id: 'emancipacao',
    periodo: '1994–2000',
    titulo: 'A vila vira município, ainda rural',
    mapa: { ano: 1994, imagem: 'landsat_cor', vetor: 'mancha_propria' },
    texto: (d) => (
      <>
        <p>
          A Lei estadual 5.860, de 1994, cria o município, instalado em 1997. A sede ocupava cerca de{' '}
          {fmtHa(d.area(1994)?.area_sede_ajustada_ha, 0)} em 1994. No Censo 2000, Canaã tinha {fmtNum(d.pop(2000))} habitantes,
          dois terços deles na zona rural: a economia era a pecuária leiteira.
        </p>
      </>
    ),
    refs: ['cabral2011canaa', 'ribeiro2014analise'],
  },
  {
    id: 'sossego',
    periodo: '2002–2004',
    titulo: 'O Sossego: a primeira mina e o primeiro salto',
    mapa: { ano: 2004, imagem: 'landsat_cor', vetor: 'mancha_propria', anoFantasma: 1994 },
    texto: (d) => (
      <>
        <p>
          As obras da mina de cobre do Sossego (Vale), entre 2002 e 2004, trazem a primeira onda de migrantes. A sede passa de{' '}
          {fmtHa(d.area(2000)?.area_sede_ajustada_ha)} em 2000 para {fmtHa(d.area(2004)?.area_sede_ajustada_ha)} em 2004. A
          Contagem de 2007 encontra {fmtNum(d.pop(2007))} habitantes — quase o dobro do que as estimativas anuais previam.
        </p>
      </>
    ),
    refs: ['moura2005mina'],
  },
  {
    id: 's11d',
    periodo: '2013–2016',
    titulo: 'O S11D e a década em que a cidade mais cresceu',
    mapa: { ano: 2016, imagem: 'landsat_cor', vetor: 'mancha_propria', anoFantasma: 2004 },
    texto: (d) => (
      <>
        <p>
          Entre o Sossego e o S11D, a maior mina de ferro da Vale (obras 2013–16, operação em dezembro de 2016), a sede chega a{' '}
          {fmtHa(d.area(2016)?.area_sede_ajustada_ha)}. Mais da metade da cidade de 2026 foi construída nesse intervalo, no maior
          ritmo absoluto da série.
        </p>
      </>
    ),
    refs: ['padilha2020estado', 'castriota2024housing'],
  },
  {
    id: 'hoje',
    periodo: '2022–2026',
    titulo: 'Uma cidade de migrantes, nove em cada dez moradores urbanos',
    mapa: { ano: 2026, imagem: 's2_cor', vetor: 'mancha_propria', anoFantasma: 2016 },
    texto: (d) => (
      <>
        <p>
          O Censo 2022 conta {fmtNum(d.pop(2022))} habitantes, {fmtPct((100 * (d.pop(2022, 'urbana') ?? 0)) / (d.pop(2022) || 1), 0)}{' '}
          na área urbana. Em 2026 a sede ocupa cerca de {fmtHa(d.area(2026)?.area_sede_ajustada_ha)} (valor provisório), com
          loteamentos novos na periferia sul e norte.
        </p>
      </>
    ),
    refs: ['castriota2024aqui', 'souza2023insercao'],
  },
]

function RefsPasso({ slugs, refs }: { slugs: string[]; refs: Map<string, Referencia> }) {
  const lista = slugs.map((s) => refs.get(s)).filter((r): r is Referencia => !!r && !!r.achados)
  if (!lista.length) return null
  return (
    <div className="narrativa__refs">
      <p className="narrativa__refs-rot">Na literatura</p>
      {lista.map((r) => (
        <Citacao key={r.slug} fonte={<a href={`#/metodologia?ref=${r.slug}`}>({citacaoCurta(r)})</a>}>
          {r.achados}
        </Citacao>
      ))}
    </div>
  )
}

export default function Inicio() {
  const { data: est } = useJSON<EstMancha>('estatisticas_mancha.json')
  const { data: pop } = useAnalise<PontoPop>('serie_populacao')
  const { data: resumo } = useJSON<Resumo>('painel/resumo_analise.json')
  const { data: bib } = useReferencias()
  const [passo, setPasso] = useState(0)
  const passosRef = useRef<(HTMLElement | null)[]>([])

  const refs = useMemo(() => new Map((bib?.referencias ?? []).map((r) => [r.slug, r])), [bib])

  const dados: Dados = useMemo(
    () => ({
      area: (ano) => est?.serie.find((s) => s.ano === ano),
      pop: (ano, recorte = 'município') =>
        pop?.find((p) => p.ano === ano && p.recorte === recorte && p.tipo_fonte.startsWith('oficial'))?.valor ?? null,
    }),
    [est, pop],
  )

  // qual passo está no centro da tela
  useEffect(() => {
    const obs = new IntersectionObserver(
      (ents) => {
        for (const e of ents) if (e.isIntersecting) setPasso(Number((e.target as HTMLElement).dataset.i))
      },
      { rootMargin: '-45% 0px -45% 0px' },
    )
    passosRef.current.forEach((p) => p && obs.observe(p))
    return () => obs.disconnect()
  }, [])

  const s = est?.serie ?? []
  const a1990 = dados.area(1990)?.area_sede_ajustada_ha
  const a2026 = dados.area(2026)?.area_sede_ajustada_ha
  const urb2000 = dados.pop(2000, 'urbana')
  const urb2022 = dados.pop(2022, 'urbana')
  const p2000 = dados.pop(2000)
  const p2022 = dados.pop(2022)
  const serieOficial = (pop ?? []).filter((p) => p.recorte === 'município' && p.tipo_fonte.startsWith('oficial'))
  const atual = PASSOS[passo]

  return (
    <div className="inicio">
      <header className="pagina pagina--estreita inicio__hero">
        <p className="ard-kicker">Painel de pesquisa · Canaã dos Carajás (PA)</p>
        <h1>Da colônia agrícola à cidade mineral</h1>
        <p className="lead">
          Como um núcleo de assentamento de 1982 virou, em quarenta anos e duas minas, uma cidade de quase cem mil habitantes. Este
          painel reúne a série anual da <Termo id="mancha">mancha urbana</Termo> da sede (1984–2026), os quatro censos com dados
          por pessoa e por setor, a migração e a economia mineral.
        </p>
      </header>

      <section className="pagina pagina--estreita" aria-labelledby="cinco">
        <p className="ard-kicker">A história em cinco números</p>
        <h2 id="cinco" className="sr-only">
          A história em cinco números
        </h2>
        <div className="kpis kpis--5">
          <Kpi
            rotulo="Habitantes, Censo 2022"
            valor={fmtNum(p2022)}
            delta={p2000 && p2022 ? `${fmtNum(p2022 / p2000, 1)} vezes a população de 2000 (${fmtNum(p2000)})` : undefined}
            serie={serieOficial.map((p) => p.valor)}
            destaque={serieOficial.length - 1}
            nota="IBGE, Censos e Contagem 2007"
          />
          <Kpi
            rotulo="Área construída da sede, 2026"
            valor={fmtNum(a2026)}
            unidade="ha"
            delta={a1990 && a2026 ? `${fmtNum(a2026 / a1990, 0)} vezes a de 1990 (${fmtHa(a1990)})` : undefined}
            serie={s.map((x) => x.area_sede_ajustada_ha)}
            destaque={s.length - 1}
            nota="área ajustada pela acurácia; 2026 provisório"
          />
          <Kpi
            rotulo="População urbana, 2022"
            valor={p2022 && urb2022 ? fmtPct((100 * urb2022) / p2022, 0) : '—'}
            delta={p2000 && urb2000 ? `${fmtPct((100 * urb2000) / p2000, 0)} em 2000` : undefined}
            nota="IBGE, situação do domicílio"
          />
          <Kpi
            rotulo="Não naturais que chegaram desde 2013"
            valor={resumo ? fmtPct(resumo.chegados_2022_pos_2013_pct, 0) : '—'}
            delta={resumo ? `de ${fmtNum(resumo.chegados_2022_total / 1000, 1)} mil moradores nascidos fora, em 2022` : undefined}
            nota="Censo 2022, amostra (estimativa)"
          />
          <Kpi
            rotulo="Ocupados na extração mineral, 2022"
            valor={resumo ? fmtPct(resumo.setor_extrativa_canaa['2022'], 1) : '—'}
            delta={resumo ? `${fmtDelta(resumo.setor_extrativa_canaa['2022'] - resumo.setor_extrativa_canaa['2010'], 1, ' p.p.')} desde 2010` : undefined}
            nota="município, Censo 2022, amostra"
          />
        </div>
      </section>

      <section className="narrativa pagina" aria-label="Narrativa: de 1982 a 2026">
        <div className="narrativa__passos">
          {PASSOS.map((p, i) => (
            <article
              key={p.id}
              ref={(e) => {
                passosRef.current[i] = e
              }}
              data-i={i}
              className={'narrativa__passo' + (i === passo ? ' ativo' : '')}
              aria-current={i === passo ? 'step' : undefined}
            >
              <p className="ard-kicker">{p.periodo}</p>
              <h3>{p.titulo}</h3>
              <div className="narrativa__texto">{p.texto(dados)}</div>
              <RefsPasso slugs={p.refs} refs={refs} />
              <a className="narrativa__link" href={`#/mancha?ano=${Math.max(p.mapa.ano, 1984)}`}>
                Explorar {Math.max(p.mapa.ano, 1984)} no mapa →
              </a>
            </article>
          ))}
        </div>
        <div className="narrativa__fixo">
          <MapaNarrativa
            estado={atual.mapa}
            rotulo={`Mapa da sede de Canaã dos Carajás em ${atual.mapa.ano}: ${atual.titulo}`}
          />
          <p className="nota-miuda narrativa__credito">
            Imagens: Landsat (USGS/NASA) e Copernicus Sentinel-2 (2026); mancha: classificação própria.
          </p>
        </div>
      </section>

      <section className="pagina pagina--estreita" aria-labelledby="explore">
        <p className="ard-kicker">Explore</p>
        <h2 id="explore">Seções do painel</h2>
        <div className="cartoes">
          {[
            ['mancha', 'Mancha urbana', 'Mapa ano a ano, 1984–2026, com camadas de comparação, imagens de satélite e estatísticas de crescimento.'],
            ['censos', 'Anos censitários', '1991 (Parauapebas), 2000, 2010 e 2022 lado a lado: mancha, pirâmide, escolaridade, trabalho, domicílios.'],
            ['setores', 'Setores censitários', 'Indicadores por setor da sede em 2010 e 2022: densidade, saneamento, renda, idade do tecido urbano.'],
            ['migracao', 'Migração', 'Migrantes de data fixa, origens, coortes de chegada e o perfil de quem chegou.'],
            ['economia', 'Mineração e economia', 'CFEM, PIB, emprego formal e o descompasso entre obras e royalties.'],
            ['artigo', 'Artigo', 'O artigo científico completo (PDF) com métodos, resultados e referências.'],
          ].map(([id, t, d]) => (
            <a key={id} className="cartao ard-card" href={`#/${id}`}>
              <span className="cartao__titulo">{t}</span>
              <span className="cartao__desc">{d}</span>
            </a>
          ))}
        </div>
      </section>
    </div>
  )
}
