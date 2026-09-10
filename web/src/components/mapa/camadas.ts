// Motor de camadas do mapa da aba Mancha urbana: liga o manifesto (`geo/camadas.json`) a
// fontes/camadas do MapLibre, mantendo a ordem visual fixa. Troca de ano é sempre leve:
// imagem → `updateImage`; camadas com `anos` (mancha própria, MapBiomas, clareiras) → `setData`
// com o GeoJSON do novo ano (já em cache por `loadJSON`, sem nova requisição perceptível);
// camadas com rampa contínua (expansão, WSF-Evolution) → só troca o `filter`. Layers só são
// recriadas quando a camada liga/desliga, muda opacidade ou o tema claro/escuro muda de cor.
import type maplibregl from 'maplibre-gl'
import type { Camada, Manifesto, MLMap } from '../../lib/mapa'
import { carregarGeojson, corPorClasse, corRampa, definirImagem, expressaoMultiAtributo, opacidadePorClasse } from '../../lib/mapa'
import type { VizTokens } from '../../lib/theme'

export const ORDEM_CAMADAS = [
  'imagem-ativa',
  'mancha_mapbiomas',
  'ghsl',
  'wsf_evolution',
  'wsf2019',
  'areas_urbanizadas_2019_revisado',
  'areas_urbanizadas_2022',
  'expansao',
  'mineracao_mascara',
  'mancha_propria10',
  'mancha_propria',
  'mancha_propria-fantasma',
  'clareira_mss',
  'setores_2010',
  'setores_2022',
  'anm_lavra',
  'osm_rodovias_regiao',
  'osm_ferrovia',
  'osm_vias',
  'nucleo_historico',
  'aoi_municipio',
  'aoi_sede',
] as const

export const GRUPO_IMAGENS = ['landsat_cor', 'landsat_falsacor', 's2_cor', 'mss_falsacor']
export const CAMADAS_PADRAO_ON = new Set(['mancha_propria', 'nucleo_historico', 'osm_vias'])
export const IMAGEM_PADRAO = 'landsat_cor'

interface Meta {
  sourceIds: string[]
  layerIds: string[]
  fator: number
  tema: 'light' | 'dark'
  ano: number | null
}

const COR_NEUTRA_CLARO = '#7B7D78'
const COR_NEUTRA_ESCURO = '#7E8A90'
function corNeutra(viz: VizTokens): string {
  return viz.tema === 'dark' ? COR_NEUTRA_ESCURO : COR_NEUTRA_CLARO
}

function anoMaisProximo(anos: number[], ano: number): number | null {
  let r: number | null = null
  for (const a of anos) if (a <= ano) r = a
  return r
}
function anoAnterior(anos: number[], ano: number): number | null {
  let r: number | null = null
  for (const a of anos) if (a < ano) r = a
  return r
}
/** Ano a usar para uma camada com `anos`: `mancha_propria10` exige presença exata no ano
 *  (a série secundária só existe 2017–2026); as demais usam o mais próximo ≤ ano (ex.: GHSL). */
function anoParaCamada(c: Camada, ano: number): number | null {
  if (!c.anos) return null
  if (c.id === 'mancha_propria10') return c.anos.includes(ano) ? ano : null
  return anoMaisProximo(c.anos, ano)
}

/** Recupera o id da camada do manifesto a partir do id da layer real do MapLibre
 *  (`mancha_propria-fill` → `mancha_propria`, `img-landsat_cor-layer` → `landsat_cor`…). */
export function idLogicoDeLayer(layerId: string): string {
  return layerId
    .replace(/^img-/, '')
    .replace(/-layer$/, '')
    .replace(/-fill$/, '')
    .replace(/-linha\d*$/, '')
    .replace(/-hit$/, '')
    .replace(/-ponto$/, '')
}

interface SincOpcoes {
  manifesto: Manifesto
  ativos: Set<string>
  opacidades: Record<string, number>
  imagemAtiva: string | null
  ghost: boolean
  ano: number
  viz: VizTokens
}

export class ControladorCamadas {
  private presentes = new Map<string, Meta>()
  /** Fila: sincronizar/trocarAno são assíncronos (carregam GeoJSON); duas chamadas simultâneas
   *  (ex.: ligar duas camadas em sequência rápida) criavam a mesma layer duas vezes. */
  private fila: Promise<unknown> = Promise.resolve()
  private enfileirar<T>(f: () => Promise<T>): Promise<T> {
    const p = this.fila.then(f, f)
    this.fila = p.catch(() => undefined)
    return p
  }

  constructor(private map: MLMap) {}

  /** Id de uma layer REAL do MapLibre (nunca o id lógico da camada — `addLayer` recusa um
   *  beforeId que não exista) para ancorar a inserção logo abaixo da próxima camada presente
   *  na ordem fixa; usa a primeira layer daquele grupo (a mais no fundo dele). */
  private beforeId(id: string): string {
    const i = ORDEM_CAMADAS.indexOf(id as (typeof ORDEM_CAMADAS)[number])
    for (let j = i + 1; j < ORDEM_CAMADAS.length; j++) {
      const m = this.presentes.get(ORDEM_CAMADAS[j])
      if (m?.layerIds[0]) return m.layerIds[0]
    }
    return 'rotulos'
  }

  private remover(id: string) {
    const m = this.presentes.get(id)
    if (!m) return
    for (const l of m.layerIds) if (this.map.getLayer(l)) this.map.removeLayer(l)
    for (const s of m.sourceIds) if (this.map.getSource(s)) this.map.removeSource(s)
    this.presentes.delete(id)
  }

  destruir() {
    for (const id of Array.from(this.presentes.keys())) this.remover(id)
  }

  /** Sincronização completa: chamar quando ligam/desligam camadas, mudam opacidade, o tema ou
   *  a imagem ativa. Para só o ano (slider correndo), use `trocarAno`, bem mais barato. */
  sincronizar(o: SincOpcoes): Promise<void> {
    return this.enfileirar(() => this.sincronizarJa(o))
  }

  private async sincronizarJa(o: SincOpcoes) {
    const byId = new Map(o.manifesto.camadas.map((c) => [c.id, c]))
    const desejadas = new Set<string>()
    for (const id of o.ativos) {
      const c = byId.get(id)
      if (!c || c.grupo === 'imagens') continue
      if (c.anos && anoParaCamada(c, o.ano) === null) continue
      desejadas.add(id)
    }
    if (o.imagemAtiva) desejadas.add('imagem-ativa')
    if (o.ghost && o.ativos.has('mancha_propria')) desejadas.add('mancha_propria-fantasma')

    for (const id of Array.from(this.presentes.keys())) if (!desejadas.has(id)) this.remover(id)

    for (const id of desejadas) {
      const m = this.presentes.get(id)
      if (!m) continue
      const fatorChave = id === 'mancha_propria-fantasma' ? 'mancha_propria' : id === 'imagem-ativa' ? o.imagemAtiva! : id
      const fator = o.opacidades[fatorChave] ?? 1
      // troca de tipo de imagem (ex.: Landsat → MSS no modo "antes do assentamento") exige recriar a fonte
      const outraImagem = id === 'imagem-ativa' && m.sourceIds[0] !== 'img-' + o.imagemAtiva
      if (m.fator !== fator || m.tema !== o.viz.tema || outraImagem) this.remover(id)
    }

    for (const id of ORDEM_CAMADAS) {
      if (!desejadas.has(id) || this.presentes.has(id)) continue
      const fatorChave = id === 'mancha_propria-fantasma' ? 'mancha_propria' : id === 'imagem-ativa' ? o.imagemAtiva! : id
      const fator = o.opacidades[fatorChave] ?? 1
      if (id === 'imagem-ativa') {
        const c = byId.get(o.imagemAtiva!)
        if (c) await this.aplicarImagem(c, o.ano, fator)
        continue
      }
      if (id === 'mancha_propria-fantasma') {
        await this.aplicarFantasma(byId.get('mancha_propria')!, o.ano, o.viz, fator)
        continue
      }
      const c = byId.get(id)
      if (!c) continue
      await this.aplicarGeojson(c, o.ano, o.viz, fator, byId)
    }
  }

  /** Troca leve de ano: atualiza imagem (updateImage), filtro (rampas) ou dados (setData) das
   *  camadas já presentes, sem recriar layers. Chamar a cada passo do slider/autoplay. */
  trocarAno(manifesto: Manifesto, ano: number): Promise<void> {
    return this.enfileirar(() => this.trocarAnoJa(manifesto, ano))
  }

  private async trocarAnoJa(manifesto: Manifesto, ano: number) {
    const byId = new Map(manifesto.camadas.map((c) => [c.id, c]))
    for (const [id, m] of this.presentes) {
      if (id === 'imagem-ativa') {
        // resolvido pelo id real armazenado no primeiro source id: 'img-<id>'
        const realId = m.sourceIds[0]?.replace(/^img-/, '')
        const c = realId ? byId.get(realId) : undefined
        if (!c) continue
        const anoUso = c.anos ? anoParaCamada(c, ano) : ano
        definirImagem(this.map, m.sourceIds[0], c, anoUso)
        m.ano = anoUso
        continue
      }
      if (id === 'mancha_propria-fantasma') {
        const c = byId.get('mancha_propria')!
        const novo = anoAnterior(c.anos ?? [], ano)
        if (novo === null || novo === m.ano) continue
        const dados = await carregarGeojson(c, novo)
        ;(this.map.getSource(m.sourceIds[0]) as maplibregl.GeoJSONSource | undefined)?.setData(dados)
        m.ano = novo
        continue
      }
      const c = byId.get(id)
      if (!c) continue
      if (c.anos) {
        const anoUso = anoParaCamada(c, ano)
        if (anoUso === null || anoUso === m.ano) continue
        const dados = await carregarGeojson(c, anoUso)
        ;(this.map.getSource(m.sourceIds[0]) as maplibregl.GeoJSONSource | undefined)?.setData(dados)
        m.ano = anoUso
      } else if (c.rampa && c.propriedade && c.dominio) {
        const idFill = c.id + '-fill'
        if (!this.map.getLayer(idFill)) continue
        const filtro =
          c.id === 'wsf_evolution'
            ? (['all', ['!=', ['get', c.propriedade], 0], ['<=', ['get', c.propriedade], Math.min(2015, ano)]] as unknown as maplibregl.FilterSpecification)
            : (['<=', ['get', c.propriedade], ano] as unknown as maplibregl.FilterSpecification)
        this.map.setFilter(idFill, filtro)
        m.ano = ano
      }
    }
  }

  camadaPresente(id: string): boolean {
    return this.presentes.has(id)
  }

  /** Todas as layers reais do MapLibre hoje em cena (para hover/tooltip). */
  todosLayerIds(): string[] {
    return Array.from(this.presentes.values()).flatMap((m) => m.layerIds)
  }

  private async aplicarImagem(c: Camada, ano: number, fator: number) {
    const anoUso = c.anos ? anoParaCamada(c, ano) : ano
    const sourceId = 'img-' + c.id
    definirImagem(this.map, sourceId, c, anoUso)
    const layerId = 'img-' + c.id + '-layer'
    // a MSS em falsa-cor (vegetação vermelha) competiria com o vermelho da classe urbana (MapBiomas 24):
    // exibida em tons de cinza, como na página inicial
    const saturacao = c.id === 'mss_falsacor' ? -1 : 0
    this.map.addLayer({ id: layerId, type: 'raster', source: sourceId, paint: { 'raster-opacity': fator, 'raster-fade-duration': 0, 'raster-saturation': saturacao } }, this.beforeId('imagem-ativa'))
    this.presentes.set('imagem-ativa', { sourceIds: [sourceId], layerIds: [layerId], fator, tema: 'light', ano: anoUso })
  }

  private async aplicarFantasma(c: Camada, ano: number, viz: VizTokens, fator: number) {
    const novo = anoAnterior(c.anos ?? [], ano)
    if (novo === null) return
    const dados = await carregarGeojson(c, novo)
    const sourceId = 'src-mancha_propria-fantasma'
    const layerId = 'mancha_propria-fantasma-linha'
    if (!this.map.getSource(sourceId)) this.map.addSource(sourceId, { type: 'geojson', data: dados, attribution: c.atribuicao })
    else (this.map.getSource(sourceId) as maplibregl.GeoJSONSource).setData(dados)
    this.map.addLayer(
      {
        id: layerId,
        type: 'line',
        source: sourceId,
        filter: ['==', ['get', 'classe'], 1],
        paint: { 'line-color': corNeutra(viz), 'line-width': 1.5, 'line-dasharray': [2, 2], 'line-opacity': 0.9 * fator },
      },
      this.beforeId('mancha_propria-fantasma'),
    )
    this.presentes.set('mancha_propria-fantasma', { sourceIds: [sourceId], layerIds: [layerId], fator, tema: viz.tema, ano: novo })
  }

  private async aplicarGeojson(c: Camada, ano: number, viz: VizTokens, fator: number, byId: Map<string, Camada>) {
    const anoDependente = !!c.anos
    const anoUso = anoDependente ? anoParaCamada(c, ano) : null
    if (anoDependente && anoUso === null) return
    const dados = await carregarGeojson(c, anoUso)
    const sourceId = 'src-' + c.id
    if (!this.map.getSource(sourceId)) this.map.addSource(sourceId, { type: 'geojson', data: dados, attribution: c.atribuicao })
    else (this.map.getSource(sourceId) as maplibregl.GeoJSONSource).setData(dados)

    const before = this.beforeId(c.id)
    const layerIds: string[] = []
    const legenda = c.legenda ?? (c.legenda_de ? byId.get(c.legenda_de)?.legenda : undefined)

    if (legenda && c.propriedade_classe && legenda.some((l) => l.classe !== undefined)) {
      const semPreench = legenda.filter((l) => l.classe !== undefined && !l.cor)
      const comPreench = legenda.filter((l) => l.classe !== undefined && l.cor)
      if (comPreench.length) {
        const idFill = c.id + '-fill'
        this.map.addLayer(
          {
            id: idFill,
            type: 'fill',
            source: sourceId,
            filter: ['in', ['get', c.propriedade_classe], ['literal', comPreench.map((l) => l.classe)]],
            paint: { 'fill-color': corPorClasse(c.propriedade_classe, legenda), 'fill-opacity': opacidadePorClasse(c.propriedade_classe, legenda, fator) },
          },
          before,
        )
        layerIds.push(idFill)
      }
      for (const l of semPreench) {
        const idL = c.id + '-linha' + String(l.classe)
        this.map.addLayer(
          {
            id: idL,
            type: 'line',
            source: sourceId,
            filter: ['==', ['get', c.propriedade_classe], l.classe as number],
            paint: { 'line-color': l.contorno ?? corNeutra(viz), 'line-width': 1.5, 'line-opacity': fator },
          },
          before,
        )
        layerIds.push(idL)
      }
    } else if (legenda && legenda.some((l) => (l as Record<string, unknown>).propriedade)) {
      const exprCor = expressaoMultiAtributo(legenda, 'cor')
      const exprContorno = expressaoMultiAtributo(legenda, 'contorno')
      if (exprCor) {
        const idFill = c.id + '-fill'
        this.map.addLayer({ id: idFill, type: 'fill', source: sourceId, paint: { 'fill-color': exprCor, 'fill-opacity': 0.65 * fator } }, before)
        layerIds.push(idFill)
      }
      if (exprContorno) {
        const idL = c.id + '-linha'
        this.map.addLayer({ id: idL, type: 'line', source: sourceId, paint: { 'line-color': exprContorno, 'line-width': 1.5, 'line-opacity': fator } }, before)
        layerIds.push(idL)
      }
    } else if (c.rampa && c.dominio && c.propriedade) {
      const filtro =
        c.id === 'wsf_evolution'
          ? (['all', ['!=', ['get', c.propriedade], 0], ['<=', ['get', c.propriedade], Math.min(2015, ano)]] as unknown as maplibregl.FilterSpecification)
          : (['<=', ['get', c.propriedade], ano] as unknown as maplibregl.FilterSpecification)
      const idFill = c.id + '-fill'
      this.map.addLayer(
        { id: idFill, type: 'fill', source: sourceId, filter: filtro, paint: { 'fill-color': corRampa(c.propriedade, c.rampa, c.dominio), 'fill-opacity': (c.opacidade ?? 0.75) * fator } },
        before,
      )
      layerIds.push(idFill)
    } else if (c.id === 'clareira_mss') {
      const idFill = c.id + '-fill'
      const idL = c.id + '-linha'
      this.map.addLayer({ id: idFill, type: 'fill', source: sourceId, paint: { 'fill-color': c.cor ?? corNeutra(viz), 'fill-opacity': 0.35 * fator } }, before)
      this.map.addLayer({ id: idL, type: 'line', source: sourceId, paint: { 'line-color': c.cor ?? corNeutra(viz), 'line-width': 1.5, 'line-dasharray': [3, 2], 'line-opacity': fator } }, before)
      layerIds.push(idFill, idL)
    } else if (c.id === 'nucleo_historico') {
      const idP = c.id + '-ponto'
      this.map.addLayer(
        {
          id: idP,
          type: 'circle',
          source: sourceId,
          paint: { 'circle-color': c.cor ?? corNeutra(viz), 'circle-radius': 5, 'circle-stroke-color': viz.superficie, 'circle-stroke-width': 1.5, 'circle-opacity': fator },
        },
        before,
      )
      layerIds.push(idP)
    } else if (c.id === 'osm_vias' || c.id === 'osm_rodovias_regiao' || c.id === 'osm_ferrovia') {
      const idL = c.id + '-linha'
      const cor = c.cor_ferrovia
        ? (['match', ['get', 'tipo'], 'ferrovia', c.cor_ferrovia, c.cor ?? corNeutra(viz)] as unknown as maplibregl.ExpressionSpecification)
        : c.cor ?? corNeutra(viz)
      const largura = c.id === 'osm_vias' ? 1 : 1.5
      const paint: Record<string, unknown> = { 'line-color': cor, 'line-width': largura, 'line-opacity': fator }
      if (c.id === 'osm_ferrovia') paint['line-dasharray'] = [1, 1]
      this.map.addLayer({ id: idL, type: 'line', source: sourceId, paint } as maplibregl.LayerSpecification, before)
      layerIds.push(idL)
    } else if (c.cor && !c.contorno) {
      const idFill = c.id + '-fill'
      this.map.addLayer({ id: idFill, type: 'fill', source: sourceId, paint: { 'fill-color': c.cor, 'fill-opacity': (c.opacidade ?? 0.55) * fator } }, before)
      layerIds.push(idFill)
    } else {
      // contorno-only (setores, ANM, AU 2019 revisado, limites): setores e ANM levam também um
      // preenchimento invisível, só para o hover funcionar em polígono (a linha sozinha exige
      // apontar exatamente para o traço).
      if (c.grupo === 'setores' || c.id === 'anm_lavra') {
        const idHit = c.id + '-hit'
        this.map.addLayer({ id: idHit, type: 'fill', source: sourceId, paint: { 'fill-color': '#000000', 'fill-opacity': 0 } }, before)
        layerIds.push(idHit)
      }
      const idL = c.id + '-linha'
      const paint: Record<string, unknown> = { 'line-color': c.contorno ?? corNeutra(viz), 'line-width': c.grupo === 'setores' ? 0.75 : 1.5, 'line-opacity': fator }
      if (c.grupo === 'limites') paint['line-dasharray'] = [4, 2]
      this.map.addLayer({ id: idL, type: 'line', source: sourceId, paint } as maplibregl.LayerSpecification, before)
      layerIds.push(idL)
    }

    this.presentes.set(c.id, { sourceIds: [sourceId], layerIds, fator, tema: viz.tema, ano: anoUso })
  }
}
