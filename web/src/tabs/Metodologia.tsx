// Metodologia e dados: fontes, pipeline, controle de revelação, validação da mancha,
// limitações, camadas com atribuição/licença, bibliografia verificada e declaração de IA.
import { useEffect, useMemo, useState } from 'react'
import { useJSON } from '../lib/data'
import { fmtNum, fmtPct } from '../lib/format'
import { useRota } from '../lib/rota'
import { useManifesto, GRUPOS } from '../lib/mapa'
import { EIXOS, useReferencias } from '../lib/referencias'
import { Secao, Segmentado, Selecao, Tabela, Termo } from '../components/ui'
import ComoCitar from '../components/ComoCitar'
import '../styles/textos.css'

interface Validacao {
  referencia: string
  n_pontos: number
  acuracia_global: number
  acuracia_global_ic95: number
  usuario_urbano: number
  produtor_urbano: number
  area_mapa_urbano_ha: number
  area_ajustada_urbano_ha: number
  area_ajustada_ic95_ha: number
}
interface ArtigoMeta {
  limitacoes: string[]
  declaracao_ia: string[]
}

const FONTES = [
  ['IBGE — SIDRA (API)', 'População 1970–2022, Contagens 1996/2007, estimativas 2001–2026, PIB municipal, CEMPRE', 'público'],
  ['IBGE — Agregados por setor censitário (Universo)', 'Indicadores por setor da sede, 2010 e 2022; malhas de setores', 'público'],
  ['IBGE — Microdados da amostra', '1991 (Parauapebas), 2000, 2010 (públicos) e 2022 (acesso controlado, termo de compromisso): perfil, migração de data fixa, domicílios', 'só agregados aprovados pelo controle de revelação'],
  ['Landsat 5/7/8/9 Collection 2 (USGS/NASA)', 'Composições anuais jun–set 1984–2026, classificação da mancha (30 m)', 'domínio público'],
  ['Copernicus Sentinel-2 L2A (ESA)', 'Série secundária de 10 m, 2017–2026; imagens de fundo', 'uso livre com atribuição'],
  ['INPE — CBERS-2B HRC, CBERS-4 PAN5M, CBERS-4A WPM', 'Referência de alta resolução para validar a mancha (2009, 2017, 2022)', 'uso livre'],
  ['MapBiomas Coleção 11', 'Classe 24 (área urbanizada) e 30 (mineração): comparação e máscara de mineração', 'CC BY 4.0'],
  ['JRC GHSL GHS-BUILT-S R2023A; DLR WSF-Evolution e WSF 2019', 'Produtos globais de comparação', 'CC BY 4.0'],
  ['IBGE — Áreas Urbanizadas 2019 e 2022', 'Referência vetorial oficial; loteamentos vazios', 'público'],
  ['ANM — CFEM e SIGMINE', 'Royalties da mineração 2004–2026; concessões de lavra', 'público'],
  ['OpenStreetMap', 'Rodovias e ferrovia', 'ODbL 1.0'],
  ['Bibliografia (OpenAlex, Crossref, BDTD, CAPES)', '150 trabalhos triados sobre Canaã e Carajás, todos verificados na fonte', '—'],
]

const PASSOS = [
  ['Dados oficiais e setores', 'API do IBGE (SIDRA, malhas, localidades) e agregados do Universo por setor, recortados para a sede.', '10_ibge_api.py, 11_setores.py'],
  ['Microdados harmonizados', 'Leitura dos quatro censos pelos layouts oficiais (sem posição de coluna à mão), esquema único de variáveis, renda em R$ de julho de 2022.', '12_microdados.py'],
  ['Estimação e controle de revelação', 'Estimativas ponderadas com erro-padrão por bootstrap de domicílios (200 réplicas); regras R1–R8 aplicadas e verificadas por um gate independente.', '13_migracao_perfil.py, disclosure_check.py'],
  ['Mancha urbana anual', 'Recortes Landsat/Sentinel-2 via STAC, composições medianas da estação seca, Random Forest por era de sensor, filtros de maioria temporal, máscara de mineração.', '21–23_*.py'],
  ['Validação', 'Pontos estratificados fotointerpretados em CBERS corregistrado; acurácia e área ajustada com IC (Olofsson et al. 2014).', '24_validar_mancha.py'],
  ['Estatísticas e camadas', 'Áreas, taxas, densidades, direção da expansão, ODS 11.3.1; vetores e imagens para este mapa.', '26_estatisticas_mancha.py, 27_tiles_camadas.py'],
  ['Análise, figuras e artigo', 'Tabelas analíticas, figuras e o artigo em DOCX/PDF, lendo só dados aprovados.', '40_analise_artigo.py, 41_figuras.py, 50_artigo.py'],
  ['Painel', 'Exportação dos agregados aprovados para JSON (com verificação do carimbo do gate) e este site estático.', '60_dados_web.py, web/'],
]

const REGRAS = [
  ['n ≥ 20 / 10', 'Censo 2022: toda célula publicada tem pelo menos 20 pessoas e 10 domicílios na amostra (1991–2010: 10 pessoas e 5 domicílios).'],
  ['× 10', 'Estimativas de contagem arredondadas a múltiplos de 10.'],
  ['faixas de n', 'O número de casos na amostra só aparece em faixas (10–19, 20–49…), nunca exato.'],
  ['≤ 2 dimensões', 'Nenhuma tabela cruza mais de duas dimensões temáticas.'],
  ['sem área de ponderação', 'Nada é publicado por área de ponderação nem com identificador de domicílio.'],
  ['CV sempre', 'Toda estimativa leva coeficiente de variação e classe de precisão.'],
  ['diferenciação', 'Uma célula da sede só sai se a célula rural implícita (município − sede) também cumprir o limiar.'],
  ['supressão complementar', 'Categorias pequenas são fundidas em "Outros (…)", sempre com os constituintes visíveis.'],
]

export default function Metodologia() {
  const [rota] = useRota()
  const alvo = rota.params.get('ref')
  const { data: est } = useJSON<{ validacao: Record<string, Validacao> }>('estatisticas_mancha.json')
  const { data: art } = useJSON<ArtigoMeta>('painel/artigo.json')
  const { data: man } = useManifesto()
  const { data: bib } = useReferencias()
  const { data: carimbo } = useJSON<{ versao_gate: string }>('painel/_manifesto.json')

  const [busca, setBusca] = useState('')
  const [eixo, setEixo] = useState('todos')
  const [camada, setCamada] = useState<'todas' | 'nucleo' | 'contexto'>('todas')

  const refs = useMemo(() => {
    const q = busca.trim().toLocaleLowerCase('pt-BR')
    return (bib?.referencias ?? []).filter(
      (r) =>
        (camada === 'todas' || r.camada === camada) &&
        (eixo === 'todos' || r.eixos?.includes(eixo)) &&
        (!q || `${r.abnt ?? ''} ${r.achados ?? ''}`.toLocaleLowerCase('pt-BR').includes(q)),
    )
  }, [bib, busca, eixo, camada])

  useEffect(() => {
    if (alvo && bib) document.getElementById(`ref-${alvo}`)?.scrollIntoView({ block: 'center' })
  }, [alvo, bib])

  const validacao = est
    ? Object.entries(est.validacao)
        .map(([ano, v]) => ({ ano, ...v }))
        .sort((a, b) => a.ano.localeCompare(b.ano))
    : []

  return (
    <div className="pagina pagina--estreita">
      <Secao kicker="Metodologia e dados" titulo="De onde vêm os números e até onde eles vão">
        <p>
          O painel combina dados oficiais do IBGE, microdados da amostra dos censos, uma classificação própria de imagens de
          satélite e a bibliografia verificada. Tudo o que aparece aqui é agregado; os microdados nunca saem da máquina de
          processamento.
        </p>
        <ul className="met__indice">
          {[
            ['fontes', 'Fontes'],
            ['pipeline', 'Processamento'],
            ['sigilo', 'Controle de revelação'],
            ['validacao', 'Validação da mancha'],
            ['limites', 'Limitações'],
            ['camadas', 'Camadas e licenças'],
            ['bibliografia', 'Bibliografia'],
            ['como-citar', 'Como citar'],
            ['ia', 'Uso de IA'],
          ].map(([id, t]) => (
            <li key={id}>
              <a href={`#/metodologia`} onClick={(e) => { e.preventDefault(); document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' }) }}>
                {t}
              </a>
            </li>
          ))}
        </ul>
      </Secao>

      <section className="bloco" id="fontes">
        <h3>Fontes</h3>
        <Tabela
          legenda="Fontes de dados"
          colunas={[
            { id: '0', rotulo: 'Fonte' },
            { id: '1', rotulo: 'Uso no painel' },
            { id: '2', rotulo: 'Acesso / licença' },
          ]}
          linhas={FONTES.map((f) => ({ 0: f[0], 1: f[1], 2: f[2] }))}
        />
      </section>

      <section className="bloco" id="pipeline">
        <h3>Processamento</h3>
        <p className="leitura">
          Cada etapa é um script reprodutível; os dados publicados são sempre regenerados a partir dele. A pasta{' '}
          <code>pipeline/</code> do repositório tem o código de todas as etapas.
        </p>
        <ol className="met__passos">
          {PASSOS.map(([t, d, s]) => (
            <li key={t}>
              <div>
                <h4>{t}</h4>
                <p>
                  {d} <code>{s}</code>
                </p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="bloco" id="sigilo">
        <h3>Controle de revelação</h3>
        <p className="leitura">
          Os microdados do Censo 2022 são de acesso controlado, e as amostras de Canaã em 2000 e 2010 são pequenas. Por isso toda
          estimativa amostral passa por oito regras antes de ser publicada, verificadas por um script independente que reconta cada
          célula a partir dos microdados. As estimativas levam <Termo id="cv">CV</Termo> e classe de precisão; as de precisão
          baixa aparecem com textura nos gráficos.
          {carimbo && <> Versão do carimbo que aprovou estes dados: <code>{carimbo.versao_gate}</code>.</>}
        </p>
        <div className="met__regras">
          {REGRAS.map(([t, d], i) => (
            <div key={t} className="ard-card">
              <p>
                <strong>
                  R{i + 1} · {t}
                </strong>
                {d}
              </p>
            </div>
          ))}
        </div>
      </section>

      <section className="bloco" id="validacao">
        <h3>Validação da mancha urbana</h3>
        <p className="leitura">
          A classificação foi validada em três épocas com imagens CBERS de alta resolução, com amostra estratificada e estimador de
          área de Olofsson et al. (2014). A acurácia global é alta porque a maior parte da janela não é urbana; o que importa é a
          acurácia do usuário da classe urbana (comissão na franja), que justifica usar a <Termo id="area_ajustada">área ajustada</Termo>.
          Antes de 1999 não há referência independente.
        </p>
        <Tabela
          legenda="Validação da mancha urbana"
          colunas={[
            { id: 'ano', rotulo: 'Época' },
            { id: 'referencia', rotulo: 'Referência', fmt: (l) => ({ hrc: 'CBERS-2B HRC 2,7 m', pan5m: 'CBERS-4 PAN 5 m', wpm: 'CBERS-4A WPM 2 m' } as Record<string, string>)[l.referencia] ?? l.referencia },
            { id: 'n_pontos', rotulo: 'Pontos', num: true },
            { id: 'ag', rotulo: 'Acurácia global', num: true, fmt: (l) => `${fmtPct(100 * l.acuracia_global, 1)} ± ${fmtNum(100 * l.acuracia_global_ic95, 1)}` },
            { id: 'u', rotulo: 'Usuário (urbano)', num: true, fmt: (l) => fmtPct(100 * l.usuario_urbano, 1) },
            { id: 'p', rotulo: 'Produtor (urbano)', num: true, fmt: (l) => fmtPct(100 * l.produtor_urbano, 1) },
            { id: 'am', rotulo: 'Área mapeada (ha)', num: true, fmt: (l) => fmtNum(l.area_mapa_urbano_ha) },
            { id: 'aa', rotulo: 'Área ajustada ± IC 95 % (ha)', num: true, fmt: (l) => `${fmtNum(l.area_ajustada_urbano_ha)} ± ${fmtNum(l.area_ajustada_ic95_ha)}` },
          ]}
          linhas={validacao}
        />
      </section>

      <section className="bloco" id="limites">
        <h3>Limitações</h3>
        <div className="leitura">{art?.limitacoes.map((p, i) => <p key={i}>{p}</p>)}</div>
      </section>

      <section className="bloco" id="camadas">
        <h3>Camadas do mapa, atribuições e licenças</h3>
        <p className="leitura nota-miuda">
          As cores das camadas temáticas seguem a legenda da fonte (MapBiomas, estilos oficiais do IBGE); a interface e os gráficos
          seguem a identidade Ardósia. Mapa de base: © contribuidores do OpenStreetMap, © CARTO.
        </p>
        {man && (
          <Tabela
            legenda="Camadas do mapa"
            colunas={[
              { id: 'grupo', rotulo: 'Grupo', fmt: (c) => GRUPOS.find((g) => g.id === c.grupo)?.rotulo ?? c.grupo },
              { id: 'titulo', rotulo: 'Camada' },
              { id: 'anos', rotulo: 'Anos', fmt: (c) => (c.anos?.length ? `${c.anos[0]}–${c.anos[c.anos.length - 1]} (${c.anos.length})` : '') },
              { id: 'atribuicao', rotulo: 'Atribuição' },
              { id: 'licenca', rotulo: 'Licença' },
            ]}
            linhas={[...man.camadas].sort((a, b) => GRUPOS.findIndex((g) => g.id === a.grupo) - GRUPOS.findIndex((g) => g.id === b.grupo))}
          />
        )}
      </section>

      <section className="bloco" id="bibliografia">
        <h3>Bibliografia verificada</h3>
        <p className="leitura">
          Levantamento em bases abertas (OpenAlex, Crossref, Semantic Scholar, BDTD, Catálogo de Teses da CAPES) em 10/09/2026. Só
          entra referência cuja existência, autoria, ano e veículo foram conferidos na fonte (DOI ou página do repositório). O
          resumo de cada obra é uma síntese própria do levantamento, não uma citação literal.
        </p>
        <div className="bib__filtros">
          <label>
            <span className="sr-only">Buscar na bibliografia</span>
            <input className="bib__busca" type="search" placeholder="Buscar autor, título, tema…" value={busca} onChange={(e) => setBusca(e.target.value)} />
          </label>
          <Segmentado
            rotulo="Recorte"
            valor={camada}
            onChange={setCamada}
            opcoes={[
              { valor: 'todas', rotulo: 'Todas' },
              { valor: 'nucleo', rotulo: 'Sobre Canaã' },
              { valor: 'contexto', rotulo: 'Contexto regional' },
            ]}
          />
          <Selecao rotulo="Eixo" valor={eixo} onChange={setEixo} opcoes={[{ valor: 'todos', rotulo: 'Todos' }, ...Object.entries(EIXOS).map(([valor, rotulo]) => ({ valor, rotulo }))]} />
          <span className="bib__contagem" aria-live="polite">
            {refs.length} de {bib?.referencias.length ?? 0} obras
          </span>
        </div>
        <ul className="bib__lista">
          {refs.map((r) => (
            <li key={r.slug} id={`ref-${r.slug}`} className={'bib__item' + (r.slug === alvo ? ' alvo' : '')}>
              <p className="bib__abnt">{r.abnt}</p>
              <p className="bib__meta">
                {r.camada && <span>{r.camada === 'nucleo' ? 'Sobre Canaã' : 'Contexto'}</span>}
                {r.eixos?.map((e) => <span key={e}>{EIXOS[e] ?? e}</span>)}
                {r.citada_no_artigo && <span className="ard-pill ard-pill--conforme">citada no artigo</span>}
                {r.url && (
                  <a href={r.url} target="_blank" rel="noopener">
                    {r.doi ? `doi:${r.doi}` : 'acessar'}
                  </a>
                )}
              </p>
              {r.achados && !r.achados.startsWith('resumo indisponível') && <p className="bib__achados">{r.achados}</p>}
            </li>
          ))}
        </ul>
      </section>

      <ComoCitar />

      <section className="bloco" id="ia">
        <h3>Declaração de uso de inteligência artificial</h3>
        <div className="leitura">
          {art?.declaracao_ia.map((p, i) => <p key={i}>{p}</p>)}
          <p>
            Este painel foi implementado com a mesma assistência (Claude, Anthropic), sob a mesma supervisão: o código lê apenas os
            agregados aprovados pelo controle de revelação.
          </p>
        </div>
      </section>
    </div>
  )
}
