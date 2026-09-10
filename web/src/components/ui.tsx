// Componentes de interface do painel (Ardósia): figura com tabela alternativa, KPI com
// sparkline, tabela, marca de precisão, citação, controle segmentado, glossário, esqueleto.
import { useId, useState, type ReactNode } from 'react'
import type { Classe } from '../lib/data'
import { useTema } from '../lib/theme'
import { fmtNum, TRACO } from '../lib/format'

// ---------------------------------------------------------------------------
// Figura: kicker + título serifado + gráfico + fonte + botão "tabela"
// ---------------------------------------------------------------------------

export interface Coluna<L> {
  id: string
  rotulo: string
  num?: boolean
  fmt?: (l: L) => ReactNode
}

interface FiguraProps<L> {
  kicker?: string
  titulo: string
  subtitulo?: ReactNode
  fonte: ReactNode
  notas?: ReactNode
  /** Visão em tabela dos mesmos dados (acessibilidade). */
  tabela?: { colunas: Coluna<L>[]; linhas: L[] }
  children: ReactNode
  controles?: ReactNode
  className?: string
}

export function Figura<L>({ kicker, titulo, subtitulo, fonte, notas, tabela, children, controles, className }: FiguraProps<L>) {
  const [verTabela, setVerTabela] = useState(false)
  const id = useId()
  return (
    <figure className={'figura ' + (className ?? '')} aria-labelledby={id}>
      <header className="figura__cab">
        {kicker && <p className="ard-kicker">{kicker}</p>}
        <h3 id={id} className="figura__titulo">
          {titulo}
        </h3>
        {subtitulo && <p className="figura__sub">{subtitulo}</p>}
        {controles && <div className="figura__controles">{controles}</div>}
      </header>
      <div className="figura__corpo">{verTabela && tabela ? <Tabela {...tabela} /> : children}</div>
      <figcaption className="figura__rodape">
        <span className="figura__fonte">
          <span className="rotulo-fonte">Fonte:</span> {fonte}
        </span>
        {tabela && (
          <button type="button" className="botao-texto" aria-pressed={verTabela} onClick={() => setVerTabela((v) => !v)}>
            {verTabela ? 'Ver gráfico' : 'Ver tabela'}
          </button>
        )}
      </figcaption>
      {notas && <div className="figura__notas">{notas}</div>}
    </figure>
  )
}

// ---------------------------------------------------------------------------
// Tabela
// ---------------------------------------------------------------------------

export function Tabela<L>({ colunas, linhas, legenda }: { colunas: Coluna<L>[]; linhas: L[]; legenda?: string }) {
  return (
    <div className="tabela-wrap" tabIndex={0} role="region" aria-label={legenda ?? 'Tabela de dados'}>
      <table>
        {legenda && <caption className="sr-only">{legenda}</caption>}
        <thead>
          <tr>
            {colunas.map((c) => (
              <th key={c.id} className={c.num ? 'num' : undefined} scope="col">
                {c.rotulo}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {linhas.map((l, i) => (
            <tr key={i}>
              {colunas.map((c) => {
                const v = c.fmt ? c.fmt(l) : ((l as Record<string, unknown>)[c.id] as ReactNode)
                return (
                  <td key={c.id} className={c.num ? 'num' : undefined}>
                    {v === null || v === undefined || v === '' ? TRACO : v}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ---------------------------------------------------------------------------
// KPI com delta e sparkline
// ---------------------------------------------------------------------------

interface KpiProps {
  rotulo: string
  valor: ReactNode
  unidade?: string
  delta?: ReactNode
  nota?: ReactNode
  serie?: (number | null)[]
  /** índice da série a destacar (ano corrente) */
  destaque?: number
}

export function Kpi({ rotulo, valor, unidade, delta, nota, serie, destaque }: KpiProps) {
  return (
    <div className="kpi ard-card">
      <p className="ard-kpi-label">{rotulo}</p>
      <p className="ard-kpi-value">
        {valor}
        {unidade && <span className="kpi__unidade"> {unidade}</span>}
      </p>
      {delta && <p className="kpi__delta">{delta}</p>}
      {serie && serie.length > 1 && <Sparkline serie={serie} destaque={destaque} />}
      {nota && <p className="kpi__nota">{nota}</p>}
    </div>
  )
}

export function Sparkline({ serie, destaque, altura = 28 }: { serie: (number | null)[]; destaque?: number; altura?: number }) {
  const { viz } = useTema()
  const w = 120
  const vals = serie.filter((v): v is number => v !== null && Number.isFinite(v))
  if (vals.length < 2) return null
  const min = Math.min(...vals)
  const max = Math.max(...vals)
  const x = (i: number) => (i / (serie.length - 1)) * (w - 6) + 3
  const y = (v: number) => altura - 3 - ((v - min) / (max - min || 1)) * (altura - 6)
  let d = ''
  serie.forEach((v, i) => {
    if (v === null || !Number.isFinite(v)) return
    d += (d && serie[i - 1] !== null ? 'L' : 'M') + x(i).toFixed(1) + ',' + y(v).toFixed(1)
  })
  const vd = destaque !== undefined ? serie[destaque] : null
  return (
    <svg className="sparkline" viewBox={`0 0 ${w} ${altura}`} width={w} height={altura} aria-hidden="true">
      <path d={d} fill="none" stroke={viz.cat[0]} strokeWidth={1.5} strokeLinejoin="round" strokeLinecap="round" />
      {vd !== null && vd !== undefined && destaque !== undefined && (
        <circle cx={x(destaque)} cy={y(vd)} r={3} fill={viz.enfase} stroke={viz.superficie} strokeWidth={1.5} />
      )}
    </svg>
  )
}

// ---------------------------------------------------------------------------
// Precisão, citações, glossário
// ---------------------------------------------------------------------------

/** Marca de precisão: boa = nada; cautela (CV 15–30 %) = *; baixa (CV > 30 %) = **.
 *  `cv` em percentual (como em estimativas.json). */
export function Precisao({ classe, cv }: { classe: Classe | null | undefined; cv?: number | null }) {
  if (!classe || classe === 'boa') return null
  const txt = classe === 'cautela' ? 'cautela' : 'baixa precisão'
  const title = `${cv !== null && cv !== undefined ? 'CV ' + fmtNum(cv, 0) + ' % — ' : ''}${txt}`
  return (
    <span className={'ard-pill ' + (classe === 'cautela' ? 'ard-pill--atencao' : 'ard-pill--critico')} title={title}>
      {classe === 'cautela' ? '*' : '**'} {txt}
    </span>
  )
}

export function Citacao({ children, fonte }: { children: ReactNode; fonte?: ReactNode }) {
  return (
    <blockquote className="ard-quote citacao">
      {children}
      {fonte && <footer className="citacao__fonte">{fonte}</footer>}
    </blockquote>
  )
}

export const GLOSSARIO: Record<string, string> = {
  data_fixa:
    'Migrante de data fixa: pessoa que, cinco anos antes da data de referência do censo, morava em outro município. É a medida de migração recente comparável entre 1991, 2000, 2010 e 2022.',
  area_ponderacao:
    'Área de ponderação: unidade geográfica da amostra do censo. Nada é publicado por área de ponderação neste painel, por regra de sigilo.',
  setor:
    'Setor censitário: menor unidade territorial de coleta do IBGE (algumas centenas de domicílios). Os dados por setor vêm do Universo, não da amostra.',
  mancha:
    'Mancha urbana: área construída contígua da sede, classificada ano a ano em imagens Landsat (30 m) com Random Forest e validada com imagens CBERS de alta resolução.',
  area_ajustada:
    'Área ajustada: área mapeada corrigida pelos erros de comissão e omissão medidos na validação (Olofsson et al. 2014), com intervalo de confiança de 95 %.',
  cv: 'Coeficiente de variação da estimativa amostral (erro-padrão ÷ estimativa). Até 15 %: boa precisão; 15–30 %: cautela (*); acima de 30 %: baixa precisão (**).',
  sede: 'Sede: a cidade de Canaã dos Carajás (situação urbana do distrito-sede), distinta do município inteiro, que inclui a zona rural e as vilas.',
}

export function Termo({ id, children }: { id: keyof typeof GLOSSARIO | string; children: ReactNode }) {
  const [aberto, setAberto] = useState(false)
  const tid = useId()
  const def = GLOSSARIO[id]
  if (!def) return <>{children}</>
  return (
    <span className="termo">
      <button
        type="button"
        className="termo__botao"
        aria-describedby={aberto ? tid : undefined}
        aria-expanded={aberto}
        onClick={() => setAberto((a) => !a)}
        onBlur={() => setAberto(false)}
        onMouseEnter={() => setAberto(true)}
        onMouseLeave={() => setAberto(false)}
      >
        {children}
      </button>
      {aberto && (
        <span role="tooltip" id={tid} className="termo__def">
          {def}
        </span>
      )}
    </span>
  )
}

// ---------------------------------------------------------------------------
// Controle segmentado (filtros em uma linha acima dos gráficos)
// ---------------------------------------------------------------------------

interface SegProps<V extends string | number> {
  rotulo: string
  opcoes: { valor: V; rotulo: string; desabilitado?: boolean }[]
  valor: V
  onChange: (v: V) => void
}

export function Segmentado<V extends string | number>({ rotulo, opcoes, valor, onChange }: SegProps<V>) {
  return (
    <div className="segmentado" role="radiogroup" aria-label={rotulo}>
      <span className="segmentado__rotulo">{rotulo}</span>
      {opcoes.map((o) => (
        <button
          key={String(o.valor)}
          type="button"
          role="radio"
          aria-checked={o.valor === valor}
          disabled={o.desabilitado}
          className={'segmentado__op' + (o.valor === valor ? ' ativo' : '')}
          onClick={() => onChange(o.valor)}
        >
          {o.rotulo}
        </button>
      ))}
    </div>
  )
}

export function Selecao<V extends string>({
  rotulo,
  opcoes,
  valor,
  onChange,
}: {
  rotulo: string
  opcoes: { valor: V; rotulo: string }[]
  valor: V
  onChange: (v: V) => void
}) {
  const id = useId()
  return (
    <label className="selecao" htmlFor={id}>
      <span className="segmentado__rotulo">{rotulo}</span>
      <select id={id} value={valor} onChange={(e) => onChange(e.target.value as V)}>
        {opcoes.map((o) => (
          <option key={o.valor} value={o.valor}>
            {o.rotulo}
          </option>
        ))}
      </select>
    </label>
  )
}

// ---------------------------------------------------------------------------
// Estados de carga
// ---------------------------------------------------------------------------

export function Esqueleto({ altura = 240 }: { altura?: number }) {
  return <div className="esqueleto" style={{ height: altura }} aria-busy="true" aria-label="Carregando" />
}

export function Erro({ erro }: { erro: Error }) {
  return (
    <p className="erro" role="alert">
      Não foi possível carregar os dados ({erro.message}).
    </p>
  )
}

/** Seção de aba: kicker + título + introdução em coluna de leitura. */
export function Secao({ kicker, titulo, children, id }: { kicker: string; titulo: string; children?: ReactNode; id?: string }) {
  return (
    <section className="secao" id={id} aria-labelledby={id ? id + '-t' : undefined}>
      <p className="ard-kicker">{kicker}</p>
      <h2 id={id ? id + '-t' : undefined}>{titulo}</h2>
      {children && <div className="secao__intro">{children}</div>}
    </section>
  )
}
