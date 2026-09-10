# Metodologia — urbanização de Canaã dos Carajás (PA), 1982–2026

Documento de referência do conjunto de dados, do painel e do artigo. Consolida o que foi de fato
executado nas etapas E0–E8 (relatórios em `docs/qa/`). O artigo (`artigo/artigo.pdf`, seção 4)
traz a mesma metodologia em forma de texto científico, com as referências.

## 1. Área de estudo e recortes

- **Município**: Canaã dos Carajás (IBGE 1502152), criado pela Lei estadual 5.860/1994 e instalado
  em 1997; antes, localidade (ex-CEDERE II do Projeto de Assentamento Carajás, GETAT, 1982) de
  Marabá e, a partir de 1988, de Parauapebas. **Nunca foi distrito.**
- **Sede**: situação urbana do distrito-sede nos microdados; nas imagens, a mancha construída
  contígua ao núcleo (encadeamento de 1 km), distinta de "outros núcleos" (vilas) e do construído
  em área de mineração.
- **1991**: Canaã não existia; usa-se **Parauapebas 1991 (inclui o atual Canaã)** — um
  superconjunto, rotulado assim em todas as tabelas.
- **Janela de análise das imagens**: 26,6 × 22,2 km em torno da sede, grade fixa de 30 m
  (887 × 740 pixels, EPSG:31982; `pipeline/lib/grade.py`). Áreas sempre em CRS métrico.

## 2. Fontes

| Fonte | Uso |
|---|---|
| IBGE — SIDRA (API) | população 1970–2022, Contagens 1996/2007, estimativas 2001–2026, PIB, CEMPRE |
| IBGE — agregados por setor (Universo) e malhas | indicadores por setor da sede, 2010 e 2022 |
| IBGE — microdados da amostra 1991, 2000, 2010 (públicos) e 2022 (acesso controlado) | perfil, migração de data fixa, trabalho, domicílios |
| Landsat 5/7/8/9 C2 L2, Sentinel-2 L2A, Landsat MSS L1 (STAC: Planetary Computer, Element84, Brazil Data Cube) | mancha anual 1984–2026; marcos 1973/1982 |
| INPE — CBERS-2B HRC, CBERS-4 PAN5M, CBERS-4A WPM | referência para validação (2009, 2017, 2022) |
| MapBiomas Col. 11; JRC GHSL; DLR WSF-Evolution/WSF 2019; IBGE Áreas Urbanizadas 2019/2022 | comparação; rótulos de treino; máscara de mineração; legenda de cores |
| ANM — CFEM e SIGMINE | royalties 2004–2026; concessões de lavra |
| OpenStreetMap | vias e ferrovia |
| OpenAlex, Crossref, Semantic Scholar, BDTD, CAPES | bibliografia (150 obras triadas, todas verificadas na fonte) |

## 3. Microdados: harmonização e estimação

- Leitura do Pará inteiro pelos **layouts oficiais** (nenhuma posição de coluna escrita à mão),
  esquema único (`pipeline/lib/censos.py`): sexo, idade, cor ou raça, instrução (4 classes),
  ocupação, posição (6), vínculo formal, setor (9; CNAE-Dom 1.0/2.0 e seção CNAE em 2022), renda
  do trabalho e total em R$ de julho de 2022 (IPCA), **status migratório de data fixa** (saltos de
  pergunta de cada questionário tratados), origem, naturalidade, tempo de moradia, ano de chegada;
  domicílios: tipo, condição de ocupação, água, esgoto, lixo, energia (até 2010), internet,
  moradores por dormitório, renda per capita e índice de adequação.
- **Conferência**: a população expandida reproduz o SIDRA com desvio nulo em 2000 e 2010 e de
  0,3 % em 2022 (o arquivo de 2022 exclui domicílios coletivos); domicílios × Universo < 0,1 %.
- **Erro-padrão** por bootstrap de domicílios (Rao-Wu, 200 réplicas; estratificado por área de
  ponderação em 2022); cada estimativa leva **CV** e **classe de precisão** (boa ≤ 15 %, cautela
  15–30 %, baixa > 30 %). Razões e diferenças entre grupos: método delta, supondo independência
  entre células (conservador).

## 4. Controle estatístico de revelação (R1–R8)

Regras em `pipeline/disclosure_rules.py`, aplicadas na estimação (`13_migracao_perfil.py`) e
verificadas de forma independente por `pipeline/disclosure_check.py`, que reconta **todas** as
células publicadas (20.458) a partir dos microdados, incluindo as uniões "outros" e a célula rural
implícita de cada sede:

| Regra | Conteúdo |
|---|---|
| R1 | n ≥ 20 pessoas e ≥ 10 domicílios distintos na amostra por célula (2022); ≥ 10 e ≥ 5 (1991–2010) |
| R2 | contagens ponderadas arredondadas a múltiplos de 10 |
| R3 | contagem amostral só em faixas (10–19, 20–49, 50–99, 100–499, ≥ 500) |
| R4 | no máximo 2 dimensões temáticas cruzadas |
| R5 | nenhuma coluna de domicílio, peso ou área de ponderação; nada por área de ponderação |
| R6 | toda estimativa com CV e classe de precisão |
| R7 | diferenciação: célula da sede só sai se a rural implícita (município − sede) cumprir R1 |
| R8 | supressão complementar: categorias pequenas fundidas em "Outros (…)", constituintes visíveis |

O gate grava `data/processed/.gate_ok` (SHA-256 de cada arquivo de `data/processed`) e
`docs/relatorio_revelacao_<versão>.md`. `pipeline/verify_gate.py` confere o carimbo sem microdados
(no CI, em modo `--clone`); `pipeline/60_dados_web.py` recusa exportar dados para o painel se o
carimbo não conferir e grava o SHA-256 de cada arquivo exportado.

### Conformidade com a política de acesso controlado do IBGE

- Os microdados de 2022 são usados sob Termo de Compromisso de Confidencialidade e
  Responsabilidade (finalidade: pesquisa acadêmica); **nenhum microdado é publicado** e nenhum
  arquivo de microdados ou intermediário sai da máquina do titular do acesso (`data/raw` e
  `data/interim` são ignorados pelo git; o CI rejeita qualquer arquivo desses tipos no histórico).
- Só agregados aprovados pelo gate entram em `data/processed`, no painel e no artigo.
- A cobertura explícita, pelo termo, da divulgação pública de agregados em site e depósito com DOI
  está registrada como item a confirmar em `docs/CHECKLIST_PUBLICACAO.md`.

## 5. Mancha urbana anual (1984–2026)

1. **Composições**: mediana da estação seca (jun–set, nuvem < 40 %) com máscara de qualidade;
   harmonização OLI → ETM+ (Roy et al., 2016); NDVI máximo da estação chuvosa e amplitude
   intersazonal (separa construído de solo exposto/pasto seco). 42 dos 43 anos com 100 % dos
   pixels observados.
2. **Feições** (20): 6 bandas, NDVI, NDBI, MNDWI, BUI, BSI, IBI, NBR2, textura, NDVI da chuva,
   amplitude, declividade (Copernicus DEM).
3. **Classificação**: Random Forest por era de sensor (TM/ETM+ 1984–2012; OLI 2013–2026; MSI
   2017–2026 a 10 m, série secundária); limiar 0,5 fixado a priori; validação cruzada em blocos de
   3 km: 0,95–0,98.
4. **Pós-processamento**: abertura morfológica; maioria temporal (3 anos); persistência de 2 anos
   antes de "selar" um pixel; máscara de mineração; unidade mínima de 1 ha; sede = encadeamento de
   1 km ao núcleo; loteamentos vazios (IBGE AU 2022) como classe própria a partir de 2022.
5. **Validação** (Olofsson et al., 2014; Stehman, 2014): 2009 (CBERS-2B HRC, corregistrada),
   2017 (CBERS-4 PAN5M), 2022 (CBERS-4A WPM); acurácia global 0,984–0,996; comissão do urbano de
   15–20 % na franja; área ajustada ± IC 95 % aplicada à série por fator interpolado entre as
   épocas (0,79–0,87). **Antes de 1999 não há referência independente; 2026 é provisório.**
6. **Estatísticas** (`26_estatisticas_mancha.py`): áreas mapeada e ajustada, Δ, taxa geométrica,
   densidades nos censos, forma (raio equivalente, índice de proximidade), direção da expansão por
   octante e período mineral, ODS 11.3.1.
7. **Imagens MSS 1973/1982**: cenas Tier 2 (duas L1GS, sem pontos de controle), com erro de
   posição de centenas de metros a ~1 km e, em out/1982, muitos cúmulos; servem só como marco
   visual. A primeira imagem que distingue a vila é o TM de 1984.

## 6. Setores censitários

Indicadores do Universo 2010 e 2022 para os setores da sede (pertença pela sobreposição com a
mancha): população, domicílios, densidade líquida (sobre a área construída), moradores por
domicílio, água, esgoto, lixo, energia (2010), rendimento do responsável (2010), cor ou raça e
razão de sexo (2022), fração construída, distância ao núcleo histórico e ano mediano de
urbanização. As malhas de 2010 e 2022 diferem: compara-se padrão, não setor a setor.

## 7. Análise (E5)

Blocos (a)–(j) em `pipeline/40_analise_artigo.py`: série populacional por tipo de fonte (oficial,
citação de terceiro, estimativa própria só como faixa); mancha × população (elasticidade,
densidade); coortes de chegada; seletividade migrante × não migrante; inserção ocupacional e
cadeia da mineração (B + F + C, limite inferior); condições domiciliares; desigualdade intraurbana;
comparação regional (painel de áreas mínimas comparáveis 2000–2022, diferença-em-diferenças
descritiva); linha de base de 1991; economia (CFEM deflacionada, PIB, CEMPRE).

## 8. Visualização

Identidade visual Ardósia na interface e nos gráficos (paleta validada para daltonismo; até três
séries sem segundo sinal, a partir da quarta sempre com traço ou marcador; tabela alternativa em
todo gráfico; contraste AA verificado com axe-core). **Exceção**: toda classe de uso ou cobertura do
solo usa a legenda oficial MapBiomas/IBGE (urbano = classe 24; mineração = 30; loteamento vazio =
estilo IBGE; clareiras agropecuárias = 21), e as escalas da classe urbana no tempo ou em
intensidade usam vermelhos derivados da classe 24 (`pipeline/lib/legendas.py`).

## 9. Reprodutibilidade

- Todo número publicado é regenerado por script; figuras e painel leem só `data/processed`.
- `pipeline/validate.py --smoke|--e2|--e3a|--e3b|--e3c|--e4|--e5|--e6|--e7` confere cada etapa.
- Painel: `web/` (Vite 8, React 19, MapLibre GL 5, ECharts 6), base cartográfica OpenFreeMap.
- Publicação: `.github/workflows/publicar.yml` (gate em modo clone, auditoria de dados pessoais,
  gitleaks no histórico, checagem de arquivos proibidos, build, checagem pós-build, deploy).

## 10. Limitações

1. Amostra censitária pequena (~1,9 mil pessoas em 2000, 2,6 mil em 2010, 7,4 mil em 2022): o
   controle de revelação funde ou suprime categorias, sobretudo na sede.
2. Migrantes de data fixa captam só quem chegou nos cinco anos anteriores e sobreviveu no
   município; coortes de chegada são sobreviventes, não fluxos.
3. Comissão na franja da mancha; sem validação antes de 1999; 2026 provisório.
4. Estimativas populacionais anuais do IBGE subestimaram Canaã entre censos — afeta indicadores per
   capita anuais.
5. População 1982–2000 reconstituída só como faixa, a partir de fontes secundárias.
