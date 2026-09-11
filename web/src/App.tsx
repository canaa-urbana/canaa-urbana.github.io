import { lazy, Suspense, useEffect, useRef, type KeyboardEvent } from 'react'
import { useRota } from './lib/rota'
import { useTema } from './lib/theme'
import { asset } from './lib/data'
import { DOI, VERSAO } from './lib/publicacao'
import { Esqueleto } from './components/ui'

const Inicio = lazy(() => import('./tabs/Inicio'))
const Mancha = lazy(() => import('./tabs/Mancha'))
const Censos = lazy(() => import('./tabs/Censos'))
const Setores = lazy(() => import('./tabs/Setores'))
const Migracao = lazy(() => import('./tabs/Migracao'))
const Economia = lazy(() => import('./tabs/Economia'))
const Artigo = lazy(() => import('./tabs/Artigo'))
const Metodologia = lazy(() => import('./tabs/Metodologia'))

export const ABAS = [
  { id: 'inicio', rotulo: 'Início', C: Inicio },
  { id: 'mancha', rotulo: 'Mancha urbana', C: Mancha },
  { id: 'censos', rotulo: 'Anos censitários', C: Censos },
  { id: 'setores', rotulo: 'Setores censitários', C: Setores },
  { id: 'migracao', rotulo: 'Migração', C: Migracao },
  { id: 'economia', rotulo: 'Mineração e economia', C: Economia },
  { id: 'artigo', rotulo: 'Artigo', C: Artigo },
  { id: 'metodologia', rotulo: 'Metodologia e dados', C: Metodologia },
] as const

function IconeTema({ escuro }: { escuro: boolean }) {
  return escuro ? (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
      <circle cx="12" cy="12" r="4.5" />
      <path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4" />
    </svg>
  ) : (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
      <path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z" />
    </svg>
  )
}

export default function App() {
  const [rota, ir] = useRota()
  const { tema, alternar } = useTema()
  const abasRef = useRef<HTMLDivElement>(null)
  const atual = ABAS.find((a) => a.id === rota.aba) ?? ABAS[0]

  useEffect(() => {
    document.title = `${atual.rotulo} — Canaã dos Carajás: urbanização e mineração`
    window.scrollTo({ top: 0 })
  }, [atual])

  // setas esquerda/direita percorrem as abas (padrão WAI-ARIA tabs)
  function teclado(e: KeyboardEvent<HTMLDivElement>) {
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft' && e.key !== 'Home' && e.key !== 'End') return
    e.preventDefault()
    const i = ABAS.findIndex((a) => a.id === atual.id)
    const j =
      e.key === 'Home' ? 0 : e.key === 'End' ? ABAS.length - 1 : (i + (e.key === 'ArrowRight' ? 1 : -1) + ABAS.length) % ABAS.length
    ir(ABAS[j].id)
    requestAnimationFrame(() => abasRef.current?.querySelectorAll<HTMLElement>('[role=tab]')[j]?.focus())
  }

  const C = atual.C
  return (
    <>
      <a className="pular" href="#conteudo" onClick={(e) => { e.preventDefault(); document.getElementById('conteudo')?.focus() }}>
        Pular para o conteúdo
      </a>
      <header className="cab">
        <div className="cab__linha">
          <a className="cab__marca" href="#/inicio" aria-label="Início">
            <img src={asset(`marks/cohort-glyph-${tema === 'dark' ? 'light' : 'slate'}.svg`)} alt="" />
            <p className="cab__titulo">
              Canaã dos Carajás
              <small>urbanização e mineração, 1982–2026</small>
            </p>
          </a>
          <div className="abas" role="tablist" aria-label="Seções do painel" ref={abasRef} onKeyDown={teclado}>
            {ABAS.map((a) => (
              <a
                key={a.id}
                role="tab"
                className="aba"
                href={`#/${a.id}`}
                aria-selected={a.id === atual.id}
                aria-controls="conteudo"
                tabIndex={a.id === atual.id ? 0 : -1}
              >
                {a.rotulo}
              </a>
            ))}
          </div>
          <div className="cab__acoes">
            <button type="button" className="botao-icone" onClick={alternar} aria-label={tema === 'dark' ? 'Usar tema claro' : 'Usar tema escuro'} title={tema === 'dark' ? 'Tema claro' : 'Tema escuro'}>
              <IconeTema escuro={tema === 'dark'} />
            </button>
          </div>
        </div>
      </header>
      <main id="conteudo" tabIndex={-1} role="tabpanel" aria-label={atual.rotulo}>
        <Suspense fallback={<div className="pagina"><Esqueleto altura={400} /></div>}>
          <C />
        </Suspense>
      </main>
      <footer className="rodape">
        <div className="rodape__linha">
          <p>
            Daniel Pessini Sobreira, 2026. Dados: IBGE (Censos 1991–2022, SIDRA, malhas), MapBiomas, USGS/NASA Landsat,
            Copernicus Sentinel-2, INPE CBERS, JRC GHSL, DLR WSF, ANM, OpenStreetMap. Estimativas amostrais publicadas só
            como agregados aprovados pelo controle de revelação.
          </p>
          <p>
            Versão {VERSAO}
            {DOI && (
              <>
                {' '}· DOI <a href={`https://doi.org/${DOI}`}>{DOI}</a>
              </>
            )}{' '}
            · <a href="#/metodologia">Como citar</a> · código MIT, dados CC BY 4.0
          </p>
        </div>
      </footer>
    </>
  )
}
