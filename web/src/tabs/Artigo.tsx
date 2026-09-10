// Aba do artigo: resumo, sumário, PDF embutido com download e a lista das figuras.
import { useState } from 'react'
import { asset, useJSON } from '../lib/data'
import { Esqueleto, Erro } from '../components/ui'
import ComoCitar from '../components/ComoCitar'
import '../styles/textos.css'

interface ArtigoMeta {
  titulo: string
  autor: string
  versao: string
  resumo: string[]
  palavras_chave: string[]
  abstract: string[]
  keywords: string[]
  secoes: { nivel: number; titulo: string }[]
}
interface FiguraArtigo {
  arquivo: string
  titulo: string
  legenda: string
  fonte: string
  resumo: string
}

export default function Artigo() {
  const { data: a, error } = useJSON<ArtigoMeta>('painel/artigo.json')
  const { data: figs } = useJSON<FiguraArtigo[]>('painel/figuras.json')
  const [ingles, setIngles] = useState(false)
  const pdf = asset('artigo/artigo.pdf')

  if (error) return <div className="pagina"><Erro erro={error} /></div>
  if (!a) return <div className="pagina"><Esqueleto altura={480} /></div>

  return (
    <div className="pagina">
      <header className="artigo__cab">
        <p className="ard-kicker">Artigo científico · {a.versao.replace(/\.$/, '')}</p>
        <h1 className="artigo__titulo">{a.titulo}</h1>
        <p className="artigo__autor">{a.autor}</p>
        <div className="artigo__acoes">
          <a className="ard-btn ard-btn--primary" href={pdf} download="sobreira_2026_canaa_urbanizacao.pdf">
            Baixar PDF
          </a>
          <a className="ard-btn" href={pdf} target="_blank" rel="noopener">
            Abrir em nova aba
          </a>
        </div>
      </header>

      <div className="grade artigo__corpo">
        <section className="c-7" aria-labelledby="resumo-t">
          <div className="artigo__idioma">
            <h2 id="resumo-t">{ingles ? 'Abstract' : 'Resumo'}</h2>
            <button type="button" className="botao-texto" aria-pressed={ingles} onClick={() => setIngles((v) => !v)}>
              {ingles ? 'Ver em português' : 'Read in English'}
            </button>
          </div>
          <div className="leitura" lang={ingles ? 'en' : 'pt-BR'}>
            {(ingles ? a.abstract : a.resumo).map((p, i) => (
              <p key={i}>{p}</p>
            ))}
            <p className="artigo__pc">
              <strong>{ingles ? 'Keywords' : 'Palavras-chave'}:</strong> {(ingles ? a.keywords : a.palavras_chave).join('; ')}.
            </p>
          </div>
        </section>
        <nav className="c-5 artigo__sumario" aria-labelledby="sumario-t">
          <p className="ard-kicker">Sumário</p>
          <h2 id="sumario-t" className="sr-only">
            Sumário
          </h2>
          <ol>
            {a.secoes.map((s, i) => (
              <li key={i} className={s.nivel === 3 ? 'sub' : undefined}>
                {s.titulo}
              </li>
            ))}
          </ol>
        </nav>
      </div>

      <ComoCitar />

      <section className="bloco" aria-labelledby="pdf-t">
        <p className="ard-kicker">Texto completo</p>
        <h2 id="pdf-t">Leia o artigo</h2>
        <object className="artigo__pdf" data={pdf} type="application/pdf" aria-label={`PDF do artigo: ${a.titulo}`}>
          <p className="aviso">
            Seu navegador não exibe PDF embutido. <a href={pdf}>Abra ou baixe o artigo em PDF</a>.
          </p>
        </object>
      </section>

      {figs && (
        <section className="bloco" aria-labelledby="figs-t">
          <p className="ard-kicker">Figuras</p>
          <h2 id="figs-t">As {figs.length} figuras do artigo</h2>
          <p className="leitura nota-miuda">
            Cada figura tem uma versão interativa nas abas do painel; o texto abaixo é a leitura principal de cada uma.
          </p>
          <ol className="artigo__figs">
            {figs.map((f) => (
              <li key={f.arquivo}>
                <p className="artigo__fig-t">{f.titulo}</p>
                <p className="artigo__fig-r">{f.resumo}</p>
                <p className="nota-miuda">{f.legenda.split(' — ')[0]} · Fonte: {f.fonte}</p>
              </li>
            ))}
          </ol>
        </section>
      )}
    </div>
  )
}
