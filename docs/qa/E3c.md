# QA — E3c Estatísticas e camadas web (2026-09-10)

Etapa E3c do checklist do `PLANO.md`: Fase 3 passos 6–7. A etapa transforma a série própria
da E3b em tabelas analíticas e nas camadas que o dashboard (E7) vai consumir. Sessão principal
Opus 5, sem subagentes. Nenhum microdado foi lido para produzir as saídas: elas vêm de imagens
públicas, dos agregados do Universo por setor (IBGE) e das tabelas SIDRA da E1. O gate de
revelação foi regravado ao fim, porque a E3b tinha deixado 129 arquivos novos fora do carimbo.

## Entregáveis

| Arquivo | Conteúdo |
|---|---|
| `pipeline/26_estatisticas_mancha.py propria` | parte nova, ao lado da parte MapBiomas da E3a (`mapbiomas`); sem argumento roda as duas |
| `data/processed/geo/estatisticas_mancha.{parquet,csv}` | 43 anos (1984–2026), 60 colunas: áreas, Δ, área ajustada com IC 95 %, série de 10 m, MapBiomas 24, população, densidades, forma e qualidade do ano |
| `data/processed/geo/estatisticas_mancha_periodos.{parquet,csv}` | 7 períodos (4 minerais, 2 intercensitários, série inteira) com taxa geométrica, ha/ano e ODS 11.3.1 |
| `data/processed/geo/estatisticas_mancha_censos.{parquet,csv}` | densidade bruta e ajustada (hab/ha, dom/ha) em 2000, 2010 e 2022 |
| `data/processed/geo/expansao_direcao.{parquet,csv}` | área acrescida por octante e período mineral |
| `data/processed/setores/setores_mancha.parquet` | 158 setores (2010 e 2022): construído mapeado, fração construída, densidade líquida, pertença sede/outros/rural |
| `data/processed/geo/osm_vias.parquet` | 421 trechos de rodovia do OpenStreetMap na janela (ODbL, acesso 2026-09-10) |
| `pipeline/27_tiles_camadas.py` | `vetores`, `imagens`, `manifesto` → `web/public/data/geo/` |
| `web/public/data/geo/camadas.json` | manifesto com 19 camadas: arquivo, anos, cores e fonte de cada cor, coordenadas das imagens, atribuição e licença |
| `web/public/data/estatisticas_mancha.json`, `setores_mancha.json` | dados dos KPIs, gráficos e coroplético de densidade líquida |
| `pipeline/validate.py --e3c` | 24 checagens, **OK (0 falhas)** |

Camadas geradas em `web/public/data/geo/`:

| Camada | Arquivos | Tamanho |
|---|---|---|
| Mancha própria 30 m, classes 1–4 | `mancha/mancha_propria_{1984..2026}.json` | 2,9 MB (máx. 214 KB) |
| Mancha Sentinel-2 10 m (secundária) | `mancha/mancha_propria10_{2017..2026}.json` | 3,8 MB (máx. 603 KB) |
| Ano de urbanização (anel de expansão) | `expansao_ano_urbanizacao.json` | 974 KB |
| Máscara de mineração, concessões ANM, núcleo histórico, vias OSM | 4 arquivos | 132 KB |
| Clareiras MSS 1973 e 1982 | `clareira_mss_{ano}.json` | 781 KB |
| Landsat cor natural e falsa-cor | `img/landsat_{ano}_{cor,falsacor}.webp`, 86 arquivos | 15,6 MB (~180 KB cada) |
| Sentinel-2 cor natural | `img/s2_{ano}_cor.webp`, 10 arquivos | 13,0 MB (máx. 1,39 MB) |
| MSS falsa-cor | `img/mss_{1973,1982}_falsacor.webp` | 0,4 MB |

O total de `web/public/data/geo/` passou de 6,3 MB para 44,1 MB. As imagens são carregadas sob
demanda pelo slider, então o custo por visita é de uma imagem e uma mancha por ano exibido.

## Como foi feito

### Estatísticas (`26_estatisticas_mancha.py propria`)
- **Área ajustada**: fator área ajustada ÷ área mapeada das três épocas validadas na E3b
  (2009: 0,793; 2017: 0,838; 2022: 0,874), interpolado linearmente entre elas e mantido
  constante fora. O IC 95 % relativo segue a mesma regra. A coluna `ajuste_origem` marca cada
  ano como validado, interpolado ou extrapolado.
- **População da sede** nos censos de 2010 e 2022: soma dos setores urbanos do Universo cujo
  construído mapeado é majoritariamente sede. O resultado fica em 99,7 % (2010) e 98,0 % (2022)
  da população urbana do SIDRA. A diferença de 2022 é a Vila Planalto (1.417 hab.), núcleo
  urbano separado que cai em "outros núcleos". Em 2000 não há malha digital de setores, então
  a população da sede é a urbana do SIDRA (3.924).
- **População urbana anual**: interpolação geométrica entre os censos (2000–2022) e
  extrapolação 2023–2026 pelas estimativas municipais pós-censo, com a taxa de urbanização de
  2022. É estimativa própria e está rotulada em `fonte_pop_urbana`. As estimativas do IBGE de
  2001–2006 e 2011–2021 levam `aviso_pop` por subcontagem conhecida.
- **Forma**: raio equivalente, distância média e percentil 95 ao núcleo histórico (centroide
  da sede em 1990), índice de proximidade de Angel et al. 2010 (1 = disco), e deslocamento e
  azimute do centroide.
- **Direção**: cada pixel da sede de 2026 recebe o seu primeiro ano urbano; a área acrescida é
  somada por octante (N, NE, L, SE, S, SO, O, NO) em cada período mineral.
- **ODS 11.3.1** (UN-Habitat): razão entre a taxa de consumo de solo e a de crescimento
  populacional, com a população da sede nos intervalos censitários.

### Camadas (`27_tiles_camadas.py`)
- Vetores em GeoJSON 4326 com coordenadas de 5 casas (≈ 1 m), dissolvidos por classe e
  simplificados com meio pixel (15 m) a 30 m, um pixel (10 m) a 10 m e 40 m no MSS. A área
  gravada em cada feição é a do raster, não a do polígono simplificado.
- Imagens WebP com alfa, reprojetadas para EPSG:3857 e prontas para `image` source do
  MapLibre, com os quatro cantos em lon/lat no manifesto. O estiramento é fixo por sensor
  (percentis 2–98 do conjunto de anos), para que diferença de cor entre anos seja diferença de
  superfície. O MSS, em DN de nível 1, tem estiramento por ano.
- Cores lidas das fontes, nunca digitadas: sede e outros núcleos com a classe 24 do MapBiomas
  (outros núcleos com opacidade menor); construído em mineração com a classe 30; loteamento
  vazio com o símbolo do `.qml` oficial do IBGE (só contorno azul, sem preenchimento); rampa de
  expansão, ANM, vias e clareiras com tokens Ardósia. A checagem confere que as 12 cores do
  manifesto existem em uma dessas três fontes.
- O manifesto também referencia as camadas herdadas da E1 e da E3a (MapBiomas por ano, AU
  2019/2022, setores, limites), para o dashboard ter uma entrada única.

## Resultados

| Ano | Sede mapeada (ha) | Sede ajustada ± IC95 (ha) | Origem do ajuste | Raio equiv. (km) | Proximidade |
|---|---|---|---|---|---|
| 1984 | 8 | 6 ± 1 | extrapolado | 0,16 | 0,95 |
| 1990 | 46 | 37 ± 7 | extrapolado | 0,38 | 0,96 |
| 2000 | 139 | 110 ± 21 | extrapolado | 0,66 | 0,87 |
| 2004 | 504 | 400 ± 76 | extrapolado | 1,27 | 0,80 |
| 2010 | 1.076 | 860 ± 158 | interpolado | 1,85 | 0,82 |
| 2016 | 2.397 | 1.995 ± 298 | interpolado | 2,76 | 0,81 |
| 2022 | 2.644 | 2.311 ± 499 | validado | 2,90 | 0,78 |
| 2026 | 3.656 | 3.196 ± 690 | extrapolado | 3,41 | 0,69 |

Densidade da sede nos censos:

| Censo | População da sede | Densidade bruta (hab/ha) | Densidade ajustada (hab/ha, faixa do IC) | Dom/ha ajustado | Moradores/dom. |
|---|---|---|---|---|---|
| 2000 | 3.924 | 28,3 | 35,6 (30,0–43,9) | — | — |
| 2010 | 20.668 | 19,2 | 24,0 (20,3–29,5) | 6,8 | 3,55 |
| 2022 | 67.915 | 25,7 | 29,4 (24,2–37,5) | 10,5 | 2,79 |

Períodos:

| Período | Taxa geométrica (% a.a.) | ha/ano | População da sede (% a.a.) | ODS 11.3.1 |
|---|---|---|---|---|
| 1984–1994 assentamento → emancipação | 24,4 | 6 | — | — |
| 1994–2004 emancipação → Sossego | 22,2 | 44 | — | — |
| 2004–2016 Sossego → S11D | 13,9 | 158 | — | — |
| 2016–2026 S11D → 2026 | 4,3 | 126 | — | — |
| 2000–2010 intercensitário | 22,7 | 94 | 18,1 | 1,23 |
| 2010–2022 intercensitário | 7,8 | 131 | 10,4 | 0,76 |

Leitura para E5 e E6:
- **Mais da metade da sede de 2026 (52 %) foi acrescida entre o Sossego e o S11D**
  (2004–2016), com o maior ritmo absoluto da série (158 ha/ano).
- **A cidade se espraiou na década de 2000 e adensou na de 2010.** A área cresceu mais rápido
  que a população em 2000–2010 (razão ODS 1,23) e mais devagar em 2010–2022 (0,76). A densidade
  ajustada cai de 36 para 24 hab/ha e sobe para 29 hab/ha. Os domicílios por hectare também
  sobem (6,8 → 10,5), com menos moradores por domicílio (3,55 → 2,79).
- **Direção**: oeste e sudoeste até 2004; noroeste e sudoeste no ciclo Sossego–S11D; sudoeste
  (31 %) e norte (21 %) depois do S11D. O centroide se afasta 1,1 km do núcleo histórico até
  2026, rumo oeste-noroeste (azimute 282°).
- **A forma fica menos compacta depois de 2022** (proximidade 0,78 → 0,69). A expansão
  2023–2026 é de loteamentos periféricos, mas 2026 é o último ano da série e só tem maioria
  temporal parcial, então parte desse salto pode ser comissão ainda não filtrada.

## Achados de qualidade

- **Sentinel-2 é 0,015 a 0,03 mais claro que o Landsat OLI no visível e no SWIR**, mesmo
  depois da harmonização. O NIR é igual. Medido por classe MapBiomas (floresta, pastagem,
  urbano) em 2018, 2022 e 2025. É a diferença conhecida entre as correções atmosféricas Sen2Cor
  e LaSRC, e justifica o modelo separado do Sentinel-2 e a série principal em Landsat. Para as
  imagens, o Sentinel-2 ganhou estiramento próprio.
- **A composição de 1985 tem névoa e uma faixa de pixels coloridos** (mediana por banda com
  poucas observações, 3 por pixel). É o mesmo ano em que a área bruta classificada sobe para
  1.616 ha antes do filtro temporal. A imagem fica publicada como está; a legenda do dashboard
  deve indicar a qualidade do ano (colunas `n_cenas` e `frac_preenchida`).
- **A cena MSS de 1982 é de outubro, com nuvens mascaradas em buracos pretos.** Serve como
  marco visual, não como medida.
- **O OpenStreetMap não tem ferrovia na janela da sede.** A consulta devolveu só rodovias
  (26 primárias, 123 secundárias, 272 terciárias). O ramal do S11D passa fora da janela; se E7
  quiser mostrá-lo, a consulta precisa usar a AOI municipal.
- **Correlação MapBiomas 24 × série própria é 0,56 (1985–2025), com razão mediana 4,09.**
  Confirma que o MapBiomas só serve como camada de comparação.

## Verificações

- `validate.py --e3c`: **OK, 24 checagens.** Série 43/43; sem retração do urbano total; fator
  de ajuste em 0,793–0,874; épocas validadas 2009, 2017 e 2022; população da sede pelos setores
  entre 95 % e 100 % da urbana SIDRA; densidades em 5–100 hab/ha; ODS 11.3.1 nos dois
  intervalos; octantes somando 100 %; manifesto sem arquivo ausente; 43 + 10 manchas; 98
  imagens; vetores e cantos das imagens dentro da janela; orçamento de tamanho; cores com fonte
  declarada; JSON do dashboard igual ao parquet.
- `validate.py --e3a`, `--e3b`: continuam **OK**.
- Sede 2022 × IBGE AU 2022 (2.139 ha): mapeada +24 %, ajustada +8 %.
- Gate: `disclosure_check.py --versao 2026-09-10-e3c` **aprovado** (R1–R8, 20.458 células
  recontadas), carimbo com 207 arquivos; `verify_gate.py` **aprovado**.
- **Conferência no navegador**: página de teste com MapLibre 4.7 servida só no scratchpad,
  fora do repositório. Sentinel-2 2022 com a mancha, os setores 2022 e as vias OSM no zoom
  12–15,5: a avenida principal e a rotatória da imagem coincidem com o traçado OSM com erro
  abaixo de um pixel de 10 m. Landsat 1990 em falsa-cor: o núcleo em magenta fica dentro do
  contorno da sede, com o ponto do núcleo histórico no centro.

## Decisões tomadas nesta sessão

1. GeoJSON por ano em vez de PMTiles. Não há `tippecanoe` na máquina, e 2,9 MB para 43 anos a
   30 m cabem no orçamento. Se E7 sentir o peso da série de 10 m, ela pode virar PMTiles depois.
2. O fator de ajuste é aplicado à sede inteira, derivado do urbano total (classes 1 e 2) das
   épocas validadas. Antes de 2009 ele é extrapolado com o valor de 2009.
3. O núcleo histórico é o centroide da sede de 1990, não o centroide da AU 2022 usado no
   pós-processamento da E3b.
4. Estiramento fixo por sensor; Sentinel-2 separado do Landsat.

## Pendências

- **E5 escolhe entre área mapeada e ajustada** nas figuras. As duas estão em todas as tabelas.
- **2026 é o último ano da série** e só tem maioria temporal parcial. A área e a queda de
  compacidade de 2026 devem ser apresentadas como provisórias.
- `data/interim/cenas` (8,8 GB) já pode ser apagado se o espaço fizer falta. Os scripts
  rebaixam tudo e são resumíveis. Não apaguei.
- A consulta de ferrovia do OSM usa a janela da sede; ampliar para a AOI municipal se E7 quiser
  o ramal do S11D.

## Próxima etapa

**E5 — Análise e figuras** (Fase 5 passos 1–2). Depende de E1, E2 e E3c, todas concluídas.
Modelo da sessão: Fable 5.1. Aguardar pedido explícito do usuário.
