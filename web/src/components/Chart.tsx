// Wrapper mínimo do ECharts (renderer SVG): cria, atualiza, redimensiona e descarta.
import { useEffect, useRef } from 'react'
import { echarts, type Opcao } from '../lib/charts'

interface Props {
  option: Opcao
  height?: number | string
  /** Resumo de uma frase do que o gráfico mostra (vai para aria-label). */
  ariaLabel: string
  /** Eventos ECharts: { click: (p) => ..., mouseover: ... } */
  onEvents?: Record<string, (p: unknown) => void>
  /** Clique em qualquer ponto da área de plotagem (grade 0): recebe o valor do eixo x.
   *  Serve para sincronizar gráfico → mapa sem exigir clique exato sobre um marcador. */
  aoClicarEixoX?: (x: number) => void
  className?: string
}

export default function Chart({ option, height = 320, ariaLabel, onEvents, aoClicarEixoX, className }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const inst = useRef<echarts.ECharts | null>(null)

  useEffect(() => {
    if (!ref.current) return
    const c = echarts.init(ref.current, undefined, { renderer: 'svg' })
    inst.current = c
    const ro = new ResizeObserver(() => c.resize())
    ro.observe(ref.current)
    return () => {
      ro.disconnect()
      c.dispose()
      inst.current = null
    }
  }, [])

  useEffect(() => {
    inst.current?.setOption(option, { notMerge: true })
  }, [option])

  useEffect(() => {
    const c = inst.current
    if (!c || !onEvents) return
    for (const [ev, fn] of Object.entries(onEvents)) c.on(ev, fn)
    return () => {
      for (const [ev, fn] of Object.entries(onEvents)) c.off(ev, fn)
    }
  }, [onEvents])

  useEffect(() => {
    const c = inst.current
    if (!c || !aoClicarEixoX) return
    const zr = c.getZr()
    const f = (e: { offsetX: number; offsetY: number }) => {
      const px = [e.offsetX, e.offsetY]
      if (!c.containPixel({ gridIndex: 0 }, px)) return
      const v = c.convertFromPixel({ gridIndex: 0 }, px) as number[] | number
      const x = Array.isArray(v) ? v[0] : v
      if (Number.isFinite(x)) aoClicarEixoX(x)
    }
    zr.on('click', f)
    return () => {
      zr.off('click', f)
    }
  }, [aoClicarEixoX])

  return <div ref={ref} className={className} style={{ height, width: '100%' }} role="img" aria-label={ariaLabel} />
}
