// Tipos dos JSON da E3c consumidos pela aba Mancha urbana (estatisticas_mancha.json e
// painel/geo/*.json). Só os campos usados aqui; os arquivos têm mais colunas.
export interface SerieAno {
  ano: number
  area_sede_ha: number
  area_outros_nucleos_ha: number
  area_urbana_total_ha: number
  area_construido_mineracao_ha: number
  area_loteamento_vazio_ha: number
  area_sede_delta_ha: number | null
  area_sede_var_pct: number | null
  area_sede_ajustada_ha: number
  area_sede_ajustada_ic95_ha: number
  ajuste_origem: 'validado' | 'interpolado' | 'extrapolado'
  area_sede_10m_ha: number | null
  mapbiomas24_janela_ha: number | null
  pop_municipio: number | null
  fonte_pop: string | null
  aviso_pop: string | null
  pop_urbana: number | null
  fonte_pop_urbana: string | null
  densidade_popurb_hab_ha: number | null
  densidade_popurb_ajustada_hab_ha: number | null
  raio_equivalente_km: number | null
  dist_media_nucleo_km: number | null
  indice_proximidade: number | null
  centroide_desloc_km: number | null
  n_cenas: number | null
  sensores: string | null
  frac_preenchida: number | null
  validacao: string | null
}

export interface Periodo {
  periodo: string
  rotulo: string
  anos: number
  sede_ha_inicio: number
  sede_ha_fim: number
  acrescimo_ha: number
  ha_por_ano: number
  participacao_na_area_final_pct: number
  taxa_geometrica_aa_pct: number
  pop_sede_inicio: number | null
  pop_sede_fim: number | null
  taxa_pop_aa_pct: number | null
  ods_11_3_1_razao: number | null
}

export interface CensoStat {
  ano: number
  pop_sede: number | null
  dom_sede: number | null
  area_sede_ha: number
  area_sede_ajustada_ha: number
  area_sede_ajustada_ic95_ha: number
  ajuste_origem: string
  densidade_bruta_hab_ha: number
  densidade_ajustada_hab_ha: number
  dom_por_ha_ajustado: number | null
  moradores_por_domicilio: number | null
}

export interface EstatisticasMancha {
  fonte: string
  notas: string[]
  serie: SerieAno[]
  periodos: Periodo[]
  censos: CensoStat[]
  validacao: Record<string, unknown>
}

export interface DirecaoItem {
  periodo: string
  rotulo: string
  octante: 'N' | 'NE' | 'L' | 'SE' | 'S' | 'SO' | 'O' | 'NO'
  area_ha: number
  participacao_pct: number
  dist_media_km: number
}

export interface ComparacaoProdutoItem {
  produto: string
  ano: number
  natureza: string
  area_ha: number
}

export interface MapbiomasSerieItem {
  ano: number
  area_urbanizada_ha: number
  mineracao_ha: number
  area_urbanizada_delta_ha: number | null
  area_urbanizada_var_pct: number | null
}
