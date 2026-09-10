// Tipos dos dados de setores censitários (web/public/data/painel/setores_{2010,2022}.json,
// indicadores_setores.json e analise/desigualdade_intraurbana.json). Só os campos usados aqui.

export type Pertence = 'sede' | 'outros_nucleos' | 'rural'

export interface SetorProps {
  cod_setor: string
  ano: number
  pop: number | null
  dom: number | null
  densidade_liquida: number | null
  moradores_dom: number | null
  agua_pct: number | null
  esgoto_pct: number | null
  lixo_pct: number | null
  energia_pct?: number | null
  renda_resp?: number | null
  pretos_pardos_pct?: number | null
  razao_sexo?: number | null
  frac_construida: number | null
  ano_urbanizacao: number | null
  dist_nucleo_km: number | null
  situacao: string
  pertence: Pertence
}

export type SetorFeature = GeoJSON.Feature<GeoJSON.Polygon | GeoJSON.MultiPolygon, SetorProps>
export type SetorFC = GeoJSON.FeatureCollection<GeoJSON.Polygon | GeoJSON.MultiPolygon, SetorProps>

export interface IndicadorMeta {
  id: string
  rotulo: string
  unidade: string
  escala: 'seq' | string
  casas: number
  anos: number[]
}

export interface IndicadoresSetores {
  fonte: string
  notas: string[]
  indicadores: IndicadorMeta[]
}

/** `data/painel/analise/desigualdade_intraurbana.json` (E5): dispersão e gradiente por
 *  indicador × ano, só setores da sede. */
export interface DesigualdadeItem {
  ano: number
  indicador: string
  n_setores: number
  media_ponderada: number | null
  minimo: number | null
  p10: number | null
  p50: number | null
  p90: number | null
  maximo: number | null
  cv_entre_setores_pct: number | null
  razao_p90_p10: number | null
  gradiente_por_km: number | null
  spearman_distancia: number | null
  gradiente_por_ano_urbanizacao: number | null
  spearman_ano_urbanizacao: number | null
}

export const PERTENCE_ROTULO: Record<Pertence, string> = {
  sede: 'Sede',
  outros_nucleos: 'Outros núcleos',
  rural: 'Rural',
}
