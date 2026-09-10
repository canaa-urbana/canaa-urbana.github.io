// Bloco "Como citar" (E8): referência ABNT, DOI quando houver, repositório e licenças.
import { AUTOR, DOI, REPO_URL, referenciaAbnt } from '../lib/publicacao'

export default function ComoCitar() {
  return (
    <section className="bloco" id="como-citar" aria-labelledby="como-citar-t">
      <p className="ard-kicker">Como citar</p>
      <h3 id="como-citar-t">Citação e licenças</h3>
      <div className="leitura">
        <p className="citar__ref">{referenciaAbnt()}</p>
        <p className="nota-miuda">
          {DOI ? (
            <>
              DOI (todas as versões): <a href={`https://doi.org/${DOI}`}>{DOI}</a> ·{' '}
            </>
          ) : (
            <>DOI do Zenodo a ser atribuído na primeira versão arquivada · </>
          )}
          Código e dados: <a href={REPO_URL}>{REPO_URL.replace('https://', '')}</a> · ORCID do autor:{' '}
          <a href={`https://orcid.org/${AUTOR.orcid}`}>{AUTOR.orcid}</a>
        </p>
        <p className="nota-miuda">
          Código sob licença MIT; dados agregados, figuras, textos e o artigo sob CC BY 4.0 (camadas derivadas do
          OpenStreetMap sob ODbL). Os microdados dos censos não estão incluídos e não são redistribuídos.
        </p>
      </div>
    </section>
  )
}
