// Modo "Comparar dois anos": dois mapas sincronizados (câmera em espelho) empilhados; o de
// cima (ano A, à esquerda) é recortado por `clip-path` até um divisor vertical arrastável
// (mouse, toque e teclado ←/→ com foco na alça); a partir do divisor aparece o mapa de baixo
// (ano B, à direita). Mesmas camadas ativas nos dois lados.
import { useCallback, useEffect, useRef, useState } from 'react'
import type { Manifesto, MLMap } from '../../lib/mapa'
import type { Tema } from '../../lib/theme'
import { Selecao } from '../ui'
import MapaMancha, { type MapaManchaHandle } from './MapaMancha'

interface Props {
  manifesto: Manifesto | undefined
  tema: Tema
  ativos: Set<string>
  opacidades: Record<string, number>
  imagemAtiva: string | null
  ghost: boolean
  anoA: number
  anoB: number
  onAnoA: (a: number) => void
  onAnoB: (a: number) => void
  onSair: () => void
}

const ANOS = Array.from({ length: 2026 - 1984 + 1 }, (_, i) => 1984 + i)

export default function Comparador({ manifesto, tema, ativos, opacidades, imagemAtiva, ghost, anoA, anoB, onAnoA, onAnoB, onSair }: Props) {
  const refA = useRef<MapaManchaHandle>(null)
  const refB = useRef<MapaManchaHandle>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [divisor, setDivisor] = useState(50) // % a partir da esquerda
  const sincronizandoRef = useRef(false)

  // sincroniza câmera entre os dois mapas (sem loop: quem disparou marca `sincronizandoRef`)
  useEffect(() => {
    const mA = refA.current?.map
    const mB = refB.current?.map
    if (!mA || !mB) return
    const espelhar = (origem: MLMap, destino: MLMap) => () => {
      if (sincronizandoRef.current) return
      sincronizandoRef.current = true
      destino.jumpTo({ center: origem.getCenter(), zoom: origem.getZoom(), bearing: origem.getBearing(), pitch: origem.getPitch() })
      sincronizandoRef.current = false
    }
    const deAparaB = espelhar(mA, mB)
    const deBparaA = espelhar(mB, mA)
    mA.on('move', deAparaB)
    mB.on('move', deBparaA)
    return () => {
      mA.off('move', deAparaB)
      mB.off('move', deBparaA)
    }
  }, [manifesto])

  const moverDivisor = useCallback((clientX: number) => {
    const el = containerRef.current
    if (!el) return
    const r = el.getBoundingClientRect()
    const p = Math.min(100, Math.max(0, ((clientX - r.left) / r.width) * 100))
    setDivisor(p)
  }, [])

  function iniciarArraste(e: React.PointerEvent) {
    e.currentTarget.setPointerCapture(e.pointerId)
    function mover(ev: PointerEvent) {
      moverDivisor(ev.clientX)
    }
    function soltar() {
      window.removeEventListener('pointermove', mover)
      window.removeEventListener('pointerup', soltar)
    }
    window.addEventListener('pointermove', mover)
    window.addEventListener('pointerup', soltar)
  }

  function teclado(e: React.KeyboardEvent) {
    if (e.key === 'ArrowLeft') {
      e.preventDefault()
      setDivisor((d) => Math.max(0, d - 2))
    } else if (e.key === 'ArrowRight') {
      e.preventDefault()
      setDivisor((d) => Math.min(100, d + 2))
    }
  }

  return (
    <div className="comparador">
      <div className="comparador__cab">
        <Selecao rotulo="Ano A (esquerda)" opcoes={ANOS.map((a) => ({ valor: String(a), rotulo: String(a) }))} valor={String(anoA)} onChange={(v) => onAnoA(Number(v))} />
        <Selecao rotulo="Ano B (direita)" opcoes={ANOS.map((a) => ({ valor: String(a), rotulo: String(a) }))} valor={String(anoB)} onChange={(v) => onAnoB(Number(v))} />
        <button type="button" className="botao-texto" onClick={onSair}>
          Sair da comparação
        </button>
      </div>
      <div className="comparador__mapas" ref={containerRef}>
        <MapaMancha
          ref={refB}
          manifesto={manifesto}
          tema={tema}
          ano={anoB}
          ativos={ativos}
          opacidades={opacidades}
          imagemAtiva={imagemAtiva}
          ghost={ghost}
          mostrarControles={false}
          className="comparador__mapa comparador__mapa--b"
        />
        <div className="comparador__mapa comparador__mapa--a" style={{ clipPath: `polygon(0 0, ${divisor}% 0, ${divisor}% 100%, 0 100%)` }}>
          <MapaMancha
            ref={refA}
            manifesto={manifesto}
            tema={tema}
            ano={anoA}
            ativos={ativos}
            opacidades={opacidades}
            imagemAtiva={imagemAtiva}
            ghost={ghost}
            mostrarControles={false}
            interativo
          />
        </div>
        <div className="comparador__rotulo comparador__rotulo--a">{anoA}</div>
        <div className="comparador__rotulo comparador__rotulo--b">{anoB}</div>
        <div
          className="comparador__divisor"
          style={{ left: `${divisor}%` }}
          role="slider"
          tabIndex={0}
          aria-label="Divisor da comparação"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={Math.round(divisor)}
          onKeyDown={teclado}
          onPointerDown={iniciarArraste}
        >
          <span className="comparador__alca" />
        </div>
      </div>
    </div>
  )
}
