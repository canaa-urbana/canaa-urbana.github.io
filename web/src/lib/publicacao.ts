// Metadados de publicação (E8). Único lugar a atualizar quando o Zenodo atribuir o DOI
// (ver docs/CHECKLIST_PUBLICACAO.md): o painel mostra "Como citar" a partir daqui.
export const SITE_URL = 'https://canaa-urbana.github.io'
export const REPO_URL = 'https://github.com/canaa-urbana/canaa-urbana.github.io'
/** DOI conceitual do Zenodo (todas as versões); null até a primeira release arquivada. */
export const DOI: string | null = null
export const VERSAO = '2026-09-10'
export const AUTOR = { nome: 'Daniel Pessini Sobreira', abnt: 'SOBREIRA, Daniel Pessini', orcid: '0000-0002-6632-3991' }
export const TITULO =
  'Da colônia agrícola à cidade mineral: urbanização, migração e mancha urbana em Canaã dos Carajás (PA), 1982–2026'

/** Referência ABNT do conjunto (dados, painel e artigo). */
export function referenciaAbnt(): string {
  const acesso = DOI ? `DOI: ${DOI}.` : `Disponível em: ${SITE_URL}.`
  return `${AUTOR.abnt}. ${TITULO}: dados, painel interativo e artigo. Versão ${VERSAO}. [S. l.]: Zenodo, 2026. ${acesso}`
}
