// Mapa de fluxos migratórios em MapLibre: arcos das capitais estaduais de origem até Canaã dos
// Carajás sobre o mapa base (contexto geográfico real, ao contrário do SVG solto anterior).
// Espessura do arco ∝ estimativa; só desenha células publicadas (a fusão "outros:" some só na
// tabela, nunca como arco). Rolagem da página nunca é capturada (scrollZoom desligado).
import { useEffect, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import { criarMapa, trocarTemaBase, FONTE_MAPA, type MLMap } from '../../lib/mapa'
import { useTema } from '../../lib/theme'
import { fmtNum, fmtPct } from '../../lib/format'
import { CAPITAIS_UF, CANAA } from '../censos/estimativas'
import type { Classe } from '../../lib/data'

export interface FluxoUF {
  uf: string
  valor: number
  cv: number | null
  classe: Classe | null
  /** Volume estimado de migrantes (contagem ponderada, arredondada pelo gate). */
  pessoas?: number | null
}

/** Bbox aproximado do Brasil, com folga (o `criarMapa` ajusta com `padding`). */
const LIMITES_BRASIL: [[number, number], [number, number]] = [
  [-74, -34],
  [-34, 6],
]

const LARGURA_MIN = 1
const LARGURA_MAX = 10

/** Amostra uma curva de Bézier quadrática (arco suave) entre dois pontos em lon/lat, com o ponto
 *  de controle deslocado na perpendicular — mesma construção do SVG anterior, agora em GeoJSON. */
function arco(a: [number, number], b: [number, number], n = 32): [number, number][] {
  const [x1, y1] = a
  const [x2, y2] = b
  const mx = (x1 + x2) / 2
  const my = (y1 + y2) / 2
  const dx = x2 - x1
  const dy = y2 - y1
  const cx = mx - dy * 0.15
  const cy = my + dx * 0.15
  const pts: [number, number][] = []
  for (let i = 0; i <= n; i++) {
    const t = i / n
    const u = 1 - t
    pts.push([u * u * x1 + 2 * u * t * cx + t * t * x2, u * u * y1 + 2 * u * t * cy + t * t * y2])
  }
  return pts
}

function propriedades(d: FluxoUF) {
  return { uf: d.uf, valor: d.valor, pessoas: d.pessoas ?? null, cv: d.cv, classe: d.classe ?? 'boa' }
}

function arcosGeojson(dados: FluxoUF[]): GeoJSON.FeatureCollection {
  const maxValor = Math.max(1, ...dados.map((d) => d.valor))
  return {
    type: 'FeatureCollection',
    features: dados
      .filter((d) => CAPITAIS_UF[d.uf])
      .map((d) => {
        const largura = LARGURA_MIN + Math.sqrt(d.valor / maxValor) * (LARGURA_MAX - LARGURA_MIN)
        return {
          type: 'Feature',
          properties: { ...propriedades(d), largura },
          geometry: { type: 'LineString', coordinates: arco(CAPITAIS_UF[d.uf], CANAA) },
        }
      }),
  }
}

function ufsGeojson(dados: FluxoUF[]): GeoJSON.FeatureCollection {
  return {
    type: 'FeatureCollection',
    features: dados
      .filter((d) => CAPITAIS_UF[d.uf])
      .map((d) => ({
        type: 'Feature',
        properties: propriedades(d),
        geometry: { type: 'Point', coordinates: CAPITAIS_UF[d.uf] },
      })),
  }
}

function tooltipHtml(props: Record<string, unknown>): string {
  const pessoas = props.pessoas as number | null
  const linhas = [
    pessoas != null
      ? `<tr><th>Migrantes</th><td><b>${fmtNum(pessoas)}</b> pessoas</td></tr>`
      : '',
    `<tr><th>Participação</th><td><b>${fmtPct(props.valor as number)}</b> dos migrantes internos</td></tr>`,
    `<tr class="mapa-tooltip__destaque"><th>Precisão</th><td><b>CV ${fmtPct(props.cv as number)}</b> (${props.classe})</td></tr>`,
  ]
  return `<div class="mapa-tooltip"><p class="mapa-tooltip__titulo">${props.uf} → Canaã dos Carajás</p><table>${linhas.join('')}</table></div>`
}

const DESTINO: GeoJSON.FeatureCollection = {
  type: 'FeatureCollection',
  features: [{ type: 'Feature', properties: { nome: 'Canaã dos Carajás' }, geometry: { type: 'Point', coordinates: CANAA } }],
}

export function FlowMap({ dados }: { dados: FluxoUF[] }) {
  const el = useRef<HTMLDivElement>(null)
  const mapa = useRef<MLMap | null>(null)
  const popupRef = useRef<maplibregl.Popup | null>(null)
  const [pronto, setPronto] = useState(false)
  const { tema, viz } = useTema()

  // cria o mapa uma vez
  useEffect(() => {
    if (!el.current) return
    const m = criarMapa(el.current, { tema, limites: LIMITES_BRASIL, padding: 28, interativo: true })
    m.scrollZoom.disable() // a página precisa rolar por cima do mapa
    mapa.current = m
    m.on('load', () => {
      m.addSource('arcos', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } })
      m.addSource('ufs', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } })
      m.addSource('destino', { type: 'geojson', data: DESTINO })
      m.addLayer(
        {
          id: 'arcos',
          type: 'line',
          source: 'arcos',
          layout: { 'line-cap': 'round', 'line-join': 'round' },
          paint: { 'line-color': viz.enfase, 'line-opacity': 0.8, 'line-width': ['get', 'largura'] },
        },
        'rotulos',
      )
      // faixa invisível e larga sobre cada arco: um arco de 1–2 px é quase impossível de acertar
      // com o mouse, então o alvo do hover é esta camada, não a linha desenhada.
      m.addLayer(
        {
          id: 'arcos-toque',
          type: 'line',
          source: 'arcos',
          layout: { 'line-cap': 'round', 'line-join': 'round' },
          paint: { 'line-color': viz.enfase, 'line-opacity': 0, 'line-width': ['max', ['get', 'largura'], 14] },
        },
        'rotulos',
      )
      m.addLayer(
        { id: 'ufs-pontos', type: 'circle', source: 'ufs', paint: { 'circle-radius': 3.5, 'circle-color': viz.cat[0], 'circle-stroke-width': 1.25, 'circle-stroke-color': viz.superficie } },
        'rotulos',
      )
      m.addLayer(
        {
          id: 'ufs-rotulos',
          type: 'symbol',
          source: 'ufs',
          layout: { 'text-field': ['get', 'uf'], 'text-font': FONTE_MAPA, 'text-size': 10, 'text-offset': [0.7, 0], 'text-anchor': 'left' },
          paint: { 'text-color': viz.texto2, 'text-halo-color': viz.superficie, 'text-halo-width': 1.4 },
        },
        'rotulos',
      )
      m.addLayer(
        { id: 'destino-ponto', type: 'circle', source: 'destino', paint: { 'circle-radius': 6, 'circle-color': viz.marco, 'circle-stroke-width': 1.5, 'circle-stroke-color': viz.superficie } },
        'rotulos',
      )
      m.addLayer(
        {
          id: 'destino-rotulo',
          type: 'symbol',
          source: 'destino',
          layout: { 'text-field': ['get', 'nome'], 'text-font': FONTE_MAPA, 'text-size': 11, 'text-offset': [0.9, 0], 'text-anchor': 'left' },
          paint: { 'text-color': viz.texto, 'text-halo-color': viz.superficie, 'text-halo-width': 1.4 },
        },
        'rotulos',
      )
      const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, className: 'mapa-popup', maxWidth: 'none' })
      popupRef.current = popup
      for (const camada of ['arcos-toque', 'ufs-pontos', 'ufs-rotulos'] as const) {
        m.on('mousemove', camada, (e) => {
          const f = e.features?.[0]
          if (!f) return
          m.getCanvas().style.cursor = 'pointer'
          popup.setLngLat(e.lngLat).setHTML(tooltipHtml(f.properties ?? {})).addTo(m)
        })
        m.on('mouseleave', camada, () => {
          m.getCanvas().style.cursor = ''
          popup.remove()
        })
      }
      setPronto(true)
    })
    return () => {
      popupRef.current?.remove()
      popupRef.current = null
      m.remove()
      mapa.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // troca de tema preservando as camadas próprias
  useEffect(() => {
    if (mapa.current && pronto) trocarTemaBase(mapa.current, tema)
  }, [tema, pronto])

  // recoloração ao trocar de tema (as camadas sobrevivem ao setStyle, mas o paint precisa ser
  // reaplicado com os novos hex do tema)
  useEffect(() => {
    const m = mapa.current
    if (!m || !pronto) return
    if (m.getLayer('arcos')) m.setPaintProperty('arcos', 'line-color', viz.enfase)
    if (m.getLayer('ufs-pontos')) {
      m.setPaintProperty('ufs-pontos', 'circle-color', viz.cat[0])
      m.setPaintProperty('ufs-pontos', 'circle-stroke-color', viz.superficie)
    }
    if (m.getLayer('ufs-rotulos')) {
      m.setPaintProperty('ufs-rotulos', 'text-color', viz.texto2)
      m.setPaintProperty('ufs-rotulos', 'text-halo-color', viz.superficie)
    }
    if (m.getLayer('destino-ponto')) {
      m.setPaintProperty('destino-ponto', 'circle-color', viz.marco)
      m.setPaintProperty('destino-ponto', 'circle-stroke-color', viz.superficie)
    }
    if (m.getLayer('destino-rotulo')) {
      m.setPaintProperty('destino-rotulo', 'text-color', viz.texto)
      m.setPaintProperty('destino-rotulo', 'text-halo-color', viz.superficie)
    }
  }, [viz, pronto])

  // atualiza os dados (troca de censo no seletor)
  useEffect(() => {
    const m = mapa.current
    if (!m || !pronto) return
    ;(m.getSource('arcos') as maplibregl.GeoJSONSource)?.setData(arcosGeojson(dados))
    ;(m.getSource('ufs') as maplibregl.GeoJSONSource)?.setData(ufsGeojson(dados))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dados, pronto])

  return (
    <div
      ref={el}
      className="mapa-fluxos"
      role="figure"
      aria-label="Mapa de fluxos migratórios das capitais estaduais de origem até Canaã dos Carajás, espessura do arco proporcional à estimativa. O arco mostra volume, participação e precisão ao passar o cursor; os mesmos valores estão na tabela abaixo."
    />
  )
}
