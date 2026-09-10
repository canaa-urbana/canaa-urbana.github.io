// Tabela de setores do recorte/ano corrente: ordenável por qualquer coluna, linha selecionada
// em destaque (rolagem automática quando a seleção vem do mapa) e exportação CSV.
import { useEffect, useMemo, useRef, useState } from 'react'
import { fmtNum } from '../../lib/format'
import { baixarCsv, fmtIndicador } from './dados'
import { PERTENCE_ROTULO, type IndicadorMeta, type SetorProps } from './tipos'

type Dir = 'asc' | 'desc'

interface Props {
  linhas: SetorProps[]
  ano: number
  indicadores: IndicadorMeta[]
  selecionado: string | null
  onSelecionar: (cod: string) => void
}

const COL_FIXAS: { id: keyof SetorProps; rotulo: string }[] = [
  { id: 'cod_setor', rotulo: 'Setor' },
  { id: 'pertence', rotulo: 'Pertença' },
  { id: 'pop', rotulo: 'População' },
  { id: 'dom', rotulo: 'Domicílios' },
]

export default function TabelaSetores({ linhas, ano, indicadores, selecionado, onSelecionar }: Props) {
  const [ordem, setOrdem] = useState<{ campo: string; dir: Dir }>({ campo: 'cod_setor', dir: 'asc' })
  // pop e dom já são colunas fixas: não repetir entre os indicadores
  const indAno = useMemo(() => indicadores.filter((i) => i.anos.includes(ano) && i.id !== 'pop' && i.id !== 'dom'), [indicadores, ano])
  const linhaRefs = useRef<Map<string, HTMLTableRowElement>>(new Map())

  const ordenadas = useMemo(() => {
    const v = (l: SetorProps): string | number => {
      if (ordem.campo === 'pertence') return PERTENCE_ROTULO[l.pertence] ?? ''
      const raw = (l as unknown as Record<string, unknown>)[ordem.campo]
      return typeof raw === 'number' ? raw : raw === null || raw === undefined ? -Infinity : String(raw)
    }
    return [...linhas].sort((a, b) => {
      const va = v(a)
      const vb = v(b)
      const cmp = typeof va === 'number' && typeof vb === 'number' ? va - vb : String(va).localeCompare(String(vb), 'pt-BR')
      return ordem.dir === 'asc' ? cmp : -cmp
    })
  }, [linhas, ordem])

  useEffect(() => {
    if (!selecionado) return
    linhaRefs.current.get(selecionado)?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  }, [selecionado])

  function alternarOrdem(campo: string) {
    setOrdem((o) => (o.campo === campo ? { campo, dir: o.dir === 'asc' ? 'desc' : 'asc' } : { campo, dir: 'asc' }))
  }

  function ariaSort(campo: string): 'ascending' | 'descending' | 'none' {
    if (ordem.campo !== campo) return 'none'
    return ordem.dir === 'asc' ? 'ascending' : 'descending'
  }

  function baixar() {
    const colunas = [
      ...COL_FIXAS.map((c) => ({ rotulo: c.rotulo, valor: (l: SetorProps) => (c.id === 'pertence' ? PERTENCE_ROTULO[l.pertence] : (l[c.id] as string | number | null)) })),
      ...indAno.map((i) => ({ rotulo: `${i.rotulo} (${i.unidade})`, valor: (l: SetorProps) => (l as unknown as Record<string, number | null>)[i.id] })),
    ]
    baixarCsv(`setores_${ano}.csv`, colunas, ordenadas)
  }

  return (
    <div className="setores-tabela">
      <div className="setores-tabela__cab">
        <p className="nota-miuda">
          {linhas.length} setores · {ano}
        </p>
        <button type="button" className="botao-texto" onClick={baixar}>
          Baixar CSV
        </button>
      </div>
      <div className="tabela-wrap" tabIndex={0} role="region" aria-label={`Tabela de setores censitários, ${ano}`}>
        <table>
          <thead>
            <tr>
              {COL_FIXAS.map((c) => (
                <th key={c.id} scope="col" aria-sort={ariaSort(c.id)}>
                  <button type="button" className="th-ordenar" onClick={() => alternarOrdem(c.id)}>
                    {c.rotulo}
                  </button>
                </th>
              ))}
              {indAno.map((i) => (
                <th key={i.id} scope="col" className="num" aria-sort={ariaSort(i.id)}>
                  <button type="button" className="th-ordenar" onClick={() => alternarOrdem(i.id)}>
                    {i.rotulo}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ordenadas.map((l) => (
              <tr
                key={l.cod_setor}
                ref={(el) => {
                  if (el) linhaRefs.current.set(l.cod_setor, el)
                  else linhaRefs.current.delete(l.cod_setor)
                }}
                className={l.cod_setor === selecionado ? 'linha-selecionada' : undefined}
                onClick={() => onSelecionar(l.cod_setor)}
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    onSelecionar(l.cod_setor)
                  }
                }}
              >
                <td>{l.cod_setor}</td>
                <td>{PERTENCE_ROTULO[l.pertence]}</td>
                <td className="num">{fmtNum(l.pop)}</td>
                <td className="num">{fmtNum(l.dom)}</td>
                {indAno.map((i) => (
                  <td key={i.id} className="num">
                    {fmtIndicador((l as unknown as Record<string, number | null>)[i.id], i)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
