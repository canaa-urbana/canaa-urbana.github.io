# Da colônia agrícola à cidade mineradora — urbanização de Canaã dos Carajás (PA), 1982–2026

**[canaa-urbana.github.io](https://canaa-urbana.github.io)** ·
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22699960.svg)](https://doi.org/10.5281/zenodo.22699960) ·
licenças: código MIT, dados e textos CC BY 4.0

Conjunto de dados, painel interativo e artigo científico sobre a urbanização da sede de Canaã dos
Carajás (IBGE 1502152), do assentamento dirigido GETAT/CEDERE II (1982) a 2026, com foco nos
grandes projetos minerais — a mina de cobre do Sossego (2004) e a de ferro do S11D (2016) — e na
migração de data fixa. Combina três fontes sob um desenho único:

1. uma **série anual da área construída da sede (1984–2026)**, classificada em composições Landsat
   (30 m) e Sentinel-2 (10 m) com Random Forest por era de sensor e validada em três épocas com
   imagens CBERS de alta resolução (área ajustada pela acurácia, Olofsson et al. 2014);
2. os **microdados da amostra dos Censos Demográficos de 1991, 2000, 2010 e 2022**, harmonizados
   num esquema único, com erro-padrão por bootstrap de domicílios e **controle estatístico de
   revelação** (os de 2022 são de acesso controlado do IBGE);
3. os **agregados do Universo por setor censitário** de 2010 e 2022, cruzados com a mancha.

Somam-se a série populacional oficial, a CFEM (ANM), o PIB municipal, o CEMPRE, um painel regional
2000–2022 e uma bibliografia verificada sobre o município.

## Principais achados

- **A sede cresceu de ~37 ha em 1990 para ~3.200 ha em 2026** (área ajustada; 2026 provisório);
  **52 % da cidade de 2026 foi construída entre o Sossego e o S11D** (2004–2016), no maior ritmo
  absoluto da série (158 ha/ano).
- **Espraiamento e depois adensamento**: a área cresceu mais que a população nos anos 2000
  (elasticidade 1,24) e menos nos anos 2010 (0,83); densidade de 35,6 → 24,0 → 29,4 hab./ha.
- **Uma cidade de migrantes**: 60 % dos não naturais residentes em 2022 chegaram a partir de 2013;
  o ritmo de chegadas sobreviventes passa de ~250/ano no assentamento a ~4,5 mil/ano em 2017–2022.
- **Seletividade**: em 2022, migrantes recentes são mais jovens, mais escolarizados e mais
  formalizados, com renda média igual; 36 % dos migrantes ocupados estão na cadeia da mineração
  (extrativa + construção + transformação), contra 29 % dos não migrantes.
- **Moradia**: metade dos domicílios com migrante recente é alugada, contra um em cada cinco nos
  demais; água e esgoto convergem, mas o pior decil de setores segue com ~24 % de esgoto por rede.
- **Obras × royalties**: a cidade cresce nas janelas de obras das minas; a CFEM explode só depois
  de 2018, sobre uma cidade já construída.

Detalhes, incerteza e ressalvas de cada número: artigo (`artigo/artigo.pdf`), painel e
`docs/qa/*.md` (relatórios de QA de cada etapa).

## Fonte e política de uso dos microdados

Os microdados censitários **não estão neste repositório** e nunca saíram da máquina local do
titular do acesso. Tudo o que o projeto publica (`data/processed/`, `web/public/data/`, painel,
figuras, artigo) passou por um **gate automático de controle de revelação** (regras R1–R8):

- **R1** — limiar por célula: Censo 2022, ≥ 20 pessoas e ≥ 10 domicílios distintos na amostra;
  1991/2000/2010, ≥ 10 pessoas e ≥ 5 domicílios;
- **R2** — estimativas de contagem arredondadas a múltiplos de 10;
- **R3** — contagem amostral só em faixas (10–19, 20–49…), nunca exata;
- **R4** — no máximo duas dimensões temáticas cruzadas;
- **R5** — nada por área de ponderação nem com identificador de domicílio;
- **R6** — toda estimativa com coeficiente de variação e classe de precisão;
- **R7** — diferenciação: uma célula da sede só sai se a rural implícita (município − sede) também
  cumprir o limiar;
- **R8** — supressão complementar em "Outros (…)", com os constituintes visíveis.

O `pipeline/disclosure_check.py` reconta cada célula publicada a partir dos microdados e grava o
carimbo `data/processed/.gate_ok` e o relatório `docs/relatorio_revelacao_<versão>.md`; o
`pipeline/verify_gate.py` confere o carimbo **sem** microdados (roda no CI). Metodologia completa:
[`docs/METODOLOGIA.md`](docs/METODOLOGIA.md).

## Arquitetura

```
microdados IBGE (locais, fora do repositório) ─┐
imagens Landsat/Sentinel-2/CBERS (STAC) ───────┤  pipeline/1x–2x (Python)
API/agregados IBGE, MapBiomas, GHSL, WSF, ANM ─┘
        ▼
data/interim/            (intermediários — nunca versionados)
        │  13_migracao_perfil.py aplica R1–R8 · disclosure_check.py reconta e carimba
        ▼
data/processed/          (agregados aprovados pelo gate — VERSIONADO) + .gate_ok
        │  40_analise_artigo.py · 41_figuras.py · 50_artigo.py  →  artigo/ (texto, figuras, DOCX, PDF)
        │  26_estatisticas_mancha.py · 27_tiles_camadas.py      →  web/public/data/geo/ (camadas)
        │  60_dados_web.py (verifica o carimbo antes)           →  web/public/data/painel/
        ▼
web/ (Vite + React + MapLibre + ECharts)  →  GitHub Pages (.github/workflows/publicar.yml)
```

## Como rodar

### Painel (reprodutível por qualquer pessoa a partir dos dados versionados)

```bash
cd web
npm ci
npm run dev        # desenvolvimento em http://localhost:5173
npm run build      # produção em web/dist (caminhos relativos)
```

### Verificações sem microdados

```bash
pip install -r requirements-ci.txt
python pipeline/verify_gate.py --clone        # agregados publicados × carimbo do gate
python pipeline/auditoria_publicacao.py       # nenhum dado pessoal, credencial ou arquivo sigiloso
```

### Pipeline completo (requer acesso próprio aos microdados do IBGE)

Ambiente Python 3.13 com `uv` (`pyproject.toml`); os microdados ficam em `data/raw/` (links
simbólicos locais, ignorados pelo git). Ordem das etapas, entradas e saídas: `CLAUDE.md` e
`PLANO.md`. Qualquer mudança em `data/processed` exige rodar de novo
`pipeline/disclosure_check.py --versao <versão>` e, em seguida, `pipeline/60_dados_web.py`.
O hook `.githooks/pre-commit` (ativar com `git config core.hooksPath .githooks`) bloqueia commits
com o gate violado ou com dado pessoal.

## Estrutura de pastas

| Pasta | Conteúdo |
|---|---|
| `pipeline/` | scripts numerados por etapa, gate de revelação, auditoria de publicação, `lib/` |
| `data/processed/` | agregados aprovados (parquet/JSON/GeoJSON) + `.gate_ok` |
| `web/` | painel (código em `src/`, dados publicados em `public/data/`) |
| `artigo/` | texto-fonte, figuras, tabelas, bibliografia, DOCX e PDF |
| `docs/` | metodologia, revisão bibliográfica, relatórios de revelação, QA por etapa, checklist de publicação |

## Licenças

- **Código** (pipeline, painel, CI): [MIT](LICENSE).
- **Dados agregados, figuras, tabelas, artigo e textos**: [CC BY 4.0](LICENSE-DADOS.md), com as
  exceções de terceiros listadas lá (camadas do OpenStreetMap sob ODbL; imagens Copernicus e USGS
  com as respectivas atribuições).
- Os **microdados** dos censos não são redistribuídos sob nenhuma licença.

## Como citar

> SOBREIRA, Daniel Pessini. **Da colônia agrícola à cidade mineradora**: urbanização, migração e
> mancha urbana em Canaã dos Carajás (PA), 1982–2026 — dados, painel interativo e artigo.
> Versão 1.0.1. [S. l.]: Zenodo, 2026. DOI: https://doi.org/10.5281/zenodo.22699960.

O DOI acima é o **conceitual** (resolve sempre para a versão mais recente). Para citar
exatamente a versão 1.0.0 (dados `2026-09-10-e8`), use
[10.5281/zenodo.22699961](https://doi.org/10.5281/zenodo.22699961).

Metadados legíveis por máquina: [`CITATION.cff`](CITATION.cff) e [`.zenodo.json`](.zenodo.json).
ORCID do autor: [0000-0002-6632-3991](https://orcid.org/0000-0002-6632-3991).

## Aviso

As estimativas amostrais são do autor, sujeitas a erro amostral (CV e classe de precisão
publicados com cada uma) e podem divergir das tabulações oficiais do IBGE. A série de mancha
urbana tem comissão na franja e não é validável antes de 1999; 2026 é provisório. As imagens MSS
de 1973/1982 têm georreferenciamento aproximado e servem só como marco visual.

## Uso de inteligência artificial

O projeto foi desenvolvido com assistência de IA (Claude, Anthropic), sob supervisão integral do
autor; a declaração completa está no artigo e na aba "Metodologia e dados" do painel.

## Como reportar erros

Abra uma *issue* neste repositório descrevendo o número, a aba ou o arquivo e o que parece
errado. Correções de dados passam de novo pelo gate de revelação antes de serem publicadas.

## English summary

Data, interactive dashboard and a scientific paper (in Portuguese) on the urbanisation of Canaã
dos Carajás, a mining boomtown in the Brazilian Amazon, from a 1982 directed-settlement nucleus
to 2026. It combines an annual built-up series of the urban seat (1984–2026, Landsat/Sentinel-2,
validated with CBERS, accuracy-adjusted areas), harmonised census sample microdata for 1991–2022
(published only as aggregates approved by a statistical disclosure-control gate; the 2022
microdata are under IBGE's controlled access and are not included), census-tract aggregates,
mining royalties and GDP. Code under MIT; data and texts under CC BY 4.0.
