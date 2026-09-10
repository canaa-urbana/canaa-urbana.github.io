# Revisão bibliográfica — Canaã dos Carajás (E4)

Base da seção "Revisão de literatura" do artigo (E6). Fonte única das referências:
`artigo/bibliografia/referencias.json` (citar por `<cite:slug>`). A matriz abaixo é gerada por
`pipeline/31_verificar_refs.py`; o texto fora dos marcadores é escrito à mão.

## Como o levantamento foi feito

- **Busca** (`pipeline/30_bibliografia.py`, 10/09/2026): OpenAlex (título+resumo), Crossref,
  Semantic Scholar, BDTD/IBICT e Catálogo de Teses da CAPES, com 3 termos de núcleo ("Canaã dos
  Carajás" e variantes sem acento/grafia errada) e 10 de contexto (S11D, Sossego, Parauapebas e
  Carajás + urbanização, company towns, GETAT). 2.194 registros → **753 candidatos únicos**
  (deduplicação por DOI e título normalizado), dos quais 141 de geociências da província mineral
  (petrologia, geocronologia, depósitos — fora do escopo) e 608 triados título a título.
- **Triagem** (`artigo/bibliografia/triagem.json`): entram trabalhos cujo objeto é a sociedade, o
  território, a economia, o ambiente/uso da terra, a saúde ou as instituições de Canaã (camada
  *núcleo*) ou de Carajás/Parauapebas/company towns (camada *contexto*). Ficam fora biologia e
  taxonomia, microbiologia de rejeitos, engenharia de mina e de processo, relatos de prática
  didática e notícias. 150 selecionados (+1 manual: o capítulo do CETEM).
- **Verificação** (`pipeline/31_verificar_refs.py`): DOI conferido no Crossref/DataCite (título,
  ano, 1º autor); sem DOI, página do repositório ou registro oficial da BDTD (API) ou da CAPES.
  **132 verificadas** (101 núcleo, 31 contexto); 18 pendentes (lista no fim). A verificação
  corrigiu dois erros de metadados de terceiros: o capítulo CETEM "do leite ao cobre" é de
  Cabral, Enríquez e Santos (2011, in *Recursos minerais & sustentabilidade territorial*, v. 1,
  p. 39–68) — não dos organizadores do livro, como constava no projeto irmão — e a tese da UFRN
  sobre conflitos é de Alcione Santos de Souza (2024), não "Alcione Lescano de Souza Junior"
  (OpenAlex).
- **Limites**: SciELO não foi consultado diretamente (a busca do site tem desafio anti-bot); os
  14 artigos com DOI SciELO chegaram por OpenAlex/Crossref. Google Acadêmico e buscas na web
  ficaram indisponíveis nesta sessão — anais sem DOI (ENANPUR, ANPEGE, ABEP) e literatura
  cinzenta (Plano Diretor 2006/2007 e revisão, PLHIS, EIA/RIMA do Sossego e do S11D) estão
  sub-representados e listados como pendências. Resumos só existiam para ~70 % dos
  selecionados; os achados abaixo resumem o que o resumo mostra, e os demais estão marcados
  para leitura integral na E6.

## Panorama

A produção sobre Canaã é **recente e concentrada**: dos 101 trabalhos de núcleo, 5 são de
2005–2010, 14 de 2011–2016, 29 de 2017–2020 e 53 de 2021–2026 — a curva acompanha o S11D
(licença prévia 2012, operação 2016), não o Sossego (2004). Quase metade são dissertações e
teses (52 no total), sobretudo da UFPA/NAEA, da Unifesspa (PDTSA, PPGPDRU), do mestrado
profissional do ITV e de programas de Economia/Geografia da Unicamp, UFMG, UFRRJ e USP. Os eixos
mais cobertos são urbanização/produção do espaço (44 referências), economia mineral e royalties
(39), planejamento e gestão (27) e colonização/conflitos agrários (26); migração (10), moradia
(9) e trabalho (11) são os menos estudados — justamente os eixos em que este projeto traz
evidência nova (microdados 1991–2022 e mancha anual).

## Síntese por eixo

**Colonização e formação do município.** O ponto de partida é o assentamento dirigido do GETAT
(CEDEREs, 1982–85) e o desmembramento de Marabá nos anos 1980, lido como parte da modernização
capitalista e da formação de novas lideranças locais (`silva2006arranjos`); a emancipação de
Canaã (1994) aparece como narrativa de história local (`nascimentoneto2021emancipacao`).
Cabral, Enríquez e Santos (`cabral2011canaa`) e Carmo (`carmo2023mineracao`, `carmo2023cidade`)
reconstroem a vida dos colonos nos CEDEREs e a passagem da pecuária leiteira ao cobre — são as
fontes secundárias da trajetória populacional pré-1994 (Fase 1b), mas nenhuma estima a
população do núcleo antes de 2000.

**Urbanização e produção do espaço.** Há duas linhagens. A primeira, lefebvriana e ligada a
Monte-Mór e à UFPA, lê Canaã como "laboratório da urbanização na periferia global"
(`cardoso2017canaa`) e a região como urbanização extensiva
(`melo2016papel`, `melo2020invisivel`, `santos2021urbanizacao`): o crescimento urbano mediado por
grupos locais sob impulsos globais exclui quem mais depende da cidade. A segunda, da geografia
regional, trata do uso do território e da produção do espaço urbano financiada pela CFEM
(`medeiros2016dinamicas`, `silva2016territorio`, `almeida2017mineracao`, `carmo2023mineracao`), com
Castriota (`castriota2024aqui`) mostrando o autoritarismo neoextrativista na cidade, no campo e
na floresta. Trabalhos recentes descem à escala intraurbana — condomínios fechados e
fragmentação (`correa2026enclave`), áreas verdes (`nascimento2024dinamica`), ilha de calor
(`monteiro2025variacoes`). **Nenhum mede a expansão da mancha urbana ano a ano nem a relaciona
com a população**: Amaral (`amaral2021paisagens`, 1984–2019) e Furtado et al.
(`furtado2023deteccao`, 30 anos) mapeiam uso e cobertura do município inteiro, com a área
urbana como uma classe entre outras. O contexto regional — Parauapebas como núcleo planejado
que virou o município de maior crescimento do Pará (`furtado2014ocupacao`, `souza2024urbanizacao`,
`godinho2021fast`), company towns (`rodrigues2001company`, `juarez2021espaco`) e a urbanização
induzida pelos grandes projetos (`trevisan2025complexo`, `macchiavelloferradas2022urbanizacao`)
— dá o termo de comparação.

**Moradia.** A evidência é pontual: famílias pobres do CadÚnico com condições habitacionais
precárias (`silva2022condicoes`), conjunto do PMCMV com inserção urbana problemática
(`souza2023insercao`), regularização fundiária de núcleo informal em área de risco
(`santos2024utilizacao`, `silva2025regularizacao`, `correa2022politica`) e, sobretudo, Castriota
(`castriota2024housing`), que descreve, a partir de campo em 2018–2019, as formas de morar
criadas pela chegada de dezenas de milhares de migrantes do S11D. Falta uma leitura censitária
da condição de ocupação — o achado da E2 (51 % dos domicílios com migrante recente alugados em
2022, contra 20 % nos demais) preenche essa lacuna.

**Migração e população.** É o eixo mais citado e menos medido. A literatura afirma o afluxo
("cidade ímã", "cidade do imigrante") com base em crescimento populacional agregado
(`ribeiro2014analise`, `sanches2025canaa`, `matlaba2019socioeconomic`); os únicos trabalhos que
tocam dados de pessoas são epidemiológicos — HIV-1 numa área de mineração "com intenso fluxo
migratório" (`macedo2020prevalence`) — e a dissertação da ENCE (`almeida2017mineracao`). Para
Parauapebas há estudos de trajetórias de migrantes maranhenses (`cruz2022migracao`,
`pereira2023migracao`). **Não há, na literatura verificada, análise de migração de data fixa,
de coortes de chegada ou de seletividade dos migrantes com microdados censitários** — é a
contribuição central da E2.

**Trabalho e renda.** O Sossego gerava ~1.300 empregos (500 diretos, 800 terceirizados) e a
exigência de 70 % de mão de obra local esbarrava na baixa qualificação (`moura2005mina`); a
subcontratação e seus limites para o desenvolvimento regional (`farias2008mineracao`), a
participação feminina na extração mineral (`souza2022mulheres`) e os quintais produtivos de
mulheres rurais (`alencar2025quintal`) completam um eixo pequeno. Não há série de formalização,
setor e renda para a sede — que os microdados agora oferecem (carteira assinada de 7 % para
53 % dos empregados entre 2000 e 2022).

**Economia mineral, royalties e finanças públicas.** O eixo mais volumoso fora da urbanização.
Converge em três pontos: (i) especialização produtiva e dependência — quocientes locacionais,
matriz de dinamismo e grau de dependência orçamentária (`matos2014estruturas`,
`ribeiro2014analise`, `araujo2023sina`, `montecardoso2018mineracao`); (ii) CFEM abundante e
aplicação pouco estratégica ou pouco transparente (`vianajunior2008royalties`, `pinheiro2016royalties`,
`caitano2022potencial`, `oliveira2021cfem`, `cruz2021compliance`, `cruz2024sustainable`,
`assuncao2022fundo`, `moraes2023compensacao`); (iii) o S11D como estratégia da Vale após 2008 e
o papel do Estado e dos incentivos fiscais (`padilha2020estado`, `dias2025incentivos`,
`castro2025circulacao`). A leitura neoextrativista (`castriota2024aqui`, `santos2017desenvolvimento`)
é a moldura crítica dominante.

**Planejamento, gestão e percepção social.** Um grupo coeso do ITV/UFPA mede licença social de
operação (`cruz2021measuring`, `cruz2017licenca`), percepção de resiliência (`matlaba2021resilience`,
`pereira2017percepcao`) e percepção social da mineração (`matlaba2017social`, `matlaba2024local`)
com surveys; outros tratam de responsabilidade social corporativa e parcerias público-privadas
(`medeiros2016gestao`, `filgueiras2018approaches`, `rodrigues2016politicas`), do licenciamento do
S11D (`cirne2021ferro`) e da fragilidade ambiental como subsídio ao plano territorial
(`araujo2020analise`). O Plano Diretor e o PLHIS municipais, porém, não aparecem como objeto de
análise na literatura verificada.

**Conflitos agrários.** Literatura densa e de campo: o avanço do S11D desestrutura a produção
camponesa e multiplica acampamentos em áreas de interesse mineral (`cruz2017avanco`,
`santos2017conflitos`, `santos2021mineracao`, `miranda2023territorializacao`,
`ferreira2025sobrevivendo`, `souza2024conflitos`). É o contraponto rural da urbanização: a
expulsão do campo alimenta a cidade.

**Meio ambiente e uso da terra.** Desmatamento e mudança de paisagem (`cortez2019quantificacao`,
`amaral2021paisagens`, `furtado2023deteccao`, `chagas2024dinamica`), fragilidade e risco
(`araujo2020analise`) e a relação desmatamento–infraestrutura desde 1984–86
(`fernandes2023natureza`). Siravenha (`siravenha2017avaliacao`) testa detecção de mudança
semi-supervisionada em Landsat na região — referências metodológicas diretas para a E3b.

**Saúde.** Hanseníase e atenção primária (`sousa2017hanseniase`, `sousa2016avaliacao`), HIV/AIDS
associado à mineração e à migração (`macedo2020prevalence`, `macedo2020caracterizacao` — pendente,
`sousa2024volatilidade`), malária e uso da terra (`pereira2021producao`) e a reorganização da rede
na COVID-19 (`vale2020reorganizacao`).

## Lacunas que o projeto preenche

1. **Série da mancha urbana** anual e com método único (1984–2024), cruzada com população —
   inexistente; os estudos de uso da terra tratam o urbano como classe residual.
2. **Migração de data fixa, coortes de chegada e seletividade** com microdados 1991–2022 —
   inexistente; a literatura infere migração do crescimento agregado.
3. **Trajetória populacional pré-1994** reconstituída com fontes datadas e faixas de incerteza —
   as fontes (CETEM, Carmo) trazem números soltos e parcialmente inconsistentes (Fase 1b).
4. **Condições domiciliares e desigualdade intraurbana por setor censitário** (2010 → 2022) —
   só há estudos de caso (PMCMV, Paraíso das Águas) e CadÚnico.
5. **Densidade e forma urbana** (elasticidade área-população) — ausente para Canaã e raro para
   Parauapebas.

## Pendências de verificação (18)

Ficaram fora de `referencias.json` até conferência: 6 registros só no Semantic Scholar, sem
veículo (Rodrigues 2007; Monteiro 2007; Reis 2010; Souza 2011; Piquet 2012; Pinheiro 2013 — todos
de contexto e provavelmente capítulos/anais do NAEA ou do CETEM); anais sem página acessível
(Cardoso et al. 2017 ENANPUR — a versão RBEUR está verificada; Villela 2017 ABEP; Benevides
2019); artigos sem URL de registro (Pereira 2014; Cruz 2019; Silva 2020; Contente 2020 — DOAJ
responde 403); repositórios fora do ar ou com bloqueio (CPRM/SGB 2014; UnB — Aguiar 2025; UFPI —
Vieira 2019); e um capítulo sem autoria nos metadados (geotecnologias em zonas de extração de
ouro, 2024). Detalhes em `data/processed/bibliografia/verificacao.parquet`.

## Matriz de revisão

<!-- MATRIZ:INICIO -->
_Gerado por `pipeline/31_verificar_refs.py` em 2026-09-10: 132 referências verificadas._


### Urbanização e produção do espaço (44)

| Referência | Tipo | Camada | Período | Método | Principais achados |
|---|---|---|---|---|---|
| Pires (1995) `pires1995organizacao` | tese | contexto | 1980s–1995 | tese (Geografia) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — organização do espaço ao longo da Estrada de Ferro Carajás. |
| Rodrigues (2001) `rodrigues2001company` | dissertacao | contexto | 1960s–2001 | dissertação (NAEA) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — company towns na Amazônia Oriental. |
| Cabral et al. (2011) `cabral2011canaa` | capitulo | nucleo | 1982–2010 | capítulo de livro (CETEM); dados secundários, entrevistas e relatos de comunidades | Transição da pecuária leiteira à mineração de cobre após o Sossego; fonte da população de 1996 (11.139) e dos relatos sobre os CEDEREs usados na Fase 1b. |
| Bandeira (2014) `bandeira2014alteracoes` | dissertacao | nucleo | 2000s–2014 | dissertação (Arquitetura e Urbanismo) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — conversão de terra rural em solo urbano. |
| Furtado e Ponte (2014) `furtado2014ocupacao` | artigo | contexto | 1980s–2014 | artigo | Parauapebas nasceu como núcleo planejado para a mineração de ferro e tornou-se o município de maior crescimento demográfico do Pará. |
| Trindade et al. (2015) `trindade2015ciclo` | artigo | contexto | 2000s–2014 | artigo | Contradições do crescimento econômico e demográfico acelerado pelo ciclo mineral em Parauapebas e necessidade de políticas locais. |
| Medeiros (2016) `medeiros2016dinamicas` | artigo | nucleo | c. 2004–2014 | artigo; categoria território e indicadores socioeconômicos de dez anos | Produção do espaço de Canaã antes e depois da chegada das mineradoras, com leitura dialética do desenvolvimento. |
| Melo e Cardoso (2016) `melo2016papel` | artigo | contexto | 2000s–2015 | artigo; urbanização extensiva e níveis da realidade social (Lefebvre) | A mineração articula os territórios de extração aos circuitos globais, alterando a estruturação urbana e a relação urbano-rural na fronteira. |
| Reis (2016) `reis2016usos` | dissertacao | contexto | 1950s–2016 | dissertação (UFU); dois circuitos da economia urbana | Parauapebas combina modernização mineral e circuito inferior da economia urbana. |
| Silva (2016) `silva2016territorio` | dissertacao | nucleo | 2000s–2016 | dissertação (Geografia) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — uso do território e implicações socioespaciais da mineração. |
| Almeida (2017) `almeida2017mineracao` | dissertacao | nucleo | 2000–2016 | dissertação (ENCE/IBGE, População, Território e Estatísticas Públicas) | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Cardoso et al. (2017) `cardoso2017canaa` | artigo | nucleo | 2000s–2017 | artigo; níveis da realidade social (Lefebvre), pesquisa de campo | O crescimento urbano mediado por grupos locais sob impulsos globais (mineração, pecuária) exclui os grupos sociais que mais dependem da cidade. |
| Costa (2017) `costa2017pela` | dissertacao | nucleo | 2017 | dissertação (Arquitetura e Urbanismo); projeto urbano | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Candido (2018) `candido2018cidade` | dissertacao | nucleo | 2010s | dissertação (Arquitetura e Urbanismo) | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Tonelli (2018) `tonelli2018canaa` | dissertacao | nucleo | 2000s–2018 | dissertação (Geografia, Unicamp) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — 'saque anunciado' na Serra Sul. |
| Melo (2020) `melo2020invisivel` | tese | nucleo | 2000s–2020 | tese (Economia, Cedeplar/UFMG) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — o urbano no sudeste paraense. |
| Amaral (2021) `amaral2021paisagens` | dissertacao | nucleo | 1984–2019 | dissertação (USP); ecologia da paisagem, vias como driver, estudos quantitativos e qualitativo | Transformação da paisagem de Canaã impulsionada por agropecuária e mineração, com a malha viária como vetor de fragmentação — referência direta para a E3. |
| Castro (2021) `castro2021logistica` | dissertacao | nucleo | 2000–2019 | dissertação (Geografia) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — logística de transporte do S11D. |
| Domingues e Godinho (2021) `domingues2021geografias` | artigo | contexto | — | artigo teórico; urbanização planetária | O 'hinterland' formado por geografias do extrativismo — de favelas a company towns. |
| Godinho (2021) `godinho2021fast` | capitulo | contexto | 1980s–2020 | capítulo; morfologia urbana em três fases | Três tipologias urbanas em Parauapebas (Núcleo de Carajás, cidade aberta, expansão) ligadas ao ferro. |
| Juarez (2021) `juarez2021espaco` | artigo | contexto | 1950s–2021 | artigo; estudo de caso de company town | Espaço urbano de Serra do Navio como efeito do fordismo. |
| Santos (2021) `santos2021urbanizacao` | tese | nucleo | 1960s–2020 | tese (UFMG); urbanização extensiva (Monte-Mór), trabalho de campo | Reinterpreta a colonização e a mineração em Carajás como urbanização extensiva, a 'não-cidade'. |
| Cruz (2022) `cruz2022migracao` | tese | contexto | 1980s–2022 | tese (UNESP); trajetórias de migrantes | Migrantes maranhenses formaram o primeiro núcleo urbano de Parauapebas (Vila Rio Verde) atraídos pela mineração. |
| Macchiavello Ferradas et al. (2022) `macchiavelloferradas2022urbanizacao` | artigo | contexto | — | artigo; comparação de megaprojetos | Urbanização desencadeada por megaprojetos em Fordlândia, Pecém e Carajás. |
| Silva Reis e Macedo de Sousa (2022) `silvareis2022modernizacao` | artigo | contexto | 2010s–2020 | artigo; circuito inferior da economia urbana | Espaço antagônico em Parauapebas entre a mineração moderna e pequenas atividades locais. |
| Carmo (2023) `carmo2023cidade` | dissertacao | nucleo | 1982–2020 | dissertação (Unifesspa) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — base do artigo da RTG (Carmo 2023); fonte-chave da Fase 1b. |
| Carmo (2023) `carmo2023mineracao` | artigo | nucleo | 2000–2020 (com recuo aos anos 1970) | artigo; histórico dos CEDEREs e produção do espaço urbano | O crescimento da cidade está diretamente ligado à exploração mineral e aos recursos dela advindos; modo de vida dos colonos nos CEDEREs e transformações posteriores. |
| Fernandes (2023) `fernandes2023natureza` | capitulo | contexto | 1984–2020s | capítulo; geoprocessamento de imagens desde 1984–1986 | Desmatamento em Carajás fortemente vinculado às infraestruturas dos governos militares. |
| Furtado et al. (2023) `furtado2023deteccao` | artigo | nucleo | c. 1990–2020 (30 anos) | artigo; classificação de imagens, matriz de conversão | Série histórica de uso e cobertura com matriz de transição e persistência — comparação direta para a mancha da E3b. |
| Leopoldo (2023) `leopoldo2023apresentacao` | artigo | contexto | 2023 | apresentação de dossiê (Confins) | Dossiê 'Planejamento, Urbanização e Políticas Públicas na Região de Carajás'. |
| Souza e Ferreira Júnior (2023) `souza2023insercao` | artigo | nucleo | c. 2022 | artigo; formulários e campo no Residencial Canaã | Conjunto do PMCMV com inserção urbana problemática — desigualdade socioespacial em município de grande afluxo populacional. |
| Castriota (2024) `castriota2024aqui` | artigo | nucleo | 2016–2023 | artigo; dados secundários e pesquisa qualitativa em Canaã | Autoritarismo neoextrativista: produção do espaço urbano com recursos da CFEM e influência corporativa na cidade, no campo e na floresta. |
| Castriota (2024) `castriota2024housing` | artigo | nucleo | 2018–2019 | artigo; trabalho de campo | Formas emergentes de moradia após o S11D, que atraiu dezenas de milhares de migrantes e mais que dobrou a população de Canaã. |
| Machado et al. (2024) `machado2024urbanizacao` | artigo | contexto | 2000–2024 | artigo; materialismo histórico-dialético | Desigualdades socioespaciais na produção da moradia em Parauapebas desde 2000. |
| Nascimento (2024) `nascimento2024dinamica` | dissertacao | nucleo | 2024 | dissertação (Unifesspa) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — áreas verdes e espaço urbano. |
| Souza (2024) `souza2024urbanizacao` | tese | contexto | 1960s–2024 | tese/dissertação | Parauapebas como cidade produzida pela mineração no âmbito do Programa Grande Carajás. |
| Emilio e João (2025) `emilio2025cidade` | artigo | contexto | 2020s | artigo; entrevistas, campo e dados | A Vale molda a psicosfera urbana e a governança territorial de Parauapebas. |
| Monteiro e Gallardo (2025) `monteiro2025variacoes` | artigo | nucleo | c. 2003–2023 | artigo; Índice Humidex com dados NASA POWER | Aumento do índice de calor ao longo de duas décadas, associado ao crescimento urbano. |
| Rego et al. (2025) `rego2025urbanizacao` | artigo | contexto | 2020s | artigo | Agricultura urbana na 'Capital do Minério'. |
| Sanches et al. (2025) `sanches2025canaa` | anais | nucleo | 2000s–2025 | anais; ensaio | Relação entre o processo migratório de Canaã e os investimentos minerários no sudeste paraense. |
| Souza e Souza (2025) `souza2025reestruturacao` | artigo | contexto | 2020s | artigo | Reestruturação urbana e novas centralidades em Parauapebas. |
| Trevisan et al. (2025) `trevisan2025complexo` | artigo | contexto | 1960s–1985 | artigo; fontes e documentos | Geopolítica militar e a criação ou expansão de núcleos urbanos para viabilizar Carajás. |
| Xavier et al. (2025) `xavier2025metropolizacao` | artigo | contexto | 1960s–2025 | artigo | Metropolização de Marabá como polo da Região de Integração de Carajás. |
| Corrêa (2026) `correa2026enclave` | artigo | nucleo | 2010s–2026 | tese/dissertação | Espaços residenciais fechados e fragmentação socioespacial em Canaã, Marabá e Parauapebas. |

### Moradia e habitação (9)

| Referência | Tipo | Camada | Período | Método | Principais achados |
|---|---|---|---|---|---|
| Bandeira (2014) `bandeira2014alteracoes` | dissertacao | nucleo | 2000s–2014 | dissertação (Arquitetura e Urbanismo) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — conversão de terra rural em solo urbano. |
| Corrêa et al. (2022) `correa2022politica` | artigo | nucleo | 2009–2018 | artigo; entrevistas com 15 técnicos (Cohab, Defensoria, Instituto de Desenvolvimento Urbano de Canaã) | Limites e dificuldades da regularização fundiária urbana de interesse social no Pará. |
| Silva e Sousa (2022) `silva2022condicoes` | artigo | nucleo | 2020–2021 | artigo; revisão e dados do CadÚnico | Panorama das condições habitacionais das famílias pobres de uma cidade mineral; precariedade concentrada nesse grupo. |
| Souza e Ferreira Júnior (2023) `souza2023insercao` | artigo | nucleo | c. 2022 | artigo; formulários e campo no Residencial Canaã | Conjunto do PMCMV com inserção urbana problemática — desigualdade socioespacial em município de grande afluxo populacional. |
| Castriota (2024) `castriota2024housing` | artigo | nucleo | 2018–2019 | artigo; trabalho de campo | Formas emergentes de moradia após o S11D, que atraiu dezenas de milhares de migrantes e mais que dobrou a população de Canaã. |
| Machado et al. (2024) `machado2024urbanizacao` | artigo | contexto | 2000–2024 | artigo; materialismo histórico-dialético | Desigualdades socioespaciais na produção da moradia em Parauapebas desde 2000. |
| Santos et al. (2024) `santos2024utilizacao` | anais | nucleo | 2023 | anais; SIG | Regularização fundiária de zona de risco no bairro Paraíso das Águas. |
| Silva (2025) `silva2025regularizacao` | artigo | nucleo | 2010s–2025 | artigo; avaliação pós-regularização | Pós-regularização fundiária do núcleo urbano informal Paraíso das Águas. |
| Corrêa (2026) `correa2026enclave` | artigo | nucleo | 2010s–2026 | tese/dissertação | Espaços residenciais fechados e fragmentação socioespacial em Canaã, Marabá e Parauapebas. |

### Migração e população (10)

| Referência | Tipo | Camada | Período | Método | Principais achados |
|---|---|---|---|---|---|
| Cabral et al. (2011) `cabral2011canaa` | capitulo | nucleo | 1982–2010 | capítulo de livro (CETEM); dados secundários, entrevistas e relatos de comunidades | Transição da pecuária leiteira à mineração de cobre após o Sossego; fonte da população de 1996 (11.139) e dos relatos sobre os CEDEREs usados na Fase 1b. |
| Almeida (2017) `almeida2017mineracao` | dissertacao | nucleo | 2000–2016 | dissertação (ENCE/IBGE, População, Território e Estatísticas Públicas) | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Matlaba et al. (2019) `matlaba2019socioeconomic` | artigo | nucleo | 2000–2016 | artigo; indicadores socioeconômicos | resumo indisponível nas fontes de busca — ler o texto integral na E6 — dinâmica socioeconômica de uma cidade mineradora. |
| Bringel e Machado (2020) `bringel2020processos` | artigo | contexto | 2010s | artigo; estudo de bairro em Barcarena | Migração induzida pelo complexo mínero-industrial e relação campo-cidade. |
| Macêdo (2020) `macedo2020caracterizacao` | tese | nucleo | c. 2015–2019 | tese (IEC); epidemiologia molecular | Prevalência e características do HIV-1 em quatro municípios do complexo de Carajás, motivada pelo grande fluxo migratório. |
| Macêdo et al. (2020) `macedo2020prevalence` | artigo | nucleo | c. 2015–2019 | artigo; inquérito sorológico e epidemiológico | resumo indisponível nas fontes de busca — ler o texto integral na E6 — prevalência de HIV-1 em área de mineração de ferro com intenso fluxo migratório. |
| Cruz (2022) `cruz2022migracao` | tese | contexto | 1980s–2022 | tese (UNESP); trajetórias de migrantes | Migrantes maranhenses formaram o primeiro núcleo urbano de Parauapebas (Vila Rio Verde) atraídos pela mineração. |
| Pereira (2023) `pereira2023migracao` | artigo | contexto | 1960s–2023 | artigo | Desterritorialização, sociabilidade afetada e exclusão da força de trabalho migrante maranhense em Parauapebas. |
| Castriota (2024) `castriota2024housing` | artigo | nucleo | 2018–2019 | artigo; trabalho de campo | Formas emergentes de moradia após o S11D, que atraiu dezenas de milhares de migrantes e mais que dobrou a população de Canaã. |
| Sanches et al. (2025) `sanches2025canaa` | anais | nucleo | 2000s–2025 | anais; ensaio | Relação entre o processo migratório de Canaã e os investimentos minerários no sudeste paraense. |

### Trabalho e renda (11)

| Referência | Tipo | Camada | Período | Método | Principais achados |
|---|---|---|---|---|---|
| Moura et al. (2005) `moura2005mina` | anais | nucleo | 2004–2005 | relato técnico da mineradora (congresso ABM) | Sossego gerava ~500 empregos diretos Vale e ~800 em contratadas; meta de 70% de mão de obra local esbarrava na baixa qualificação de um município recém-emancipado. |
| Costa (2008) `costa2008mineworkers` | artigo | nucleo | c. 2006–2008 | tese; estudo de casos múltiplos | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Farias (2008) `farias2008mineracao` | tese | nucleo | 2000s | tese (NAEA/UFPA) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — subcontratação e desenvolvimento em Parauapebas e Canaã. |
| Paz (2011) `paz2011mineiros` | artigo | contexto | 1943–1964 | tese (história social) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — Serra do Navio como fronteira de mineração industrial. |
| Reis (2016) `reis2016usos` | dissertacao | contexto | 1950s–2016 | dissertação (UFU); dois circuitos da economia urbana | Parauapebas combina modernização mineral e circuito inferior da economia urbana. |
| Alencar et al. (2022) `alencar2022gestao` | artigo | nucleo | c. 2021 | artigo; trajetórias familiares e organização do trabalho em acampamento | Gestão de recursos e sucessão em família acampada em Canaã. |
| Silva Reis e Macedo de Sousa (2022) `silvareis2022modernizacao` | artigo | contexto | 2010s–2020 | artigo; circuito inferior da economia urbana | Espaço antagônico em Parauapebas entre a mineração moderna e pequenas atividades locais. |
| Souza (2022) `souza2022mulheres` | dissertacao | nucleo | 2010s–2022 | dissertação (Direito, Políticas Públicas e Desenvolvimento Regional) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — mulheres no mercado de trabalho da extração mineral. |
| Chagas (2023) `chagas2023dinamica` | dissertacao | nucleo | 1985–2021 | dissertação (Agronomia) | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Pereira (2023) `pereira2023migracao` | artigo | contexto | 1960s–2023 | artigo | Desterritorialização, sociabilidade afetada e exclusão da força de trabalho migrante maranhense em Parauapebas. |
| Alencar e Drebes (2025) `alencar2025quintal` | anais | nucleo | 2025 | anais SOBER | resumo indisponível nas fontes de busca — ler o texto integral na E6 — quintais produtivos de mulheres. |

### Economia mineral, royalties e finanças públicas (39)

| Referência | Tipo | Camada | Período | Método | Principais achados |
|---|---|---|---|---|---|
| Moura et al. (2005) `moura2005mina` | anais | nucleo | 2004–2005 | relato técnico da mineradora (congresso ABM) | Sossego gerava ~500 empregos diretos Vale e ~800 em contratadas; meta de 70% de mão de obra local esbarrava na baixa qualificação de um município recém-emancipado. |
| Farias (2008) `farias2008mineracao` | tese | nucleo | 2000s | tese (NAEA/UFPA) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — subcontratação e desenvolvimento em Parauapebas e Canaã. |
| Viana Júnior (2008) `vianajunior2008royalties` | dissertacao | nucleo | 1989–2007 | dissertação; análise comparativa de indicadores municipais e da CFEM | Avalia impactos positivos e negativos da CFEM em Parauapebas, Oriximiná, Canaã dos Carajás e Ipixuna do Pará. |
| Cabral et al. (2011) `cabral2011canaa` | capitulo | nucleo | 1982–2010 | capítulo de livro (CETEM); dados secundários, entrevistas e relatos de comunidades | Transição da pecuária leiteira à mineração de cobre após o Sossego; fonte da população de 1996 (11.139) e dos relatos sobre os CEDEREs usados na Fase 1b. |
| Santos (2011) `santos2011grande` | dissertacao | nucleo | 2004–2011 | dissertação (Administração) | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Matos et al. (2014) `matos2014estruturas` | artigo | nucleo | 2000s–2012 | artigo; Quociente Locacional, índice de Hirschman-Herfindahl e matriz de dinamismo | Classifica as atividades econômicas estratégicas de Canaã e a especialização produtiva induzida pela mineração. |
| Ribeiro et al. (2014) `ribeiro2014analise` | artigo | nucleo | 2001–2012 | artigo; indicadores de estrutura produtiva | Município recém-criado com PIB de R$ 17 mi (2001), baseado na pecuária leiteira, passa a 'cidade ímã' com investimento de >R$ 1 bi no Sossego. |
| Trindade et al. (2015) `trindade2015ciclo` | artigo | contexto | 2000s–2014 | artigo | Contradições do crescimento econômico e demográfico acelerado pelo ciclo mineral em Parauapebas e necessidade de políticas locais. |
| Leite (2016) `leite2016mensuracao` | dissertacao | nucleo | 2000s–2015 | dissertação; metodologia de contas alfa | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Medeiros (2016) `medeiros2016gestao` | dissertacao | nucleo | 2010–2016 | dissertação; responsabilidade social corporativa e gestão do território | Prefeitura e Vale se articulam para preparar Canaã para o S11D, com investimento em infraestrutura voltado às obras. |
| Pinheiro (2016) `pinheiro2016royalties` | dissertacao | nucleo | 2000s–2016 | dissertação profissional (ITV) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — royalties minerais em Canaã. |
| Cruz (2017) `cruz2017licenca` | dissertacao | nucleo | 2016–2017 | dissertação profissional (ITV); licença social de operação | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Matlaba et al. (2017) `matlaba2017social` | artigo | nucleo | c. 2016 | artigo; survey de percepção social | resumo indisponível nas fontes de busca — ler o texto integral na E6 — percepção social no início do empreendimento S11D. |
| Santos (2017) `santos2017desenvolvimento` | artigo | contexto | 1980s–2016 | artigo; sociologia e antropologia do desenvolvimento | PFC e S11D induziram transformação estrutural na Amazônia Oriental, sem convergência ao desenvolvimento social. |
| Silva et al. (2017) `silva2017conflicts` | artigo | nucleo | 2000–2017 | artigo; leitura geográfica do território da Região de Carajás | Conflitos pelo uso do território nos municípios que concentram os projetos da Vale (Parauapebas, Canaã, Marabá etc.). |
| Filgueiras et al. (2018) `filgueiras2018approaches` | capitulo | nucleo | 2010s | capítulo de livro; parceria social público-privada (fundação corporativa) | Governança intersetorial liderada por fundação corporativa, governo e sociedade civil no desenvolvimento social de cidade com grande empreendimento. |
| Lima e Silva (2018) `lima2018economia` | artigo | nucleo | 2004–2012 | artigo; análise territorial comparada | Mineração como instrumento de ordenamento territorial produz efeitos socioeconômicos diferenciados em Marabá, Parauapebas e Canaã. |
| Medeiros et al. (2018) `medeiros2018gestao` | artigo | nucleo | 2010–2017 | artigo; análise de receitas e PIB | Impostos, taxas e CFEM tornam Parauapebas e Canaã vetores econômicos do Pará. |
| Monte-Cardoso (2018) `montecardoso2018mineracao` | dissertacao | nucleo | 2004–2015 | dissertação (Economia, Unicamp); indicadores socioeconômicos municipais | resumo indisponível nas fontes de busca — ler o texto integral na E6 — mineração e subdesenvolvimento em Canaã, Marabá e Parauapebas. |
| Matlaba et al. (2019) `matlaba2019socioeconomic` | artigo | nucleo | 2000–2016 | artigo; indicadores socioeconômicos | resumo indisponível nas fontes de busca — ler o texto integral na E6 — dinâmica socioeconômica de uma cidade mineradora. |
| Padilha (2020) `padilha2020estado` | tese | nucleo | 2008–2020 | tese (UFRRJ) | O S11D como resposta da Vale à queda do preço do ferro pós-2008 e o papel do Estado no licenciamento e na produção do território. |
| Santos et al. (2020) `santos2020avaliacao` | relatorio | nucleo | 2020 | relatório técnico ITV | resumo indisponível nas fontes de busca — ler o texto integral na E6 — potencial de diversificação socioeconômica. |
| Castro (2021) `castro2021logistica` | dissertacao | nucleo | 2000–2019 | dissertação (Geografia) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — logística de transporte do S11D. |
| Cruz (2021) `cruz2021compliance` | capitulo | nucleo | 2010s | capítulo; análise crítica jurídica | resumo indisponível nas fontes de busca — ler o texto integral na E6 — (des)cumprimento das leis de finanças públicas no uso da tributação mineral. |
| Cruz et al. (2021) `cruz2021measuring` | artigo | nucleo | c. 2019 | artigo; escala de licença social de operação (Boutilier e Thomson) | Mede a licença social de operação da mineração em Canaã, sede do maior projeto de ferro do mundo. |
| Oliveira (2021) `oliveira2021cfem` | dissertacao | nucleo | 2000s–2020 | dissertação (Unifesspa) | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Almeida et al. (2022) `almeida2022gestao` | artigo | nucleo | c. 2021 | artigo; estudo de caso, entrevistas, análise de conteúdo | Percepção dos cidadãos de duas comunidades do entorno sobre a conformidade da gestão mineral às normas. |
| Assuncao (2022) `assuncao2022fundo` | dissertacao | nucleo | 2010s–2022 | dissertação; comparação com fundos subnacionais de royalties | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Caitano e Morales (2022) `caitano2022potencial` | artigo | nucleo | 2010s–2020 | artigo; dados secundários de CFEM e indicadores socioeconômicos | Potencial (e baixa eficiência) da CFEM na promoção do desenvolvimento de Parauapebas e Canaã. |
| Faro (2022) `faro2022amunicipios` | dissertacao | nucleo | 2020–2021 | dissertação (Direito) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — uso da CFEM no combate à COVID-19. |
| Araújo (2023) `araujo2023sina` | dissertacao | nucleo | 2010–2022 | dissertação (UFPA); execução orçamentária municipal | Grau de dependência fiscal da mineração em Parauapebas e Canaã, em paralelo com Itabira. |
| Loureiro et al. (2023) `loureiro2023conhecimento` | artigo | contexto | c. 2022 | artigo; dois levantamentos por survey em Parauapebas | A população desconhece a CFEM e as compensações ambientais e tem baixo pertencimento territorial. |
| Moraes (2023) `moraes2023compensacao` | dissertacao | nucleo | 2010s–2023 | dissertação profissional | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Chagas et al. (2024) `chagas2024dinamica` | artigo | nucleo | 1985–2021 | artigo; uso do solo em 1985, 1995, 2005, 2015 e 2021 | A mineração afetou o crescimento e a diversificação da agropecuária, antes base econômica do município. |
| Cruz (2024) `cruz2024sustainable` | capitulo | nucleo | 2010s–2023 | capítulo; análise da Constituição, legislação da CFEM e LOA municipal | Se a CFEM foi aplicada em áreas estratégicas e prioritárias, conforme a legislação. |
| Matlaba et al. (2024) `matlaba2024local` | artigo | nucleo | c. 2022 | artigo; survey de percepção | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Castro e Palheta (2025) `castro2025circulacao` | artigo | nucleo | 2000–2020s | artigo; teoria da circulação, transporte e logística | Organização e gestão do território pela Vale em Canaã. |
| Dias (2025) `dias2025incentivos` | dissertacao | nucleo | 2010s–2025 | dissertação (UFPA) | Lacuna entre os objetivos dos incentivos fiscais federais ao S11D e os resultados de desenvolvimento regional. |
| Lopes et al. (2026) `lopes2026impacto` | artigo | contexto | 2010s–2026 | artigo; análise documental e dados secundários | Aplicação da CFEM em Parauapebas limitada por falhas institucionais. |

### Meio ambiente e uso da terra (20)

| Referência | Tipo | Camada | Período | Método | Principais achados |
|---|---|---|---|---|---|
| Pereira (2011) `pereira2011programa` | tese | nucleo | 2004–2011 | dissertação; estudo de caso (Vila Bom Jesus) sobre o Programa de Educação Ambiental do Projeto Sossego | Questiona se o PEA da Vale promove transformação socioambiental e cidadania na comunidade do entorno da mina. |
| Cruz (2015) `cruz2015mineracao` | dissertacao | nucleo | 2004–2015 | dissertação (Unifesspa) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — mineração e campesinato. |
| Costa (2017) `costa2017pela` | dissertacao | nucleo | 2017 | dissertação (Arquitetura e Urbanismo); projeto urbano | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Cruz (2017) `cruz2017avanco` | artigo | nucleo | 2004–2012 | artigo; pesquisa de campo e documental | Intensificação da mineração desestrutura a produção camponesa em Canaã; famílias desenvolvem resistências para permanecer na terra. |
| Siravenha (2017) `siravenha2017avaliacao` | tese | nucleo | décadas de 1980–2010 | tese; detecção de mudanças por C2VA semi-supervisionado em imagens Landsat | Testa técnica de detecção de mudança de uso e cobertura na região de Carajás, incluindo Canaã — referência metodológica para a E3b. |
| Cortez et al. (2019) `cortez2019quantificacao` | capitulo | nucleo | multitemporal | capítulo; geotecnologias e análise multitemporal | Quantifica o desflorestamento do município associado ao avanço da fronteira agropecuária e mineral. |
| Araújo et al. (2020) `araujo2020analise` | artigo | nucleo | 2010s | artigo; geoprocessamento (declividade, solos, geologia, uso e cobertura) | Fragilidade potencial e emergente como subsídio ao planejamento territorial ambiental de Canaã. |
| Pereira Júnior et al. (2020) `pereirajunior2020analise` | artigo | contexto | 2006–2017 | artigo; PRODES/DETER (INPE) na sub-bacia do Itacaiúnas | Evolução trienal do desflorestamento no sudeste paraense. |
| Amaral (2021) `amaral2021paisagens` | dissertacao | nucleo | 1984–2019 | dissertação (USP); ecologia da paisagem, vias como driver, estudos quantitativos e qualitativo | Transformação da paisagem de Canaã impulsionada por agropecuária e mineração, com a malha viária como vetor de fragmentação — referência direta para a E3. |
| Casseb e Vasconcellos (2021) `casseb2021avaliacao` | capitulo | nucleo | 2010s–2021 | capítulo; análise de mudança de paisagem | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Cirne e Giacomazzi (2021) `cirne2021ferro` | artigo | contexto | 2009–2012 | artigo; análise da audiência pública do licenciamento do S11D (Ibama) | Demandas da participação social no licenciamento do S11D em unidade de conservação. |
| Mascarenhas e Vidal (2021) `mascarenhas2021conflitos` | artigo | nucleo | 2018 | artigo; dados da CPT e cartografia temática | Tipologias dos conflitos por terra e água na região. |
| Pereira et al. (2021) `pereira2021producao` | artigo | nucleo | 2014–2018 | artigo; estudo ecológico (SIVEP-Malária, IBGE, TerraClass) | Produção socioambiental da malária em Marabá, Parauapebas e Canaã associada ao uso da terra. |
| Cruz e Pinto (2022) `cruz2022mudancas` | anais | nucleo | 2022 | anais SOBER | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Chagas (2023) `chagas2023dinamica` | dissertacao | nucleo | 1985–2021 | dissertação (Agronomia) | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Fernandes (2023) `fernandes2023natureza` | capitulo | contexto | 1984–2020s | capítulo; geoprocessamento de imagens desde 1984–1986 | Desmatamento em Carajás fortemente vinculado às infraestruturas dos governos militares. |
| Furtado et al. (2023) `furtado2023deteccao` | artigo | nucleo | c. 1990–2020 (30 anos) | artigo; classificação de imagens, matriz de conversão | Série histórica de uso e cobertura com matriz de transição e persistência — comparação direta para a mancha da E3b. |
| Chagas et al. (2024) `chagas2024dinamica` | artigo | nucleo | 1985–2021 | artigo; uso do solo em 1985, 1995, 2005, 2015 e 2021 | A mineração afetou o crescimento e a diversificação da agropecuária, antes base econômica do município. |
| Nascimento (2024) `nascimento2024dinamica` | dissertacao | nucleo | 2024 | dissertação (Unifesspa) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — áreas verdes e espaço urbano. |
| Monteiro e Gallardo (2025) `monteiro2025variacoes` | artigo | nucleo | c. 2003–2023 | artigo; Índice Humidex com dados NASA POWER | Aumento do índice de calor ao longo de duas décadas, associado ao crescimento urbano. |

### Saúde (11)

| Referência | Tipo | Camada | Período | Método | Principais achados |
|---|---|---|---|---|---|
| Costa (2008) `costa2008mineworkers` | artigo | nucleo | c. 2006–2008 | tese; estudo de casos múltiplos | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Sousa (2016) `sousa2016avaliacao` | dissertacao | nucleo | 2015–2016 | dissertação; avaliação de programa por triangulação de métodos | resumo indisponível nas fontes de busca — ler o texto integral na E6 — programa de controle da hanseníase na APS de Canaã. |
| Sousa et al. (2017) `sousa2017hanseniase` | artigo | nucleo | 2015–2016 | artigo; avaliação de estrutura com questionários a gestores | Estrutura do programa municipal de hanseníase classificada entre insatisfatória e regular. |
| Pinto (2018) `pinto2018mineracao` | artigo | nucleo | c. 2018 | projeto/relatório Fiocruz; entrevistas com assentados do MST | Impactos do Programa Grande Carajás no processo saúde-doença de assentamentos rurais de cinco municípios, incluindo Canaã. |
| Lima (2019) `lima2019sistematizacao` | dissertacao | nucleo | 2019 | dissertação profissional; sistematização de experiência | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Macêdo (2020) `macedo2020caracterizacao` | tese | nucleo | c. 2015–2019 | tese (IEC); epidemiologia molecular | Prevalência e características do HIV-1 em quatro municípios do complexo de Carajás, motivada pelo grande fluxo migratório. |
| Macêdo et al. (2020) `macedo2020prevalence` | artigo | nucleo | c. 2015–2019 | artigo; inquérito sorológico e epidemiológico | resumo indisponível nas fontes de busca — ler o texto integral na E6 — prevalência de HIV-1 em área de mineração de ferro com intenso fluxo migratório. |
| Vale et al. (2020) `vale2020reorganizacao` | artigo | nucleo | 2020 | artigo; relato de experiência a partir de documentos da gestão | Reorganização da Rede de Atenção à Saúde para a COVID-19, com ampliação da carteira da Atenção Básica. |
| Pereira et al. (2021) `pereira2021producao` | artigo | nucleo | 2014–2018 | artigo; estudo ecológico (SIVEP-Malária, IBGE, TerraClass) | Produção socioambiental da malária em Marabá, Parauapebas e Canaã associada ao uso da terra. |
| Faro (2022) `faro2022amunicipios` | dissertacao | nucleo | 2020–2021 | dissertação (Direito) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — uso da CFEM no combate à COVID-19. |
| Sousa et al. (2024) `sousa2024volatilidade` | artigo | nucleo | 2010s–2023 | artigo; dados DATASUS | Perfil epidemiológico do HIV/AIDS em Canaã e Parauapebas. |

### Planejamento e gestão urbana (27)

| Referência | Tipo | Camada | Período | Método | Principais achados |
|---|---|---|---|---|---|
| Rodrigues (2001) `rodrigues2001company` | dissertacao | contexto | 1960s–2001 | dissertação (NAEA) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — company towns na Amazônia Oriental. |
| Silva (2006) `silva2006arranjos` | tese | nucleo | década de 1980–1990 | tese; sociologia política (Bourdieu), pesquisa documental e entrevistas | A criação dos municípios desmembrados de Marabá (Parauapebas e, depois, Canaã) insere-se na modernização capitalista e na formação de novas lideranças e estruturas de poder locais. |
| Medeiros (2016) `medeiros2016gestao` | dissertacao | nucleo | 2010–2016 | dissertação; responsabilidade social corporativa e gestão do território | Prefeitura e Vale se articulam para preparar Canaã para o S11D, com investimento em infraestrutura voltado às obras. |
| Rodrigues (2016) `rodrigues2016politicas` | dissertacao | nucleo | 2010s | dissertação; teoria social crítica, entrevistas com comunidades, governo, empresas | Estrutura e estratégias de comunicação das políticas 'sociais' de mineradoras em comunidades atingidas no Pará. |
| Cardoso et al. (2017) `cardoso2017canaa` | artigo | nucleo | 2000s–2017 | artigo; níveis da realidade social (Lefebvre), pesquisa de campo | O crescimento urbano mediado por grupos locais sob impulsos globais (mineração, pecuária) exclui os grupos sociais que mais dependem da cidade. |
| Pereira (2017) `pereira2017percepcao` | dissertacao | nucleo | 2016–2017 | dissertação profissional (ITV); percepção de resiliência | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Candido (2018) `candido2018cidade` | dissertacao | nucleo | 2010s | dissertação (Arquitetura e Urbanismo) | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Filgueiras et al. (2018) `filgueiras2018approaches` | capitulo | nucleo | 2010s | capítulo de livro; parceria social público-privada (fundação corporativa) | Governança intersetorial liderada por fundação corporativa, governo e sociedade civil no desenvolvimento social de cidade com grande empreendimento. |
| Lima e Silva (2018) `lima2018economia` | artigo | nucleo | 2004–2012 | artigo; análise territorial comparada | Mineração como instrumento de ordenamento territorial produz efeitos socioeconômicos diferenciados em Marabá, Parauapebas e Canaã. |
| Araújo et al. (2020) `araujo2020analise` | artigo | nucleo | 2010s | artigo; geoprocessamento (declividade, solos, geologia, uso e cobertura) | Fragilidade potencial e emergente como subsídio ao planejamento territorial ambiental de Canaã. |
| Padilha (2020) `padilha2020estado` | tese | nucleo | 2008–2020 | tese (UFRRJ) | O S11D como resposta da Vale à queda do preço do ferro pós-2008 e o papel do Estado no licenciamento e na produção do território. |
| Santos et al. (2020) `santos2020avaliacao` | relatorio | nucleo | 2020 | relatório técnico ITV | resumo indisponível nas fontes de busca — ler o texto integral na E6 — potencial de diversificação socioeconômica. |
| Cirne e Giacomazzi (2021) `cirne2021ferro` | artigo | contexto | 2009–2012 | artigo; análise da audiência pública do licenciamento do S11D (Ibama) | Demandas da participação social no licenciamento do S11D em unidade de conservação. |
| Cruz (2021) `cruz2021compliance` | capitulo | nucleo | 2010s | capítulo; análise crítica jurídica | resumo indisponível nas fontes de busca — ler o texto integral na E6 — (des)cumprimento das leis de finanças públicas no uso da tributação mineral. |
| Matlaba et al. (2021) `matlaba2021resilience` | artigo | nucleo | c. 2017 | artigo; survey de percepção de resiliência | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Muller (2021) `muller2021conhecimento` | dissertacao | nucleo | 2021 | dissertação profissional (ITV) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — estrutura fundiária de Parauapebas e Canaã. |
| Almeida et al. (2022) `almeida2022gestao` | artigo | nucleo | c. 2021 | artigo; estudo de caso, entrevistas, análise de conteúdo | Percepção dos cidadãos de duas comunidades do entorno sobre a conformidade da gestão mineral às normas. |
| Assuncao (2022) `assuncao2022fundo` | dissertacao | nucleo | 2010s–2022 | dissertação; comparação com fundos subnacionais de royalties | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Corrêa et al. (2022) `correa2022politica` | artigo | nucleo | 2009–2018 | artigo; entrevistas com 15 técnicos (Cohab, Defensoria, Instituto de Desenvolvimento Urbano de Canaã) | Limites e dificuldades da regularização fundiária urbana de interesse social no Pará. |
| Leopoldo (2023) `leopoldo2023apresentacao` | artigo | contexto | 2023 | apresentação de dossiê (Confins) | Dossiê 'Planejamento, Urbanização e Políticas Públicas na Região de Carajás'. |
| Moraes (2023) `moraes2023compensacao` | dissertacao | nucleo | 2010s–2023 | dissertação profissional | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Castriota (2024) `castriota2024aqui` | artigo | nucleo | 2016–2023 | artigo; dados secundários e pesquisa qualitativa em Canaã | Autoritarismo neoextrativista: produção do espaço urbano com recursos da CFEM e influência corporativa na cidade, no campo e na floresta. |
| Cruz (2024) `cruz2024sustainable` | capitulo | nucleo | 2010s–2023 | capítulo; análise da Constituição, legislação da CFEM e LOA municipal | Se a CFEM foi aplicada em áreas estratégicas e prioritárias, conforme a legislação. |
| Santos et al. (2024) `santos2024utilizacao` | anais | nucleo | 2023 | anais; SIG | Regularização fundiária de zona de risco no bairro Paraíso das Águas. |
| Castro e Palheta (2025) `castro2025circulacao` | artigo | nucleo | 2000–2020s | artigo; teoria da circulação, transporte e logística | Organização e gestão do território pela Vale em Canaã. |
| Emilio e João (2025) `emilio2025cidade` | artigo | contexto | 2020s | artigo; entrevistas, campo e dados | A Vale molda a psicosfera urbana e a governança territorial de Parauapebas. |
| Silva (2025) `silva2025regularizacao` | artigo | nucleo | 2010s–2025 | artigo; avaliação pós-regularização | Pós-regularização fundiária do núcleo urbano informal Paraíso das Águas. |

### Colonização, história e conflitos agrários (27)

| Referência | Tipo | Camada | Período | Método | Principais achados |
|---|---|---|---|---|---|
| Pires (1995) `pires1995organizacao` | tese | contexto | 1980s–1995 | tese (Geografia) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — organização do espaço ao longo da Estrada de Ferro Carajás. |
| Silva (2006) `silva2006arranjos` | tese | nucleo | década de 1980–1990 | tese; sociologia política (Bourdieu), pesquisa documental e entrevistas | A criação dos municípios desmembrados de Marabá (Parauapebas e, depois, Canaã) insere-se na modernização capitalista e na formação de novas lideranças e estruturas de poder locais. |
| Teixeira (2006) `teixeira2006interferencia` | dissertacao | contexto | 1970s–2006 | dissertação (UFPA); três assentamentos de Parauapebas | A mineração de grande escala alterou a produção camponesa nos assentamentos. |
| Cabral et al. (2011) `cabral2011canaa` | capitulo | nucleo | 1982–2010 | capítulo de livro (CETEM); dados secundários, entrevistas e relatos de comunidades | Transição da pecuária leiteira à mineração de cobre após o Sossego; fonte da população de 1996 (11.139) e dos relatos sobre os CEDEREs usados na Fase 1b. |
| Paz (2011) `paz2011mineiros` | artigo | contexto | 1943–1964 | tese (história social) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — Serra do Navio como fronteira de mineração industrial. |
| Cruz (2015) `cruz2015mineracao` | dissertacao | nucleo | 2004–2015 | dissertação (Unifesspa) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — mineração e campesinato. |
| Cruz (2017) `cruz2017avanco` | artigo | nucleo | 2004–2012 | artigo; pesquisa de campo e documental | Intensificação da mineração desestrutura a produção camponesa em Canaã; famílias desenvolvem resistências para permanecer na terra. |
| Santos (2017) `santos2017conflitos` | dissertacao | nucleo | 2010–2017 | dissertação; análise jurídica, econômica e social de conflito (Vila Racha Placa) | Conflito agrário entre trabalhadores rurais e a Vale na implantação do S11D. |
| Silva et al. (2017) `silva2017conflicts` | artigo | nucleo | 2000–2017 | artigo; leitura geográfica do território da Região de Carajás | Conflitos pelo uso do território nos municípios que concentram os projetos da Vale (Parauapebas, Canaã, Marabá etc.). |
| Pinto (2018) `pinto2018mineracao` | artigo | nucleo | c. 2018 | projeto/relatório Fiocruz; entrevistas com assentados do MST | Impactos do Programa Grande Carajás no processo saúde-doença de assentamentos rurais de cinco municípios, incluindo Canaã. |
| Tonelli (2018) `tonelli2018canaa` | dissertacao | nucleo | 2000s–2018 | dissertação (Geografia, Unicamp) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — 'saque anunciado' na Serra Sul. |
| Bentes et al. (2021) `bentes2021impactos` | artigo | contexto | 2010s–2021 | artigo; análise jurídica | Impactos do S11D sobre os Xikrin do Cateté e violação do ODS 16. |
| Mascarenhas e Vidal (2021) `mascarenhas2021conflitos` | artigo | nucleo | 2018 | artigo; dados da CPT e cartografia temática | Tipologias dos conflitos por terra e água na região. |
| Muller (2021) `muller2021conhecimento` | dissertacao | nucleo | 2021 | dissertação profissional (ITV) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — estrutura fundiária de Parauapebas e Canaã. |
| Nascimento Neto (2021) `nascimentoneto2021emancipacao` | artigo | nucleo | 1994–2020 | artigo; história local com documentos | Contexto de emancipação e crescimento de Canaã e consequências ambientais da mineração, para uso em sala de aula. |
| Oliveira e Nogueira (2021) `oliveira2021processo` | artigo | nucleo | 2007–2016 | artigo; documentos do Conselho Municipal de Educação | Desativação e extinção de escolas rurais no período de expansão mineral. |
| Santos et al. (2021) `santos2021mineracao` | capitulo | nucleo | 2012–2020 | capítulo; revisão, documentos, entrevistas | Implantação do S11D acirra conflitos pela posse da terra (acampamento Planalto Serra Dourada). |
| Alencar et al. (2022) `alencar2022gestao` | artigo | nucleo | c. 2021 | artigo; trajetórias familiares e organização do trabalho em acampamento | Gestão de recursos e sucessão em família acampada em Canaã. |
| Carmo (2023) `carmo2023cidade` | dissertacao | nucleo | 1982–2020 | dissertação (Unifesspa) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — base do artigo da RTG (Carmo 2023); fonte-chave da Fase 1b. |
| Carmo (2023) `carmo2023mineracao` | artigo | nucleo | 2000–2020 (com recuo aos anos 1970) | artigo; histórico dos CEDEREs e produção do espaço urbano | O crescimento da cidade está diretamente ligado à exploração mineral e aos recursos dela advindos; modo de vida dos colonos nos CEDEREs e transformações posteriores. |
| Fernandes (2023) `fernandes2023natureza` | capitulo | contexto | 1984–2020s | capítulo; geoprocessamento de imagens desde 1984–1986 | Desmatamento em Carajás fortemente vinculado às infraestruturas dos governos militares. |
| Miranda e Gomes (2023) `miranda2023territorializacao` | artigo | nucleo | 2010s–2023 | artigo; revisão, documentos, campo | Acampamentos disputam áreas de interesse mineral da Vale; territorialização da luta pela terra. |
| Santos (2023) `santos2023marias` | dissertacao | nucleo | 2020s | dissertação (Unifesspa) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — mulheres acampadas. |
| Souza (2024) `souza2024conflitos` | tese | nucleo | 2000–2024 | tese/dissertação | Grandes projetos alimentam conflitos e expropriação de populações camponesas no Pará. |
| Ferreira e Bringel (2025) `ferreira2025sobrevivendo` | artigo | nucleo | 2020s | artigo; estudo de caso do Acampamento Oziel Alves (MST) | Proletarização do camponês no circuito espacial da mineração e estratégias de resistência. |
| Trevisan et al. (2025) `trevisan2025complexo` | artigo | contexto | 1960s–1985 | artigo; fontes e documentos | Geopolítica militar e a criação ou expansão de núcleos urbanos para viabilizar Carajás. |
| Silva e Souza (2026) `silva2026atividades` | artigo | nucleo | 2020s | trabalho de congresso; cartografia de conflitos | Mapeamento de conflitos da mineração em territórios tradicionais (Barcarena, Canaã, Parauapebas). |

### Sociedade, cultura e educação (19)

| Referência | Tipo | Camada | Período | Método | Principais achados |
|---|---|---|---|---|---|
| Pereira (2011) `pereira2011programa` | tese | nucleo | 2004–2011 | dissertação; estudo de caso (Vila Bom Jesus) sobre o Programa de Educação Ambiental do Projeto Sossego | Questiona se o PEA da Vale promove transformação socioambiental e cidadania na comunidade do entorno da mina. |
| Santos (2011) `santos2011grande` | dissertacao | nucleo | 2004–2011 | dissertação (Administração) | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Rodrigues (2016) `rodrigues2016politicas` | dissertacao | nucleo | 2010s | dissertação; teoria social crítica, entrevistas com comunidades, governo, empresas | Estrutura e estratégias de comunicação das políticas 'sociais' de mineradoras em comunidades atingidas no Pará. |
| Cruz (2017) `cruz2017licenca` | dissertacao | nucleo | 2016–2017 | dissertação profissional (ITV); licença social de operação | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Matlaba et al. (2017) `matlaba2017social` | artigo | nucleo | c. 2016 | artigo; survey de percepção social | resumo indisponível nas fontes de busca — ler o texto integral na E6 — percepção social no início do empreendimento S11D. |
| Miranda (2017) `miranda2017efeito` | dissertacao | nucleo | 2000s–2016 | dissertação (Segurança Pública) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — crescimento da criminalidade em Canaã e Parauapebas. |
| Pereira (2017) `pereira2017percepcao` | dissertacao | nucleo | 2016–2017 | dissertação profissional (ITV); percepção de resiliência | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Santos (2017) `santos2017desenvolvimento` | artigo | contexto | 1980s–2016 | artigo; sociologia e antropologia do desenvolvimento | PFC e S11D induziram transformação estrutural na Amazônia Oriental, sem convergência ao desenvolvimento social. |
| Almeida (2021) `almeida2021analise` | dissertacao | nucleo | 2021 | dissertação profissional | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Bentes et al. (2021) `bentes2021impactos` | artigo | contexto | 2010s–2021 | artigo; análise jurídica | Impactos do S11D sobre os Xikrin do Cateté e violação do ODS 16. |
| Cruz et al. (2021) `cruz2021measuring` | artigo | nucleo | c. 2019 | artigo; escala de licença social de operação (Boutilier e Thomson) | Mede a licença social de operação da mineração em Canaã, sede do maior projeto de ferro do mundo. |
| Matlaba et al. (2021) `matlaba2021resilience` | artigo | nucleo | c. 2017 | artigo; survey de percepção de resiliência | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Oliveira e Nogueira (2021) `oliveira2021processo` | artigo | nucleo | 2007–2016 | artigo; documentos do Conselho Municipal de Educação | Desativação e extinção de escolas rurais no período de expansão mineral. |
| Nogueira (2022) `nogueira2022gestao` | dissertacao | nucleo | 1997–2021 | dissertação profissional (UFT); pesquisa documental | Institucionalização da gestão democrática escolar no Sistema Municipal de Educação. |
| Zonta (2022) `zonta2022adentrando` | dissertacao | nucleo | 2010s–2022 | dissertação (UNESP) | Atuação cultural da Vale ao longo do corredor Carajás, incluindo Canaã. |
| Loureiro et al. (2023) `loureiro2023conhecimento` | artigo | contexto | c. 2022 | artigo; dois levantamentos por survey em Parauapebas | A população desconhece a CFEM e as compensações ambientais e tem baixo pertencimento territorial. |
| Santos (2023) `santos2023marias` | dissertacao | nucleo | 2020s | dissertação (Unifesspa) | resumo indisponível nas fontes de busca — ler o texto integral na E6 — mulheres acampadas. |
| Matlaba et al. (2024) `matlaba2024local` | artigo | nucleo | c. 2022 | artigo; survey de percepção | resumo indisponível nas fontes de busca — ler o texto integral na E6 |
| Alencar e Drebes (2025) `alencar2025quintal` | anais | nucleo | 2025 | anais SOBER | resumo indisponível nas fontes de busca — ler o texto integral na E6 — quintais produtivos de mulheres. |
<!-- MATRIZ:FIM -->
