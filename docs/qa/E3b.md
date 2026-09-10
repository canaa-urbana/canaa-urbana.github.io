# QA — E3b Classificação própria da mancha urbana (2026-09-10)

Etapa E3b do checklist do `PLANO.md`: Fase 3 passos 2–5 — recortes de cenas, composições
anuais, Random Forest por era de sensor, pós-processamento, validação independente e
comparação com produtos prontos. Sessão principal Fable 5.1, sem subagentes (o trabalho pesado
rodou em script; o modelo leu resumos e as montagens de fotointerpretação). Nenhum microdado
tocado: tudo é imagem pública (Planetary Computer, Element84, INPE BDC, ANM, IBGE). O gate de
revelação não se aplica; nada de `data/raw` ou `data/interim` saiu da máquina.

## Entregáveis

| Arquivo | Conteúdo |
|---|---|
| `pipeline/lib/grade.py` | grade fixa da janela da sede: 30 m (887 × 740 px) e 10 m (3× exato), EPSG:31982, alinhada a múltiplos de 30 m |
| `pipeline/lib/feicoes.py` | 20 feições: 6 bandas, NDVI, NDBI, MNDWI, BUI, BSI, IBI, NBR2, textura local (std 3×3/5×5 de NIR e NDBI), NDVI máx. da chuva, amplitude intersazonal, declividade |
| `pipeline/lib/referencias.py` | AU IBGE 2019/2022 rasterizadas, MapBiomas Col. 11/Col. 4, WSF-Evo/WSF2019, GHSL, máscara de mineração (MapBiomas 30 ∪ ANM) |
| `pipeline/21_baixar_cenas.py` | 1.777 recortes em `data/interim/cenas/` (8,8 GB, fora do git) + `manifesto.parquet` |
| `pipeline/22_compor_anual.py` | 43 composições Landsat 30 m (1984–2026), 10 Sentinel-2 10 m (2017–2026), 2 MSS (1973, 1982), NDVI máx. da chuva, declividade → `data/interim/composicoes/` (1 GB) + `composicoes.parquet` |
| `pipeline/23_classificar_mancha.py` | RF por era + pós-processamento → `data/processed/geo/mancha_propria/` (43 rasters + 43 GeoParquet a 30 m; 10 + 10 a 10 m; `ano_urbanizacao30.tif`; clareiras MSS), `mancha_propria_anual.{parquet,csv}`, `modelos_rf.json`, `mascara_mineracao_30m.{tif,json}`, `anm_lavra.parquet`, `marcos_mss.parquet` |
| `pipeline/24_validar_mancha.py` | `registrar` (corregistro), `amostrar`, `avaliar`, `comparar` → `data/processed/geo/validacao/` (pontos, rótulos, `validacao_acuracia.{json,csv}`, `corregistro.csv`, `sensibilidade_limiar.csv`) e `comparacao_serie_propria.{parquet,csv}` |
| `pipeline/validate.py --e3b` | 19 checagens — **OK (0 falhas)** |

## Como foi feito

### Recortes (`21_baixar_cenas.py`)
- Leitura por janela (WarpedVRT) direto na grade fixa — nunca a cena inteira. Landsat C2 L2 do
  Planetary Computer (token SAS anônimo), Sentinel-2 L2A do Element84 (sem conta), CBERS do BDC.
- Seleção: estação seca (jun–set), nuvem < 40 %, até 6 cenas por (path, row) por ano — a janela
  cruza 223/224 × 064/065, então uma cena cobre em média 44 % da janela e a mediana junta os
  pedaços. Estação chuvosa (jan–abr, nuvem < 70 %, só red/nir/QA) para o NDVI máximo intersazonal.
- Sentinel-2: a janela cruza os tiles 22MFT/22MFU; até 8 datas por ano com os dois tiles. O BOA
  offset (baseline ≥ 04.00) já vem aplicado pelo Element84 — **verificado empiricamente**: floresta
  densa tem blue 150–430 DN em 2018, 2021, 2023 e 2025, sem salto de +1000.
- Falhas: 1 cena Landsat de 2022 (erro persistente de leitura no PC; 2022 ficou com 23 cenas) e
  1 Sentinel-2 de chuva de 2018 (asset no S3 privado). Ambas em `cenas/falhas.jsonl`.
- Correção durante a execução: o manifesto perdia cenas gravadas entre dois registros quando o
  processo era interrompido (1995 aparecia com 5 cenas, havia 18 em disco). `reconciliar()` relê
  as tags dos GeoTIFFs; roda ao fim de toda execução e em `--manifesto`.

### Composições (`22_compor_anual.py`)
- Máscara QA_PIXEL (bits 0–4) + faixa válida C2; SCL ∈ {0,1,3,8,9,10,11}. Mediana por banda.
  Harmonização OLI→ETM+ de Roy et al. 2016 (coeficientes OLS, como no LandTrendr), aplicada a
  Landsat 8/9 e ao Sentinel-2 (MSI ≈ OLI — declarar no artigo).
- Cobertura: 42 dos 43 anos têm 100 % dos pixels observados antes do preenchimento; 1984 tem
  97,2 % (2,8 % preenchidos com 1985). Mediana de observações por pixel: 2 (1989) a 13 (2022–23).
  2012 (só ETM+ SLC-off): 20 cenas, mediana 6 obs, 93 % com ≥ 3 — sem gap-fill espacial.
- NDVI máximo da chuva: cobertura anual irregular (Amazônia): 1995 sem nenhuma cena limpa,
  1988 26 %, 2012–13 45 %. Preenchido pixel a pixel com os anos vizinhos (±1, ±2, ±3), como as
  composições; `--preencher` refaz só isso.
- MSS: 1973 (2 cenas, ago/1973, nuvem 0–4 %) e 1982 (3 cenas, out/1982). Nível L1 DN.

### Classificação (`23_classificar_mancha.py`)
Eras e rótulos (revisão crítica do plano: treino por era + amostra estável comum):

| Era | Anos | Referências de treino | Amostras | OOB | CV blocos 3 km (5 dobras) |
|---|---|---|---|---|---|
| tm_etm (Landsat 5/7) | 1984–2012 | 2000 e 2010: MapBiomas 24 ∩ WSF-Evo (ano ≤ ref), erodido | 38.102 | 0,980 | OA 0,976 · F1 0,941 |
| oli (Landsat 8/9) | 2013–2026 | 2019: AU 2019 rev. ∩ (WSF2019 ∨ MapBiomas 10 m); 2022: AU 2022 ∩ MapBiomas 10 m 24 | 43.065 | 0,969 | OA 0,962 · F1 0,938 |
| msi10 (Sentinel-2) | 2017–2026 | 2022: AU 2022 ∩ MapBiomas 10 m 24 | 50.390 | 0,957 | OA 0,952 · F1 0,931 |

- A AU 2015 do IBGE não cobre Canaã (E3a) — a era OLI usa 2019 e 2022, não 2015 como o plano previa.
- Negativos estratificados (floresta / pastagem / outros) e **loteamentos vazios sem construção como
  negativos explícitos**; amostra estável (urbano desde ≤ 1990; floresta/pasto/água em todos os
  41 anos MapBiomas) com feições de 3 anos por era.
- Feição mais importante nas três eras: **NBR2** (swir1 − swir2), seguida de NDVI, swir2, BUI e
  NDVI máximo da chuva — a confusão dominante é mesmo solo exposto/pasto seco, como a revisão do
  plano antecipou; a amplitude intersazonal entra entre as 6 primeiras na era OLI.
- Textura GLCM foi substituída por desvio-padrão local (3×3 e 5×5) de NIR e NDBI — mesma
  informação, ~100× mais barato; declividade do Copernicus DEM GLO-30 (Planetary Computer), não
  TOPODATA (o BDC devolve 404 nos assets do `landsat-lgi`, e o COP-DEM é COG).

Pós-processamento, nesta ordem (as três primeiras regras vêm da revisão crítica do plano):
0. abertura 3×3 com restauração de 1 pixel de borda em cada ano — **tira rodovias e estradas de
   1 pixel e pontinhos**, que na primeira versão eram "selados" e encadeados à sede (a sede 2022
   caía de 3.811 ha para 2.644 ha só com isso);
1. maioria temporal em janela de 3 anos (1º ano exige confirmação no 2º; último ano fica bruto);
2. persistência: urbano em 2 anos consecutivos = selado, sem retração; não retração só no núcleo
   selado (pixels de um ano só podem sair — retrações pequenas em 1992, −6 ha);
3. máscara de mineração → classe 3 (curva separada);
4. unidade mínima 1 ha (8-conectividade), buracos ≤ 1 ha preenchidos;
5. sede contígua (classe 1) = componentes ligados ao núcleo por encadeamento de 1 km (distância
   euclidiana, até 10 km do núcleo) × outros núcleos (classe 2);
6. de 2022 em diante, polígonos "loteamento vazio" da AU 2022 sem construção = classe 4.

Máscara de mineração: MapBiomas 30 (união 1985–2025, 690 ha) dilatado 1 km ∪ concessões de
lavra ANM/SIGMINE (7 processos, WFS) **restritas a ≤ 3 km da lavra observada** — a concessão de
cobre da Vale tem 97,8 mil ha e engoliria a janela; menos os polígonos de área urbanizada da
AU 2022. Total 11.210 ha (19 % da janela). Construído dentro dela: 11 ha (1984) → 75 (2010) →
184 (2022) → 280 ha (2026).

### Série própria (30 m, sede contígua)

| Ano | Sede (ha) | Outros núcleos | Constr. em mineração | Lot. vazio (AU 2022) |
|---|---|---|---|---|
| 1984 | 8 | 0 | 11 | — |
| 1990 | 46 | 68 | 41 | — |
| 1996 | 76 | 72 | 41 | — |
| 2000 | 139 | 84 | 42 | — |
| 2004 | 504 | 171 | 57 | — |
| 2007 | 745 | 203 | 74 | — |
| 2010 | 1.076 | 201 | 75 | — |
| 2016 | 2.397 | 245 | 125 | — |
| 2019 | 2.508 | 280 | 137 | — |
| 2022 | 2.644 | 300 | 184 | 235 |
| 2026 | 3.656 | 265 | 280 | 136 |

Série de 10 m (Sentinel-2) coincide com a de 30 m no ano de referência (sede 2022: 2.640 ha ×
2.644 ha) e diverge um pouco nos extremos (2017: 2.000 × 2.450; 2026: 3.851 × 3.656) — a de 30 m
é a principal, como decidido no plano. Marcos MSS (clareira NDVI < Otsu, não mancha urbana):
347 ha de clareira a ≤ 3 km do núcleo atual em 1973 e 538 ha em 1982.

### Validação independente (`24_validar_mancha.py`)
**Achado que mudou o desenho**: as cenas CBERS-2B HRC L2 (2008–2010) chegam com erro de
georreferência de **0,5 a 3 km** (só correção por efemérides); a primeira rodada de validação
"2010" estava comparando o mapa com outro lugar (UA 0,65, PA 0,17, área ajustada 4.753 ± 5.380 ha).
Solução: subcomando `registrar` — correlação de fase (skimage) entre cada cena de validação e a
composição Landsat do ano, em duas passagens (estimar → aplicar → residual). As subcenas do mesmo
dia convergem para o mesmo deslocamento (jul/2009: +530 m E, −1.720 m N; abr/2009: +807 / −4.119;
out/2008: +2.540 / −675), residual 0,0–0,1 px. CBERS-4A WPM L4 e CBERS-4 PAN5M L4 (2017–18) estão
a ≤ 27 m; PAN5M 2015 a 210 m. Cenas com residual ≥ 1,5 px (fev/2010 nublada; abr/2009 161/B) e uma
WPM de abr/2022 com 20 % de cobertura e pico espúrio de 1,3 km ficaram fora.

Desenho: 3 épocas × amostra aleatória estratificada pelo mapa (urbano; não urbano a ≤ 300 m;
restante), 50 pontos por estrato, recortes de 400 m com o pixel de 30 m marcado, fotointerpretados
pela sessão principal em montagens (`data/interim/validacao/montagem_*.png`). Estimador de
Olofsson et al. 2014 / Stehman 2014 com pesos W_h = N_h/N; "incerto" (nuvem, borda ambígua,
loteamento sem construção, equipamento isolado) sai da matriz e é contado.

| Época | Referência | n útil (incertos) | OA ± IC95 | UA urbano | PA urbano | Área mapa (ha) | Área ajustada ± IC95 (ha) |
|---|---|---|---|---|---|---|---|
| 2022 | CBERS-4A WPM 2 m (jul–ago/2022) | 131 (15) | 0,984 ± 0,009 | 0,775 | 0,887 | 2.944 | 2.573 ± 555 |
| 2017 | CBERS-4 PAN5M 5 m (jun/2017) | 127 (23) | 0,991 ± 0,007 | 0,838 | 1,000 | 2.697 | 2.260 ± 325 |
| 2009 | CBERS-2B HRC 2,5 m (jul/2009, corregistrada) | 57 (29) | 0,996 ± 0,003 | 0,793 | 1,000 | 1.174 | 931 ± 176 |

Leitura: a acurácia global é alta porque o não urbano domina a janela; o que importa é o par
UA/PA — **o mapa tem comissão de ~15–20 % na franja** (lotes abertos/terraplenados, pátios de
equipamentos, chácaras à beira da cidade) e omissão baixa. As áreas ajustadas pelo erro, com IC,
são o número honesto para os anos censitários; E5 pode aplicar o fator mapa/ajustada (0,85–0,87,
estável nas três épocas) à série inteira, ou usar as ajustadas só nas épocas validadas.
Sensibilidade ao limiar de probabilidade (`sensibilidade_limiar.csv`, mesmos pontos): 0,6 dá
UA/PA mais equilibrados (2022: 0,88/0,80; 2017: 0,88/0,94; 2009: 0,84/0,91) e áreas de mapa mais
próximas das ajustadas. **O limiar publicado continua 0,5 (fixado a priori)** — escolhê-lo pela
amostra tiraria a independência da validação; a tabela fica para a discussão em E5/E6.
Antes de 1999 não há referência independente (o PLANO.md já previa declarar).

### Comparação com produtos prontos (`comparacao_serie_propria.csv`)
- **MapBiomas 24 / própria**: razão mediana **4,1** em 1985–2025; IoU 0,01 (1985) → 0,33 (2010)
  → 0,65 (2017–2024). Confirma o diagnóstico de E3a: MapBiomas superestima e estagna 1996–2014
  (3.140 ha constantes enquanto a série própria vai de 148 a 2.133 ha).
- **WSF-Evolution**: própria e WSF andam juntas até 2002 (própria/WSF ≈ 1,2), depois a própria
  cresce mais rápido (2010: 1.277 × 777 ha; 2015: 2.442 × 920) — WSF-Evo é conhecido por
  subestimar crescimento recente em cidades pequenas; IoU máximo 0,57 (2004).
- **IBGE AU**: IoU 0,57 (2019) e 0,58 (2022); própria 2.944 ha × AU 2.035 ha em 2022. A AU exclui a
  franja pouco densa e os equipamentos, e a própria tem a comissão medida acima — as duas
  diferenças explicam a razão 1,45. Dos 673 ha de "loteamento vazio" da AU 2022, 431 ha são
  classificados como construídos pela própria (arruamento/terraplenagem lê como construído) e
  235 ha ficam como classe 4; em 2026 restam 136 ha vazios.
- **MapBiomas 10 m** (2017–2025): IoU 0,67–0,72, áreas 2.045–2.852 ha × própria 2.710–3.555 ha.
- **GHSL**: fração ≥ 0,2 dá 615 ha (2010) e 1.078 ha (2020) — magnitude 2–3× menor (100 m).

## Verificações (`validate.py --e3b` — OK, 19 checagens)
Composições 43/43 e 10/10; cobertura ≥ 95 % antes do preenchimento (mín 97,2 % em 1984);
modelos com OA ≥ 0,85 e F1 ≥ 0,75 na CV por blocos; série 43/43 anos, rasters e vetores 43/43;
sem retração do urbano total > 5 % e > 10 ha; validação OA ≥ 0,85 nas 3 épocas; IoU × AU ≥ 0,5
(0,57/0,58); IoU × WSF-Evo mediana 0,35; razão MapBiomas/própria 4,1 (reportada). Também
`validate.py --e3a` e `--smoke` continuam OK.

Inspeção visual da sessão principal: mapas de 1990, 2010 e 2022 sobre as composições em falsa-cor
com o contorno da AU 2022 — núcleo compacto em 1990 (46 ha), expansão contígua em 2010, contorno
2022 acompanhando a AU com franja a mais no noroeste, ao longo da rodovia de acesso e de equipamentos.

## Decisões tomadas nesta sessão (registrar no artigo)
1. Série principal Landsat 30 m 1984–2026 (mesma família de sensores); Sentinel-2 10 m secundária.
2. Rodovias removidas por abertura morfológica antes do filtro temporal; unidade mínima 1 ha;
   encadeamento de 1 km para a sede contígua.
3. Máscara de mineração = lavra observada (MapBiomas) + 1 km, mais concessões ANM só perto da lavra.
4. Época de validação 2009 (não 2010) e 2017 (PAN5M) além de 2022; HRC corregistrada.
5. Limiar 0,5 mantido a priori; sensibilidade reportada.
6. Substituições declaradas: COP-DEM por TOPODATA; std local por GLCM; AU 2019/2022 por AU 2015.

## Pendências
- **Acurácia pré-1999 não verificável** (sem referência independente; SPOT World Heritage / KH-9
  a cargo do usuário, como já constava). Declarar no artigo.
- **Comissão na franja (~15–20 %)**: E5 decide entre publicar a série bruta com as áreas ajustadas
  nas épocas validadas, ou aplicar o fator 0,85–0,87 a toda a série (com a ressalva).
- A montagem de validação de 2009 perdeu 29 de 86 pontos por nuvem (HRC sem máscara); n útil 57.
  Se o usuário quiser reforçar 2009, a HRC de out/2008 (corregistrada, limpa) permite mais pontos.
- TerraClass continua dependendo de download manual (E3a); entraria em `comparar` sem código novo.
- Volume: `data/interim/cenas` tem 8,8 GB (fora do git). Pode ser apagado depois de E3c — os
  scripts rebaixam tudo, resumível.
- `web/public/data/geo/` ainda não recebeu a série própria: é o passo 7 (E3c), junto com PMTiles
  e os WebP das composições por ano (os quicklooks em `composicoes/quicklook/` já servem de base).

## Próxima etapa
**E3c — Estatísticas e camadas web** (Fase 3 passos 6–7): `26_estatisticas_mancha.py` passa a ler
`mancha_propria_anual` (Δ ano a ano, taxas por período mineral, densidade hab/ha e dom/ha nos anos
censitários com as áreas ajustadas, direção da expansão via `ano_urbanizacao30.tif`) e
`27_tiles_camadas.py` gera as camadas de `web/public/data/geo/`. Modelo da sessão: Opus 5.
Aguardar pedido explícito do usuário.
