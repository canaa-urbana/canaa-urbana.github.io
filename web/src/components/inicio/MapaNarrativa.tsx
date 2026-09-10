// Mapa fixo da narrativa da página inicial: a cada passo troca a imagem de satélite do ano,
// a mancha (ou a clareira MSS de 1982) e mostra o contorno do passo anterior como "fantasma".
// Não interativo (a rolagem da página comanda), para não capturar o scroll.
import { useEffect, useRef, useState } from 'react'
import {
  arquivoCamada,
  carregarGeojson,
  corPorClasse,
  criarMapa,
  JANELA_SEDE,
  dataUrl,
  opacidadePorClasse,
  trocarTemaBase,
  useManifesto,
  type Camada,
  type MLMap,
} from '../../lib/mapa'
import { useTema } from '../../lib/theme'

export interface EstadoMapa {
  ano: number
  imagem: 'mss_falsacor' | 'landsat_cor' | 's2_cor'
  vetor: 'mancha_propria' | 'clareira_mss'
  anoFantasma?: number
  /** imagem de fundo em tons de cinza (só a classe urbana fica em cor) */
  pb?: boolean
  /** enquadramento do passo (lon/lat); sem ele, a janela inteira da sede */
  limites?: [[number, number], [number, number]]
}

const VAZIO: GeoJSON.FeatureCollection = { type: 'FeatureCollection', features: [] }

export default function MapaNarrativa({ estado, rotulo }: { estado: EstadoMapa; rotulo: string }) {
  const el = useRef<HTMLDivElement>(null)
  const mapa = useRef<MLMap | null>(null)
  const [pronto, setPronto] = useState(false)
  const { tema, viz } = useTema()
  const { data: man } = useManifesto()
  const temaInicial = useRef(tema)

  const camada = (id: string): Camada | undefined => man?.camadas.find((c) => c.id === id)

  // cria o mapa uma vez
  useEffect(() => {
    if (!el.current || !man) return
    const m = criarMapa(el.current, { tema: temaInicial.current, interativo: false, padding: 8 })
    mapa.current = m
    m.on('load', () => {
      const img = man.camadas.find((c) => c.id === 'landsat_cor')!
      m.addSource('img', { type: 'image', url: dataUrl(arquivoCamada(img, 1994)), coordinates: img.coordenadas as [[number, number], [number, number], [number, number], [number, number]] })
      m.addLayer({ id: 'img', type: 'raster', source: 'img', paint: { 'raster-opacity': 1, 'raster-fade-duration': 250 } }, 'rotulos')
      m.addSource('vetor', { type: 'geojson', data: VAZIO })
      m.addSource('fantasma', { type: 'geojson', data: VAZIO })
      m.addLayer({ id: 'vetor-preench', type: 'fill', source: 'vetor', paint: { 'fill-color': viz.cat[1], 'fill-opacity': 0 } }, 'rotulos')
      m.addLayer({ id: 'vetor-linha', type: 'line', source: 'vetor', paint: { 'line-color': viz.cat[1], 'line-width': 1 } }, 'rotulos')
      m.addLayer({ id: 'fantasma', type: 'line', source: 'fantasma', paint: { 'line-color': '#FAF9F6', 'line-width': 1.5, 'line-dasharray': [2, 2] } }, 'rotulos')
      setPronto(true)
    })
    return () => {
      m.remove()
      mapa.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [man])

  useEffect(() => {
    if (mapa.current && pronto) trocarTemaBase(mapa.current, tema)
  }, [tema, pronto])

  // aplica o estado do passo
  useEffect(() => {
    const m = mapa.current
    if (!m || !pronto || !man) return
    const img = camada(estado.imagem)
    if (img?.coordenadas) {
      const src = m.getSource('img') as maplibregl.ImageSource
      src.updateImage({ url: dataUrl(arquivoCamada(img, estado.ano)), coordinates: img.coordenadas as [[number, number], [number, number], [number, number], [number, number]] })
      // passo do assentamento: imagem em preto e branco para que só a mancha tenha cor
      m.setPaintProperty('img', 'raster-saturation', estado.pb || estado.imagem === 'mss_falsacor' ? -1 : 0)
    }
    m.fitBounds(estado.limites ?? JANELA_SEDE, { padding: 8, duration: 700 })
    const vet = camada(estado.vetor)
    let vivo = true
    if (vet) {
      carregarGeojson(vet, estado.ano).then((g) => {
        if (!vivo) return
        // mancha: sede, outros núcleos e mineração; clareira MSS: só o núcleo do assentamento (classe 1)
        // — as demais clareiras (agropecuária) ficam na imagem em preto e branco
        const classes = estado.vetor === 'mancha_propria' ? [1, 2, 3] : [1]
        const fc = { ...g, features: g.features.filter((f) => classes.includes(Number(f.properties?.classe))) }
        ;(m.getSource('vetor') as maplibregl.GeoJSONSource).setData(fc)
        if (estado.vetor === 'mancha_propria' && vet.legenda) {
          m.setPaintProperty('vetor-preench', 'fill-color', corPorClasse('classe', vet.legenda))
          m.setPaintProperty('vetor-preench', 'fill-opacity', opacidadePorClasse('classe', vet.legenda, 0.9))
          m.setPaintProperty('vetor-linha', 'line-color', corPorClasse('classe', vet.legenda))
        } else {
          const cor = vet.legenda?.find((l) => l.classe === 1)?.cor ?? vet.cor
          if (cor) {
            m.setPaintProperty('vetor-preench', 'fill-color', cor)
            m.setPaintProperty('vetor-preench', 'fill-opacity', 0.85)
            m.setPaintProperty('vetor-linha', 'line-color', cor)
          }
        }
      })
    }
    const mp = camada('mancha_propria')
    if (mp && estado.anoFantasma) {
      carregarGeojson(mp, estado.anoFantasma).then((g) => {
        if (!vivo) return
        ;(m.getSource('fantasma') as maplibregl.GeoJSONSource).setData({ ...g, features: g.features.filter((f) => Number(f.properties?.classe) === 1) })
      })
    } else {
      ;(m.getSource('fantasma') as maplibregl.GeoJSONSource).setData(VAZIO)
    }
    return () => {
      vivo = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [estado, pronto, man])

  return (
    <div className="narrativa__mapa" aria-label={rotulo} role="figure">
      <div ref={el} className="narrativa__canvas" />
      <div className="narrativa__selo" aria-hidden="true">
        <span className="narrativa__ano">{estado.ano}</span>
        <span className="narrativa__legenda">
          {estado.vetor === 'clareira_mss' ? (
            <>
              <i className="narrativa__amostra" style={{ background: camada('clareira_mss')?.legenda?.find((l) => l.classe === 1)?.cor }} /> núcleo do assentamento (clareira)
            </>
          ) : (
            <>
              <i className="narrativa__amostra" style={{ background: camada('mancha_propria')?.legenda?.[0]?.cor }} /> mancha urbana
              {estado.anoFantasma && (
                <>
                  {' '}
                  <i className="narrativa__amostra narrativa__amostra--linha" style={{ borderColor: viz.texto2 }} /> {estado.anoFantasma}
                </>
              )}
            </>
          )}
        </span>
      </div>
    </div>
  )
}
