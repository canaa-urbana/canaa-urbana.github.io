// Tema claro/escuro e os hex literais que o canvas/SVG dos gráficos e do mapa precisam
// (canvas não resolve custom property). Todos os hex vêm da paleta Ardósia
// (references/palette.md e styles/ardosia.css); nenhum fora dela.
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'

export type Tema = 'light' | 'dark'

export interface VizTokens {
  tema: Tema
  texto: string
  texto2: string
  texto3: string
  fundo: string
  superficie: string
  filete: string
  grade: string
  /** Categórica em ordem fixa. Até 3 séries passam no validador de CVD; da 4ª em diante,
   *  sempre com segundo sinal (traço/marcador/rótulo). */
  cat: string[]
  /** Cinza de contexto na ênfase (uma série importa, o resto é contexto). */
  contexto: string
  /** Série de ênfase. */
  enfase: string
  /** Sequencial de uma matiz, do menor (claro no tema claro) ao maior. */
  seq: string[]
  /** Divergente terracota ↔ petróleo com neutro no meio (7 passos). */
  div: string[]
  /** Sombreado das janelas de obras (construção das minas). */
  obras: string
  /** Linhas de marco (tracejadas). */
  marco: string
  status: { conforme: string; atencao: string; critico: string; semdado: string }
  /** Cor fixa de cada censo (ordinal, validada para CVD em claro e escuro); 1991 é
   *  Parauapebas (inclui o atual Canaã). Sempre com o marcador de `MARCADOR_CENSO`. */
  censo: Record<1991 | 2000 | 2010 | 2022, string>
}

/** Segundo sinal dos censos em pontos/linhas (a cor nunca é o único código). */
export const MARCADOR_CENSO: Record<1991 | 2000 | 2010 | 2022, string> = {
  1991: 'diamond',
  2000: 'triangle',
  2010: 'rect',
  2022: 'circle',
}

const CLARO: VizTokens = {
  tema: 'light',
  texto: '#1B1F23',
  texto2: '#4A5157',
  texto3: '#7B7D78',
  fundo: '#F4F2ED',
  superficie: '#FAF9F6',
  filete: '#D8D4CC',
  grade: '#E6E2DA',
  cat: ['#24404F', '#9C5B41', '#7E9BAA', '#3D5A4C', '#A98A3F', '#6E3B45'],
  contexto: '#B4B2A9',
  enfase: '#9C5B41',
  seq: ['#E3E9EC', '#A9BEC9', '#7E9BAA', '#3A6076', '#24404F'],
  div: ['#9C5B41', '#C08066', '#E0BCAC', '#D8D4CC', '#A7BFB4', '#6C8F80', '#3D5A4C'],
  obras: '#F2E2DC',
  marco: '#7B7D78',
  status: { conforme: '#4A6B57', atencao: '#A98A3F', critico: '#9A4B3F', semdado: '#8A8781' },
  censo: { 1991: '#7B7D78', 2000: '#A9BEC9', 2010: '#24404F', 2022: '#9C5B41' },
}

const ESCURO: VizTokens = {
  tema: 'dark',
  texto: '#EDEAE4',
  texto2: '#9AA6AC',
  texto3: '#7E8A90',
  fundo: '#171B1E',
  superficie: '#212A2F',
  filete: '#3A4348',
  grade: '#3A4348',
  cat: ['#A9BEC9', '#B8795C', '#3A6076', '#6C8F80', '#A98A3F', '#E0BCAC'],
  contexto: '#4A5157',
  enfase: '#B8795C',
  seq: ['#24404F', '#3A6076', '#7E9BAA', '#A9BEC9', '#E3E9EC'],
  div: ['#9C5B41', '#C08066', '#E0BCAC', '#7B7D78', '#A7BFB4', '#6C8F80', '#3D5A4C'],
  obras: '#3A4348',
  marco: '#7E8A90',
  status: { conforme: '#4A6B57', atencao: '#A98A3F', critico: '#9A4B3F', semdado: '#8A8781' },
  censo: { 1991: '#9AA6AC', 2000: '#3A6076', 2010: '#E3E9EC', 2022: '#B8795C' },
}

export function tokens(tema: Tema): VizTokens {
  return tema === 'dark' ? ESCURO : CLARO
}

interface TemaCtx {
  tema: Tema
  alternar: () => void
  viz: VizTokens
}

const Ctx = createContext<TemaCtx>({ tema: 'light', alternar: () => {}, viz: CLARO })

function temaInicial(): Tema {
  const t = document.documentElement.getAttribute('data-theme')
  return t === 'dark' ? 'dark' : 'light'
}

export function TemaProvider({ children }: { children: ReactNode }) {
  const [tema, setTema] = useState<Tema>(temaInicial)
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', tema)
  }, [tema])
  const alternar = useCallback(() => {
    setTema((t) => {
      const novo = t === 'dark' ? 'light' : 'dark'
      try {
        localStorage.setItem('tema', novo)
      } catch {
        /* armazenamento bloqueado: segue só na sessão */
      }
      return novo
    })
  }, [])
  return <Ctx.Provider value={{ tema, alternar, viz: tokens(tema) }}>{children}</Ctx.Provider>
}

export function useTema(): TemaCtx {
  return useContext(Ctx)
}
