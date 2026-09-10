// Bibliografia verificada (E4/E6) em data/painel/referencias.json e citação curta ABNT.
import { useJSON } from './data'

export interface Referencia {
  slug: string
  tipo?: string
  autores?: string[]
  ano?: number
  titulo?: string
  veiculo?: string
  doi?: string
  url?: string
  camada?: 'nucleo' | 'contexto'
  eixos?: string[]
  periodo?: string
  metodo?: string
  achados?: string
  abnt?: string
  verificado_em?: string
  citada_no_artigo?: boolean
}

export function useReferencias() {
  return useJSON<{ fonte: string; referencias: Referencia[] }>('painel/referencias.json')
}

/** Citação autor-data ABNT: (SOBRENOME, ano), "et al." a partir de três autores. */
export function citacaoCurta(r: Referencia | undefined): string {
  if (!r) return ''
  const sobren = (a: string) => a.split(',')[0].trim().toLocaleUpperCase('pt-BR')
  const au = r.autores ?? []
  const nomes = au.length >= 3 ? `${sobren(au[0])} et al.` : au.length === 2 ? `${sobren(au[0])}; ${sobren(au[1])}` : au.length === 1 ? sobren(au[0]) : 'S. A.'
  return `${nomes}, ${r.ano ?? 's.d.'}`
}

export const EIXOS: Record<string, string> = {
  urbanizacao: 'Urbanização',
  moradia: 'Moradia',
  migracao: 'Migração',
  trabalho: 'Trabalho',
  economia_mineral: 'Economia mineral',
  meio_ambiente: 'Meio ambiente',
  saude: 'Saúde',
  planejamento: 'Planejamento',
  historia: 'História e conflitos',
  sociedade: 'Sociedade',
}
