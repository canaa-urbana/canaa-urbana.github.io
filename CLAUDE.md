# CLAUDE.md — Urbanização de Canaã dos Carajás (PA)

Guia para qualquer sessão Claude Code neste repositório. Ler antes de trabalhar.
Plano aprovado: `PLANO.md` (cópia de `~/.claude/plans/quero-preparar-um-dashboard-functional-twilight.md`) — inclui o **checklist de etapas** ao final; atualizar ao concluir cada etapa.

## O que este projeto é

Conjunto de dados + dashboard interativo (GitHub Pages) + artigo científico (PDF) sobre a urbanização
da sede de Canaã dos Carajás (IBGE 1502152) desde o assentamento GETAT/CEDERE II (1982) até 2026,
com foco no impacto dos projetos minerais (Sossego 2004, S11D 2016) e na migração de data fixa.
Fontes: API IBGE (SIDRA, localidades, malhas), agregados por setor censitário (2000/2010/2022),
microdados da amostra 1991/2000/2010/2022, MapBiomas Col. 11, Landsat/Sentinel-2/CBERS via STAC,
Áreas Urbanizadas IBGE, bibliografia verificada. Identidade visual: sistema **Ardósia**.

## Regras de sigilo (não negociáveis)

Os microdados do Censo 2022 são de **acesso controlado** (termo de compromisso assinado pelo autor).
Os de 2000/2010 são públicos mas a amostra de Canaã é pequena. Portanto:

1. **Nunca imprimir registros individuais** de `data/raw`, `data/interim` ou dos parquets de pessoas/domicílios
   em saída de ferramenta. Proibido: `head` além do cabeçalho, `SELECT * ... LIMIT`, `cat`, prints de linhas.
   Permitido: esquemas (`DESCRIBE`), contagens, somas de peso, distribuições agregadas com n ≥ 10.
2. **Nada de `data/raw`/`data/interim` sai da máquina**: não colar trechos em prompts, não enviar a subagentes
   remotos/nuvem, não publicar em Artifact. Subagentes locais recebem instruções e caminhos, nunca conteúdo.
3. Só `data/processed` aprovado pelo gate (`pipeline/disclosure_check.py` → `.gate_ok`) vai para
   `web/public/data`, `artigo/` ou commit. `pipeline/verify_gate.py` confere sem microdados.
4. Limiares: 2022 — n ≥ 20 pessoas amostrais e ≥ 10 domicílios por célula; 2000/2010/1991 — n ≥ 10;
   contagens ponderadas arredondadas a 10 (50 no rural); nunca contagens amostrais exatas (faixas);
   no máximo 2 dimensões temáticas cruzadas; nada por área de ponderação; checar diferenciação
   (município − sede ⇒ rural). CV publicado com classe de precisão.
5. `.gitignore` bloqueia `data/raw`, `data/externo`, `data/interim` (exceto layouts), `*.csv`, `*.txt`, `*.dbf`.
   Não contornar. Em dúvida sobre individualização: não publicar.

## Caminhos

- Microdados: `data/raw/microdados_local` → pasta local de microdados (fora do repositório) (2010 TXT em `microdados_censo_amostra_2010_txt/PA/`;
  2022 controlado em `microdados_censo_amostra_2022_csv_<entrega>/15/`; **1991** em
  `Microdados_Censo_Demografico_1991_Amostra_ftp/` — zip baixado do FTP público do IBGE em 10/09/2026, SHA-256 idêntico
  à cópia do disco externo de backup); `data/raw/zeitmaschine` → disco externo de backup (1970/1980/1991/2000 amostra).
  O zip de 1991 usa Deflate64 (`zipfile` não lê) — `12_microdados.py` extrai o DBF do PA com `unzip -p` para
  `data/interim/censo1991/`. 1991 tem um registro por pessoa com as variáveis de domicílio repetidas; a chave de
  domicílio é reconstruída pela sequência `PESSOAN == 1`.
- Layouts oficiais 2000/2010 (JSON, posições 0-based): `data/interim/layouts/` (gerados por `migracoes-mineracao/scripts/00c_layouts.py`);
  2022 (exportado do xlsx oficial) em `data/interim/layouts_2022/`; dicionário 1991 em `data/interim/censo1991/docs/`;
  documentação 2000 convertida para texto em `data/interim/censo2000_docs/`.
- Microdados harmonizados (E2): `pipeline/12_microdados.py` → `data/interim/microdados/{pessoas,domicilios}_{censo}.parquet`
  (Pará inteiro, esquema único de `pipeline/lib/censos.py`: sexo, idade, cor, instrução, ocupação/posição/setor
  harmonizados, renda em R$ jul/2022 e em SM, `tipo_mig_5anos`, origem, naturalidade, tempo de moradia, ano de chegada;
  domicílios: condição de ocupação, água/esgoto/lixo/energia/internet, densidade, adequação). Geografias: Canaã sede
  (situação urbana) e município, Parauapebas (comparação; **proxy de 1991**, Canaã só existe a partir de 1994), Pará.
- Estimação e publicação (E2): `pipeline/13_migracao_perfil.py` (bootstrap de domicílios em `lib/estimacao.py`,
  dimensões/universos/cruzamentos em `lib/dimensoes.py`) → `data/processed/microdados/estimativas.parquet`
  (tabela longa: censo, geografia, universo, estatística, dim1/cat1, dim2/cat2, valor, ep, cv, classe, faixas de n).
  As regras R1–R8 são aplicadas na estimação; células suprimidas viram `outros:<a+b>` (constituintes explícitos).
- Libs reutilizadas (cópia de `../migracoes-mineracao/scripts/lib` em 09/09/2026, commit 67dde19): `pipeline/lib/`
  — `fwf.py` (leitura FWF por layout), `migracao.py` (`classificar_5anos(df, censo=2000|2010|2022)`, saltos de pergunta
  já tratados), `seletividade.py`, `deflator.py`, `mineracao.py` (CFEM/ANM), `malhas.py`, `geo.py`, `viz.py`,
  `ardosia_palette.py`; `ardosia_mpl.py` = `palette.py` da skill Ardósia (`apply_ardosia()`).
- Gate de revelação (adaptado em E2 do `../atlas-migração/pipeline`, commit 1c05d27): `pipeline/disclosure_rules.py`
  (R1–R8 e limiares por censo), `disclosure_check.py` (reconta TODA célula publicada a partir de `data/interim/microdados`,
  inclusive uniões `outros:` e a célula rural implícita de cada sede; grava `.gate_ok` + `docs/relatorio_revelacao_*.md`),
  `verify_gate.py` (confere o carimbo sem microdados). Rodar o gate sempre que `data/processed` mudar.
- Bibliografia (E4): `pipeline/30_bibliografia.py` (APIs abertas → `data/processed/bibliografia/candidatos.parquet`)
  → triagem manual em `artigo/bibliografia/triagem.json` (por `cid`; `manuais`, `correcoes`, `urls_alt`) →
  `pipeline/31_verificar_refs.py` (DOI/repositório/BDTD/CAPES) → `referencias.json` + `.bib` + matriz em
  `docs/revisao_bibliografica.md` (texto fora dos marcadores MATRIZ é manual). Slugs estáveis entre execuções.
  Só entra referência verificada; `validate.py --e4` confere.
- Sensoriamento remoto (E3a/E3b): grade fixa da sede em `pipeline/lib/grade.py` (30 m e 10 m, EPSG:31982);
  `21_baixar_cenas.py` (recortes por janela → `data/interim/cenas/`, 8,8 GB, resumível, `--manifesto` reconcilia),
  `22_compor_anual.py` (composições medianas → `data/interim/composicoes/`), `23_classificar_mancha.py` (RF por era +
  pós-processamento → `data/processed/geo/mancha_propria/`, `mancha_propria_anual.*`, `modelos_rf.json`),
  `24_validar_mancha.py registrar|amostrar|avaliar|comparar` (corregistro das cenas CBERS — a HRC L2 vem deslocada
  0,5–3 km —, fotointerpretação em montagens, Olofsson, comparação com produtos). Limiar 0,5 fixado a priori; a série
  tem ~15–20 % de comissão na franja (ver `docs/qa/E3b.md`) — usar áreas ajustadas nas épocas validadas.
- Estatísticas e camadas (E3c): `26_estatisticas_mancha.py [mapbiomas|propria]` → `data/processed/geo/estatisticas_mancha*.parquet`,
  `expansao_direcao.parquet`, `setores/setores_mancha.parquet`, `web/public/data/estatisticas_mancha.json`;
  `27_tiles_camadas.py [vetores|imagens|manifesto]` → `web/public/data/geo/` (manchas por ano em `mancha/`, WebP em
  EPSG:3857 em `img/`, manifesto `camadas.json` com cores lidas de MapBiomas/.qml IBGE/Ardósia). O dashboard lê só o
  manifesto para descobrir camadas. `validate.py --e3c` confere.
- Análise e figuras (E5): `pipeline/40_analise_artigo.py` (blocos a–j; lê só `data/processed`) →
  `data/processed/analise/*.parquet|csv` + `resumo_analise.json` + `artigo/tabelas/tab_XX_*.md|csv`;
  `pipeline/41_figuras.py [--so fig_01,...]` → `artigo/figuras/fig_XX_*.png|svg` + `figuras.json` (título,
  legenda, fonte, resumo/alt). Rótulos e marcos em `pipeline/lib/rotulos.py`. Área da mancha nas figuras =
  **ajustada pela acurácia** (mapeada tracejada como referência; 2026 provisório). `validate.py --e5` confere
  (inclui hex fora da paleta Ardósia nos SVG). Rodar o gate depois de qualquer mudança em `data/processed/analise`.
- Artigo (E6): `artigo/texto.md` (marcadores `<cite:slug>`, `<citet:slug>`, `<!-- tab: tab_XX -->`, `<!-- fig: fig_XX -->`,
  `<!-- referencias -->`) → `pipeline/50_artigo.py` resolve citações/tabelas/figuras, gera `artigo/texto_resolvido.md`,
  `citadas.json`, `artigo.docx` (`docx_pipeline/md_to_docx.js`) e `artigo.pdf` (`soffice --headless`). Referências
  metodológicas fora do escopo da E4 ficam em `artigo/bibliografia/referencias_metodologicas.json` (verificadas no
  Crossref). `validate.py --e6` confere. Edite `texto.md`, nunca `texto_resolvido.md`.
- Web: `web/` (Vite + React + MapLibre + ECharts), `web/src/styles/ardosia.css`, marcas em `web/public/marks/`.
  Dados do painel (E7): `pipeline/60_dados_web.py` roda `verify_gate.py` e exporta para `web/public/data/painel/`
  (+ `_manifesto.json` com SHA-256; nunca editar esses JSON à mão) e copia o PDF; camadas do mapa seguem vindo de
  `27_tiles_camadas.py` (`geo/camadas.json`). Base cartográfica OpenFreeMap (CARTO exige chave); camadas próprias com
  `beforeId: 'rotulos'`. Convenções de front-end em `docs/qa/E7_briefing_frontend.md`; tema claro por padrão.
  `npm --prefix web run build` → `web/dist`; `validate.py --e7` confere dados, sigilo, paleta e build.
- GDAL CLI (se precisar fora do Python): `/Applications/QGIS.app/Contents/MacOS/`.

## Ambiente

```bash
.venv/bin/python                      # Python 3.13 (uv); deps em pyproject.toml
uv pip install -p .venv/bin/python -r pyproject.toml   # reinstalar
.venv/bin/python pipeline/validate.py --smoke           # checagem do ambiente (E0)
```

## Regime de execução (decisão do usuário, 09/09/2026)

- **Uma etapa por sessão**, ordem E0 → E1 → E3a → E2 → E4 → E3b → E3c → E5 → E6 → E7 → E8 (ver `PLANO.md`).
  Cada sessão: ler `PLANO.md` (checklist) e `docs/qa/` da etapa anterior; ao terminar, gravar `docs/qa/E<n>.md` e
  atualizar o checklist. Não iniciar a etapa seguinte sem o usuário pedir.
- Sessão principal: Opus 5 em E0/E1/E3a/E3c/E7; Fable 5.1 em E2/E3b/E5/E6/E8. Subagentes locais: Haiku (mecânico),
  Sonnet (código), Opus/Fable (análise/redação). **Máximo 2 subagentes em paralelo; sem Workflow tool.**
- Trabalho pesado roda em script; o modelo lê resumos, nunca saídas longas. Orçamento total ~4–5 M tokens.
- Deploy em GitHub Pages só com autorização explícita do usuário.

## Convenções

- Nenhuma posição de coluna escrita à mão: tudo vem dos layouts JSON.
- Áreas sempre em CRS métrico (EPSG:31982); nunca em EPSG:4326.
- Cores: **toda classe de uso/cobertura do solo** (mancha urbana = MapBiomas 24, mineração = 30, loteamento vazio =
  `.qml` IBGE AU 2022, clareiras agropecuárias = 21) usa a legenda oficial MapBiomas/IBGE — no painel **e nas figuras
  do artigo** (decisão do usuário, 10/09/2026); cores lidas de `pipeline/lib/legendas.py` / `web/src/legend/`, nunca
  digitadas. Escalas da classe urbana (ano de urbanização, WSF, GHSL) usam `legendas.rampa_urbana` (vermelhos derivados
  da classe 24). UI e gráficos seguem Ardósia. Imagens MSS (1973/1982) têm georreferenciamento aproximado e nuvens:
  não comparar com a série TM/OLI (ver `docs/qa/E7.md`). Imagens de fundo
  que competem com a cor da classe (MSS falsa-cor) são exibidas em tons de cinza.
- Toda estimativa amostral publicada leva CV e classe de precisão; toda figura lê só `data/processed`.
- Referências bibliográficas em `artigo/bibliografia/referencias.json` (ABNT autor-data, `verificado_em` obrigatório).
- Commits só quando o usuário pedir; mensagens em português.
