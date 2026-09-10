// Painel de camadas: agrupado por `GRUPOS`, colapsável, um checkbox por camada (radio dentro
// de "imagens", só uma imagem de satélite por vez), controle de opacidade por camada ativa e
// disclosure "i" com atribuição/licença/fonte da cor/notas.
import { useId, useState } from 'react'
import { GRUPOS, type Camada, type Manifesto } from '../../lib/mapa'
import { GRUPO_IMAGENS } from './camadas'

interface Props {
  manifesto: Manifesto
  ativos: Set<string>
  onToggle: (id: string) => void
  opacidades: Record<string, number>
  onOpacidade: (id: string, v: number) => void
  imagemAtiva: string | null
  onImagemAtiva: (id: string) => void
}

function LinhaCamada({
  c,
  ativa,
  onToggle,
  opacidade,
  onOpacidade,
  radio,
  onRadio,
}: {
  c: Camada
  ativa: boolean
  onToggle?: () => void
  opacidade: number
  onOpacidade: (v: number) => void
  radio?: boolean
  onRadio?: () => void
}) {
  const [info, setInfo] = useState(false)
  const idBase = useId()
  return (
    <li className="painel-camadas__item">
      <div className="painel-camadas__linha">
        <label className="painel-camadas__rotulo">
          <input
            type={radio ? 'radio' : 'checkbox'}
            name={radio ? 'imagem-ativa' : undefined}
            checked={ativa}
            onChange={radio ? onRadio : onToggle}
            aria-label={c.titulo}
          />
          <span>{c.titulo}</span>
        </label>
        <button
          type="button"
          className="painel-camadas__info"
          aria-expanded={info}
          aria-controls={idBase + '-info'}
          aria-label={`Sobre a camada ${c.titulo}`}
          onClick={() => setInfo((v) => !v)}
        >
          i
        </button>
      </div>
      {ativa && (
        <div className="painel-camadas__opacidade">
          <label>
            Opacidade
            <input
              type="range"
              min={0.1}
              max={1}
              step={0.05}
              value={opacidade}
              onChange={(e) => onOpacidade(Number(e.target.value))}
              aria-label={`Opacidade de ${c.titulo}`}
            />
          </label>
        </div>
      )}
      {info && (
        <div id={idBase + '-info'} className="painel-camadas__disclosure">
          <p>{c.atribuicao}</p>
          {c.licenca && <p>Licença: {c.licenca}</p>}
          {c.fonte_cor && <p>Cor: {c.fonte_cor}</p>}
          {c.notas && <p className="nota-miuda">{c.notas}</p>}
        </div>
      )}
    </li>
  )
}

export default function PainelCamadas({ manifesto, ativos, onToggle, opacidades, onOpacidade, imagemAtiva, onImagemAtiva }: Props) {
  const [abertos, setAbertos] = useState<Set<string>>(new Set(GRUPOS.map((g) => g.id)))
  const porGrupo = new Map<string, Camada[]>()
  for (const c of manifesto.camadas) {
    if (!porGrupo.has(c.grupo)) porGrupo.set(c.grupo, [])
    porGrupo.get(c.grupo)!.push(c)
  }

  function alternar(g: string) {
    setAbertos((s) => {
      const n = new Set(s)
      if (n.has(g)) n.delete(g)
      else n.add(g)
      return n
    })
  }

  return (
    <div className="painel-camadas">
      {GRUPOS.map((g) => {
        const itens = porGrupo.get(g.id) ?? []
        if (!itens.length) return null
        const aberto = abertos.has(g.id)
        return (
          <section key={g.id} className="painel-camadas__grupo">
            <button type="button" className="painel-camadas__grupo-cab" aria-expanded={aberto} onClick={() => alternar(g.id)}>
              <span>{g.rotulo}</span>
              <span className="painel-camadas__seta" aria-hidden="true">
                {aberto ? '−' : '+'}
              </span>
            </button>
            {aberto && (
              <ul className="painel-camadas__lista">
                {itens.map((c) =>
                  g.id === 'imagens' ? (
                    <LinhaCamada
                      key={c.id}
                      c={c}
                      ativa={imagemAtiva === c.id}
                      radio
                      onRadio={() => onImagemAtiva(c.id)}
                      opacidade={opacidades[c.id] ?? 1}
                      onOpacidade={(v) => onOpacidade(c.id, v)}
                    />
                  ) : (
                    <LinhaCamada
                      key={c.id}
                      c={c}
                      ativa={ativos.has(c.id)}
                      onToggle={() => onToggle(c.id)}
                      opacidade={opacidades[c.id] ?? 1}
                      onOpacidade={(v) => onOpacidade(c.id, v)}
                    />
                  ),
                )}
              </ul>
            )}
          </section>
        )
      })}
      <p className="nota-miuda painel-camadas__nota">Só uma imagem de satélite por vez ({GRUPO_IMAGENS.length} disponíveis).</p>
    </div>
  )
}
