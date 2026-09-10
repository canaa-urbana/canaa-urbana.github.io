// Aba "Mancha urbana": mapa central com a série 1984–2026, camadas de comparação, mineração e
// infraestrutura, comparação de dois anos e os gráficos de trajetória da E3c.
import { useEffect, useMemo, useRef, useState } from 'react'
import { Esqueleto, Erro, Secao, Termo } from '../components/ui'
import { useManifesto, precarregarImagem } from '../lib/mapa'
import { useJSON } from '../lib/data'
import { useRotulos } from '../lib/rotulos'
import { useTema } from '../lib/theme'
import { useRota, trocarParam } from '../lib/rota'
import MapaMancha, { type MapaManchaHandle } from '../components/mapa/MapaMancha'
import PainelCamadas from '../components/mapa/PainelCamadas'
import Legenda from '../components/mapa/Legenda'
import PainelKpi from '../components/mapa/PainelKpi'
import Slider from '../components/mapa/Slider'
import Comparador from '../components/mapa/Comparador'
import GraficoAreaSede from '../components/mapa/GraficoAreaSede'
import GraficoAcrescimo from '../components/mapa/GraficoAcrescimo'
import GraficoDirecao from '../components/mapa/GraficoDirecao'
import GraficoComparacaoProdutos from '../components/mapa/GraficoComparacaoProdutos'
import TabelaPeriodos from '../components/mapa/TabelaPeriodos'
import { CAMADAS_PADRAO_ON, IMAGEM_PADRAO } from '../components/mapa/camadas'
import type { EstatisticasMancha, DirecaoItem, ComparacaoProdutoItem } from '../components/mapa/tipos'
import '../styles/mancha.css'

const ANO_MIN = 1984
const ANO_MAX = 2026

function anoInicial(param: string | null): number {
  const n = Number(param)
  if (Number.isFinite(n) && n >= ANO_MIN && n <= ANO_MAX) return n
  return 2022
}

export default function Mancha() {
  const manifesto = useManifesto()
  const estat = useJSON<EstatisticasMancha>('estatisticas_mancha.json')
  const rotulos = useRotulos()
  const direcao = useJSON<DirecaoItem[]>('painel/geo/expansao_direcao.json')
  const comparacao = useJSON<ComparacaoProdutoItem[]>('painel/geo/comparacao_produtos.json')
  const { tema } = useTema()
  const [rota] = useRota()

  const [ano, setAno] = useState(() => anoInicial(rota.params.get('ano')))
  const [ativos, setAtivos] = useState<Set<string>>(new Set(CAMADAS_PADRAO_ON))
  const [opacidades, setOpacidades] = useState<Record<string, number>>({})
  const [imagemAtiva, setImagemAtiva] = useState<string | null>(IMAGEM_PADRAO)
  const [ghost, setGhost] = useState(true)
  const [carregando, setCarregando] = useState(false)
  const [mssModo, setMssModo] = useState(false)
  const [anoMss, setAnoMss] = useState<1973 | 1982>(1982)
  const [compareModo, setCompareModo] = useState(false)
  const [compareAnoA, setCompareAnoA] = useState(2004)
  const [compareAnoB, setCompareAnoB] = useState(2022)

  const mapaRef = useRef<MapaManchaHandle>(null)

  useEffect(() => {
    trocarParam('ano', ano)
  }, [ano])

  function mudarAno(a: number) {
    setAno(Math.min(ANO_MAX, Math.max(ANO_MIN, a)))
  }

  function alternarCamada(id: string) {
    setAtivos((s) => {
      const n = new Set(s)
      if (n.has(id)) n.delete(id)
      else n.add(id)
      return n
    })
  }

  function mudarOpacidade(id: string, v: number) {
    setOpacidades((o) => ({ ...o, [id]: v }))
  }

  function precarregarProximo(proximoAno: number) {
    if (!imagemAtiva || !manifesto.data) return
    const c = manifesto.data.camadas.find((c2) => c2.id === imagemAtiva)
    if (c) precarregarImagem(c, proximoAno)
  }

  // efetivo: quando o modo "antes do assentamento" está ligado, o mapa mostra 1973/1982 com a
  // clareira MSS e a imagem falsa-cor MSS, sem mexer no estado "normal" do slider/camadas.
  const ativosEfetivos = useMemo(() => {
    if (!mssModo) return ativos
    const n = new Set(ativos)
    n.add('clareira_mss')
    return n
  }, [ativos, mssModo])
  const anoEfetivo = mssModo ? anoMss : ano
  const imagemEfetiva = mssModo ? 'mss_falsacor' : imagemAtiva

  if (manifesto.error || estat.error || rotulos.error) return <Erro erro={(manifesto.error ?? estat.error ?? rotulos.error)!} />
  if (!manifesto.data || !estat.data || !rotulos.data) {
    return (
      <div className="pagina">
        <Esqueleto altura={640} />
      </div>
    )
  }

  return (
    <div className="pagina mancha-pagina">
      <Secao kicker="Mancha urbana" titulo="Mais da metade da cidade de 2026 foi construída entre o Sossego e o S11D (2004–2016)">
        <p>
          Cada ano da série tem uma <Termo id="mancha">mancha urbana</Termo> classificada em imagens de satélite (30 m, 1984–2026) e uma{' '}
          <Termo id="area_ajustada">área ajustada</Termo> pelo erro de mapeamento, com intervalo de confiança de 95 %. Navegue pela linha do tempo, compare camadas de mineração,
          infraestrutura e produtos externos, e veja como a cidade cresceu e mudou de direção a cada ciclo mineral.
        </p>
      </Secao>

      {compareModo ? (
        <Comparador
          manifesto={manifesto.data}
          tema={tema}
          ativos={ativos}
          opacidades={opacidades}
          imagemAtiva={imagemAtiva}
          ghost={ghost}
          anoA={compareAnoA}
          anoB={compareAnoB}
          onAnoA={setCompareAnoA}
          onAnoB={setCompareAnoB}
          onSair={() => setCompareModo(false)}
        />
      ) : (
        <>
          <div className="mancha-layout">
            <div className="mancha-layout__mapa">
              <MapaMancha
                ref={mapaRef}
                manifesto={manifesto.data}
                tema={tema}
                ano={anoEfetivo}
                ativos={ativosEfetivos}
                opacidades={opacidades}
                imagemAtiva={imagemEfetiva}
                ghost={ghost && !mssModo}
                onCarregando={setCarregando}
              />
              {carregando && (
                <div className="mancha-carregando" role="status" aria-live="polite">
                  Carregando…
                </div>
              )}
              <div className="mancha-layout__botoes">
                <button type="button" className="botao-texto" onClick={() => mapaRef.current?.recentrar()}>
                  Recentralizar
                </button>
                <button type="button" className="botao-texto" onClick={() => mapaRef.current?.municipioInteiro()}>
                  Município inteiro
                </button>
                <button type="button" className="botao-texto" onClick={() => setCompareModo(true)}>
                  Comparar dois anos
                </button>
              </div>
            </div>
            <aside className="mancha-layout__painel">
              <PainelKpi estat={estat.data} ano={ano} />
              <div className="mancha-layout__ghost">
                <label>
                  <input type="checkbox" checked={ghost} disabled={mssModo} onChange={(e) => setGhost(e.target.checked)} /> Contorno do ano anterior (fantasma)
                </label>
              </div>
              <Legenda manifesto={manifesto.data} ativos={ativosEfetivos} imagemAtiva={imagemEfetiva} ghost={ghost && !mssModo} ano={anoEfetivo} />
              <PainelCamadas
                manifesto={manifesto.data}
                ativos={ativos}
                onToggle={alternarCamada}
                opacidades={opacidades}
                onOpacidade={mudarOpacidade}
                imagemAtiva={imagemAtiva}
                onImagemAtiva={setImagemAtiva}
              />
            </aside>
          </div>

          <div className="mancha-layout__slider">
            <Slider ano={ano} onChange={mudarAno} censos={rotulos.data.censos} marcos={rotulos.data.marcos} janelasObras={rotulos.data.janelas_obras} onProximoAno={precarregarProximo} />
            <div className="mancha-mss">
              <label>
                <input type="checkbox" checked={mssModo} onChange={(e) => setMssModo(e.target.checked)} /> Antes do assentamento (clareira, imagens MSS 1973/1982 — não é mancha urbana)
              </label>
              {mssModo && (
                <div className="segmentado" role="radiogroup" aria-label="Ano da imagem MSS">
                  {[1973, 1982].map((a) => (
                    <button key={a} type="button" role="radio" aria-checked={anoMss === a} className={'segmentado__op' + (anoMss === a ? ' ativo' : '')} onClick={() => setAnoMss(a as 1973 | 1982)}>
                      {a}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}

      <div className="grade bloco">
        <div className="c-12">
          <GraficoAreaSede serie={estat.data.serie} ano={ano} onAno={mudarAno} censos={rotulos.data.censos} marcos={rotulos.data.marcos} janelasObras={rotulos.data.janelas_obras} />
        </div>
        <div className="c-6">
          <GraficoAcrescimo serie={estat.data.serie} ano={ano} janelasObras={rotulos.data.janelas_obras} />
        </div>
        <div className="c-6">{direcao.data && <GraficoDirecao dados={direcao.data} />}</div>
        <div className="c-6">{comparacao.data && <GraficoComparacaoProdutos serie={estat.data.serie} produtos={comparacao.data} />}</div>
        <div className="c-6">
          <TabelaPeriodos periodos={estat.data.periodos} />
        </div>
      </div>
    </div>
  )
}
