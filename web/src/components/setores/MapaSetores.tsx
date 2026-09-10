// Um mapa coroplético de setores censitários (usado sozinho ou duas vezes, lado a lado, no
// modo "Lado a lado"). Cria o MapLibre uma única vez, ajusta ao bbox dos setores da sede no
// primeiro carregamento e depois só troca dados/estilo das camadas (sem recriar o mapa).
import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from 'react'
import { carregarGeojson, criarMapa, maplibregl, trocarTemaBase, type Manifesto, type MLMap } from '../../lib/mapa'
import type { Tema, VizTokens } from '../../lib/theme'
import { tokens } from '../../lib/theme'
import { fmtNum } from '../../lib/format'
import { bboxFC } from './dados'
import { PERTENCE_ROTULO, type IndicadorMeta, type IndicadoresSetores, type SetorFC } from './tipos'

export interface MapaSetoresHandle {
  map: MLMap | null
}

export interface MapaSetoresProps {
  fc: SetorFC | undefined
  ano: number
  indicador: IndicadorMeta
  indicadores: IndicadoresSetores | undefined
  breaks: number[] | null
  tema: Tema
  mostrarMancha: boolean
  manifesto: Manifesto | undefined
  selecionado: string | null
  hover: string | null
  onHover: (cod: string | null) => void
  onClick: (cod: string) => void
  interativo?: boolean
  className?: string
}

const FONTE_SETORES = 'setores-src'
const FONTE_MANCHA = 'setores-mancha-src'

function linhaTooltip(rotulo: string, valor: string): string {
  return `<tr><th>${rotulo}</th><td>${valor}</td></tr>`
}

function tooltipHtml(props: Record<string, unknown>, indicadores: IndicadoresSetores | undefined, ano: number): string {
  const cod = String(props.cod_setor ?? '')
  const pertence = PERTENCE_ROTULO[props.pertence as keyof typeof PERTENCE_ROTULO] ?? String(props.pertence ?? '')
  const linhas = [
    linhaTooltip('Pertença', pertence),
    linhaTooltip('População', fmtNum(props.pop as number)),
    linhaTooltip('Domicílios', fmtNum(props.dom as number)),
  ]
  for (const ind of indicadores?.indicadores ?? []) {
    if (!ind.anos.includes(ano)) continue
    const v = props[ind.id]
    if (v === undefined || v === null) continue
    const un = ind.unidade === '%' ? ' %' : ' ' + ind.unidade
    linhas.push(linhaTooltip(ind.rotulo, `${fmtNum(v as number, ind.casas)}${un}`))
  }
  return `<div class="mapa-tooltip"><p class="mapa-tooltip__titulo">Setor ${cod}</p><table>${linhas.join('')}</table></div>`
}

function expressaoCor(indicadorId: string, breaks: number[] | null, viz: VizTokens): maplibregl.ExpressionSpecification {
  const cores = viz.seq
  if (!breaks) return cores[2] as unknown as maplibregl.ExpressionSpecification
  const passos: (string | number)[] = [cores[0]]
  breaks.forEach((b, i) => passos.push(b, cores[i + 1]))
  // to-number com padrão: setores sem valor são filtrados da camada, mas a expressão é avaliada
  // antes do filtro em alguns caminhos do MapLibre e acusava null
  return ['step', ['to-number', ['get', indicadorId], 0], ...passos] as unknown as maplibregl.ExpressionSpecification
}

const MapaSetores = forwardRef<MapaSetoresHandle, MapaSetoresProps>(function MapaSetores(
  { fc, ano, indicador, indicadores, breaks, tema, mostrarMancha, manifesto, selecionado, hover, onHover, onClick, interativo = true, className },
  ref,
) {
  const elRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MLMap | null>(null)
  const popupRef = useRef<maplibregl.Popup | null>(null)
  const [pronto, setPronto] = useState(false)
  const ajustadoRef = useRef(false)
  const indicadoresRef = useRef(indicadores)
  const anoRef = useRef(ano)

  useImperativeHandle(ref, () => ({
    get map() {
      return mapRef.current
    },
  }))

  useEffect(() => {
    indicadoresRef.current = indicadores
    anoRef.current = ano
  }, [indicadores, ano])

  // cria o mapa uma única vez
  useEffect(() => {
    if (!elRef.current) return
    const m = criarMapa(elRef.current, { tema, interativo })
    mapRef.current = m

    m.on('load', () => {
      m.addSource(FONTE_SETORES, { type: 'geojson', data: { type: 'FeatureCollection', features: [] } })
      m.addLayer(
        { id: 'setor-outros', type: 'fill', source: FONTE_SETORES, filter: ['!=', ['get', 'pertence'], 'sede'], paint: { 'fill-color': tokens(tema).contexto, 'fill-opacity': 0.22 } },
        'rotulos',
      )
      m.addLayer(
        {
          id: 'setor-dados',
          type: 'fill',
          source: FONTE_SETORES,
          filter: ['all', ['==', ['get', 'pertence'], 'sede'], ['!=', ['get', indicador.id], null]],
          paint: { 'fill-color': tokens(tema).seq[2], 'fill-opacity': 0.88 },
        },
        'rotulos',
      )
      m.addLayer(
        {
          id: 'setor-semdado',
          type: 'fill',
          source: FONTE_SETORES,
          filter: ['all', ['==', ['get', 'pertence'], 'sede'], ['==', ['get', indicador.id], null]],
          paint: { 'fill-color': tokens(tema).contexto, 'fill-opacity': 0.06 },
        },
        'rotulos',
      )
      m.addLayer(
        { id: 'setor-linha', type: 'line', source: FONTE_SETORES, paint: { 'line-color': tokens(tema).superficie, 'line-width': 0.6, 'line-opacity': 0.8 } },
        'rotulos',
      )
      m.addLayer(
        {
          id: 'setor-destaque',
          type: 'line',
          source: FONTE_SETORES,
          filter: ['==', ['get', 'cod_setor'], '__nenhum__'],
          paint: { 'line-color': tokens(tema).texto, 'line-width': 2.5 },
        },
        'rotulos',
      )
      m.addSource(FONTE_MANCHA, { type: 'geojson', data: { type: 'FeatureCollection', features: [] } })
      m.addLayer(
        { id: 'setor-mancha', type: 'line', source: FONTE_MANCHA, layout: { visibility: 'none' }, paint: { 'line-color': tokens(tema).enfase, 'line-width': 1.2, 'line-dasharray': [2, 1.5] } },
        'rotulos',
      )
      setPronto(true)
    })

    const CAMADAS_INTERATIVAS = ['setor-dados', 'setor-semdado', 'setor-outros']
    if (interativo) {
      popupRef.current = new maplibregl.Popup({ closeButton: false, closeOnClick: false, className: 'mapa-popup', maxWidth: '260px' })
      m.on('mousemove', (e) => {
        const layers = CAMADAS_INTERATIVAS.filter((id) => m.getLayer(id))
        if (!layers.length) return
        const f = m.queryRenderedFeatures(e.point, { layers })[0]
        if (!f) {
          m.getCanvas().style.cursor = ''
          onHover(null)
          popupRef.current?.remove()
          return
        }
        m.getCanvas().style.cursor = 'pointer'
        onHover(String(f.properties?.cod_setor ?? ''))
        popupRef.current?.setLngLat(e.lngLat).setHTML(tooltipHtml(f.properties ?? {}, indicadoresRef.current, anoRef.current)).addTo(m)
      })
      m.on('mouseleave', () => {
        m.getCanvas().style.cursor = ''
        onHover(null)
        popupRef.current?.remove()
      })
      m.on('click', (e) => {
        const layers = CAMADAS_INTERATIVAS.filter((id) => m.getLayer(id))
        if (!layers.length) return
        const f = m.queryRenderedFeatures(e.point, { layers })[0]
        const cod = f?.properties?.cod_setor
        if (cod) onClick(String(cod))
      })
    }

    return () => {
      popupRef.current?.remove()
      m.remove()
      mapRef.current = null
      setPronto(false)
      ajustadoRef.current = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // tema: troca a base preservando as camadas próprias
  useEffect(() => {
    const m = mapRef.current
    if (!m || !pronto) return
    trocarTemaBase(m, tema)
    const v = tokens(tema)
    m.setPaintProperty('setor-outros', 'fill-color', v.contexto)
    m.setPaintProperty('setor-semdado', 'fill-color', v.contexto)
    m.setPaintProperty('setor-linha', 'line-color', v.superficie)
    m.setPaintProperty('setor-destaque', 'line-color', v.texto)
    if (breaks) m.setPaintProperty('setor-dados', 'fill-color', expressaoCor(indicador.id, breaks, v))
  }, [tema, pronto, breaks, indicador.id])

  // dados: troca a FeatureCollection e ajusta o mapa ao bbox da sede na 1ª carga
  useEffect(() => {
    const m = mapRef.current
    if (!m || !pronto || !fc) return
    ;(m.getSource(FONTE_SETORES) as maplibregl.GeoJSONSource).setData(fc)
    if (!ajustadoRef.current) {
      const sede = { type: 'FeatureCollection', features: fc.features.filter((f) => f.properties.pertence === 'sede') } as SetorFC
      const b = bboxFC(sede.features.length ? sede : fc)
      if (b) m.fitBounds(b, { padding: 24, duration: 0 })
      ajustadoRef.current = true
    }
  }, [fc, pronto])

  // filtros e cor: mudam com o indicador escolhido
  useEffect(() => {
    const m = mapRef.current
    if (!m || !pronto) return
    m.setFilter('setor-dados', ['all', ['==', ['get', 'pertence'], 'sede'], ['!=', ['get', indicador.id], null]])
    m.setFilter('setor-semdado', ['all', ['==', ['get', 'pertence'], 'sede'], ['==', ['get', indicador.id], null]])
    m.setPaintProperty('setor-dados', 'fill-color', expressaoCor(indicador.id, breaks, tokens(tema)))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pronto, indicador.id, breaks])

  // realce de hover/seleção
  useEffect(() => {
    const m = mapRef.current
    if (!m || !pronto) return
    const alvo = hover ?? selecionado
    m.setFilter('setor-destaque', ['==', ['get', 'cod_setor'], alvo ?? '__nenhum__'])
    m.setPaintProperty('setor-destaque', 'line-width', hover && hover === alvo ? 2.5 : 3)
  }, [hover, selecionado, pronto])

  // contorno opcional da mancha urbana 2022 (classe 1: sede contígua)
  useEffect(() => {
    const m = mapRef.current
    if (!m || !pronto) return
    if (!mostrarMancha) {
      m.setLayoutProperty('setor-mancha', 'visibility', 'none')
      return
    }
    const camada = manifesto?.camadas.find((c) => c.id === 'mancha_propria')
    if (!camada) return
    let vivo = true
    carregarGeojson(camada, 2022).then((g) => {
      if (!vivo || !mapRef.current) return
      const fcMancha = { ...g, features: g.features.filter((f) => Number(f.properties?.classe) === 1) }
      ;(mapRef.current.getSource(FONTE_MANCHA) as maplibregl.GeoJSONSource).setData(fcMancha)
      // contorno da mancha na cor oficial da classe urbana (MapBiomas 24), lida do manifesto
      const corUrbano = camada.legenda?.find((l) => l.classe === 1)?.cor
      if (corUrbano) mapRef.current.setPaintProperty('setor-mancha', 'line-color', corUrbano)
      mapRef.current.setLayoutProperty('setor-mancha', 'visibility', 'visible')
    })
    return () => {
      vivo = false
    }
  }, [mostrarMancha, manifesto, pronto])

  return <div ref={elRef} className={'mapa-setores' + (className ? ' ' + className : '')} />
})

export default MapaSetores
