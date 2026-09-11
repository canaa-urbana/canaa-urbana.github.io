# Plano — Urbanização de Canaã dos Carajás: dashboard interativo + artigo científico

## Contexto

Canaã dos Carajás (PA, cód. IBGE 1502152) passou de núcleo de assentamento dirigido (CEDERE II, Projeto de Assentamento Carajás/GETAT, 1982) — localidade do distrito-sede de Marabá e, a partir de 1988, de Parauapebas (nunca foi distrito) — a município (Lei estadual 5.860 de 05/10/1994, instalado em 01/01/1997) e, com as minas de Sossego (Vale, cobre, 2004) e S11D (Vale, ferro, construção 2013–16, operação dez/2016), a um dos municípios de crescimento populacional mais rápido do Brasil. Série confirmada na API do IBGE (SIDRA t/200, t/9923, t/6579):

| Ano | Total | Urbana | Rural | % urbana |
|---|---|---|---|---|
| 1991 | (localidade de Parauapebas: 53.335 no município inteiro; sem dado para Canaã) | | | |
| 1996 | 11.139 (retabulação da Contagem 1996 citada pelo CETEM; SIDRA só traz Parauapebas 74.702) | — | — | — |
| 2005 | 20.474 (censo municipal Diagonal Urbana, PDP 2007; estimativa IBGE 13.421) | 14.305 | 6.169 | 69,9 |
| 2007 | 23.757 (Contagem, SIDRA t/793) | — | — | — |
| 2000 | 10.922 | 3.924 | 6.998 | 35,9 |
| 2010 | 26.716 | 20.727 | 5.989 | 77,6 |
| 2022 | 77.079 | 69.332 | 7.747 | 90,0 |
| 2026 (estimativa) | 92.311 | — | — | — |

Objetivo: construir um conjunto de dados integrado (API IBGE + agregados por setor + microdados da amostra 1991/2000/2010/2022 + sensoriamento remoto), um dashboard interativo (Ardósia) e um artigo científico (PDF, aba do dashboard) que avalie o impacto dos grandes projetos minerais na urbanização da sede municipal, com ênfase na migração de data fixa e no perfil dos migrantes.

## Restrições e decisões de base

- **Sigilo dos microdados**: o Censo 2022 é de **acesso controlado** (termo de compromisso arquivado localmente, fora do repositório). Reaplicar integralmente as regras do projeto irmão `atlas-migração` (`pipeline/disclosure_rules.py`: n≥5 pessoas / ≥3 domicílios por célula, arredondamento a múltiplo de 5, faixas de n, sem cruzamento de 3+ dimensões temáticas, nunca publicar `controle`/área de ponderação). Nunca imprimir registros individuais; nada de `data/raw` sai da máquina nem vai a subagentes remotos ou Artifacts. Tudo que entra no dashboard/artigo passa por um gate de revelação (`pipeline/disclosure_check.py`) antes da cópia para `web/public/data`.
- **Reuso máximo dos projetos irmãos** (mesma pasta `estudos-pesquisa/`):
  - `migracoes-mineracao/scripts/lib/{fwf,migracao,seletividade,deflator,mineracao,amc,geo,malhas,viz,ardosia_palette}.py` — leitura FWF por layout oficial (2000/2010), classificação harmonizada de migração de data fixa nos três censos (`classificar_5anos(df, censo=...)`, com os saltos de pergunta já documentados: 2010 `V0626`/`V6264` vs município atual; 2000 `V0415`/`V0416`/`V0424`; 2022 `P0530`/`P0550`/`P0600`), CFEM/ANM, deflator IPCA.
  - `migracoes-mineracao/data/interim/layouts/{2000,2010}_{pessoas,domicilios,familias}.json` — layouts já parseados (nenhuma posição de coluna à mão).
  - `migracoes-mineracao/data/processed/raw_{2000,2010,2022}/{pessoas,domicilios}_15.parquet` — Pará já convertido, porém **sem** `V1006` (situação urbana/rural), `V0011` (área de ponderação), `V1001`, `V4001` e demais variáveis de domicílio necessárias aqui. Decisão: **re-parsear apenas o Pará** (rápido) com lista de campos ampliada, usando o mesmo `lib/fwf.py` e os TXT já locais (`microdados_censo_amostra_2010_txt/PA/`; 2000 e 1991 em o disco externo de backup).
  - `migracoes-mineracao/.venv` (Python 3.14 com duckdb, pandas 3, pyarrow, geopandas, shapely, pyproj, pyogrio, scikit-learn, statsmodels, matplotlib, pdfplumber). O Python global é vazio; criar venv próprio com `uv` clonando esses requisitos e acrescentando o stack raster (rasterio, rioxarray, xarray, pystac-client, planetary-computer, odc-stac, scipy).
  - `migracoes-mineracao/scripts/docx_pipeline/{md_to_docx.js,ardosia_docx.js}` + `soffice --headless --convert-to pdf` — pipeline pronto markdown → DOCX Ardósia → PDF para o artigo.
  - `atlas-migração/pipeline/{disclosure_rules,disclosure_check,verify_gate}.py` — gate de revelação.
  - `compat-setor-censitario/tools/preprocess.py` + `data/oficial/2010_2022/` — sobreposição de malhas 2010↔2022 e tabela de correspondência oficial de setores.
  - Identidade visual: skill `ardosia-brand-guidelines` (glifo de coorte no dashboard; monograma no artigo; `scripts/ardosia.css`, `scripts/palette.py`).
- **GDAL**: não está no PATH; usar o bundle do QGIS 3.44 (`/Applications/QGIS.app/Contents/MacOS/`) ou rasterio/pyogrio no venv.
- **Sem conta GEE configurada**: pipeline de imagens em Python puro via STAC (Planetary Computer / Element84 / INPE-BDC), sem depender de Google Earth Engine. MapBiomas via download direto (GeoTIFF por município / estatísticas) — detalhes na seção de imagens.

## Requisitos adicionais do usuário (mensagens durante o planejamento)

1. Execução orquestrada com subagentes, escolhendo automaticamente o modelo Claude de melhor custo-benefício por tarefa (ver seção "Orquestração").
2. O app deve ter um **mapa interativo com slider ano a ano** (1990→2026) mostrando a evolução da mancha urbana da sede, com **estatísticas de crescimento de área entre anos consecutivos** (ha/km², variação absoluta, % e taxa anual), além dos recortes dos anos censitários.
3. O mapa deve ter **controle de camadas selecionáveis para todos os dados espaciais utilizados**: mancha urbana classificada (por ano), MapBiomas classe 24, produtos globais de cross-validation (GHSL, WSF), Áreas Urbanizadas IBGE (2005/2015/2019/2022), setores censitários 2010 e 2022 com indicadores coropléticos, limite municipal e perímetro urbano, minas e infraestrutura (Sossego, S11D, ferrovia/rodovias), composições de satélite de fundo (Landsat/Sentinel-2/CBERS por ano).
4. O artigo deve conter **revisão bibliográfica abrangente** de toda a produção acadêmica conhecida sobre o município (Fase 4).
5. Os microdados controlados do Censo 2022 **podem ser usados** na análise migratória, sem publicar microdados e com cuidados anti-identificação (ver "Restrição legal").
6. O plano deve permitir **execução em etapas** (ver "Execução em etapas").
7. **Reconstituir a trajetória populacional** do assentamento desde o início (antes da criação do município) a partir de bibliografia, citações e fontes históricas (Fase 1b).
8. **Avaliar a mancha do assentamento em imagens anteriores a 1991** (ver avaliação na Fase 3: viável com Landsat TM desde 1984 e MSS 1979–82).

## Inventário de dados (verificado)

### Microdados da amostra — identificação de Canaã

| Censo | Canaã identificável? | Fonte local | Formato | Variáveis-chave |
|---|---|---|---|---|
| 1970 | Não (Marabá; distrito só se "ponderável", sem DTB Norte local) | `<disco externo>/…1970_Amostra/Dados/DAMO70PA.txt` | FWF 76 | — |
| 1980 | Não (só `MUNIC` 4 díg., sem distrito) | `…1980_Amostra/Dados/Região Norte/{Pessoas,Domicilios}/CD80{PES,DOM}15.DBF` | dBase | `MITEMPMU`, `SITUACAO` |
| 1991 | **Não** — só `MUNICNUM`; Canaã dentro de Parauapebas 1505536 | `…1991_Amostra/Microdados_…_1991_Amostra.zip` → `Dados/Região Norte/CD91AMOUP15.DBF` (usar `unzip -p`, zipfile do Python não lê) | dBase, arquivo único pessoa+domicílio | `PESO`, `SITSET`, data fixa 01/09/1986 `MIMO86UF`/`MIMO86MU`/`MIMO86ZN`, `MIANMOMU`, `EDANOEST`, `RTOTALPV`, `POSOCUP`, `AGUA`/`SANESCOA`/`LIXO`/`ILUMINA` |
| 2000 | **Sim** (distrito 150215205, 1 área de ponderação; maioria rural) | `<disco externo>/…2000_Amostra/PA/{Pes15,Dom15,FAMI15}.txt` + `SAS/LE *.sas` | FWF 390/170/118 | `V0103`/`V1103`, `V0104`, `V1006`, `AREAP`, `P001`; data fixa 31/07/1995 `V0424`+`V4260`+`V4250`; `V0415`/`V0416`; `V4300`; `V4614`/`V7616`; `V4452`/`V4462`/`V0447`; `V0207`/`V0211`/`V0212`/`V0213`/`V7203`/`V7204` |
| 2010 | **Sim** (1 área de ponderação) | `<microdados locais>/microdados_censo_amostra_2010_txt/PA/Amostra_{Pessoas,Domicilios}_15.txt` | FWF 540/172 | `V0002`, `V0011`, `V1006`, `V1005`, `V0010`; data fixa 31/07/2005 `V0626`+`V6262`+`V6264`; `V0624`; `V0618`; `V6400`; `V6527`/`V6531`; `V6461`/`V6471`/`V0648`/`V6930`; `V4001`, `V0201`, `V0207`/`V0208`/`V0210`/`V0211`, `V6203`/`V6204`, `V6210` |
| 2022 | **Sim, só no acesso controlado** (5 áreas de ponderação) | `<microdados locais>/microdados_censo_amostra_2022_csv_…/15/{Pessoas,Domicilios,Familia}_15_controlado.csv` | CSV `;` | `P0080`, `P0090`, `P0140`, `P0120`, `P0111`; data fixa 31/07/2017 `P0600`+`P0610`+`P0620`; `P0550`; `P0480`/`P0500`; `P0770` (compatível 2010) + `P0790`; `P1110`/`D0360`; `P0970`/`P0980`/`P0990`/`P1020`; `D0190`, `D0240`, `D0250`/`D0260`/`D0310`, `D0330`, `D0350` |

Notas: (i) `Composição das Áreas de Ponderação.txt` (2010) é UTF-16LE; (ii) layout 2010 `PESS` tem posições nas colunas 8/9 da planilha (já tratado em `00c_layouts.py`); (iii) 2022 não tem energia elétrica nem densidade por cômodo — índice de adequação domiciliar comparável 2000/2010/2022 usa água/esgoto/lixo (+ densidade por dormitório); (iv) pesos controlados 2022 só coincidem com o oficial para população total e sexo por área de ponderação — declarar nos métodos.

**1991 — estratégia (revista após o levantamento histórico)**: a Formação Administrativa do IBGE confirma que Canaã foi "ex-localidade" elevada a município e distrito em 1994 — não existe tabela de distrito nem lei municipal de 1991 a procurar. Portanto: (a) o Censo 1991 só oferece Parauapebas inteiro (53.335; 4,76 moradores/domicílio, t/156) — rotular "Parauapebas 1991 (inclui o atual Canaã)"; (b) tentar ainda a Sinopse Preliminar 1991 e os "Resultados do Universo – Pará" na Biblioteca IBGE (lista de localidades/aglomerados urbanos, que pode conter o "CEDERE II"/Canaã como aglomerado) e o DATASUS TABNET (estimativas IBGE 1996–1999 por município recém-criado); (c) 1991 no dashboard = mancha do assentamento (imagens TM) + população reconstituída da Fase 1b (intervalo, estimativa própria) + perfil demográfico de Parauapebas 1991 como contexto regional.

### Agregados oficiais e malhas (FTP/API IBGE, todos verificados HTTP 200)
- API SIDRA: t/200 (1970–2010, urbano/rural), t/202 (N10 distrito), t/1378 (2010), t/9923 (2022 por situação), t/4714 (área 3.146,821 km²), t/4709, t/9605, t/6579 (estimativas 2001–2026; lacunas 2007/2010/2022/2023; quebra de regime 2006→2008 pela Contagem 2007). Cidades/indicadores (96385, 96386, 60045, 60036…). Localidades: 1 distrito (150215205), sem subdistritos/bairros — desagregação intraurbana só por setor censitário.
- Setores censitários: 2000 **sem malha urbana digital para Canaã** (404), mas com agregados (`Agregado_de_setores_2000_PA.zip`, 21,7 MB); 2010 malha `censo_2010/setores_censitarios_shp/pa/pa_setores_censitarios.zip` (7,8 MB) + agregados universo `PA_20260615.zip` (53,9 MB); 2022 malha `censo_2022/setores/shp/UF/PA_setores_CD2022.zip` (23,8 MB), `malha_com_atributos/`, agregados temáticos nacionais (básico 15,4 MB, demografia, alfabetização, cor/raça, domicílio 1–3, entorno, rendimento do responsável), `Historico_formacao_Setores_Censitarios_2010_2022.xlsx` (comparabilidade); malhas 2019/2020/2021 por município (KML) e WFS do geoserver IBGE para 2020–2022 (já usado em `compat-setor-censitario`). Áreas de ponderação 2010/2022 via composição de setores.
- **Áreas Urbanizadas do Brasil** (IBGE): 2005, 2015, 2019, 2022 (`AreasUrbanizadas2022_Brasil.zip`, 54,5 MB; tabelas de comparação 2019–2022) — âncora vetorial oficial para validar a classificação.
- Malha municipal: API v3/v4 (GeoJSON). Malha 2000/2010 de município via geoftp.

### Restrição legal (2022) — decisão do usuário
O termo de compromisso (assinado 31/08/2026, finalidade "pesquisa acadêmica / migrações") proíbe compartilhar os arquivos; a consulta ao IBGE sobre divulgação de agregados está pendente. **Decisão do usuário (09/09/2026): usar os microdados 2022 na análise de migração; nenhum microdado é publicado, só agregados, com cuidados anti-identificação.** Regras aplicadas (gate automático `disclosure_check.py`, herdado do atlas-migração e endurecido): células com n ≥ 10 pessoas amostrais e ≥ 10 domicílios distintos; estimativas ponderadas arredondadas a múltiplos de 5 (percentuais a 1 casa); nunca contagens amostrais exatas (faixas de n); no máximo 2 dimensões temáticas cruzadas por tabela; supressão complementar e categoria "outros"; matriz OD só para origens com n ≥ 10 e demais agregadas por UF/região; nada por área de ponderação; nenhum registro individual em logs/saídas; `data/raw`/`interim` gitignored e fora de qualquer subagente remoto ou Artifact; CV publicado. As mesmas regras valem para 2000/2010 (públicos, mas amostra pequena em Canaã) e 1991.

## Estrutura do projeto (`urban-canaa/`, criar repositório git)

- `CLAUDE.md` — regras de sigilo + comandos (modelo: `migracoes-mineracao/CLAUDE.md`); `PLANO.md` — cópia deste plano com checklist de etapas.
- `pyproject.toml` / `.venv` — uv; base = requisitos do `migracoes-mineracao` + stack raster.
- `data/raw/` — symlinks para os Microdados (gitignored, nunca copiado); `data/externo/` — downloads públicos (SIDRA, malhas, agregados por setor, Áreas Urbanizadas, MapBiomas, GHSL/WSF, cenas de satélite; gitignored, reproduzível por script); `data/interim/` — parquet por censo (só PA/Canaã), layouts JSON, composições raster; `data/processed/` — agregados aprovados pelo gate (versionados) + `.gate_ok`.
- `pipeline/` — `00_setup_env.sh`; `10_ibge_api.py`, `11_setores.py`, `12_microdados_{1991,2000,2010,2022}.py`, `13_migracao_perfil.py`, `14_indicadores_setor.py`; `20_imagens_catalogo.py`, `21_baixar_cenas.py`, `22_compor_anual.py`, `23_classificar_mancha.py`, `24_validar_mancha.py`, `25_mapbiomas_ghsl.py`, `26_estatisticas_mancha.py`, `27_tiles_camadas.py`; `30_bibliografia.py`, `31_verificar_refs.py`; `40_analise_artigo.py`, `41_figuras.py`; `disclosure_rules.py`, `disclosure_check.py`, `verify_gate.py`, `validate.py`; `lib/` (cópia de `migracoes-mineracao/scripts/lib` + Ardósia, com nota de origem).
- `web/` — dashboard (Vite + React + MapLibre GL + ECharts/Recharts); `artigo/` — `texto.md`, `figuras/`, `tabelas/`, `artigo.docx`, `artigo.pdf`, `bibliografia/referencias.json`; `docs/` — `METODOLOGIA.md`, `revisao_bibliografica.md`, `qa/*.md`.

## Fase 1 — Dados IBGE (API + agregados por setor)

1. `10_ibge_api.py`: baixa e versiona em `data/processed/ibge/` (dados públicos, sem gate): t/200, t/202 (Parauapebas 1991 e distrito), t/1378, t/9923, t/4714, t/4709, t/9605, t/6579, indicadores Cidades; também t/1552/t/9514 (pirâmides etárias 2010/2022 por sexo e idade), t/3175/t/9520 (idade × situação), tabelas de instrução/renda/trabalho municipais 2000/2010/2022 (universo e amostra: t/1383, t/3596, t/2098, t/9542, t/9556, t/10063…), PIB municipal (t/5938), CEMPRE (t/6449), CFEM (ANM — reutilizar `lib/mineracao.py`), RAIS/CAGED (opcional, via Base dos Dados ou download PDET). Cada chamada grava JSON bruto + parquet tidy com `fonte`, `tabela`, `url`, `data_acesso`.
2. `11_setores.py`: malhas de setores 2010 e 2022 do PA (geoftp) recortadas para Canaã; agregados universo 2010 (PA_20260615.zip: Básico, Domicílio01/02, Pessoa03/11/13, Responsável…), agregados 2022 (básico, demografia, alfabetização, cor/raça, domicílio 1–3, entorno, rendimento do responsável); 2000 só tabela (sem geometria). Indicadores por setor da sede (situação = urbana): população, domicílios, densidade (com área efetivamente domiciliada 2022), sexo, grupos etários, alfabetização, cor/raça, rendimento médio/mediano do responsável, % sem rendimento, abastecimento de água/esgoto/lixo/energia, moradores por domicílio, entorno (pavimentação, iluminação, arborização, esgoto a céu aberto). Tabela de correspondência 2010↔2022 a partir de `Historico_formacao_Setores_Censitarios_2010_2022.xlsx` e sobreposição espacial (`compat-setor-censitario`). Áreas de ponderação 2010/2022 como camada.
3. Saída: GeoParquet + TopoJSON/GeoJSON simplificado por ano para o mapa (`web/public/data/geo/setores_{2010,2022}.json`).

## Fase 1b — Trajetória populacional pré-municipal (1982→2000), reconstituída (requisito do usuário)

Objetivo: recompor, a partir de bibliografia, citações de terceiros e fontes históricas, a população do assentamento/vila/distrito de Canaã dos Carajás desde o início do assentamento GETAT (Projeto de Assentamento Carajás, CEDERE I–III, 1982–85) até a criação (1994), instalação (1997) e os primeiros registros oficiais (Contagem 1996; Censo 2000).
1. `15_trajetoria_historica.py` + `data/externo/historico/trajetoria_pre_1994.csv`: tabela ponto a ponto — ano | valor | unidade (famílias/pessoas) | recorte (CEDERE I / sede / distrito / município) | fonte (autor, ano, página) | URL | confiabilidade. Fontes: IBGE Cidades (histórico), Biblioteca IBGE (Sinopse Preliminar 1991 e Resultados do Universo 1991 – Pará; localidades/aglomerados de Parauapebas), Contagem 1996 e 2007 (SIDRA), GETAT/INCRA (1.551 famílias assentadas 1982–85; 816 títulos até 1985), CETEM ("do leite ao cobre"), ANPUR ("A cidade na fronteira"), Carmo (2023), RBEUR, Plano Diretor (2006/2007 e revisões), EIA/RIMA do Sossego (linha de base ~2001), teses sobre Parauapebas/Carajás/GETAT, Prefeitura.
2. Série anual consistente 1982–2000: âncoras oficiais (1991 Parauapebas incl. Canaã; Contagem 1996; Censo 2000) + pontos bibliográficos; conversão famílias→pessoas com tamanho médio de domicílio regional dos próprios censos (1991/2000, microdados); interpolação geométrica entre âncoras com faixas de incerteza; cada valor rotulado como "oficial", "citação de terceiro" ou "estimativa própria". Cruzamento com a mancha urbana 1990–2000 (densidade implícita) como teste de plausibilidade.
3. Saída: gráfico de trajetória 1982–2026 no dashboard (aba "Anos censitários"/"Mineração e economia", com marcadores por tipo de fonte) e seção do artigo ("Da colônia agrícola à cidade mineral: trajetória demográfica 1982–2000").
**Pontos históricos encontrados (levantamento de 09/09/2026, todas as fontes verificadas)**

| Ano | Figura | Unidade / recorte | Fonte | Confiabilidade |
|---|---|---|---|---|
| 1977 | primeiras ocupações espontâneas (região da Vila Mozartinópolis) | qualitativo | PDP 2007 p. 53 apud Carmo (ENANPUR 2023) | qualitativa |
| 1980 | criação do GETAT (Dec.-lei 1.767, 01/02/1980) | — | Carmo (ENANPUR 2023) | alta |
| 1982 | criação do CEDERE II (atual sede de Canaã); 1983 CEDERE I (hoje vila de Parauapebas); CEDERE III (Vila Ouro Verde) 1983 ou 1985 (fontes divergem) | núcleos | Carmo 2023 (RTG) Tab. 1; PDP 2007 | média |
| 1982–84 | **1.551 famílias** assentadas nos três núcleos (PDP 2007 p. 55, citando IBGE) / "ao longo de três anos" no CEDERE (IBGE Histórico via API biblioteca) / "nos CEDEREs II e III, atual Canaã" (CETEM p. 40); Carmo Tab. 1: ~1.555 famílias no CEDERE II + ~550 colonos no CEDERE I | famílias (lotes ~50 ha) | PDP 2007; IBGE; CETEM; Carmo 2023 | alta para o total; **escopo irreconciliável** entre fontes |
| até 1985 | 816 famílias com título definitivo; fim do assentamento (GETAT extinto formalmente em 1987) | famílias | IBGE Histórico; PDP 2007 | alta |
| pós-1985 | apenas ~10% das famílias permaneceram nos lotes originais (venda de lotes, pasto, falta de infraestrutura) | estimativa | CETEM p. 42 | baixa |
| 1988 | Parauapebas desmembrado de Marabá (Lei 5.443/88); CEDERE II passa a Parauapebas | — | Carmo 2023 | alta |
| 1991 | Parauapebas 53.335 hab.; 4,76 mor./dom.; sem dado para Canaã | município (inclui Canaã) | SIDRA t/202, t/156 | alta |
| 03/04/1994 | plebiscito do nome (só a população urbana votou) | — | CETEM p. 41; Carmo 2023 | média |
| 05/10/1994 | Lei Estadual 5.860 cria o município; instalação em 01/01/1997; 1ª eleição 03/10/1996 | — | IBGE Formação Administrativa; PDP 2007 | alta |
| 1996 | Contagem: Parauapebas 74.702 (45.649 urb./29.053 rur.), **Canaã "..." no SIDRA** (t/305, t/475, t/552); **11.139** para Canaã só em fonte secundária (CETEM Tab. 3; Prefeitura) — coerente aritmeticamente (74.702 − 11.139 = 63.563) mas não recuperável no SIDRA; sem urbano/rural | município | SIDRA; CETEM | alta (ausência) / média (11.139) |
| 2000 | 10.922 (3.924 urb. / 6.998 rur.); 2.526 domicílios; 4,30 mor./dom.; 1996→2000 crescimento negativo (≈ −0,5% a.a.) | município | SIDRA t/202, t/156 | alta |
| 2001–06 | estimativas IBGE 11.425 → 13.870 | município | t/6579 | estimativas ancoradas em 2000, subestimadas |
| 2005 | **20.474** (14.305 urb. / 6.169 rur.); 42,3% das famílias urbanas com 1–3 anos de residência | censo municipal (Diagonal Urbana) | PDP 2007 Tab. 1–2 | média-alta |
| 2007 | 23.757 | Contagem | SIDRA t/793 | alta |

Números em circulação que **não** se sustentam (não usar): "11 mil → 28 mil em 2010" (PLHIS 2013; conflação 1996/2000 e 2010 = 26.716); "6 mil em 2000 → 25 mil em 2003"; "28.136 em 2004".

**Regras para a série 1982–2000** (saída da Fase 1b): âncoras duras = 2000 (10.922) e 2007 (23.757); âncora fraca = 1996 (11.139, com nota); 1991 inexistente para o recorte. Partida 1984/85 por conversão famílias→pessoas com 4,76 mor./dom. (Parauapebas 1991) como piso e 5,0–5,5 como teto, em **dois cenários de escopo** (1.551 famílias = CEDERE II+III ⇒ 7,4–8,5 mil; ou três núcleos menos CEDERE I ⇒ 4,8–5,5 mil). Não interpolar geometricamente 1985→1996: a curva é em U (esvaziamento pós-1985, recomposição por migração até 1996). Sem repartição sede/rural antes de 2000 — a "população da sede" pré-2000 só por estimativa (mancha × densidade) declarada. Fontes-chave a explorar em E1b: **PDP 2007 vol. 1 e 2** (transparenciacanaa, 44,6 MB; capítulos sobre vilas e parcelamento urbano ainda não lidos — cópias no scratchpad), CETEM "do leite ao cobre", Carmo 2023 (RTG e ENANPUR), IBGE Histórico via `servicodados.ibge.gov.br/api/v1/biblioteca?aspas=3&codmun=1502152` (contorna o 403 do site Cidades), DATASUS TABNET (estimativas 1996–1999), PLHIS 2013/2016, PDP 2016, Anuário Estatístico do Pará/IDESP, EIA/RIMA Sossego (acervo SEMAS-PA), teses (Coelho, Monteiro, Hébette, Becker).

## Fase 2 — Microdados (perfil demográfico e migrantes)

1. Ambiente: `.venv` com uv; `lib/` reutilizado de `migracoes-mineracao` (import por caminho ou cópia com nota de origem). Layouts 2000/2010 já em `migracoes-mineracao/data/interim/layouts/`; 1991: parsear `Documentação/Dicionário 1991.xls` (aba Layout) e ler o DBF via `dbfread`/`simpledbf` a partir de `unzip -p`, filtrando `MUNICNUM` ∈ {1505536 Parauapebas, 1501402 Marabá, 1502152 se existir}.
2. `12_microdados_*.py`: extrair só PA → filtrar Canaã (2000/2010/2022) e Parauapebas (1991 proxy, e como comparação em todos os anos); campos ampliados (situação urbana/rural, área de ponderação, todas as variáveis de domicílio, trabalho, renda, educação, migração). Gate `validate.py`: população expandida × SIDRA (t/200/t/9923) por situação; nº de domicílios × universo.
3. `13_migracao_perfil.py` (reutiliza `classificar_5anos`, `eh_retorno`, `seletividade`, `deflator`): para cada censo, na **sede urbana** (situação = urbana) e no município: (a) status migratório de data fixa (não migrante / migrante intraestadual / interestadual / internacional / retorno), origem (município, UF, região; matriz OD top-N), tempo de residência (coortes de chegada por ano ≈ pulsos Sossego 2002–04, S11D 2013–16), naturalidade; (b) perfil dos migrantes vs não migrantes: sexo, idade (pirâmide), cor/raça, escolaridade (`V4300`/`V6400`/`P0770`), renda pessoal e domiciliar per capita deflacionada (IPCA, R$ 2022), posição na ocupação/formalidade, setor de atividade (CNAE-Dom: mineração B, construção F, comércio/serviços…), ocupação, jornada, local de trabalho/commuting; (c) condições domiciliares dos domicílios com migrantes recentes: condição de ocupação (aluguel, cedido pelo empregador), tipo, água, esgoto, lixo, energia (até 2010), densidade por dormitório, internet (2022), adequação (índice reconstruído água+esgoto+lixo); (d) razões de seletividade (migrante/não migrante) e comparação com Parauapebas e Pará. Saída: tabelas ponderadas com erro-padrão (bootstrap por área de ponderação/ réplicas simples) e CV, passadas pelo gate (n ≥ 10 pessoas e ≥ 10 domicílios por célula, arredondamento a 5, faixas de n, cruzamento máximo de 2 dimensões temáticas).
4. Perfil demográfico geral por ano censitário (dashboard): pirâmide etária, razão de sexo, cor/raça, escolaridade, renda, ocupação, domicílios, taxa de crescimento geométrico intercensitário, componente migratório (crescimento total − crescimento vegetativo estimado via SINASC/SIM DATASUS ou método residual com t/2609/t/2654 já usados no `cohort-component`).

## Fase 4 — Bibliografia (requisito adicionado pelo usuário)

Objetivo: cobrir **toda a produção acadêmica conhecida sobre Canaã dos Carajás** (artigos, teses, dissertações, capítulos, relatórios técnicos, planos diretores e EIA/RIMA relevantes).
1. `30_bibliografia.py` consulta APIs abertas com termos "Canaã dos Carajás" (e variantes sem acento, "Canaa dos Carajas", "S11D", "Sossego mine", "Carajás urbanização"): OpenAlex (`api.openalex.org/works?search=`), Crossref, Semantic Scholar, SciELO (search + `articlemeta`), BDTD/IBICT (OAI-PMH), Catálogo de Teses CAPES, Google Scholar (via navegador, paginado), Periódicos CAPES/Scopus/WoS se houver acesso institucional, repositórios UFPA/UNIFESSPA/UFRA/NAEA, Anais ANPUR/ENANPUR/ABEP, Lattes (opcional). Deduplicação por DOI/título normalizado; export `artigo/bibliografia/referencias.json` no formato dos projetos irmãos (chave slug, ABNT autor-data, `verificado_em`) + BibTeX.
2. `31_verificar_refs.py`: cada entrada só entra após checagem de existência (DOI resolve / página do repositório), autoria, ano e veículo. Matriz de revisão (`docs/revisao_bibliografica.md`): tema (urbanização, moradia, migração, trabalho, economia mineral, meio ambiente, saúde, planejamento), período, método, principais achados — base da seção "Revisão de literatura" do artigo, com síntese por eixo e lacunas.
3. Expandir a busca para o contexto (company towns amazônicos, Parauapebas, Carajás/PGC, boom-bust, enclave mineral, resource curse local) em menor profundidade.

## Fase 5 — Análise e artigo científico

1. Desenho analítico (`40_analise_artigo.py`): (a) série populacional 1991/2000/2010/2022 + estimativas anuais vs. marcos minerais (Sossego 2002–04; S11D 2013–16; Salobo/Parauapebas; expansão Sossego/Cristalino); (b) crescimento da mancha urbana anual vs. CFEM/emprego formal/estimativas de população — elasticidade área-população, densidade urbana ao longo do tempo (compactação/dispersão); (c) coortes de chegada dos migrantes (tempo de residência) alinhadas aos ciclos de investimento; (d) perfil comparado migrantes × nativos e migrantes por período de chegada; (e) inserção ocupacional (mineração, construção, serviços) e formalidade; (f) condições domiciliares e desigualdades intraurbanas por setor (2010 → 2022); (g) comparação sintética com Parauapebas e municípios do Sudeste Paraense (controle sintético/diferença-em-diferenças descritiva com painel municipal 2000–2022 já existente em `migracoes-mineracao/data/processed/painel_temporal`); (h) 1991 como baseline pré-mineral (Parauapebas proxy, e mancha da sede).
2. `41_figuras.py`: figuras em matplotlib com `apply_ardosia()` (série temporal, mapas de mancha por ano censitário, pirâmides, dumbbells de seletividade, coropléticos por setor).
3. Texto: `artigo/texto.md` (estrutura: resumo PT/EN, introdução, revisão de literatura, área de estudo e contexto mineral, dados e métodos — incluindo pipeline de sensoriamento remoto, controle de revelação e limitações —, resultados, discussão, conclusão, referências ABNT, declaração de uso de IA reaproveitada de `bibliografia/declaracao_ia_padrao.md`). Conversão com `docx_pipeline/md_to_docx.js` → `soffice --headless --convert-to pdf` → `artigo/artigo.pdf`, exibido em aba do dashboard (`<iframe>`/pdf.js) e com download.

## Fase 6 — Dashboard (web/)

Stack: Vite + React + TypeScript, MapLibre GL JS (vetor + raster tiles/COG via PMTiles ou GeoJSON), Plotly.js ou Recharts para gráficos, CSS Ardósia (`ardosia.css`), glifo de coorte como marca. Dados estáticos em `web/public/data` (só `data/processed` aprovado). Abas:
1. **Mancha urbana** — mapa com slider ano a ano 1990→2026 (play/pause), painel de KPIs do ano (área em ha/km², Δ vs ano anterior em ha e %, taxa anual, densidade hab/ha nos anos censitários), gráfico de área acumulada e de crescimento anual com marcos minerais, comparação com MapBiomas/GHSL/WSF/Áreas Urbanizadas. Controle de camadas com **todos** os dados espaciais: mancha classificada (por ano), MapBiomas 24, GHSL, WSF-Evolution, Áreas Urbanizadas 2005/15/19/22, setores 2010/2022 (coropléticos por indicador), áreas de ponderação, limite municipal/distrito/perímetro urbano, minas e infraestrutura (Sossego, S11D, ferrovia, PA-160/PA-275), composições de satélite por ano (Landsat/Sentinel-2/CBERS) como camada de fundo, basemap OSM.
2. **Anos censitários** — para 1991 (proxy), 2000, 2010, 2022: mancha + perfil demográfico (pirâmide, escolaridade, renda, ocupação, domicílios) lado a lado.
3. **Setores censitários** — coropléticos 2010/2022 da sede com seletor de indicador, tabela e download (dados públicos do universo).
4. **Migração** — status de data fixa, origens (mapa de fluxos OD), coortes de chegada, perfil dos migrantes vs não migrantes, condições domiciliares (com faixas de n e CV).
5. **Mineração e economia** — CFEM, PIB, emprego formal, marcos dos projetos, estimativas anuais.
6. **Artigo** — PDF embutido + download; **Metodologia/Dados** — fontes, pipeline, limitações, licenças.
Publicação: site estático em GitHub Pages (repositório git; deploy só com autorização explícita do usuário; `web/public/data` contém apenas agregados aprovados pelo gate).

## Fase 6b — Princípios de visualização de dados e UI/UX (requisito do usuário)

Carregar as skills `dataviz` e `ardosia-brand-guidelines` (references `dataviz.md`, `typography-layout.md`) antes de escrever qualquer componente; checklist de QA visual em `docs/qa/E7.md`.

**Cores das classes nos mapas classificados — padrão do setor (exceção documentada à paleta Ardósia, restrita às camadas temáticas do mapa e às suas legendas; interface, tipografia e gráficos permanecem Ardósia):**

- Cobertura/uso da terra: **legenda oficial MapBiomas** (baixar a tabela de códigos/hex de `brasil.mapbiomas.org/downloads/codigos-de-legenda/` na execução e versionar em `web/src/legend/mapbiomas.json`), p.ex. 24 Área Urbanizada, 30 Mineração, 3 Formação Florestal, 15 Pastagem, 21 Mosaico de usos, 25 Outras áreas não vegetadas, 33 Rio/lago. A classificação própria adota a mesma legenda para as classes equivalentes (urbano/edificado, mineração, solo exposto, vegetação, água), de modo que MapBiomas, TerraClass e a mancha própria sejam comparáveis com um só olhar.
- Produtos de referência mantêm a cor de origem quando exibidos como tal: IBGE Áreas Urbanizadas (estilos `.qml` oficiais 2022: densidade/tipo), ESA WorldCover (built-up), GHSL/WSF (documentação JRC/DLR).
- **Expansão no tempo** (camada "ano de urbanização", padrão MapBiomas módulo urbano / WSF-Evolution): rampa sequencial perceptualmente uniforme e segura para daltonismo (viridis/magma ou ColorBrewer YlOrRd multi-hue), do mais antigo (escuro) ao mais recente (claro), com marcadores nos anos censitários e nos marcos minerais; legenda contínua com rótulos por período (1984–90, 1991–2000, 2001–10, 2011–22, 2023–26).
- Coropléticos de setores: escalas sequenciais Ardósia (`ardosia_seq`) para magnitude, divergente (`ardosia_div`) para variação 2010→2022, classes por quantis ou quebras naturais com no máximo 5–6 classes; sem vermelho-amarelo-verde saturado.
- Mesma cor sempre para a mesma entidade/classe (a cor segue a entidade, nunca a posição), em todos os anos e em todas as abas; legendas com o segundo sinal (hachura/traço) quando cores coexistem em camadas sobrepostas; transparência controlável por camada; contraste verificado sobre imagem de satélite e sobre basemap claro/escuro.

**Boas práticas de dataviz aplicadas**

- Forma pelo trabalho do dado: KPI cards com delta e sparkline (área, população, densidade, migrantes); linhas para séries (área anual, população com marcação por tipo de fonte — oficial / citação / estimativa própria e faixas de incerteza); barras/dumbbell para comparações (migrantes × não migrantes, 2010 × 2022); pirâmides etárias espelhadas; matriz OD como mapa de fluxos com largura proporcional + tabela; sem eixo duplo, sem pizza > 3 fatias, sem 3D, sem truncar eixo y em barras.
- Rotulagem direta (≤ 4 séries), anotações de contexto nos gráficos (Sossego 2004, S11D 2016, emancipação 1994, censos) como linhas verticais tracejadas discretas; unidades e fontes em cada gráfico; resumo textual de uma frase (aria-label) por gráfico e por mapa.
- Incerteza sempre visível: CV/IC nas tabelas e barras de erro; células suprimidas marcadas e explicadas; classes de precisão codificadas por textura, não só cor.

**UI/UX**

- Narrativa guiada + exploração livre: página inicial com "a história em 5 números" e um scrollytelling curto (assentamento → emancipação → Sossego → S11D → hoje) que aciona o mapa e o slider; depois abas exploratórias.
- Mapa: slider anual com play/pause e teclado, "ghost" da mancha do ano anterior para leitura do crescimento, comparação lado a lado ou swipe (antes/depois entre dois anos escolhidos), painel de camadas agrupado por tema com atribuição/licença e opacidade, legenda dinâmica conforme camadas ativas, hover/tooltip por setor com mini-tabela, sincronização mapa ↔ gráficos (brush no gráfico de área destaca o ano no mapa).
- Hierarquia tipográfica Ardósia (serifa em títulos e narrativa; sans em rótulos/eixos/tabelas; numerais tabulares), grid de 12 colunas, espaço e régua como estrutura, sem sombras/gradientes; tema claro e escuro; responsivo (mobile: mapa em tela cheia com controles mínimos).
- Acessibilidade: contraste AA, navegação por teclado no slider e nas abas, foco visível, texto alternativo em figuras, paletas testadas para deuteranopia/protanopia (simulação no QA), tamanho mínimo de fonte 10 px em gráficos.
- Performance percebida: carregamento sob demanda das composições por ano, skeletons, pré-agregação de tudo em JSON leve; feedback de estado (ano atual, camadas ativas, filtros) sempre visível.
- Qualitativo integrado: citações curtas das fontes históricas e da bibliografia (com borda-esquerda terracota Ardósia) ancoradas nos anos correspondentes da linha do tempo; glossário (data fixa, área de ponderação, setor censitário, mancha urbana) em tooltips.

## Fase 7 — Orquestração e escolha de modelo (requisito do usuário)

Execução por subagentes locais (Agent tool; microdados nunca saem da máquina — subagentes recebem caminhos e instruções, não conteúdo), com o modelo escolhido por custo-benefício:

| Tarefa | Modelo | Motivo |
|---|---|---|
| Downloads, catálogo STAC, conversões de formato, execução de scripts prontos, QA de links | **Haiku 4.5** | mecânico, alto volume |
| Scripts ETL (API IBGE, setores, parsers FWF/DBF, tiles), testes, front-end padrão do dashboard | **Sonnet 5** | código padrão com bibliotecas conhecidas |
| Pipeline de classificação de imagens, validação de acurácia, análise estatística/causal, gate de revelação, revisão bibliográfica (síntese), redação e revisão do artigo, design do dashboard | **Opus 5 / Fable 5.1** | raciocínio, julgamento metodológico |
| Coordenação, integração, verificação final | sessão principal (Fable 5.1) | contexto integral |

Fases independentes rodam em paralelo (Fase 1, Fase 2, Fase 3-imagens, Fase 4-bibliografia); Fases 5–6 dependem das anteriores. Cada subagente entrega relatório de QA em `docs/qa/`. Se o usuário optar por multi-agente com o Workflow tool ("use um workflow"/"ultracode"), o mesmo mapa de modelos vale para o script.

## Fase 3 — Mancha urbana da sede, 1990→2026 (sensoriamento remoto)

### Fontes verificadas (HTTP 200 em 09/09/2026; identificadores confirmados em catálogo)
| Fonte | Resolução / cobertura | Acesso | Uso |
|---|---|---|---|
| **MapBiomas Coleção 11** (lançada 12/08/2026), classe 24 Área Urbanizada; classe 30 Mineração separada | 30 m, anual 1985–2025 | GeoTIFF Brasil em `storage.googleapis.com/mapbiomas-public/initiatives/brasil/collection11/lulc/coverage/brazil_coverage/brazil_coverage-col11_{ANO}.tif` — BigTIFF tiled → recorte por `/vsicurl` (`gdal_translate -projwin`) sem baixar 640 MB; estatísticas municipais Col.10 (`MAPBIOMAS_BRAZIL-COL.10-BIOME_STATE_MUNICIPALITY.xlsx`, filtrar city_code 1502152, class 24) e módulo urbano (`mapbiomas_brazil_urban_v2.xlsx`) | série anual base + rótulos de treino |
| MapBiomas 10 m Sentinel Col. 4 | 10 m, 2017–2025 | `.../lulc_10m/collection4/coverage/brazil_coverage/brazil_coverage-col4_10m_{ANO}.tif` | 2017+ comparação |
| Landsat C2 L2 (TM/ETM+/OLI) | 30 m (15 m pan ETM+/OLI), 1984→2026; **WRS-2 224/064 e 224/065** (+223/064-065) | Planetary Computer STAC `landsat-c2-l2` (sem conta; token SAS anônimo via pacote `planetary-computer`) ou INPE BDC `landsat-2` (3.784 itens; cenas 1990 confirmadas) | classificação própria 1990–2016 |
| Sentinel-2 L2A | 10 m, 2017→2026; **tile T22MFT**; estação seca jun–set com nuvem ≈ 0 | Element84 earth-search `sentinel-2-l2a` (sem conta) / Planetary Computer / BDC `S2_L2A-1` (itens até 06/09/2026) | classificação própria 2017–2026 |
| **CBERS-2B HRC** 2,7 m pan | 11 cenas 2008-10-01 → 2010-02-20 (órbitas 161/162, ponto 107, subcenas 4 e 5) | INPE BDC STAC `CB2B-HRC-L2-DN-1` (sem conta) | referência de validação 2010 |
| **CBERS-4A WPM** 2 m pan / 8 m MS; fusão RGB | 40 itens 2020→2026-07-30 (211/121, 212/121) | BDC `CB4A-WPM-L4-DN-1`, `CB4A-WPM-PCA-FUSED-1` | validação 2022 e 2026; fundo de mapa |
| CBERS-4 PAN5M / MUX | 5 m / 20 m, 2014→2026 (162/107-108) | BDC `CB4-PAN5M-L4-DN-1` | validação 2014–2019 |
| IBGE Áreas Urbanizadas | vetor 2005 (provavelmente sem Canaã), 2015, 2019 revisado, 2022 (com densidade e tipo: densa/pouco edificada, loteamento vazio) | geoftp | verdade de campo 2022; camada |
| TerraClass Amazônia | 30 m: 2004, 2008, 2010, 2012, 2014, 2018, 2020, 2022 (classe Área Urbanizada; mineração separada) | formulário web terraclass.gov.br (download via navegador) | comparação |
| GHS-BUILT-S R2023A | 100 m épocas 1975–2030 (10 m só 2018); tile R10_C14 | JRC FTP | validação de magnitude |
| WSF-Evolution / WSF2019 | 30 m anual 1985–2015 / 10 m 2019; tile `-50_-8` | DLR download | validação (para em 2015) |
| GAIA / GISA, ESA WorldCover, Esri 10 m | 30 m 1985–2018/2021; 10 m 2020–21; 10 m 2017–25 | Tsinghua / Planetary Computer | comparação |
| Mapa municipal estatístico Censo 2022 (IBGE, PDF georreferenciado da sede) | — | geoftp `mapas_municipais_estatisticos/PA/canaa_dos_carajas_1502152/` | perímetro de referência |
| Planet NICFI | programa encerrado em 2025 — **não usar** | | |
| Google Earth histórico | só visualização | | validação visual/datação de bairros |

Sem conta GEE o caminho é 100% Python (`pystac-client` + `planetary-computer` + `odc-stac`/`stackstac` + `rioxarray` + `scikit-learn`); GEE seria opcional apenas para Dynamic World e Satellite Embeddings (2017+).

### Mancha do assentamento antes de 1991 — avaliação (verificada em catálogo, 09/09/2026)

| Período | Sensor / resolução | Disponibilidade sobre a sede (bbox −49,95/−6,56/−49,80/−6,44) | O que é detectável |
|---|---|---|---|
| 1973–1982 | Landsat 1–3 **MSS**, 80 m (WRS-1 240/064-065) | INPE `landsat-lgi-1` (BDC STAC, sem conta): 77 itens 1973–1983; cenas de estação seca em 1979 (jun–set), 1980 (mai–ago), 1981 (mai–set), 1982 (mai–jul); bandas B4–B7 | Desmatamento inicial e traçado viário do Projeto de Assentamento Carajás/CEDERE (padrão geométrico); **não** distingue área edificada — só "clareira/núcleo" ≥ ~5 ha. Baseline pré-assentamento (1979–81) e implantação (1982) |
| out/1982 | Landsat 4 MSS | Planetary Computer `landsat-c2-l1`: 3 cenas (nuvem 2–7%) | idem |
| 1984–1990 | **Landsat 5 TM**, 30 m (WRS-2 224/064-065, 223/064-065) | PC `landsat-c2-l2` e INPE: ≥ 20 cenas/ano com nuvem < 40%, várias com 0–5% na estação seca (ex.: 1984-05-31, 1984-07-02, 1985-05-27, 1986-05-30, 1987-05-17, 1988-07-06/07-22, 1990-07-19) | Núcleo do CEDERE I (vila) como agrupamento de solo exposto/telhados com grade viária, se ≥ ~10–20 ha; bandas 5/7 e NDBI ajudam. **Série anual pode começar em 1984**, com classe "núcleo de assentamento" (não "urbano") até a consolidação |
| 1986–1990 | **SPOT 1–2** (10 m pan / 20 m MS), programa **SPOT World Heritage** (CNES/REGARDS, gratuito para uso não comercial, com cadastro; `regards.cnes.fr/user/swh` responde 200) | cobertura sobre Canaã **a verificar** após cadastro | Melhor candidata a referência de alta resolução pré-1991 (validação da mancha 1986–90) |
| 1971–1984 | **KH-9 Hexagon** (declassificado, 6–9 m; USGS EarthExplorer "Declass 3", conta gratuita; parte digitalizada, restante sob demanda) | cobertura **a verificar** no EarthExplorer | Se houver cena 1982–84, mostra o assentamento nascente em detalhe |
| anos 1980 | Fotografias aéreas (GETAT/INCRA — projetos de assentamento eram fotointerpretados; CVRD/Projeto Ferro Carajás; DSG) | solicitar a INCRA-SR27/Marabá, Prefeitura/IDURB, Vale | Verdade de campo qualitativa |

> **Verificado em E3a (2026-09-09)**: o catálogo confirma a viabilidade — 1984–1990 têm de 6 a 16 cenas
> de estação seca com nuvem < 15% por ano; 1979–1982 têm MSS de estação seca; **1974 e 1983 não têm
> nenhuma cena** sobre a janela da sede. Correções de fonte descobertas na execução: MapBiomas 10 m Col.4
> começa em 2017 (não 2016); GHSL exige as tiles R10_C13 **e** R10_C14; IBGE Áreas Urbanizadas 2015 não
> cobre Canaã (só concentrações > 100 mil hab.), como 2005; WSF-Evolution é `WSFevolution_v1_{tile}.tif`.
> **Achado que muda o uso da fonte**: a classe 24 do MapBiomas fica estagnada 19 anos (1996–2014) e supera
> WSF-Evolution em ~9,5× na mediana — não serve como série anual, só como comparação e apoio de rótulos.

Conclusão: **é viável** estender a série para trás: 1984–1990 anual com TM (mesma metodologia, classe "núcleo de assentamento/área construída", acurácia não verificável sem referência independente — declarar), e 1979–1982 com MSS como marcos de "antes/implantação" (área de clareira do núcleo, não mancha urbana). Incluir no slider os anos 1984–1990 (e pontos 1979/1980/1982 como camadas estáticas), e cruzar com a trajetória populacional reconstituída (Fase 1b): famílias assentadas × área do núcleo ⇒ densidade implícita. Tarefas: E3a passa a catalogar MSS/TM 1979–1990; verificar SPOT World Heritage e KH-9 (cadastros a cargo do usuário, se desejar).

### Pipeline
1. `20_imagens_catalogo.py`: AOI fixa = polígono municipal atual (API v4) + janela da sede (bbox −49,99/−6,40/−49,75/−6,60; CRS métrico **EPSG:31982**). Consulta STAC (PC, Element84, BDC) e grava catálogo (`data/interim/catalogo_cenas.parquet`) por ano/sensor/nuvem.
2. `21_baixar_cenas.py`: recortes por ano (jun–set) de Landsat/Sentinel-2 via COG windowed reads; cenas CBERS HRC/WPM/PAN5M de validação; recortes MapBiomas 1985–2025 via `/vsicurl`; GHSL, WSF, TerraClass, Áreas Urbanizadas.
3. `22_compor_anual.py`: composição mediana anual da estação seca com máscara QA_PIXEL/SCL; harmonização TM/ETM+/OLI (coeficientes Roy et al. 2016); 2012 só ETM+ SLC-off (gap-fill); índices NDVI, NDBI, MNDWI, BUI, IBI, BSI, NDBaI + textura GLCM + declividade (TOPODATA via BDC).
4. `23_classificar_mancha.py`: Random Forest (500 árvores) por ano; treino em 2022 (Sentinel-2 + WPM 2 m + Áreas Urbanizadas 2022) e 2010 (HRC 2,7 m), rótulos MapBiomas 24/30/21/25 erodidos como apoio; amostra estável retropropagada; pós-processamento: filtro temporal de **não retração** (urbano em t ⇒ urbano em t+1), filtro espacial (unidade mínima 0,5–1 ha, 8-conectividade), **máscara de mineração** (MapBiomas 30 ∪ polígonos S11D/Sossego/Bacaba) reportada como curva separada; separação da **sede contígua** (regra: manchas a ≤ 10 km do núcleo conectadas/vizinhas; vilas da Vale e alojamentos S11D como camada própria) e, em 2022/2026, de **loteamentos vazios** (tipo IBGE) como classe própria.
5. `24_validar_mancha.py`: pontos aleatórios estratificados por época interpretados na melhor imagem da data (HRC 2009–10, WPM 2020–26, ETM+ pan 2000, Google Earth); matriz de confusão, acurácia global, área com IC (Olofsson et al. 2014); comparação com MapBiomas, TerraClass, GHSL, WSF, Áreas Urbanizadas.
6. `25_mapbiomas_ghsl.py` + `26_estatisticas_mancha.py`: tabela anual 1990→2026: área (ha, km²), Δ absoluto e %, taxa geométrica anual, densidade urbana (hab/ha) nos anos censitários e com estimativas anuais; domicílios/ha (10.352 dom. 2010 → 28.605 em 2022); direção da expansão (setores angulares); anos censitários destacados; 1991 mapeado sobre AOI fixa (nota: município criado em 1994).
7. `27_tiles_camadas.py`: vetorização das manchas por ano (GeoJSON/PMTiles), COGs/PNG das composições por ano para camada de fundo, camadas de apoio (setores, minas, ferrovia/rodovias via OSM), tudo em `web/public/data/geo/`.

## Verificação (fim a fim)
- `validate.py`: população expandida dos microdados × SIDRA por ano e situação (tolerância 0,5% em 2000/2010; 2022 só total/sexo); soma dos setores urbanos 2010/2022 × total urbano SIDRA; área da sede 2022 × Áreas Urbanizadas 2022 (desvio relatado); série anual monotônica; curvas MapBiomas vs própria (correlação, viés); acurácia ≥ 85% por época.
- `disclosure_check.py` obrigatório antes de copiar qualquer agregado para `web/public/data` e para `artigo/`; `verify_gate.py` sem microdados.
- Dashboard: `npm run build` + preview no navegador (mcp Browser): slider percorre 1990→2026 sem erro, camadas ligam/desligam, KPIs conferem com `26_estatisticas_mancha` CSV, aba do artigo carrega o PDF, tema claro/escuro, sem hex fora da paleta Ardósia.
- Artigo: DOCX → PDF via LibreOffice, inspeção visual das figuras e tabelas, referências todas com `verificado_em`.
- QA por fase em `docs/qa/*.md` (relatório do subagente + checagens da sessão principal).

## Decisões do usuário (09/09/2026)
- **1991**: mancha da sede em 1990/1991 sobre a AOI atual + perfil demográfico 1991 de Parauapebas como proxy (rotulado) + tentativa de recuperar a população do distrito/povoado nas publicações digitalizadas do Censo 1991 (Biblioteca IBGE).
- **Sem Google Earth Engine**: pipeline 100% Python via STAC.
- **Publicação**: site estático em **GitHub Pages** (repositório git; build Vite em `web/dist`; sem limite de 16 MB; rasters anuais como PMTiles/COG leves ou PNG por ano). Artifact privado pode ser usado só para revisão intermediária, se solicitado.
- **Orquestração**: subagentes locais (Agent tool), até 3 em paralelo, modelo por tarefa conforme tabela da Fase 7.
- **Execução em etapas** (mensagem do usuário): cada etapa abaixo é autônoma, tem entregável verificável e ponto de parada; o trabalho pode ser interrompido e retomado etapa a etapa em sessões diferentes. Estado persistido em disco (`data/`, `docs/qa/`, `PLANO.md` com checklist de status).

## Ajustes após revisão crítica (agente Plan)

**Dados**

- Acrescentar **Contagem 1996** e **Contagem 2007** (SIDRA; confirmar tabelas t/305 e t/793) — únicos pontos oficiais entre censos, próximos aos pulsos Sossego e pré-S11D. Preferir Contagem 1996 à estimativa área × densidade para o baseline pós-emancipação.
- Polígonos de mina: **ANM SIGMINE** (WFS, processos em fase de lavra) + buffer 1 km como máscara em todos os anos (MapBiomas 30 não captura as fases de construção 2002–04 e 2013–16). Perímetro urbano: Plano Diretor/lei municipal (PDF; digitalizar se necessário) — fonte declarada.
- 1991: rotular como **"Parauapebas 1991 (inclui o atual Canaã)"** — é superconjunto, não proxy de outro lugar.
- 1991 DBF: extrair para `data/interim/` (dbfread precisa de arquivo seekable), nunca para o repo.
- Venv raster: Python **3.12/3.13** (wheels de rasterio/odc-stac/stackstac podem não existir para 3.14); venv de microdados pode seguir o 3.14 do projeto irmão.

**Sensoriamento remoto**

- Substituir o filtro de não retração por **maioria temporal em janela de 3 anos + persistência ≥ 2 anos consecutivos antes de "selar"** um pixel; não retração só no núcleo selado; loteamentos vazios isentos (revegetam).
- Confusão dominante é solo exposto/pasto seco, não mineração: acrescentar **feições intersazonais** (NDVI mínimo e amplitude a partir de composição jan–abr de NDVI máximo; baixa amplitude = construído) além de textura GLCM.
- **Treino por era de sensor**: TM/ETM+ 1990–2012 com rótulos HRC 2010; OLI 2013–16 com Áreas Urbanizadas 2015; Sentinel-2 2017+ com 2022; amostra de pixels estáveis comum a todas as eras; baseline Otsu em NDBI/BUI como sanidade.
- **Série principal em grade única de 30 m** (agregar Sentinel-2) para evitar salto artificial 2016→2017; série 10 m secundária.
- 1990: aceitar cenas 1989–91, registrar datas reais, MMU 0,5 ha, IC reportado; acurácia pré-1999 sem referência independente (declarar); ETM+ pan a partir de 1999; CBERS-2 CCD 2004–07.
- 2012: mediana de ≥ 4 cenas SLC-off + interpolação temporal 2011/2013, sem gap-fill espacial.
- Rótulos de treino dependem de downloads da Fase 1 (Áreas Urbanizadas, malhas) — E3b depende de E1.

**Microdados e sigilo**

- Amostra de Canaã é pequena (≈ 2 mil pessoas em 2000, ≈ 2,6 mil em 2010, ≈ 7,4 mil em 2022): toda estimativa publicada com classe de CV (`classe_precisao`: ≤ 15 boa, 15–30 cautela, > 30 suprimida/sinalizada).
- Erro-padrão por **bootstrap Rao-Wu agrupado por domicílio** (500 réplicas), estratificado por área de ponderação em 2022; impossível "por AP" em 2000/2010 (1 AP).
- Limiares alinhados aos compromissos já assumidos sobre o mesmo arquivo: **2022: n ≥ 20 pessoas e ≥ 10 domicílios por célula; 2000/2010/1991: n ≥ 10**; contagens ponderadas arredondadas a **10** (50 no rural); checagem de **diferenciação** (município − sede ⇒ rural) — publicar uma geografia por dimensão ou verificar o complemento rural; estender `DIMENSOES`/`COLUNAS_PROIBIDAS` de `disclosure_rules.py` (status de data fixa, `AREAP`/`V0011`/`V0300`/`P0090`/`P0100`); `41_figuras.py` lê só `data/processed` aprovado.

**Dashboard**

- Site estático (GitHub Pages). Manchas anuais como vetor (TopoJSON/PMTiles, ≈ 2–3 MB total); composições de satélite como **`image` sources do MapLibre, um WebP pré-projetado em EPSG:3857 por ano/sensor** (~0,3–0,5 MB Landsat, 1–2 MB Sentinel-2), carregado sob demanda pelo slider; sem DuckDB-WASM nem Plotly (usar ECharts/Recharts com JSON pré-agregado). Cada camada com string de atribuição/licença (MapBiomas CC-BY, Copernicus, DLR WSF CC-BY, IBGE, INPE).
- Conferir os IDs de modelo disponíveis antes de fixar a tabela de orquestração.

## Regime de execução em sessões (decisão do usuário, 09/09/2026)

- **Uma etapa por sessão, em dias diferentes**, na ordem E0 → E1 → E3a → E2 → E4 → E3b → E3c → E5 → E6 → E7 → E8. Cada sessão começa lendo `PLANO.md` (checklist de status) e `docs/qa/` da etapa anterior, e termina atualizando o checklist e gravando `docs/qa/E<n>.md`.
- **Modelo da sessão principal**: Opus 5 nas etapas mecânicas (E0, E1, E3a, E3c, E7); Fable 5.1 nas etapas de julgamento (E2, E3b, E5, E6, E8). Subagentes conforme a tabela da Fase 7 (Haiku para mecânico, Sonnet para código, Opus/Fable para análise/redação).
- **Paralelismo máximo: 2 subagentes**; sem Workflow tool. Trabalho pesado (classificação raster, parsers, bootstrap) roda como script; o modelo lê apenas resumos, nunca saídas longas.
- **Orçamento de referência** (ordem de grandeza): ~4–5 milhões de tokens no total, majoritariamente Sonnet/Haiku; E7 (~0,8 M), E3b (~0,6 M) e E5 (~0,6 M) são as etapas mais caras. Se a cota apertar, pausar ao fim da etapa; alternativa de corte: E3b substituída por MapBiomas Col. 11 + Áreas Urbanizadas IBGE.
- Em E0, criar `CLAUDE.md` do projeto com estas regras e o checklist de etapas, para que qualquer sessão futura as siga.

## Execução em etapas (checkpoints)

| Etapa | Conteúdo | Entregável / critério de conclusão | Modelos | Depende de |
|---|---|---|---|---|
| **E0 — Setup** | repo git, `.venv` (uv), `CLAUDE.md` (regras de sigilo + comandos), symlinks `data/raw`, cópia de `lib/`, `.gitignore`, `pipeline/disclosure_rules.py` | `python pipeline/validate.py --smoke` passa; `docs/qa/E0.md` | sessão principal | — |
| **E1 — IBGE API e setores** | Fase 1 completa | parquets em `data/processed/ibge/`, GeoJSON setores 2010/2022 da sede com indicadores; `docs/qa/E1.md` com conferências × SIDRA | Sonnet | E0 |
| **E2 — Microdados** | Fase 2: parsers 1991/2000/2010/2022 (PA), perfil demográfico, migração de data fixa e perfil dos migrantes, gate de revelação | tabelas aprovadas em `data/processed/microdados/` + `.gate_ok`; `docs/qa/E2.md` (população × SIDRA, CVs) | Sonnet (parsers) → Opus (migração, gate) | E0 (E1 para validação) |
| **E3a — Série MapBiomas e produtos prontos** | Fase 3 passos 1–2 (parte) e 6 para MapBiomas/GHSL/WSF/TerraClass/Áreas Urbanizadas | tabela anual 1985–2025 (ha) + polígonos por ano; `docs/qa/E3a.md` | Haiku (downloads) → Sonnet | E0 |
| **E3b — Classificação própria** | Fase 3 passos 2–5: composições anuais 1990–2026, RF, filtros, validação com HRC/WPM/IBGE 2022, máscara de mineração, loteamentos vazios | rasters/vetores por ano, tabela de acurácia e áreas com IC; `docs/qa/E3b.md` | Sonnet (composição) → Opus (classificação/validação) | E3a |
| **E3c — Estatísticas e camadas web** | Fase 3 passos 6–7 | `web/public/data/geo/*` + `estatisticas_mancha.csv` (Δ ano a ano, taxas, densidades) | Sonnet | E3b, E1 |
| **E4 — Bibliografia** | Fase 4 | `artigo/bibliografia/referencias.json` (todas verificadas) + `docs/revisao_bibliografica.md` (matriz temática) | Haiku (buscas) → Opus (verificação/síntese) | E0 |
| **E5 — Análise e figuras** | Fase 5 passos 1–2 | tabelas e figuras Ardósia em `artigo/{tabelas,figuras}/`; `docs/qa/E5.md` | Opus/Fable | E1, E2, E3c |
| **E6 — Artigo** | Fase 5 passo 3 | `artigo/texto.md` → `artigo.docx` → `artigo.pdf` revisado | Fable (texto), Sonnet (conversão) | E4, E5 |
| **E7 — Dashboard** | Fase 6: abas, mapa com slider e controle de camadas, gráficos, aba do artigo | `npm run build` ok; testes de navegação no browser; `docs/qa/E7.md` | Sonnet (front-end) → Opus/Fable (design, integração) | E1, E2, E3c, E6 (aba PDF pode ser plugada por último) |
| **E8 — Publicação e QA final** | verify_gate, checklist Ardósia, deploy GitHub Pages (com autorização do usuário), README/Metodologia, declaração de IA | site publicado; `docs/qa/E8.md` | sessão principal | todas |

Paralelismo permitido: E1 ∥ E2 ∥ E3a ∥ E4 após E0; E3b após E3a; E5 após E1+E2+E3c. Cada etapa começa lendo `PLANO.md` (checklist) e `docs/qa/` da etapa anterior e termina atualizando o checklist.

## Checklist de etapas (atualizar ao fim de cada sessão)

| Etapa | Status | Data | Relatório |
|---|---|---|---|
| E0 — Setup | concluída | 2026-09-09 | `docs/qa/E0.md` |
| E1 — IBGE API e setores | concluída | 2026-09-10 | `docs/qa/E1.md` |
| E3a — Série MapBiomas e produtos prontos | concluída | 2026-09-09 | `docs/qa/E3a.md` |
| E2 — Microdados | concluída | 2026-09-10 | `docs/qa/E2.md` |
| E4 — Bibliografia | concluída | 2026-09-10 | `docs/qa/E4.md` |
| E3b — Classificação própria | concluída | 2026-09-10 | `docs/qa/E3b.md` |
| E3c — Estatísticas e camadas web | concluída | 2026-09-10 | `docs/qa/E3c.md` |
| E5 — Análise e figuras | concluída | 2026-09-10 | `docs/qa/E5.md` |
| E6 — Artigo | concluída | 2026-09-10 | `docs/qa/E6.md` |
| E7 — Dashboard | concluída | 2026-09-10 | `docs/qa/E7.md` |
| E8 — Publicação e QA final | concluída — site em https://canaa-urbana.github.io; DOI 10.5281/zenodo.22699960 (v1.0.0) | 2026-09-10 | `docs/qa/E8.md` |
