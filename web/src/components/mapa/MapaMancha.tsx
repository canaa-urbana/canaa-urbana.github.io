// Instância de mapa MapLibre da aba Mancha urbana. Usada tanto sozinha (modo normal) quanto
// duas vezes lado a lado (modo comparação, em Comparador.tsx). Cria o mapa uma única vez,
// troca de tema sem recriar (`trocarTemaBase`) e delega a sincronização de camadas ao
// `ControladorCamadas`. Ano corrente troca pelo caminho leve (`trocarAno`); qualquer outra
// mudança (camadas ligadas, opacidade, imagem ativa, fantasma, tema) passa por `sincronizar`.
import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from 'react'
import { JANELA_SEDE, carregarGeojson, criarMapa, maplibregl, trocarTemaBase, type Manifesto, type MLMap } from '../../lib/mapa'
import { tokens, type Tema } from '../../lib/theme'
import { ControladorCamadas } from './camadas'
import { tooltipHtml } from './tooltip'

export interface MapaManchaHandle {
  map: MLMap | null
  recentrar: () => void
  municipioInteiro: () => void
}

export interface MapaManchaProps {
  manifesto: Manifesto | undefined
  tema: Tema
  ano: number
  ativos: Set<string>
  opacidades: Record<string, number>
  imagemAtiva: string | null
  ghost: boolean
  interativo?: boolean
  mostrarControles?: boolean
  className?: string
  onCarregando?: (carregando: boolean) => void
}

function bboxDe(fc: GeoJSON.FeatureCollection): [[number, number], [number, number]] | null {
  let minX = Infinity,
    minY = Infinity,
    maxX = -Infinity,
    maxY = -Infinity
  const visit = (coords: unknown): void => {
    const arr = coords as unknown[]
    if (typeof arr[0] === 'number') {
      const [x, y] = arr as [number, number]
      if (x < minX) minX = x
      if (y < minY) minY = y
      if (x > maxX) maxX = x
      if (y > maxY) maxY = y
    } else {
      for (const c of arr) visit(c)
    }
  }
  for (const f of fc.features) if (f.geometry && 'coordinates' in f.geometry) visit(f.geometry.coordinates)
  if (!Number.isFinite(minX)) return null
  return [
    [minX, minY],
    [maxX, maxY],
  ]
}

const MapaMancha = forwardRef<MapaManchaHandle, MapaManchaProps>(function MapaMancha(
  { manifesto, tema, ano, ativos, opacidades, imagemAtiva, ghost, interativo = true, mostrarControles = true, className, onCarregando },
  ref,
) {
  const elRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MLMap | null>(null)
  const ctrlRef = useRef<ControladorCamadas | null>(null)
  const popupRef = useRef<maplibregl.Popup | null>(null)
  const manifestoRef = useRef<Manifesto | undefined>(manifesto)
  const [pronto, setPronto] = useState(false)

  useImperativeHandle(ref, () => ({
    get map() {
      return mapRef.current
    },
    recentrar: () => mapRef.current?.fitBounds(JANELA_SEDE, { padding: 24, duration: 500 }),
    municipioInteiro: () => {
      const c = manifestoRef.current?.camadas.find((c2) => c2.id === 'aoi_municipio')
      if (!c) return
      carregarGeojson(c).then((fc) => {
        const b = bboxDe(fc)
        if (b) mapRef.current?.fitBounds(b, { padding: 40, duration: 600 })
      })
    },
  }))

  useEffect(() => {
    manifestoRef.current = manifesto
  }, [manifesto])

  // cria o mapa uma única vez
  useEffect(() => {
    if (!elRef.current) return
    const m = criarMapa(elRef.current, { tema, interativo, limites: JANELA_SEDE })
    mapRef.current = m
    ctrlRef.current = new ControladorCamadas(m)
    m.on('load', () => setPronto(true))
    if (interativo) {
      popupRef.current = new maplibregl.Popup({ closeButton: false, closeOnClick: false, className: 'mapa-popup' })
      m.on('mousemove', (e) => {
        const ctrl2 = ctrlRef.current
        if (!ctrl2 || !manifestoRef.current) return
        const layers = ctrl2.todosLayerIds().filter((id) => m.getLayer(id))
        if (!layers.length) {
          popupRef.current?.remove()
          m.getCanvas().style.cursor = ''
          return
        }
        const feats = m.queryRenderedFeatures(e.point, { layers })
        const f = feats[0]
        const html = f ? tooltipHtml(f.layer.id, f.properties ?? {}, manifestoRef.current) : null
        if (!html) {
          popupRef.current?.remove()
          m.getCanvas().style.cursor = ''
          return
        }
        m.getCanvas().style.cursor = 'pointer'
        popupRef.current?.setLngLat(e.lngLat).setHTML(html).addTo(m)
      })
      m.on('mouseleave', () => popupRef.current?.remove())
    }
    return () => {
      ctrlRef.current?.destruir()
      popupRef.current?.remove()
      m.remove()
      mapRef.current = null
      ctrlRef.current = null
      setPronto(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // tema: troca tiles/fundo sem recriar
  useEffect(() => {
    if (mapRef.current) trocarTemaBase(mapRef.current, tema)
  }, [tema])

  const ativosChave = Array.from(ativos).sort().join(',')
  const opacidadesChave = JSON.stringify(opacidades)

  // sincronização "pesada": camadas ligadas/desligadas, opacidade, imagem ativa, fantasma, tema
  useEffect(() => {
    const ctrl = ctrlRef.current
    if (!ctrl || !manifesto || !pronto) return
    let vivo = true
    onCarregando?.(true)
    ctrl
      .sincronizar({ manifesto, ativos, opacidades, imagemAtiva, ghost, ano, viz: tokens(tema) })
      .finally(() => vivo && onCarregando?.(false))
    return () => {
      vivo = false
    }
    // ano entra só na 1ª sincronização; mudanças de ano puras usam a troca leve abaixo
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [manifesto, ativosChave, opacidadesChave, imagemAtiva, ghost, tema, pronto])

  // troca leve de ano (slider/autoplay): setData/updateImage/filter sem recriar layers
  const primeiraVezRef = useRef(true)
  useEffect(() => {
    const ctrl = ctrlRef.current
    if (!ctrl || !manifesto || !pronto) return
    if (primeiraVezRef.current) {
      primeiraVezRef.current = false
      return
    }
    let vivo = true
    onCarregando?.(true)
    ctrl.trocarAno(manifesto, ano).finally(() => vivo && onCarregando?.(false))
    return () => {
      vivo = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ano])

  return <div ref={elRef} className={'mapa-mancha__mapa' + (className ? ' ' + className : '')} data-controles={mostrarControles ? '1' : '0'} />
})

export default MapaMancha
