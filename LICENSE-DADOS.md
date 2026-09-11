# Licença dos dados e do conteúdo

Este arquivo cobre os **dados agregados publicados** (`data/processed/**`, `web/public/data/**`),
as **figuras e tabelas** (`artigo/figuras/`, `artigo/tabelas/`), o **artigo** (`artigo/texto.md`,
`artigo/artigo.docx`, `artigo/artigo.pdf`), a **documentação** (`docs/`) e o **conteúdo textual do
painel**. O código-fonte do projeto tem uma licença separada -- ver `LICENSE` (MIT).

## Licença: CC BY 4.0

Salvo as exceções abaixo, esse conteúdo está sob a licença
**[Creative Commons Atribuição 4.0 Internacional (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/deed.pt-br)**:
qualquer pessoa pode copiar, redistribuir, adaptar e usar para qualquer finalidade, inclusive
comercial, **desde que dê a atribuição apropriada**, indique se houve alterações e forneça um
link para a licença.

### Como atribuir

> Daniel Pessini Sobreira. *Da colônia agrícola à cidade mineradora: urbanização, migração e mancha
> urbana em Canaã dos Carajás (PA), 1982–2026* — dados, painel e artigo. Fontes primárias: IBGE
> (Censos Demográficos 1991–2022, SIDRA, malhas), USGS/NASA Landsat, Copernicus Sentinel-2,
> INPE (CBERS), MapBiomas, JRC GHSL, DLR WSF, ANM, OpenStreetMap.

Para citação formal, ver `CITATION.cff` e a seção "Como citar" do `README.md`.

## Exceções: conteúdo derivado de terceiros com licença própria

| Conteúdo | Fonte | Licença que prevalece |
|---|---|---|
| Vias e ferrovia (`osm_vias`, `osm_ferrovia`, `osm_rodovias_regiao`) | © contribuidores do OpenStreetMap | **ODbL 1.0** (base de dados derivada; atribuição e compartilhamento pela mesma licença) |
| Mapa de base do painel (tiles vetoriais) | OpenFreeMap / OpenMapTiles, dados OpenStreetMap | termos do OpenFreeMap e ODbL (não redistribuídos aqui) |
| Imagens Sentinel-2 (`web/public/data/geo/img/s2_*`) | Copernicus Sentinel (ESA) | uso livre com a atribuição "Contém dados modificados Copernicus Sentinel (2017–2026)" |
| Imagens e produtos Landsat (`landsat_*`, `mss_*`) | USGS/NASA | domínio público |
| MapBiomas Col. 11 (classes 24 e 30, legenda de cores) | Projeto MapBiomas | CC BY 4.0 |
| GHSL GHS-BUILT-S R2023A; WSF-Evolution e WSF 2019 | JRC (Comissão Europeia); DLR | CC BY 4.0 |
| Malhas, agregados do Universo, SIDRA, Áreas Urbanizadas | IBGE | dados públicos, com citação da fonte |
| Concessões de lavra; CFEM | ANM | dados públicos, com citação da fonte |
| Resumos de obras da bibliografia (`data/processed/bibliografia/candidatos.parquet`) | OpenAlex, Crossref, BDTD, CAPES | metadados de terceiros, mantidos só para reprodutibilidade da busca; e-mails removidos |

## Os microdados originais NÃO estão incluídos

Esta licença cobre apenas **agregados publicados** — estimativas arredondadas, com supressão
complementar e contagens amostrais só em faixas, aprovadas pelo gate de revelação R1–R8 (ver
`docs/METODOLOGIA.md` e `docs/relatorio_revelacao_<versão>.md`). Os **microdados da amostra dos
Censos Demográficos** usados para calculá-los:

- não estão neste repositório e nunca saíram da máquina local do titular do acesso;
- no caso do **Censo 2022**, são de **acesso controlado** do IBGE e permanecem sujeitos
  integralmente aos termos de uso e confidencialidade do IBGE;
- não são redistribuídos, cedidos ou compartilhados por este projeto sob nenhuma licença —
  quem quiser acessá-los deve solicitar o próprio acesso ao IBGE.

A licença CC BY 4.0 acima não outorga, e não pode outorgar, nenhum direito sobre os microdados
originais — apenas sobre os resultados agregados e estatisticamente controlados que este projeto
publica.
