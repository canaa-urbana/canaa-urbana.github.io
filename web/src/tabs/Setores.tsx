// Aba "Setores censitários": coroplético comparável entre 2010 e 2022 (classes de quantil
// calculadas sobre os dois anos juntos), tabela ordenável com exportação CSV e dois recortes
// analíticos da E5 — o gradiente centro-periferia e a dispersão entre setores.
import { useEffect, useMemo, useRef, useState } from 'react'
import { useAnalise, useJSON } from '../lib/data'
import { useManifesto, type Manifesto, type MLMap } from '../lib/mapa'
import { useTema, type Tema } from '../lib/theme'
import { fmtNum } from '../lib/format'
import { Erro, Esqueleto, Secao, Segmentado, Selecao, Termo } from '../components/ui'
import MapaSetores, { type MapaSetoresHandle } from '../components/setores/MapaSetores'
import TabelaSetores from '../components/setores/TabelaSetores'
import GraficoGradiente from '../components/setores/GraficoGradiente'
import GraficoDispersao from '../components/setores/GraficoDispersao'
import { N_CLASSES, quebrasQuantil, valoresIndicador } from '../components/setores/dados'
import type { DesigualdadeItem, IndicadorMeta, IndicadoresSetores, SetorFC } from '../components/setores/tipos'
import '../styles/setores.css'

type AnoModo = '2010' | '2022' | 'lado_a_lado'
type Recorte = 'sede' | 'todos'

function fcSede(fc: SetorFC | undefined): SetorFC | undefined {
  if (!fc) return fc
  return { ...fc, features: fc.features.filter((f) => f.properties.pertence === 'sede') }
}

function fcRecorte(fc: SetorFC | undefined, recorte: Recorte): SetorFC | undefined {
  if (!fc) return fc
  return recorte === 'sede' ? fcSede(fc) : fc
}

export default function Setores() {
  const { tema, viz } = useTema()
  const { data: d2010, error: e2010 } = useJSON<SetorFC>('painel/setores_2010.json')
  const { data: d2022, error: e2022 } = useJSON<SetorFC>('painel/setores_2022.json')
  const { data: indicadores, error: eInd } = useJSON<IndicadoresSetores>('painel/indicadores_setores.json')
  const { data: desigualdade } = useAnalise<DesigualdadeItem>('desigualdade_intraurbana')
  const { data: manifesto } = useManifesto()

  const [anoModo, setAnoModo] = useState<AnoModo>('2010')
  const [recorte, setRecorte] = useState<Recorte>('sede')
  const [indicadorId, setIndicadorId] = useState('esgoto_pct')
  const [mostrarMancha, setMostrarMancha] = useState(false)
  const [selecionado, setSelecionado] = useState<string | null>(null)
  const [hover, setHover] = useState<string | null>(null)
  const [tabelaAno, setTabelaAno] = useState<2010 | 2022>(2010)

  const indicadorAtual = useMemo(() => indicadores?.indicadores.find((i) => i.id === indicadorId) ?? indicadores?.indicadores[0], [indicadores, indicadorId])

  // opções de indicador: só os que existem no ano (ou nos dois, em "lado a lado")
  const opcoesIndicador = useMemo(() => {
    if (!indicadores) return []
    const anosNecessarios = anoModo === 'lado_a_lado' ? null : [Number(anoModo)]
    return indicadores.indicadores.filter((i) => !anosNecessarios || anosNecessarios.every((a) => i.anos.includes(a)))
  }, [indicadores, anoModo])

  // troca automática se o indicador atual não existe mais nas opções do ano escolhido
  useEffect(() => {
    if (!indicadorAtual || !opcoesIndicador.length) return
    if (!opcoesIndicador.some((i) => i.id === indicadorAtual.id)) setIndicadorId(opcoesIndicador[0].id)
  }, [opcoesIndicador, indicadorAtual])

  useEffect(() => {
    setTabelaAno(anoModo === '2022' ? 2022 : anoModo === '2010' ? 2010 : tabelaAno)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [anoModo])

  const fc2010Sede = useMemo(() => fcSede(d2010), [d2010])
  const fc2022Sede = useMemo(() => fcSede(d2022), [d2022])

  const breaks = useMemo(() => {
    if (!indicadorAtual) return null
    const valores = [...valoresIndicador(fc2010Sede, indicadorAtual.id), ...valoresIndicador(fc2022Sede, indicadorAtual.id)]
    return quebrasQuantil(valores, N_CLASSES)
  }, [fc2010Sede, fc2022Sede, indicadorAtual])

  const fc2010Recorte = useMemo(() => fcRecorte(d2010, recorte), [d2010, recorte])
  const fc2022Recorte = useMemo(() => fcRecorte(d2022, recorte), [d2022, recorte])

  const erro = e2010 || e2022 || eInd
  if (erro) return <div className="pagina"><Erro erro={erro} /></div>
  if (!d2010 || !d2022 || !indicadores || !indicadorAtual) return <div className="pagina"><Esqueleto altura={480} /></div>

  const fcTabela = tabelaAno === 2010 ? fc2010Recorte! : fc2022Recorte!
  const linhasTabela = fcTabela.features.map((f) => f.properties)

  const anosDisponiveisSel = indicadorAtual.anos
  const legendaCores = corPorFaixa(breaks, viz.seq, indicadorAtual)

  return (
    <div className="pagina">
      <Secao
        kicker="Setores censitários"
        titulo="Em 2010 o esgoto por rede caía com a distância do núcleo; em 2022 a cobertura se espalhou, mas o pior decil ficou em 24 %"
      >
        <p>
          Cada <Termo id="setor">setor censitário</Termo> resume algumas centenas de domicílios: é a menor malha em que o IBGE publica
          água, esgoto, lixo e densidade. Em 2010 a correlação de Spearman entre esgoto por rede e a distância ao núcleo histórico era
          −0,82; em 2022 o gradiente quase desaparece (−0,13) porque a cobertura média sobe de 27 % para 56 % — mas o setor mais mal
          servido segue perto de 24 %.
        </p>
        <p className="aviso">
          As malhas de setor de 2010 (24 setores na sede) e 2022 (88 setores) são diferentes: compare padrões espaciais, não um setor
          contra o mesmo setor. Os dados vêm do Universo do Censo (todos os domicílios), não da amostra — não há erro amostral aqui.
        </p>
      </Secao>

      <div className="setores__controles">
        <Selecao rotulo="Indicador" valor={indicadorAtual.id} onChange={setIndicadorId} opcoes={opcoesIndicador.map((i) => ({ valor: i.id, rotulo: i.rotulo }))} />
        <Segmentado
          rotulo="Ano"
          valor={anoModo}
          onChange={setAnoModo}
          opcoes={[
            { valor: '2010', rotulo: '2010', desabilitado: !anosDisponiveisSel.includes(2010) },
            { valor: '2022', rotulo: '2022', desabilitado: !anosDisponiveisSel.includes(2022) },
            { valor: 'lado_a_lado', rotulo: 'Lado a lado', desabilitado: !(anosDisponiveisSel.includes(2010) && anosDisponiveisSel.includes(2022)) },
          ]}
        />
        <Segmentado
          rotulo="Recorte"
          valor={recorte}
          onChange={setRecorte}
          opcoes={[
            { valor: 'sede', rotulo: 'Sede' },
            { valor: 'todos', rotulo: 'Todos os setores' },
          ]}
        />
        <label className="setores__toggle-mancha">
          <input type="checkbox" checked={mostrarMancha} onChange={(e) => setMostrarMancha(e.target.checked)} />
          Contorno da mancha urbana 2022
        </label>
      </div>

      <div className="grade" style={{ marginTop: 16 }}>
        <div className={anoModo === 'lado_a_lado' ? 'c-12' : 'c-8'}>
          <div className="setores__mapa-card ard-card">
            {anoModo === 'lado_a_lado' ? (
              <MapasLadoALado
                fc2010={fc2010Recorte!}
                fc2022={fc2022Recorte!}
                indicador={indicadorAtual}
                breaks={breaks}
                tema={tema}
                manifesto={manifesto}
                mostrarMancha={mostrarMancha}
                selecionado={selecionado}
                hover={hover}
                onHover={setHover}
                onClick={setSelecionado}
              />
            ) : (
              <MapaSetores
                fc={anoModo === '2010' ? fc2010Recorte : fc2022Recorte}
                ano={Number(anoModo)}
                indicador={indicadorAtual}
                breaks={breaks}
                tema={tema}
                manifesto={manifesto}
                mostrarMancha={mostrarMancha}
                selecionado={selecionado}
                hover={hover}
                onHover={setHover}
                onClick={setSelecionado}
                className="setores__mapa setores__mapa--unico"
              />
            )}
            <Legenda breaks={breaks} cores={legendaCores} indicador={indicadorAtual} recorte={recorte} viz={viz} />
          </div>
          <p className="nota-miuda" style={{ marginTop: 8 }}>
            Fonte: IBGE, Censos 2010 e 2022 (Universo), agregados por setor censitário; pertença sede/outros núcleos/rural, fração
            construída e densidade líquida da classificação própria (E3c); distância e ano de urbanização da E5.
          </p>
        </div>

        {anoModo !== 'lado_a_lado' && (
          <div className="c-4">
            <div className="setores__tabela-lateral">
              <TabelaSetores linhas={linhasTabela} ano={tabelaAno} indicadores={indicadores.indicadores} selecionado={selecionado} onSelecionar={setSelecionado} />
            </div>
          </div>
        )}
      </div>

      {anoModo === 'lado_a_lado' && (
        <div className="grade" style={{ marginTop: 24 }}>
          <div className="c-12">
            <Segmentado rotulo="Tabela do ano" valor={String(tabelaAno)} onChange={(v) => setTabelaAno(Number(v) as 2010 | 2022)} opcoes={[{ valor: '2010', rotulo: '2010' }, { valor: '2022', rotulo: '2022' }]} />
            <div style={{ marginTop: 12 }}>
              <TabelaSetores linhas={linhasTabela} ano={tabelaAno} indicadores={indicadores.indicadores} selecionado={selecionado} onSelecionar={setSelecionado} />
            </div>
          </div>
        </div>
      )}

      <section className="bloco">
        <p className="ard-kicker">Leituras analíticas (E5)</p>
        <h3>Do centro à periferia, e a dispersão entre setores</h3>
        <div className="grade">
          <div className="c-12">
            <GraficoGradiente fc2010={fc2010Sede} fc2022={fc2022Sede} indicador={indicadorAtual} desigualdade={desigualdade} viz={viz} />
          </div>
          <div className="c-12" style={{ marginTop: 24 }}>
            <GraficoDispersao desigualdade={desigualdade} indicadores={indicadores} viz={viz} />
          </div>
        </div>
      </section>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Modo "Lado a lado": dois mapas (2010 à esquerda, 2022 à direita) com câmera sincronizada.
// ---------------------------------------------------------------------------

interface PropsLado {
  fc2010: SetorFC
  fc2022: SetorFC
  indicador: IndicadorMeta
  breaks: number[] | null
  tema: Tema
  manifesto: Manifesto | undefined
  mostrarMancha: boolean
  selecionado: string | null
  hover: string | null
  onHover: (cod: string | null) => void
  onClick: (cod: string) => void
}

function MapasLadoALado({ fc2010, fc2022, indicador, breaks, tema, manifesto, mostrarMancha, selecionado, hover, onHover, onClick }: PropsLado) {
  const refA = useRef<MapaSetoresHandle>(null)
  const refB = useRef<MapaSetoresHandle>(null)
  const sincronizandoRef = useRef(false)

  useEffect(() => {
    const mA = refA.current?.map
    const mB = refB.current?.map
    if (!mA || !mB) return
    const espelhar = (origem: MLMap, destino: MLMap) => () => {
      if (sincronizandoRef.current) return
      sincronizandoRef.current = true
      destino.jumpTo({ center: origem.getCenter(), zoom: origem.getZoom(), bearing: origem.getBearing(), pitch: origem.getPitch() })
      sincronizandoRef.current = false
    }
    const deAparaB = espelhar(mA, mB)
    const deBparaA = espelhar(mB, mA)
    mA.on('move', deAparaB)
    mB.on('move', deBparaA)
    return () => {
      mA.off('move', deAparaB)
      mB.off('move', deBparaA)
    }
  }, [])

  return (
    <div className="setores__mapas-lado">
      <div className="setores__mapa-lado">
        <span className="setores__rotulo-ano">2010</span>
        <MapaSetores
          ref={refA}
          fc={fc2010}
          ano={2010}
          indicador={indicador}
          breaks={breaks}
          tema={tema}
          manifesto={manifesto}
          mostrarMancha={mostrarMancha}
          selecionado={selecionado}
          hover={hover}
          onHover={onHover}
          onClick={onClick}
          className="setores__mapa"
        />
      </div>
      <div className="setores__mapa-lado">
        <span className="setores__rotulo-ano">2022</span>
        <MapaSetores
          ref={refB}
          fc={fc2022}
          ano={2022}
          indicador={indicador}
          breaks={breaks}
          tema={tema}
          manifesto={manifesto}
          mostrarMancha={mostrarMancha}
          selecionado={selecionado}
          hover={hover}
          onHover={onHover}
          onClick={onClick}
          className="setores__mapa"
        />
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Legenda: classes de quantil (comparáveis entre os dois anos) + "sem dado" + contexto.
// ---------------------------------------------------------------------------

function corPorFaixa(breaks: number[] | null, seq: string[], indicador: IndicadorMeta): { cor: string; rotulo: string }[] {
  if (!breaks) return [{ cor: seq[2], rotulo: 'todos os valores' }]
  const casas = indicador.casas
  const un = indicador.unidade === '%' ? '%' : indicador.unidade
  const pontos = [null, ...breaks, null]
  return seq.map((cor, i) => {
    const a = pontos[i]
    const b = pontos[i + 1]
    const rotulo = a === null ? `até ${fmtNum(b!, casas)} ${un}` : b === null ? `≥ ${fmtNum(a, casas)} ${un}` : `${fmtNum(a, casas)}–${fmtNum(b, casas)} ${un}`
    return { cor, rotulo }
  })
}

function Legenda({
  breaks,
  cores,
  indicador,
  recorte,
  viz,
}: {
  breaks: number[] | null
  cores: { cor: string; rotulo: string }[]
  indicador: IndicadorMeta
  recorte: Recorte
  viz: { contexto: string; superficie: string }
}) {
  return (
    <div className="setores__legenda">
      <p className="setores__legenda-titulo">
        {indicador.rotulo} — classes de quantil {breaks ? `(2010 + 2022 juntos, ${N_CLASSES} classes)` : ''}
      </p>
      <div className="setores__legenda-itens">
        {cores.map((c) => (
          <span key={c.rotulo} className="setores__legenda-item">
            <i style={{ background: c.cor }} /> {c.rotulo}
          </span>
        ))}
        <span className="setores__legenda-item">
          <i style={{ background: viz.superficie, border: `1px solid ${viz.contexto}` }} /> sem dado
        </span>
        {recorte === 'todos' && (
          <span className="setores__legenda-item">
            <i style={{ background: viz.contexto, opacity: 0.4 }} /> outros núcleos / rural (fora do recorte da sede)
          </span>
        )}
      </div>
    </div>
  )
}
