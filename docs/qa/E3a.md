# QA — E3a Série MapBiomas e produtos prontos (2026-09-09)

Etapa E3a do checklist do `PLANO.md`: Fase 3 passos 1–2 (parte) e 6 para MapBiomas / GHSL / WSF /
TerraClass / Áreas Urbanizadas, mais o catálogo estendido de MSS/TM 1979–1990. Nenhum microdado
tocado — só produtos públicos de sensoriamento remoto e as tabelas SIDRA já baixadas em E1;
o gate de revelação não se aplica.

## Feito

### `pipeline/20_imagens_catalogo.py` — Fase 3 passo 1
- **AOI fixa**: polígono municipal da API v4 de Malhas (qualidade máxima) + janela da sede
  (bbox −49,99 / −6,60 / −49,75 / −6,40). Salvos em EPSG:31982 (`data/processed/geo/aoi_*.parquet`)
  e em 4326 para o mapa (`web/public/data/geo/aoi_*.json`).
- **Catálogo STAC**: 11 coleções em 3 endpoints (Planetary Computer, Element84 earth-search,
  INPE BDC) → **10.145 cenas, 1973–2026**, em `data/interim/catalogo_cenas.parquet`
  (resumo por ano × fonte em `data/processed/geo/catalogo_cenas_resumo.parquet`).

| fonte | cenas | período |
|---|---|---|
| PC `landsat-c2-l2` (TM/ETM+/OLI) | 5.112 | 1984–2026 |
| E84 `sentinel-2-l2a` | 1.877 | 2017–2026 |
| PC `sentinel-2-l2a` | 1.592 | 2016–2026 |
| BDC `S2_L2A-1` | 837 | 2021–2026 |
| BDC `landsat-lgi-1` (MSS/TM histórico) | 423 | 1973–1990 |
| BDC `CB4-MUX-L4-DN-1` | 151 | 2015–2026 |
| BDC `CB4-PAN5M-L4-DN-1` | 72 | 2015–2026 |
| BDC `CB4A-WPM-L4-DN-1` | 41 | 2020–2026 |
| BDC `CB2B-HRC-L2-DN-1` | 21 | 2008–2010 |
| BDC `CB4A-WPM-PCA-FUSED-1` | 10 | 2023–2025 |
| PC `landsat-c2-l1` (MSS) | 9 | 1973–1982 |

- **Viabilidade da série pré-1991 confirmada** (era a pergunta em aberto do PLANO.md):
  todos os anos de **1984 a 1990** têm entre 6 e 16 cenas de estação seca com nuvem < 15%
  (1984: 7, 1985: 7, 1986: 12, 1987: 10, 1988: 16, 1989: 6, 1990: 10). A série anual de E3b
  **pode começar em 1984**, como o plano previa.
- **Marcos MSS**: 1979 (8 cenas de estação seca), 1980 (10), 1981 (4), 1982 (4 + 3 do PC).
  **1983 e 1974 não têm nenhuma cena** sobre a janela da sede em nenhum catálogo consultado —
  são lacunas reais, não falha do script; o marco "implantação" fica em 1982.

### `pipeline/25_produtos_prontos.py` — Fase 3 passos 2 (parte) e 6
Manifesto de proveniência (produto, URL, bytes, data de acesso) em
`data/processed/geo/produtos_prontos.parquet` — 73 entradas, 11 produtos. Rasters/vetores
recortados em `data/interim/produtos/` (20 MB, fora do git; cache de download 256 MB em
`data/interim/_produtos_dl/`, descartável).

- **Legenda oficial MapBiomas Coleção 11**: CSV de códigos/hex de
  `brasil.mapbiomas.org/downloads/codigos-de-legenda/` → `web/src/legend/mapbiomas.json`
  (33 classes, com `hex_code`). Exigência do CLAUDE.md cumprida: nenhum código de classe ou cor
  digitado de memória, e `26_estatisticas_mancha.py` **falha em voz alta** se o IBGE/MapBiomas
  renomear as classes 21/24/25/30 (`_conferir_legenda()`).
- **MapBiomas Col.11 30 m**: 41/41 anos (1985–2025) recortados por `/vsicurl` na AOI municipal —
  leitura só da janela, sem baixar os ~650 MB por ano.
- **MapBiomas Col.4 10 m**: 9/9 anos (2017–2025). **2016 devolve 404** — a coleção 10 m começa em
  2017, não 2016 como constava no PLANO.md; constante corrigida no script.
- **GHS-BUILT-S R2023A**: 12/12 épocas 1975–2030. A AOI municipal cruza a divisa de tiles
  Mollweide em x = −5.041.000 m, então **R10_C13 e R10_C14** são baixadas e mosaicadas (o PLANO.md
  citava só R10_C14 — corrigido).
- **WSF-Evolution** e **WSF2019**: tiles `-52_-8` e `-50_-8` mosaicados.
- **IBGE Áreas Urbanizadas**: 2019 (49 polígonos, 3.039,0 ha), 2019 revisado (63 / 2.891,5 ha),
  2022 (69 / 2.894,6 ha) + os `.qml` oficiais de densidade/tipo e comparação.
  **2015 não cobre Canaã**: o produto de 2015 só existe para concentrações urbanas de mais de
  100 mil habitantes (dois shapefiles, ambos lidos, zero polígonos sobre o município). Confirma —
  e estende para 2015 — a suspeita do plano, que só previa isso para 2005.
- **TerraClass**: sem URL direta (formulário web em terraclass.gov.br). O script incorpora
  automaticamente qualquer `.tif` colocado em `data/externo/terraclass/`. **Pendência do usuário.**

### `pipeline/26_estatisticas_mancha.py` — Fase 3 passo 6
- Série anual 1985–2025 × 2 recortes (município, janela da sede), com área das classes 24, 30, 21
  e 25 em ha e km², Δ absoluto, variação %, e taxa geométrica anual por período mineral →
  `data/processed/geo/mancha_mapbiomas_anual.{parquet,csv}`.
  Áreas obtidas **reprojetando os polígonos vetorizados para EPSG:31982**, nunca multiplicando
  contagem de pixels por 900 m² (convenção do CLAUDE.md).
- 41 camadas anuais da classe 24 na janela da sede → `web/public/data/geo/mancha_mapbiomas_{ano}.json`
  (6,4 MB no total, aceitável para GitHub Pages) + a série para os KPIs em
  `web/public/data/mancha_anual.json`.
- **Série populacional anual do município** montada das tabelas de E1, com a fonte declarada por
  ano (censo 2000/2010/2022 > contagem 2007 > estimativa t/6579) →
  `data/processed/ibge/populacao_anual_municipio.parquet` (26 anos: 3 censos, 1 contagem,
  22 estimativas). Usada para a densidade hab/ha.
- Comparação entre produtos → `data/processed/geo/comparacao_produtos.{parquet,csv}`.
  (Os `.csv` são conveniência local: o `.gitignore` bloqueia `*.csv` pela regra de sigilo, então
  o parquet é o artefato canônico e versionável.)

## Achado principal: a classe 24 do MapBiomas **não é uma série anual** em Canaã

Área urbanizada da janela da sede, classe 24, Coleção 11:

| ano | ha | Δ ha |
|---|---|---|
| 1985 | 1.004,5 | — |
| 1990 | 1.841,0 | +172,7 |
| 1994 | 2.744,4 | +314,7 |
| 1995 | 3.129,8 | +385,5 |
| 2000 | 3.133,3 | −1,5 |
| 2010 | 3.122,9 | −5,3 |
| 2014 | 3.144,7 | +14,7 |
| 2022 | 3.295,0 | +38,4 |
| 2025 | 3.445,1 | +51,0 |

- **24 dos 40 anos têm |Δ| < 0,5%**, e há uma sequência contígua de **19 anos estagnados
  (1996–2014)** — período em que a população do município passou de ~7 mil para ~32 mil e o
  Sossego (2004) entrou em operação. A mancha praticamente não se move.
- Estruturalmente, a série é dominada por **um único polígono** centrado na sede
  (−49,853 / −6,530) que vai de 494 ha em 1985 a 2.540 ha em 1995 e então fica congelado
  (2.532 ha em 2010, 2.604 ha em 2022). Os outros ~35 polígonos somam poucas centenas de hectares.
- 1.004 ha "urbanizados" em 1985, quando o CEDERE II era uma vila de assentamento, é implausível
  por si só: daria menos de 3 hab/ha.
- Contra os outros produtos de referência (município inteiro):

| ano | MapBiomas | WSF-Evolution | GHS-BUILT-S | razão MB/WSF |
|---|---|---|---|---|
| 1990 | 1.974,3 | 88,3 | 282,8 | 22,3 |
| 1995 | 3.400,7 | 175,5 | 298,5 | 19,4 |
| 2000 | 3.406,4 | 357,0 | 317,4 | 9,5 |
| 2010 | 3.365,0 | 879,6 | 496,8 | 3,8 |
| 2015 | 3.391,7 | 1.029,6 | 595,4 | 3,3 |

  Mediana da razão MapBiomas ÷ WSF-Evolution: **9,5×** (faixa 3,3–30,1). WSF e GHSL,
  que têm definições diferentes entre si (máscara de construído × superfície construída em m²),
  concordam entre si em ordem de grandeza e **descrevem uma trajetória crescente**; o MapBiomas
  descreve um platô. Em 2022 as magnitudes convergem (MapBiomas 3.560,5 ha × IBGE Áreas
  Urbanizadas 2.894,6 ha, +23%), o que é coerente com a hipótese de um mapa urbano ancorado em
  referência recente e retropropagado.

Quantificado no script (`diagnostico()` → `data/processed/geo/diagnostico_serie_mapbiomas.parquet`),
não só descrito aqui.

**Consequência para as próximas etapas** — e justificativa empírica da decisão do plano de fazer
classificação própria:
1. A curva MapBiomas **não pode** ser a série anual do dashboard nem a linha do tempo do artigo
   para 1995–2014. Entra como *camada de comparação* e como *apoio de rótulos de treino*
   (classes 24/30/21/25 erodidas), exatamente o papel previsto na Fase 3 passo 4.
2. O KPI de densidade e a narrativa de expansão dependem da classificação própria de E3b.
   `web/public/data/mancha_anual.json` já carrega um campo `aviso` dizendo isso, para que nenhuma
   versão intermediária do dashboard publique a curva sem ressalva.
3. A validação de E3b (`24_validar_mancha.py`) deve comparar contra **WSF-Evolution + GHSL + IBGE
   AU 2019/2022 + HRC 2010 + WPM 2022/2026**, e reportar o viés contra MapBiomas como resultado,
   não como erro.

## Achado secundário: descontinuidade das estimativas populacionais

A série montada em `populacao_anual_municipio.parquet` mostra estimativa de **39.103 (2021)**
contra censo de **77.079 (2022)** — as estimativas intercensitárias subcontaram Canaã em ~50%.
Não é erro de montagem (censo tem precedência sobre estimativa no mesmo ano; 2022 vem de t/9923).
É um fato do caso — município de crescimento migratório rápido que as projeções não acompanham —
e precisa aparecer explicitamente no gráfico de população (Fase 6: marcação por tipo de fonte,
já prevista) e como parágrafo do artigo. **Nenhuma taxa anual de densidade deve ser calculada
sobre 2015–2021 sem essa ressalva.**

## Verificações

`.venv/bin/python pipeline/validate.py --e3a` — **OK (0 falhas)**, novo bloco acrescentado a
`validate.py`:

| Checagem | Resultado |
|---|---|
| Área da AOI × SIDRA t/4714 (3.146,821 km²) | 3.145,0 km², **desvio 0,06%** (generalização da malha da API) |
| Catálogo: anos 1984–2025 sem cena | **nenhum** |
| Catálogo: anos com < 3 cenas de estação seca e nuvem < 20% | **nenhum** |
| Série 1985–2025 completa | **41/41 anos** |
| Quedas anuais > 2% na série da sede | **0** (a série é monotônica na prática — o que é o próprio problema) |
| Camadas anuais do slider | **41/41** |
| Legenda MapBiomas: 24 = "Área Urbanizada", hex válido | **ok**, 33 classes |
| Manifesto de proveniência | **73 entradas, 11 produtos** |

`.venv/bin/python pipeline/validate.py --smoke` — **OK (6/6 blocos)**.

Correções ao PLANO.md descobertas na execução (URLs verificadas em 09/09/2026):
- MapBiomas 10 m Col.4 começa em **2017**, não 2016.
- GHSL exige **duas** tiles (R10_C13 + R10_C14), não só R10_C14.
- IBGE Áreas Urbanizadas **2015 não cobre Canaã** (só concentrações > 100 mil hab.), além de 2005.
- URL de WSF-Evolution é `WSFevolution_v1_{tile}.tif` (não `WSF_EVO_v1_...`).

## Pendências

- **TerraClass Amazônia** (2004…2022): download por formulário web em terraclass.gov.br —
  precisa do usuário; `25_produtos_prontos.py terraclass` incorpora sozinho depois. Não bloqueia
  E3b (é produto de comparação, não de treino).
- **SPOT World Heritage** (`regards.cnes.fr/user/swh`) e **KH-9 Hexagon** (USGS EarthExplorer):
  cadastros a cargo do usuário, como o PLANO.md já registrava. Se houver cena 1986–90 sobre
  Canaã, seria a única referência independente para validar a mancha pré-1991 — hoje a acurácia
  de 1984–1990 continua **não verificável**, e isso terá de ser declarado no artigo.
- **Estatísticas municipais MapBiomas em XLSX** (`MAPBIOMAS_BRAZIL-COL.10-...xlsx` e
  `mapbiomas_brazil_urban_v2.xlsx`) não estão no bucket público `mapbiomas-public` (404 nas duas
  URLs do PLANO.md; a listagem do bucket só traz `lulc/`). Sem prejuízo: a série foi calculada
  direto dos rasters, com controle total do recorte e do CRS, que é metodologicamente melhor.
  Se o usuário quiser o cruzamento com o **módulo urbano** do MapBiomas, a planilha precisa ser
  baixada manualmente da página de estatísticas.
- **Volume**: `data/interim/_produtos_dl/` tem 256 MB de zips/tifs de origem (fora do git,
  descartável — os scripts rebaixam). `web/public/data/geo/` está em 6,4 MB; quando E3b/E3c
  acrescentarem as manchas próprias e as composições, vale converter as camadas anuais para
  PMTiles (já previsto no passo 7 da Fase 3).
- As camadas anuais do slider hoje são a vetorização de um raster de 30 m — bordas em degrau.
  Aceitável como camada de comparação; a camada principal do slider virá de E3b.

## Próxima etapa

**E2 — Microdados** (Fase 2), conforme a ordem combinada E0 → E1 → **E3a** → E2 → E4 → E3b → E3c →
E5 → E6 → E7 → E8. Modelo da sessão: Fable 5.1. Primeira tarefa de E2 é adaptar
`pipeline/disclosure_rules.py` aos limiares deste projeto (2022: n ≥ 20 pessoas / ≥ 10 domicílios;
2000/2010/1991: n ≥ 10; arredondamento 10, 50 no rural), que ainda estão nos valores herdados do
atlas-migração. Aguardar pedido explícito do usuário.
