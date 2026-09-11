// Mini-mapa SVG leve da mancha urbana (classe 1) de um ano censitário, com a mesma janela
// geográfica para os quatro censos (comparável) e o contorno de 2022 como referência de
// contexto. Projeção equirretangular com escala em metros (longitude corrigida por cos(lat)),
// sem dependência de MapLibre — a aba Mancha (outro agente) já cobre o mapa interativo completo.
import { useEffect, useState } from 'react'
import { loadJSON } from '../../lib/data'
import { useTema } from '../../lib/theme'
import { useManifesto } from '../../lib/mapa'

// Janela fixa dos quatro mini-mapas: o corpo principal da sede (≈ 9 × 10 km em torno do núcleo
// histórico). O bbox da classe 1 de 2026 inteira (16 × 17 km, com braços ao longo das estradas)
// deixava a cidade minúscula; o que sai da janela é recortado pelo SVG.
const JANELA_MINIMAPA: [[number, number], [number, number]] = [
  [-49.918, -6.556],
  [-49.836, -6.462],
]

const M_POR_GRAU_LAT = 110540
function mPorGrauLon(latRef: number): number {
  return 111320 * Math.cos((latRef * Math.PI) / 180)
}

interface Projecao {
  ponto(lon: number, lat: number): [number, number]
  pxPorMetro: number
}

function projetar(w: number, h: number, pad = 10): Projecao {
  const [[minLon, minLat], [maxLon, maxLat]] = JANELA_MINIMAPA
  const latRef = (minLat + maxLat) / 2
  const mx = mPorGrauLon(latRef)
  const spanXm = (maxLon - minLon) * mx
  const spanYm = (maxLat - minLat) * M_POR_GRAU_LAT
  const escala = Math.min((w - 2 * pad) / spanXm, (h - 2 * pad) / spanYm)
  const offX = (w - spanXm * escala) / 2
  const offY = (h - spanYm * escala) / 2
  return {
    ponto: (lon, lat) => [(lon - minLon) * mx * escala + offX, (maxLat - lat) * M_POR_GRAU_LAT * escala + offY],
    pxPorMetro: escala,
  }
}

function anelParaPath(anel: number[][], proj: Projecao): string {
  return (
    anel
      .map(([lon, lat], i) => {
        const [x, y] = proj.ponto(lon, lat)
        return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`
      })
      .join(' ') + 'Z'
  )
}

function geometriaParaPath(geom: GeoJSON.Geometry, proj: Projecao): string {
  if (geom.type === 'Polygon') return geom.coordinates.map((a) => anelParaPath(a, proj)).join(' ')
  if (geom.type === 'MultiPolygon') return geom.coordinates.map((p) => p.map((a) => anelParaPath(a, proj)).join(' ')).join(' ')
  return ''
}

function pathClasse1(geo: GeoJSON.FeatureCollection | undefined, proj: Projecao): string {
  if (!geo) return ''
  return geo.features
    .filter((f) => f.properties?.classe === 1)
    .map((f) => geometriaParaPath(f.geometry, proj))
    .join(' ')
}

interface Props {
  ano: number
  arquivo: string
  /** GeoJSON de 2022 já carregado, para desenhar como contorno de referência (omitido no próprio 2022). */
  contexto?: GeoJSON.FeatureCollection
  titulo: string
}

export function MiniMapaMancha({ ano, arquivo, contexto, titulo }: Props) {
  const { viz } = useTema()
  // classe de uso do solo: cor oficial MapBiomas (classe 24) lida do manifesto, não da paleta Ardósia
  const { data: man } = useManifesto()
  const corUrbano = man?.camadas.find((c) => c.id === 'mancha_propria')?.legenda?.find((l) => l.classe === 1)?.cor ?? viz.cat[0]
  const [geo, setGeo] = useState<GeoJSON.FeatureCollection | undefined>(undefined)
  const [erro, setErro] = useState(false)
  useEffect(() => {
    let vivo = true
    setGeo(undefined)
    setErro(false)
    loadJSON<GeoJSON.FeatureCollection>(arquivo)
      .then((g) => vivo && setGeo(g))
      .catch(() => vivo && setErro(true))
    return () => {
      vivo = false
    }
  }, [arquivo])

  const w = 210
  const h = 170
  const proj = projetar(w, h)
  const path = pathClasse1(geo, proj)
  const pathContexto = ano === 2022 ? '' : pathClasse1(contexto, proj)
  const escala1km = 1000 * proj.pxPorMetro

  if (erro) return <p className="nota-miuda">Mancha de {ano} indisponível.</p>

  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      width="100%"
      height={h}
      role="img"
      aria-label={`Mancha urbana da sede em ${ano}, na mesma janela geográfica dos demais censos (contorno fino cinza = extensão de 2022 como referência).`}
    >
      <rect x={0} y={0} width={w} height={h} fill={viz.superficie} />
      {pathContexto && <path d={pathContexto} fill="none" stroke={viz.contexto} strokeWidth={0.75} />}
      {path ? (
        <path d={path} fill={corUrbano} stroke="none" />
      ) : (
        !geo && !erro && <text x={w / 2} y={h / 2} textAnchor="middle" fontSize={10} fill={viz.texto3}>carregando…</text>
      )}
      <g>
        <line x1={10} y1={h - 12} x2={10 + escala1km} y2={h - 12} stroke={viz.texto3} strokeWidth={1.25} />
        <line x1={10} y1={h - 15} x2={10} y2={h - 9} stroke={viz.texto3} strokeWidth={1} />
        <line x1={10 + escala1km} y1={h - 15} x2={10 + escala1km} y2={h - 9} stroke={viz.texto3} strokeWidth={1} />
        <text x={10 + escala1km / 2} y={h - 18} textAnchor="middle" fontSize={9} fill={viz.texto3} fontFamily="var(--ard-sans)">
          1 km
        </text>
      </g>
      <text x={6} y={14} fontSize={11} fill={viz.texto} fontWeight={600}>
        {titulo}
      </text>
    </svg>
  )
}
