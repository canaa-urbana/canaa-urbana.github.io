// Utilitários MapLibre compartilhados pelas abas (Mancha, Início, Setores, Migração).
// O manifesto `data/geo/camadas.json` (E3c) é a única porta de entrada das camadas:
// arquivo, anos, cores (com a fonte de cada cor), atribuição e licença.
import maplibregl, { type Map as MLMap, type StyleSpecification } from 'maplibre-gl'
import { dataUrl, loadJSON, useJSON } from './data'
import type { Tema } from './theme'

export { maplibregl }
export type { MLMap }

/** Janela de análise da sede (bbox das imagens, EPSG:4326). */
export const JANELA_SEDE: [[number, number], [number, number]] = [
  [-49.990521, -6.600815],
  [-49.749323, -6.399458],
]
export const CENTRO_SEDE: [number, number] = [-49.874, -6.5]

export interface ItemLegenda {
  classe?: number | string
  rotulo: string
  cor?: string
  contorno?: string
  opacidade?: number
  fonte_cor?: string
  [k: string]: unknown
}

export interface Camada {
  id: string
  titulo: string
  tipo: 'geojson' | 'image'
  arquivo: string
  grupo: 'mancha' | 'comparacao' | 'setores' | 'limites' | 'mineracao_infra' | 'imagens'
  anos?: number[]
  coordenadas?: [number, number][]
  propriedade?: string
  propriedade_classe?: string
  legenda?: ItemLegenda[]
  legenda_de?: string
  rampa?: string[]
  dominio?: [number, number]
  cor?: string
  cor_ferrovia?: string
  contorno?: string
  opacidade?: number
  fonte_cor?: string
  atribuicao: string
  licenca?: string
  notas?: string
  origem_etapa?: string
}

export interface Manifesto {
  gerado_em: string
  camadas: Camada[]
}

export const GRUPOS: { id: Camada['grupo']; rotulo: string }[] = [
  { id: 'mancha', rotulo: 'Mancha urbana (classificação própria)' },
  { id: 'comparacao', rotulo: 'Produtos de comparação' },
  { id: 'setores', rotulo: 'Setores censitários' },
  { id: 'mineracao_infra', rotulo: 'Mineração e infraestrutura' },
  { id: 'limites', rotulo: 'Limites' },
  { id: 'imagens', rotulo: 'Imagens de satélite (fundo)' },
]

export function useManifesto() {
  return useJSON<Manifesto>('geo/camadas.json')
}

/** Caminho de um arquivo da camada para um ano (substitui {ano}). */
export function arquivoCamada(c: Camada, ano?: number | null): string {
  return c.arquivo.replace('{ano}', String(ano ?? ''))
}

/** Ano disponível mais próximo ≤ `ano` (ou o primeiro, se `ano` for anterior a todos). */
export function anoDisponivel(anos: number[] | undefined, ano: number): number | null {
  if (!anos || !anos.length) return null
  let r: number | null = null
  for (const a of anos) if (a <= ano) r = a
  return r
}

/** GeoJSON de uma camada (com cache de `loadJSON`). */
export function carregarGeojson(c: Camada, ano?: number | null): Promise<GeoJSON.FeatureCollection> {
  return loadJSON<GeoJSON.FeatureCollection>(arquivoCamada(c, ano))
}

// ---------------------------------------------------------------------------
// Estilo de base: OpenFreeMap (vetorial, dados OpenStreetMap, sem chave de API) —
// "positron" no tema claro e "dark" no escuro. As camadas temáticas entram abaixo
// dos rótulos da base: a camada-marcador invisível 'rotulos' fica logo antes do
// primeiro `symbol` do estilo, e as abas usam `beforeId: 'rotulos'`.
// (A CARTO passou a exigir chave em 2026; por isso a troca.)
// ---------------------------------------------------------------------------

const ESTILO_URL: Record<Tema, string> = {
  light: 'https://tiles.openfreemap.org/styles/positron',
  dark: 'https://tiles.openfreemap.org/styles/dark',
}
/** Fundo da base na cor de figura Ardósia (claro quase branco), igual ao card que o contém. */
const FUNDO: Record<Tema, string> = { light: '#FAFAF9', dark: '#171B1E' }
const FONTES_BASE = new Set(['openmaptiles', 'ne2_shaded'])
export const ATRIB_BASE =
  '<a href="https://openfreemap.org" target="_blank">OpenFreeMap</a> © <a href="https://www.openmaptiles.org/" target="_blank">OpenMapTiles</a>, dados © contribuidores do <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>'
/** Fonte de texto disponível nos glifos do OpenFreeMap (para camadas `symbol` próprias). */
export const FONTE_MAPA = ['Noto Sans Regular']

type Camadas = StyleSpecification['layers']
const MARCADOR = { id: 'rotulos', type: 'background', paint: { 'background-opacity': 0 } } as Camadas[number]

function inserirMarcador(camadas: Camadas, tema: Tema, extras: Camadas = []): Camadas {
  const ls = camadas
    .filter((l) => l.id !== 'rotulos')
    .map((l) => (l.type === 'background' ? { ...l, paint: { ...(l.paint ?? {}), 'background-color': FUNDO[tema] } } : l)) as Camadas
  ls.splice(inicioRotulos(ls), 0, ...extras, MARCADOR)
  return ls
}

/** Índice logo após a última camada que não é `symbol` (no estilo "dark" há símbolos
 *  intercalados entre as linhas; as camadas próprias precisam ficar acima de todas as linhas). */
function inicioRotulos(ls: Camadas): number {
  let i = ls.length
  while (i > 0 && ls[i - 1].type === 'symbol') i--
  return i
}

export function estiloBase(tema: Tema): string {
  return ESTILO_URL[tema]
}

/** Primeira carga do estilo: marcador 'rotulos' antes do primeiro símbolo e fundo Ardósia.
 *  Roda em 'style.load', que sempre precede o 'load' em que as abas adicionam camadas. */
function prepararPrimeiraCarga(m: MLMap, tema: Tema) {
  const camadas = m.getStyle().layers
  for (const l of camadas) if (l.type === 'background') m.setPaintProperty(l.id, 'background-color', FUNDO[tema])
  if (!m.getLayer('rotulos')) m.addLayer(MARCADOR, camadas[inicioRotulos(camadas)]?.id)
}

/** Troca de tema: novo estilo da base preservando fontes e camadas próprias (acima e abaixo do marcador). */
function transformarTema(tema: Tema) {
  return (prev: StyleSpecification | undefined, next: StyleSpecification): StyleSpecification => {
    if (!prev) return { ...next, layers: inserirMarcador(next.layers, tema) }
    const proprias = (l: Camadas[number]) => l.id !== 'rotulos' && 'source' in l && !FONTES_BASE.has(l.source as string)
    const iMarc = prev.layers.findIndex((l) => l.id === 'rotulos')
    const abaixo = prev.layers.filter((l, i) => proprias(l) && (iMarc < 0 || i < iMarc))
    const acima = prev.layers.filter((l, i) => proprias(l) && iMarc >= 0 && i > iMarc)
    const fontes = Object.fromEntries(Object.entries(prev.sources).filter(([k]) => !FONTES_BASE.has(k)))
    return {
      ...next,
      sources: { ...next.sources, ...fontes },
      layers: [...inserirMarcador(next.layers, tema, abaixo), ...acima],
    }
  }
}

export interface OpcoesMapa {
  tema: Tema
  interativo?: boolean
  limites?: [[number, number], [number, number]]
  padding?: number
}

/** Cria um mapa MapLibre ajustado à janela da sede, com escala e controles discretos. */
export function criarMapa(el: HTMLElement, o: OpcoesMapa): MLMap {
  const m = new maplibregl.Map({
    container: el,
    style: estiloBase(o.tema),
    bounds: o.limites ?? JANELA_SEDE,
    fitBoundsOptions: { padding: o.padding ?? 16 },
    interactive: o.interativo ?? true,
    attributionControl: { compact: true },
    cooperativeGestures: false,
    maxZoom: 17,
    minZoom: o.limites ? 2 : 5, // mapas de contexto nacional (fluxos) precisam afastar mais
    locale: {
      'NavigationControl.ZoomIn': 'Aproximar',
      'NavigationControl.ZoomOut': 'Afastar',
      'NavigationControl.ResetBearing': 'Norte para cima',
      'AttributionControl.ToggleAttribution': 'Atribuições',
      'ScaleControl.Kilometers': 'km',
      'ScaleControl.Meters': 'm',
    },
  })
  m.once('style.load', () => prepararPrimeiraCarga(m, o.tema))
  // o estilo do OpenFreeMap referencia padrões que não estão no sprite (ex.: 'wood-pattern'):
  // entra um pixel transparente para não poluir o console
  m.on('styleimagemissing', (e: { id: string }) => {
    if (!m.hasImage(e.id)) m.addImage(e.id, { width: 1, height: 1, data: new Uint8Array(4) })
  })
  temaDoMapa.set(m, o.tema)
  // O MapLibre só acompanha o redimensionamento da janela; mapas criados enquanto o contêiner
  // ainda está sendo diagramado (grade, aba recém-aberta) nasciam estreitos e mal enquadrados.
  // Observa o contêiner e, enquanto o usuário não mexeu no mapa, reenquadra nos limites.
  let mexeu = false
  m.on('movestart', (e: { originalEvent?: unknown }) => {
    if (e.originalEvent) mexeu = true
  })
  const ro = new ResizeObserver(() => {
    m.resize()
    if (!mexeu) m.fitBounds(o.limites ?? JANELA_SEDE, { padding: o.padding ?? 16, animate: false })
  })
  ro.observe(el)
  m.once('remove', () => ro.disconnect())
  // atribuição recolhida no início (o botão "i" abre): com várias camadas ativas o texto
  // expandido cobre a base do mapa
  m.once('load', () => m.getContainer().querySelector('.maplibregl-ctrl-attrib')?.classList.remove('maplibregl-compact-show'))
  if (o.interativo ?? true) {
    m.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
    m.addControl(new maplibregl.ScaleControl({ unit: 'metric', maxWidth: 100 }), 'bottom-left')
  }
  return m
}

const temaDoMapa = new WeakMap<MLMap, Tema>()

/** Troca a base (claro/escuro) sem recriar o mapa: carrega o outro estilo do OpenFreeMap
 *  preservando todas as fontes e camadas próprias e o marcador 'rotulos'. */
export function trocarTemaBase(m: MLMap, tema: Tema) {
  if (temaDoMapa.get(m) === tema) return
  temaDoMapa.set(m, tema)
  m.setStyle(ESTILO_URL[tema], { transformStyle: transformarTema(tema) })
}

/** Expressão de cor por classe a partir da legenda do manifesto. */
export function corPorClasse(prop: string, legenda: ItemLegenda[], padrao = '#7B7D78'): maplibregl.ExpressionSpecification {
  const pares: (string | number)[] = []
  for (const l of legenda) if (l.classe !== undefined && l.cor) pares.push(l.classe as number, l.cor)
  return ['match', ['get', prop], ...pares, padrao] as unknown as maplibregl.ExpressionSpecification
}

/** Expressão de opacidade por classe a partir da legenda. */
export function opacidadePorClasse(prop: string, legenda: ItemLegenda[], fator = 1): maplibregl.ExpressionSpecification {
  const pares: (string | number)[] = []
  for (const l of legenda) if (l.classe !== undefined) pares.push(l.classe as number, (l.opacidade ?? 0.7) * fator)
  return ['match', ['get', prop], ...pares, 0.6 * fator] as unknown as maplibregl.ExpressionSpecification
}

/** Rampa interpolada (ex.: ano de urbanização) a partir de `rampa` + `dominio`. */
export function corRampa(prop: string, rampa: string[], dominio: [number, number]): maplibregl.ExpressionSpecification {
  const [a, b] = dominio
  const passos: (string | number)[] = []
  rampa.forEach((c, i) => passos.push(a + ((b - a) * i) / (rampa.length - 1), c))
  return ['interpolate', ['linear'], ['get', prop], ...passos] as unknown as maplibregl.ExpressionSpecification
}

/** Expressão `case` para legendas com pares (propriedade, valor) → cor/contorno (ex.: AU 2022,
 *  que cruza `Densidade` e `Tipo` em vez de uma única classe numérica). `campo` é 'cor' ou 'contorno'. */
export function expressaoMultiAtributo(legenda: ItemLegenda[], campo: 'cor' | 'contorno'): maplibregl.ExpressionSpecification | null {
  const casos: unknown[] = []
  for (const l of legenda) {
    const v = l[campo]
    const prop = (l as Record<string, unknown>).propriedade as string | undefined
    const valor = (l as Record<string, unknown>).valor as string | undefined
    if (v && prop && valor) {
      casos.push(['==', ['get', prop], valor], v)
    }
  }
  if (!casos.length) return null
  return ['case', ...casos, 'rgba(0,0,0,0)'] as unknown as maplibregl.ExpressionSpecification
}

/** Cantos [sup-esq, sup-dir, inf-dir, inf-esq] em lon/lat prontos para `image` source do MapLibre. */
export function coordenadasImagem(c: Camada): [[number, number], [number, number], [number, number], [number, number]] | null {
  const co = c.coordenadas
  if (!co || co.length !== 4) return null
  return [co[0], co[1], co[2], co[3]]
}

/** Cria (se preciso) ou atualiza a `image` source de uma camada de imagem para o ano/URL dado. */
export function definirImagem(m: MLMap, sourceId: string, c: Camada, ano: number | null) {
  const url = dataUrl(arquivoCamada(c, ano))
  const coords = coordenadasImagem(c)
  if (!coords) return
  const src = m.getSource(sourceId) as maplibregl.ImageSource | undefined
  if (src) {
    src.updateImage({ url, coordinates: coords })
  } else {
    m.addSource(sourceId, { type: 'image', url, coordinates: coords })
  }
}

/** Pré-carrega a imagem de um ano (cache do navegador) sem afetar o mapa — usado no autoplay. */
export function precarregarImagem(c: Camada, ano: number | null) {
  if (ano === null) return
  const img = new Image()
  img.src = dataUrl(arquivoCamada(c, ano))
}

export { dataUrl }
