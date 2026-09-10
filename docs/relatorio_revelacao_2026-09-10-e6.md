# Relatório de controle de revelação — microdados (E2)

- Versão dos dados: **2026-09-10-e6**
- Gerado em: 2026-09-10 14:36 (fuso local)
- Fonte: IBGE, Censos Demográficos 1991, 2000, 2010 (amostra, públicos) e 2022 (amostra, acesso controlado).

## Regras aplicadas

| Regra | Parâmetro |
|---|---|
| R1 limiar por célula | 2022: ≥ 20 pessoas e ≥ 10 domicílios; 1991/2000/2010: ≥ 10 / 5 |
| R2 arredondamento | múltiplos de 10 |
| R3 contagem amostral | só em faixas |
| R4 cruzamentos | no máximo 2 dimensões temáticas |
| R5 geografia | sede urbana e município; nada por área de ponderação; sem identificador de domicílio |
| R6 precisão | CV e classe (boa ≤ 15 %, cautela ≤ 30 %, baixa) em toda estimativa |
| R7 diferenciação | célula rural implícita (município − sede) cumpre R1 |
| R8 supressão complementar | categorias suprimidas somadas em `outros` (≥ 2 categorias) |

## Verificações independentes

- R5: 132 parquets em data/processed sem coluna de domicílio/área de ponderação/peso
- R3: n amostral publicado só em faixas válidas
- R4: 33 dimensões, nunca mais de 2 por linha; todas registradas em lib/dimensoes.py
- R2: 10,541 contagens ponderadas, todas múltiplas de 10
- R6: toda estimativa tem CV e classe de precisão
- R1: 20,458 células recontadas, todas com n ≥ limiar (pessoas e domicílios)
- R8: toda célula 'outros' agrega pelo menos 2 categorias
- R7: 5,951 células de sede recontadas na área rural implícita, todas acima do limiar

## Linhas publicadas por censo e geografia

| Censo | Geografia | Linhas |
|---|---|---:|
| 1991 | pa | 1,231 |
| 1991 | parauapebas_municipio | 998 |
| 1991 | parauapebas_sede | 815 |
| 2000 | canaa_municipio | 934 |
| 2000 | canaa_sede | 663 |
| 2000 | pa | 1,443 |
| 2000 | parauapebas_municipio | 1,283 |
| 2000 | parauapebas_sede | 1,009 |
| 2010 | canaa_municipio | 1,261 |
| 2010 | canaa_sede | 837 |
| 2010 | pa | 1,559 |
| 2010 | parauapebas_municipio | 1,446 |
| 2010 | parauapebas_sede | 1,103 |
| 2022 | canaa_municipio | 1,263 |
| 2022 | canaa_sede | 690 |
| 2022 | pa | 1,621 |
| 2022 | parauapebas_municipio | 1,468 |
| 2022 | parauapebas_sede | 834 |
