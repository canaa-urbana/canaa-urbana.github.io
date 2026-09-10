// Conteúdo do tooltip de hover por camada (nomes de propriedade reais dos GeoJSON da E3c).
import type { Camada, Manifesto } from '../../lib/mapa'
import { fmtHa, fmtNum } from '../../lib/format'
import { idLogicoDeLayer } from './camadas'

type Props = Record<string, unknown>

function rotuloClasse(c: Camada | undefined, classe: unknown): string {
  return c?.legenda?.find((l) => l.classe === classe)?.rotulo ?? String(classe)
}

function linha(rotulo: string, valor: unknown): string {
  if (valor === undefined || valor === null || valor === '') return ''
  return `<tr><th>${rotulo}</th><td>${valor}</td></tr>`
}

/** HTML do popup de hover para uma feição, dado o id da layer do MapLibre que a rendeu. */
export function tooltipHtml(layerId: string, props: Props, manifesto: Manifesto): string | null {
  const camadaId = idLogicoDeLayer(layerId)
  const byId = new Map(manifesto.camadas.map((c) => [c.id, c]))
  const c = byId.get(camadaId)
  const legendaFonte = c?.legenda ? c : c?.legenda_de ? byId.get(c.legenda_de) : c

  let titulo = c?.titulo ?? camadaId
  const linhas: string[] = []

  switch (camadaId) {
    case 'mancha_propria':
    case 'mancha_propria10': {
      titulo = rotuloClasse(legendaFonte, props.classe)
      linhas.push(linha('Área mapeada da classe', fmtHa(props.area_ha as number)))
      linhas.push(linha('Ano', props.ano))
      break
    }
    case 'ghsl': {
      titulo = rotuloClasse(legendaFonte, props.classe)
      linhas.push(linha('Área', fmtHa(props.area_ha as number)))
      break
    }
    case 'expansao': {
      titulo = 'Ano de urbanização'
      linhas.push(linha('1º ano urbano do pixel', props.ano_urbanizacao))
      linhas.push(linha('Área', fmtHa(props.area_ha as number)))
      break
    }
    case 'wsf_evolution': {
      titulo = 'WSF-Evolution'
      linhas.push(linha('1º ano assentado', props.ano))
      linhas.push(linha('Área', fmtHa(props.area_ha as number)))
      break
    }
    case 'clareira_mss': {
      titulo = Number(props.classe) === 1 ? 'Núcleo do assentamento (clareira na imagem MSS)' : 'Clareira agropecuária (imagem MSS)'
      linhas.push(linha('Ano da imagem', props.ano))
      linhas.push(linha('Área da clareira', fmtHa(props.area_ha as number)))
      break
    }
    case 'setores_2010':
    case 'setores_2022': {
      titulo = 'Setor censitário ' + (props.cod_setor ?? '')
      linhas.push(linha('Situação', props.NM_BAIRRO ?? props.SITUACAO))
      linhas.push(linha('População residente', fmtNum(props.populacao_residente as number)))
      linhas.push(linha('Domicílios', fmtNum(props.total_domicilios as number)))
      linhas.push(linha('Densidade', props.densidade_hab_km2 != null ? `${fmtNum(props.densidade_hab_km2 as number, 1)} hab/km²` : undefined))
      break
    }
    case 'anm_lavra': {
      titulo = String(props.NOME ?? 'Concessão de lavra')
      linhas.push(linha('Processo ANM', props.PROCESSO))
      linhas.push(linha('Substância', props.SUBS))
      linhas.push(linha('Fase', props.FASE))
      linhas.push(linha('Área', props.AREA_HA != null ? fmtHa(props.AREA_HA as number) : undefined))
      break
    }
    case 'osm_vias':
    case 'osm_rodovias_regiao':
    case 'osm_ferrovia': {
      titulo = String(props.nome ?? props.ref ?? (props.tipo === 'ferrovia' ? 'Ferrovia' : 'Via'))
      linhas.push(linha('Tipo', props.tipo))
      linhas.push(linha('Referência', props.ref))
      break
    }
    case 'areas_urbanizadas_2022': {
      titulo = 'IBGE Áreas Urbanizadas 2022'
      linhas.push(linha('Densidade', props.Densidade))
      linhas.push(linha('Tipo', props.Tipo))
      linhas.push(linha('Área', props.Area_ha != null ? fmtHa(props.Area_ha as number) : undefined))
      break
    }
    case 'nucleo_historico': {
      titulo = String(props.nome ?? 'Núcleo histórico')
      break
    }
    default:
      return null
  }

  return `<div class="mapa-tooltip"><p class="mapa-tooltip__titulo">${titulo}</p>${linhas.some(Boolean) ? `<table>${linhas.join('')}</table>` : ''}</div>`
}
