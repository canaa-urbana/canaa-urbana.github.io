// Linha do tempo 1984–2026: play/pause (~800 ms/ano), passo a passo, teclado (←/→, Home/End,
// espaço), marcas dos censos e dos marcos minerais, janelas de obras sombreadas.
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { Marco } from '../../lib/rotulos'
import { useTema } from '../../lib/theme'

const AGUARDA_MS = 800
const ANO_MIN = 1984
const ANO_MAX = 2026

function prefereReduzirMovimento(): boolean {
  try {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches
  } catch {
    return false
  }
}

interface Props {
  ano: number
  onChange: (ano: number) => void
  censos: number[]
  marcos: Marco[]
  janelasObras: [number, number, string][]
  onProximoAno?: (ano: number) => void
}

export default function Slider({ ano, onChange, censos, marcos, janelasObras, onProximoAno }: Props) {
  const { viz } = useTema()
  const [tocando, setTocando] = useState(false)
  const trilhaRef = useRef<HTMLDivElement>(null)
  const total = ANO_MAX - ANO_MIN

  useEffect(() => {
    if (!tocando) return
    if (ano >= ANO_MAX) {
      setTocando(false)
      return
    }
    const id = window.setTimeout(() => {
      const prox = Math.min(ANO_MAX, ano + 1)
      onProximoAno?.(prox)
      onChange(prox)
    }, AGUARDA_MS)
    return () => window.clearTimeout(id)
  }, [tocando, ano, onChange, onProximoAno])

  const alternarPlay = useCallback(() => {
    setTocando((t) => {
      if (t) return false
      if (ano >= ANO_MAX) {
        onChange(ANO_MIN)
        return true
      }
      return true
    })
  }, [ano, onChange])

  function teclado(e: React.KeyboardEvent<HTMLDivElement>) {
    if (e.key === 'ArrowRight') {
      e.preventDefault()
      onChange(Math.min(ANO_MAX, ano + 1))
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault()
      onChange(Math.max(ANO_MIN, ano - 1))
    } else if (e.key === 'Home') {
      e.preventDefault()
      onChange(ANO_MIN)
    } else if (e.key === 'End') {
      e.preventDefault()
      onChange(ANO_MAX)
    } else if (e.key === ' ') {
      e.preventDefault()
      alternarPlay()
    }
  }

  function clicarTrilha(e: React.MouseEvent<HTMLDivElement>) {
    const el = trilhaRef.current
    if (!el) return
    const r = el.getBoundingClientRect()
    const p = Math.min(1, Math.max(0, (e.clientX - r.left) / r.width))
    onChange(Math.round(ANO_MIN + p * total))
  }

  const pct = ((ano - ANO_MIN) / total) * 100
  const marcosMinerais = useMemo(() => marcos.filter((m) => m.tipo === 'mineral'), [marcos])

  return (
    <div className="slider-mancha">
      <div className="slider-mancha__controles">
        <button type="button" className="botao-icone" onClick={() => onChange(Math.max(ANO_MIN, ano - 1))} aria-label="Ano anterior">
          ‹
        </button>
        <button
          type="button"
          className="botao-icone slider-mancha__play"
          onClick={alternarPlay}
          aria-pressed={tocando}
          aria-label={tocando ? 'Pausar' : 'Reproduzir'}
          title={prefereReduzirMovimento() ? 'Reprodução automática (o sistema pede menos movimento)' : undefined}
        >
          {tocando ? '❚❚' : '▶'}
        </button>
        <button type="button" className="botao-icone" onClick={() => onChange(Math.min(ANO_MAX, ano + 1))} aria-label="Próximo ano">
          ›
        </button>
        <span className="slider-mancha__ano" aria-hidden="true">
          {ano}
        </span>
      </div>
      <div
        ref={trilhaRef}
        className="slider-mancha__trilha"
        role="slider"
        tabIndex={0}
        aria-label="Ano exibido no mapa"
        aria-valuemin={ANO_MIN}
        aria-valuemax={ANO_MAX}
        aria-valuenow={ano}
        aria-valuetext={String(ano)}
        onKeyDown={teclado}
        onClick={clicarTrilha}
      >
        {janelasObras.map(([a, b, r], i) => (
          <span key={i} className="slider-mancha__obras" style={{ left: `${((a - ANO_MIN) / total) * 100}%`, width: `${((b - a) / total) * 100}%`, background: viz.obras }} title={`Obras — ${r}`} />
        ))}
        <span className="slider-mancha__trilho" />
        <span className="slider-mancha__preenchido" style={{ width: `${pct}%`, background: viz.enfase }} />
        {censos.map((c) => (
          <span key={c} className="slider-mancha__marca slider-mancha__marca--censo" style={{ left: `${((c - ANO_MIN) / total) * 100}%` }} title={`Censo ${c}`} />
        ))}
        {marcosMinerais.map((m, i) => (
          <span key={i} className="slider-mancha__marca slider-mancha__marca--marco" style={{ left: `${((m.inicio - ANO_MIN) / total) * 100}%` }} title={m.rotulo} />
        ))}
        <span className="slider-mancha__alca" style={{ left: `${pct}%`, borderColor: viz.enfase }} />
      </div>
      <div className="slider-mancha__eixo" aria-hidden="true">
        <span className="slider-mancha__rot" style={{ left: 0 }}>{ANO_MIN}</span>
        {censos.map((c) => (
          <span key={c} className="slider-mancha__rot slider-mancha__rot--meio" style={{ left: `${((c - ANO_MIN) / total) * 100}%` }}>
            Censo {c}
          </span>
        ))}
        {janelasObras.map(([a, b, r], i) => (
          <span key={r + i} className="slider-mancha__rot slider-mancha__rot--meio slider-mancha__rot--obras" style={{ left: `${(((a + b) / 2 - ANO_MIN) / total) * 100}%` }}>
            obras {r}
          </span>
        ))}
        <span className="slider-mancha__rot" style={{ right: 0 }}>{ANO_MAX}</span>
      </div>
    </div>
  )
}
