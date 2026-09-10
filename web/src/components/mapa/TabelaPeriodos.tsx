// (e) Tabela compacta de períodos: taxa geométrica, ha/ano, participação na área final,
// crescimento populacional da sede e razão ODS 11.3.1.
import { Figura, Tabela, type Coluna } from '../ui'
import { fmtHa, fmtNum, fmtPct } from '../../lib/format'
import type { Periodo } from './tipos'

export default function TabelaPeriodos({ periodos }: { periodos: Periodo[] }) {
  const colunas: Coluna<Periodo>[] = [
    { id: 'rotulo', rotulo: 'Período' },
    { id: 'taxa_geometrica_aa_pct', rotulo: 'Taxa geométrica (% a.a.)', num: true, fmt: (l) => fmtPct(l.taxa_geometrica_aa_pct, 1) },
    { id: 'ha_por_ano', rotulo: 'ha/ano', num: true, fmt: (l) => fmtHa(l.ha_por_ano, 1) },
    { id: 'participacao_na_area_final_pct', rotulo: 'Participação na área de 2026', num: true, fmt: (l) => fmtPct(l.participacao_na_area_final_pct, 1) },
    { id: 'taxa_pop_aa_pct', rotulo: 'População da sede (% a.a.)', num: true, fmt: (l) => (l.taxa_pop_aa_pct !== null ? fmtPct(l.taxa_pop_aa_pct, 1) : undefined) },
    { id: 'ods_11_3_1_razao', rotulo: 'ODS 11.3.1', num: true, fmt: (l) => (l.ods_11_3_1_razao !== null ? fmtNum(l.ods_11_3_1_razao, 2) : undefined) },
  ]

  return (
    <Figura
      kicker="Períodos"
      titulo="A área cresceu mais rápido que a população na década de 2000 e mais devagar na de 2010"
      subtitulo="Taxas de crescimento da área e, nos intervalos censitários, da população da sede."
      fonte="Classificação própria (E3c) — estatisticas_mancha_periodos.json"
      notas="ODS 11.3.1 (UN-Habitat): razão entre a taxa de consumo de solo (área) e a taxa de crescimento populacional. Acima de 1: a área cresce mais rápido que a população (a cidade se espraia); abaixo de 1: a população cresce mais rápido (a cidade adensa). Só calculado nos intervalos censitários, com população da sede conhecida."
    >
      <Tabela colunas={colunas} linhas={periodos} legenda="Taxas de crescimento da área e da população por período, com a razão ODS 11.3.1" />
    </Figura>
  )
}
