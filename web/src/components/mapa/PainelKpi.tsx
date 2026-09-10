// KPIs do ano selecionado: área mapeada/ajustada, delta, população/densidade urbana, qualidade
// da imagem do ano e sparkline da série ajustada.
import { Kpi } from '../ui'
import { fmtDelta, fmtHa, fmtNum, fmtPct } from '../../lib/format'
import type { EstatisticasMancha } from './tipos'

function origemRotulo(o: string): string {
  return o === 'validado' ? 'validado por fotointerpretação' : o === 'interpolado' ? 'interpolado entre épocas validadas' : 'extrapolado'
}

export default function PainelKpi({ estat, ano }: { estat: EstatisticasMancha; ano: number }) {
  const linha = estat.serie.find((s) => s.ano === ano)
  if (!linha) return null
  const serieAjustada = estat.serie.map((s) => s.area_sede_ajustada_ha)
  const destaque = estat.serie.findIndex((s) => s.ano === ano)

  const avisos: string[] = []
  if (ano === 2026) avisos.push('2026 é o último ano da série, com maioria temporal parcial — resultado provisório.')
  if (ano < 1999) avisos.push('Sem referência independente de validação antes de 1999.')
  if (ano === 1985) avisos.push('Composição com névoa e faixa de pixels ruidosos (poucas cenas disponíveis).')

  return (
    <div className="painel-kpi">
      <div className="kpis">
        <Kpi
          rotulo="Área da sede mapeada"
          valor={fmtHa(linha.area_sede_ha)}
          nota={`${fmtNum(linha.area_sede_ha / 100, 2)} km²`}
        />
        <Kpi
          rotulo="Área ajustada (IC 95 %)"
          valor={fmtHa(linha.area_sede_ajustada_ha)}
          nota={`± ${fmtHa(linha.area_sede_ajustada_ic95_ha)} — ${origemRotulo(linha.ajuste_origem)}`}
          serie={serieAjustada}
          destaque={destaque}
        />
        <Kpi
          rotulo="Variação sobre o ano anterior"
          valor={fmtDelta(linha.area_sede_delta_ha, 0, ' ha')}
          nota={linha.area_sede_var_pct !== null ? fmtDelta(linha.area_sede_var_pct, 1, ' %') : undefined}
        />
        {linha.pop_urbana !== null && (
          <Kpi
            rotulo="População urbana"
            valor={fmtNum(linha.pop_urbana, 0)}
            nota={
              linha.fonte_pop_urbana === 'censo'
                ? 'Censo'
                : linha.aviso_pop
                  ? `Estimativa própria — ${linha.aviso_pop}`
                  : 'Estimativa própria (interpolação geométrica)'
            }
          />
        )}
        {linha.densidade_popurb_ajustada_hab_ha !== null && (
          <Kpi rotulo="Densidade urbana (área ajustada)" valor={fmtNum(linha.densidade_popurb_ajustada_hab_ha, 1)} unidade="hab/ha" nota="população urbana ÷ área urbana total (sede e outros núcleos)" />
        )}
      </div>
      <p className="painel-kpi__qualidade nota-miuda">
        Qualidade do ano: {linha.n_cenas ?? '—'} cena(s){linha.sensores ? ` (${linha.sensores})` : ''}, {fmtPct((linha.frac_preenchida ?? 0) * 100, 0)} dos pixels preenchidos por interpolação temporal
        {linha.validacao ? ` — ${linha.validacao}` : ''}.
      </p>
      {ano === 2026 && <p className="ard-pill ard-pill--atencao">Provisório — 2026</p>}
      {avisos.map((a, i) => (
        <p key={i} className="nota-miuda painel-kpi__aviso">
          {a}
        </p>
      ))}
    </div>
  )
}
