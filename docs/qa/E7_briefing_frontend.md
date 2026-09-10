# E7 — Convenções do front-end (briefing para subagentes)

Painel em `web/` (Vite 8 + React 19 + TypeScript 5.9 + MapLibre GL 5.24 + ECharts 6, renderer SVG).
Tudo em **português**, formato numérico brasileiro. Leia os arquivos citados antes de escrever.

## Regras de dados e sigilo (CLAUDE.md — não negociáveis)

- O painel lê **só** `web/public/data/` (JSON já aprovados pelo gate). Nunca leia `data/raw`,
  `data/interim` nem microdados; nunca copie nada novo para `web/public/data` à mão — se faltar
  um dado, diga no relatório final qual tabela de `data/processed` precisaria ser exportada por
  `pipeline/60_dados_web.py` (a sessão principal decide).
- Toda estimativa amostral exibida leva **CV / classe de precisão** (`boa` | `cautela` | `baixa`)
  e, quando relevante, a faixa de n (`n_faixa`, nunca n exato). Classes `cautela`/`baixa`
  aparecem com textura (`decalPrecisao`) nas barras e com `<Precisao>` / `*` `**` nas tabelas.
- Categorias fundidas pelo gate (`outros:a+b`) aparecem com `rotulo()` ("Outros (a, b)") — nunca
  somar, redistribuir ou esconder a fusão. As categorias de uma dimensão podem diferir entre censos.
- `estimativas.json` repete totais marginais (mesma linha em mais de um lugar): deduplique por
  (censo, geografia, universo, estatistica, variavel, dim1, cat1, dim2, cat2).
- Proporções em `estimativas` estão em **0–100** (%); `cv` em %. `ep` na mesma unidade do valor.
  IC 95 % = valor ± 1,96·ep.
- 1991: Canaã não existia — só `parauapebas_municipio`/`parauapebas_sede`, rotular **"Parauapebas
  1991 (inclui o atual Canaã)"**.

## Arquivos de dados (web/public/data)

- `painel/estimativas.json` → `useEstimativas()` / `consulta()` (`src/lib/data.ts`). Campos:
  censo, geografia (`canaa_sede`, `canaa_municipio`, `parauapebas_sede`, `parauapebas_municipio`, `pa`),
  universo (`pessoas`, `pessoas_5mais`, `pessoas_10mais`, `pessoas_25mais`, `ocupados`,
  `com_rendimento`, `migrantes_5anos`, `migrantes_internos`, `chegados`, `domicilios`),
  estatistica (`contagem` arredondada a 10, `proporcao`, `media`, `mediana`), variavel (para
  média/mediana: idade, renda_*_r2022 [R$ de jul/2022], moradores, densidade_dormitorio…),
  dim1/cat1, dim2/cat2 (no máximo 2 dimensões), valor, ep, cv, classe, n_faixa, n_dom_faixa.
- `painel/analise/<nome>.json` → `useAnalise(nome)`: as 24 tabelas da E5 (ver colunas com
  `.venv/bin/python -c "import pandas as pd; print(pd.read_parquet('data/processed/analise/<nome>.parquet').head())"`
  — são agregados aprovados, pode inspecionar).
- `painel/rotulos.json` → `useRotulos()` + `rotulo(R, cat, dim)`, `rotuloDim`, `rotuloGeo`
  (`src/lib/rotulos.ts`): marcos (assentamento 1982–85, emancipação 1994, Sossego 2002–04/2004,
  S11D 2013–16/2016), `janelas_obras`, ciclos de chegada, rótulos de dimensões/categorias.
- `painel/resumo_analise.json`, `painel/figuras.json` (títulos/legendas/resumos das figuras do artigo),
  `painel/geo/{comparacao_produtos,estatisticas_mancha_periodos,expansao_direcao}.json`,
  `painel/setores_{2010,2022}.json` + `painel/indicadores_setores.json`,
  `estatisticas_mancha.json` (série anual 1984–2026: `serie`, `periodos`, `censos`, `validacao`, `notas`),
  `mancha_anual.json` (MapBiomas, só comparação), `geo/camadas.json` (manifesto de camadas).

## Infraestrutura pronta (reutilize; não edite sem necessidade)

- `src/lib/theme.tsx`: `useTema()` → `{tema, viz}`; `viz` tem os **hex literais** para canvas/SVG
  (`cat` ordem fixa, `contexto`, `enfase`, `seq`, `div`, `obras`, `marco`, textos, grade).
  Tema claro/escuro alterna em tempo real: todo `option` deve depender de `viz` (useMemo).
- `src/lib/charts.ts`: `baseOption(viz, op)`, `eixo`, `eixoValor`, `marcosTempo(viz, janelas, marcos, categoria)`,
  `decalPrecisao(classe, viz)`, `TRACOS`, `MARCADORES`, `FONTE_SANS/SERIF`. ECharts modular: se
  precisar de outro componente (PolarComponent, HeatmapChart…), registre com `echarts.use([...])`
  no seu próprio módulo.
- `src/components/Chart.tsx`: `<Chart option ariaLabel height onEvents />`.
- `src/components/ui.tsx`: `Figura` (kicker, título serifado, subtítulo, controles, fonte, notas,
  **tabela alternativa obrigatória** via prop `tabela`), `Tabela`, `Kpi` (+ sparkline), `Precisao`,
  `Citacao`, `Termo` (glossário: data_fixa, area_ponderacao, setor, mancha, area_ajustada, cv, sede),
  `Segmentado`, `Selecao`, `Esqueleto`, `Erro`, `Secao`.
- `src/lib/format.ts`: `fmtNum`, `fmtPct` (0–100), `fmtProp` (0–1), `fmtHa`, `fmtDelta`, `fmtReais`, `fmtCompacto`.
- `src/lib/mapa.ts`: `useManifesto()`, `criarMapa(el, {tema})`, `trocarTemaBase`, `carregarGeojson`,
  `arquivoCamada`, `anoDisponivel`, `corPorClasse`, `opacidadePorClasse`, `corRampa`, `JANELA_SEDE`, `GRUPOS`.
  Camadas temáticas entram com `beforeId: 'rotulos'`.
- `src/lib/rota.ts`: `useRota()` e `trocarParam(chave, valor)` (estado na URL, ex.: `#/mancha?ano=2010`).
- Classes CSS em `src/styles/app.css` (`pagina`, `grade` 12 colunas com `c-12/c-8/c-6/c-4/c-3`, `bloco`,
  `leitura`, `lead`, `kpis`, `aviso`, `nota-miuda`) e `ardosia.css` (`ard-card`, `ard-kicker`, `ard-pill--*`).
  CSS próprio da aba em arquivo separado importado pelo componente.

## Regras visuais (skills `ardosia-brand-guidelines` e `dataviz`)

- **Nenhum hex fora da paleta Ardósia** em CSS/TS de interface e gráficos — use `viz.*` ou
  custom properties. Exceção documentada: cores das camadas temáticas do mapa vêm do manifesto
  (legenda MapBiomas/IBGE) — nunca digite essas cores, leia-as de `camadas.json`.
- Sem sombra, gradiente, 3D; raio ≤ 8 px (6 px padrão). Títulos em serifa; rótulos/eixos/tabelas em sans;
  numerais tabulares. Nada abaixo de 10 px; serifa nunca abaixo de 12 px.
- Forma pelo trabalho do dado: KPI com delta e sparkline; linha para séries; barras para magnitude
  (eixo y de barra **sempre a partir de zero**); dumbbell para antes/depois e migrante × não migrante;
  pirâmide espelhada (homens `viz.cat[0]`, mulheres `viz.cat[1]`); barra 100 % empilhada para
  composição. **Nunca eixo duplo**, nunca pizza > 3 fatias.
- Cor por papel: categórica em ordem fixa (`viz.cat`) — até 3 séries; da 4ª em diante, cada série
  também tem traço (`TRACOS`) ou marcador (`MARCADORES`) diferente, e a legenda mostra isso. Ênfase:
  a série que importa em `viz.enfase`, contexto em `viz.contexto`. A cor segue a entidade: Canaã
  sempre `viz.enfase`/`cat[1]`… defina um mapa entidade→cor por aba e mantenha em todos os gráficos.
- Rotulagem direta quando ≤ 4 séries; legenda para ≥ 2 séries; título diz a leitura principal
  (frase), subtítulo diz o que é medido e a unidade; fonte em todo gráfico; `ariaLabel` de uma frase.
- Marcos como linhas verticais tracejadas discretas e janelas de obras sombreadas (`marcosTempo`).
- Incerteza visível: IC como banda (área a ~12 % de opacidade) ou barras de erro (série `custom`
  ou `scatter` + linhas); tooltip mostra valor, IC, CV e classe.
- Tooltip em todo gráfico; filtros em uma linha acima do gráfico (`controles` da `Figura`).
- Responsivo: `grade` colapsa em < 1100 px; mapas em mobile ocupam a largura, controles mínimos.
- Acessibilidade: foco visível, botões com `aria-pressed`/`aria-label`, teclado no slider.

## Verificação que você deve fazer

`cd web && npx tsc -b --noEmit && npx vite build` sem erro. Não inicie servidores de preview
(a sessão principal testa no navegador). Não faça commit.
