// Legenda dinâmica: só as camadas ativas, com amostra de preenchimento, contorno, linha ou
// rampa (com os rótulos de período da expansão, 1984–2026 em 5 faixas).
import type { Manifesto } from '../../lib/mapa'
import { useTema } from '../../lib/theme'

const PERIODOS_EXPANSAO = ['1984–90', '1991–2000', '2001–10', '2011–22', '2023–26']

function Amostra({ tipo, cor, cores }: { tipo: 'fill' | 'linha' | 'ponto' | 'rampa'; cor?: string; cores?: string[] }) {
  if (tipo === 'rampa' && cores) {
    return <span className="legenda__amostra legenda__amostra--rampa" style={{ background: `linear-gradient(90deg, ${cores.join(',')})` }} />
  }
  if (tipo === 'linha') return <span className="legenda__amostra legenda__amostra--linha" style={{ borderColor: cor }} />
  if (tipo === 'ponto') return <span className="legenda__amostra legenda__amostra--ponto" style={{ background: cor }} />
  return <span className="legenda__amostra" style={{ background: cor }} />
}

interface Props {
  manifesto: Manifesto
  ativos: Set<string>
  imagemAtiva: string | null
  ghost: boolean
  ano: number
}

export default function Legenda({ manifesto, ativos, imagemAtiva, ghost, ano }: Props) {
  const { viz } = useTema()
  const byId = new Map(manifesto.camadas.map((c) => [c.id, c]))
  const linhas: { titulo: string; itens: { rotulo: string; tipo: 'fill' | 'linha' | 'ponto' | 'rampa'; cor?: string; cores?: string[] }[] }[] = []

  const img = imagemAtiva ? byId.get(imagemAtiva) : undefined
  if (img) linhas.push({ titulo: img.titulo, itens: [{ rotulo: 'Composição de fundo', tipo: 'fill', cor: viz.filete }] })

  for (const id of ativos) {
    const c = byId.get(id)
    if (!c || c.grupo === 'imagens') continue
    if (c.anos && !c.anos.includes(ano) && !c.anos.some((a) => a <= ano)) continue
    const legenda = c.legenda ?? (c.legenda_de ? byId.get(c.legenda_de)?.legenda : undefined)
    if (legenda && c.propriedade_classe && legenda.some((l) => l.classe !== undefined)) {
      linhas.push({
        titulo: c.titulo,
        itens: legenda
          .filter((l) => l.classe !== undefined)
          .map((l) => ({ rotulo: l.rotulo, tipo: l.cor ? 'fill' : 'linha', cor: l.cor ?? l.contorno })),
      })
    } else if (legenda && legenda.some((l) => (l as Record<string, unknown>).propriedade)) {
      linhas.push({ titulo: c.titulo, itens: legenda.map((l) => ({ rotulo: l.rotulo, tipo: l.cor ? 'fill' : 'linha', cor: l.cor ?? l.contorno })) })
    } else if (c.rampa && c.dominio) {
      const rotulo = c.id === 'expansao' ? `Ano de urbanização (${PERIODOS_EXPANSAO.join(' · ')})` : `${c.dominio[0]}–${c.dominio[1]}`
      linhas.push({ titulo: c.titulo, itens: [{ rotulo, tipo: 'rampa', cores: c.rampa }] })
    } else if (c.id === 'nucleo_historico') {
      linhas.push({ titulo: c.titulo, itens: [{ rotulo: c.titulo, tipo: 'ponto', cor: c.cor }] })
    } else if (c.cor && !c.contorno) {
      linhas.push({ titulo: c.titulo, itens: [{ rotulo: c.titulo, tipo: 'fill', cor: c.cor }] })
    } else {
      linhas.push({ titulo: c.titulo, itens: [{ rotulo: c.titulo, tipo: 'linha', cor: c.contorno ?? viz.texto3 }] })
    }
  }

  if (ghost && ativos.has('mancha_propria')) linhas.push({ titulo: 'Ano anterior', itens: [{ rotulo: 'Contorno da sede no ano anterior', tipo: 'linha', cor: viz.texto2 }] })

  if (!linhas.length) return <p className="nota-miuda">Nenhuma camada ativa.</p>

  return (
    <div className="legenda">
      {linhas.map((l, i) => (
        <div key={i} className="legenda__bloco">
          <p className="legenda__titulo">{l.titulo}</p>
          <ul>
            {l.itens.map((it, j) => (
              <li key={j}>
                <Amostra tipo={it.tipo} cor={it.cor} cores={it.cores} />
                <span>{it.rotulo}</span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}
