# Da colônia agrícola à cidade mineral: urbanização, migração e mancha urbana em Canaã dos Carajás (PA), 1982–2026

**Daniel Pessini Sobreira**

Versão de trabalho — 10 de setembro de 2026.

## Resumo

Canaã dos Carajás (PA) passou de núcleo de assentamento dirigido (CEDERE II, 1982) a município (1994) e, com as minas de cobre do Sossego (2004) e de ferro do S11D (2016), a um dos municípios de crescimento populacional mais rápido do Brasil. Este artigo mede esse processo com três fontes combinadas com método único: uma série anual da área construída da sede entre 1984 e 2026, classificada em imagens Landsat e Sentinel-2 e validada com imagens CBERS de alta resolução; os microdados da amostra dos Censos Demográficos de 1991, 2000, 2010 e 2022, harmonizados e submetidos a controle de revelação; e os agregados do Universo por setor censitário de 2010 e 2022. A sede cresceu de 46 ha em 1990 para cerca de 2.300 ha (área ajustada pela acurácia) em 2022 e 3.200 ha em 2026, com o maior ritmo entre o Sossego e o S11D; a área cresceu mais que a população nos anos 2000 (elasticidade 1,24) e menos nos anos 2010 (0,83). Seis em cada dez moradores não naturais chegaram a partir de 2013. Os migrantes de data fixa de 2022 são mais escolarizados, mais formalizados e mais presentes na cadeia produtiva da mineração (36 % dos ocupados, contra 29 % dos não migrantes), com renda média igual, e vivem em domicílios alugados em proporção duas vezes e meia maior. A infraestrutura domiciliar convergiu entre 2000 e 2022, mas o gradiente centro-periferia persiste nos setores de urbanização recente. A comparação com Parauapebas e com os municípios do Sudeste Paraense mostra que Canaã se descola dos comparáveis a partir de 2010. Discute-se o descompasso entre o ciclo das obras, que faz a cidade crescer, e o ciclo dos royalties, que chega depois.

**Palavras-chave:** urbanização; mineração; migração de data fixa; mancha urbana; Carajás; sensoriamento remoto.

## Abstract

Canaã dos Carajás (Pará, Brazil) went from a directed settlement nucleus (CEDERE II, 1982) to a municipality (1994) and, with the Sossego copper mine (2004) and the S11D iron mine (2016), to one of the fastest-growing municipalities in Brazil. This paper measures that process by combining three sources under a single method: an annual series of the built-up area of the urban seat from 1984 to 2026, classified from Landsat and Sentinel-2 imagery and validated against high-resolution CBERS scenes; harmonised sample microdata from the 1991, 2000, 2010 and 2022 Population Censuses, subject to statistical disclosure control; and census-tract aggregates for 2010 and 2022. The seat grew from 46 ha in 1990 to about 2,300 ha (accuracy-adjusted) in 2022 and 3,200 ha in 2026, fastest between Sossego and S11D; built-up area grew faster than population in the 2000s (elasticity 1.24) and slower in the 2010s (0.83). Six in ten residents born elsewhere arrived from 2013 onwards. Fixed-period migrants in 2022 are more educated, more formalised and more present in the mining production chain (36 % of the employed, against 29 % of non-migrants), earn the same on average, and rent their dwellings two and a half times as often. Household infrastructure converged between 2000 and 2022, but a centre-periphery gradient persists in recently urbanised tracts. Compared with Parauapebas and with the municipalities of Southeast Pará, Canaã decouples from its peers after 2010. We discuss the mismatch between the construction cycle, which drives urban growth, and the royalty cycle, which arrives later.

**Keywords:** urbanisation; mining; fixed-period migration; urban footprint; Carajás; remote sensing.

## 1 Introdução

Poucas cidades brasileiras cresceram tanto, em tão pouco tempo, quanto Canaã dos Carajás. O município que o Censo 2000 registrou com 10.922 habitantes, dois terços deles rurais, chegou ao Censo 2022 com 77.079, nove em cada dez urbanos, e a estimativa oficial para 2026 é de 92.311. Entre um censo e outro a economia local mudou de natureza: da pecuária leiteira dos colonos assentados pelo Grupo Executivo das Terras do Araguaia-Tocantins (GETAT) nos anos 1980 para a mineração de cobre, a partir de 2004, e de ferro, a partir de 2016, no maior complexo mineral do país. A literatura chama Canaã de "cidade ímã" e de "laboratório da urbanização na periferia global" (CARDOSO ET AL., 2017; SANCHES ET AL., 2025). O que falta a essa literatura, como se mostra na seção 2, é medida: quanto a cidade cresceu ano a ano, quem chegou e quando, em que a mão de obra migrante se inseriu, e como a expansão do tecido urbano se relaciona com a população e com a renda mineral.

Este artigo responde a essas perguntas com três corpos de evidência produzidos sob um único desenho analítico. O primeiro é uma série anual da área construída da sede de Canaã entre 1984 e 2026, classificada em composições de imagens Landsat (30 m) e Sentinel-2 (10 m) com Random Forest treinado por era de sensor, pós-processada com regras de persistência temporal e validada em três épocas com imagens CBERS de 2 a 5 m de resolução, na forma recomendada por Olofsson et al. (2014). O segundo é o conjunto dos microdados da amostra dos Censos Demográficos de 1991, 2000, 2010 e 2022, harmonizados num esquema único e estimados com bootstrap de domicílios, com aplicação de regras de controle de revelação que respeitam o termo de acesso controlado do Censo 2022. O terceiro são os agregados do Universo por setor censitário de 2010 e 2022, cruzados com a própria série de mancha para localizar cada setor no tempo da expansão urbana. A esses três corpos somam-se a série populacional oficial, as receitas da Compensação Financeira pela Exploração de Recursos Minerais (CFEM) e um painel municipal 2000–2022 que permite comparar Canaã com Parauapebas e com os demais municípios do Sudeste Paraense.

O artigo se organiza em sete seções. A seção 2 revisa a produção acadêmica sobre Canaã e identifica as lacunas que o estudo preenche. A seção 3 apresenta a área de estudo e a trajetória do assentamento à cidade mineral, com os marcos que estruturam toda a análise. A seção 4 descreve fontes, harmonização, estimação, controle de revelação e o pipeline de sensoriamento remoto, e declara as limitações. A seção 5 traz os resultados em nove blocos: população, mancha urbana, densidade e forma, coortes e origens dos migrantes, seletividade, inserção ocupacional e cadeia da mineração, condições domiciliares, desigualdade intraurbana e comparação regional. A seção 6 discute os achados à luz da literatura sobre cidades mineradoras e a seção 7 conclui.

## 2 Revisão de literatura

O levantamento bibliográfico deste projeto consultou OpenAlex, Crossref, Semantic Scholar, a Biblioteca Digital Brasileira de Teses e Dissertações e o Catálogo de Teses da CAPES com termos de núcleo ("Canaã dos Carajás" e variantes) e de contexto (S11D, Sossego, Parauapebas, Programa Grande Carajás, company towns, GETAT). Dos 753 candidatos únicos, 150 foram selecionados por tratarem da sociedade, do território, da economia, do ambiente, da saúde ou das instituições de Canaã e da região; 132 foram verificados em fonte primária e compõem a base citada aqui. A produção é recente e concentrada: dos 101 trabalhos sobre Canaã, 53 são de 2021 em diante, e a curva acompanha o licenciamento e a operação do S11D, não o Sossego. Quase metade são dissertações e teses, sobretudo da UFPA, da Unifesspa, do Instituto Tecnológico Vale e de programas de Economia e Geografia do Sudeste. Os eixos mais cobertos são urbanização e produção do espaço, economia mineral e royalties, planejamento e conflitos agrários; migração, moradia e trabalho são os menos estudados.

**Colonização e formação do município.** O ponto de partida é o assentamento dirigido do GETAT nos Centros de Desenvolvimento Regional (CEDEREs) entre 1982 e 1985, lido como parte da modernização da fronteira e da formação de novas lideranças locais (SILVA, 2006). Cabral et al. (2011) e Carmo (2023) reconstroem a vida dos colonos e a passagem da pecuária leiteira ao cobre; a emancipação de 1994 aparece como narrativa de história local (NASCIMENTO NETO, 2021). Nenhum desses trabalhos estima a população do núcleo antes de 2000, e os números que circulam para 1996 e 2005 vêm de fontes secundárias.

**Urbanização e produção do espaço.** Duas linhagens dominam. A primeira, lefebvriana, lê Canaã como laboratório da urbanização na periferia global e a região como urbanização extensiva, em que o crescimento urbano mediado por grupos locais sob impulsos globais exclui quem mais depende da cidade (CARDOSO ET AL., 2017; MELO; CARDOSO, 2016; MELO, 2020; SANTOS, 2021). A segunda, da geografia regional, trata do uso do território e da produção do espaço urbano financiada pela CFEM (MEDEIROS, 2016; SILVA, 2016; ALMEIDA, 2017; CARMO, 2023), e Castriota (2024) descreve o autoritarismo neoextrativista na cidade, no campo e na floresta. Trabalhos recentes descem à escala intraurbana: condomínios fechados e fragmentação (CORRÊA, 2026), áreas verdes (NASCIMENTO, 2024), ilha de calor (MONTEIRO; GALLARDO, 2025). Para o contexto regional, Parauapebas é o núcleo planejado que se tornou o município de maior crescimento do Pará (FURTADO; PONTE, 2014; GODINHO, 2021; SOUZA, 2024; EMILIO; JOÃO, 2025), e a urbanização induzida por grandes projetos e company towns dá o termo de comparação (RODRIGUES, 2001; JUAREZ, 2021; MACCHIAVELLO FERRADAS ET AL., 2022; TREVISAN ET AL., 2025). Nenhum desses estudos mede a expansão da mancha urbana ano a ano nem a relaciona com a população: os trabalhos de uso e cobertura da terra (AMARAL, 2021; FURTADO ET AL., 2023; CHAGAS ET AL., 2024) tratam o urbano como uma classe entre outras no município inteiro.

**Migração e população.** É o eixo mais citado e menos medido. A literatura afirma o afluxo com base no crescimento populacional agregado (RIBEIRO ET AL., 2014; MATLABA ET AL., 2019; SANCHES ET AL., 2025); os únicos trabalhos que tocam dados de pessoas são epidemiológicos, sobre HIV numa área de mineração com intenso fluxo migratório (MACÊDO ET AL., 2020; SOUSA ET AL., 2024). Para Parauapebas há estudos de trajetórias de migrantes maranhenses (CRUZ, 2022; PEREIRA, 2023) e da relação campo-cidade no entorno do complexo (BRINGEL; MACHADO, 2020). Não há, na literatura verificada, análise de migração de data fixa, de coortes de chegada ou de seletividade dos migrantes com microdados censitários.

**Moradia, trabalho e renda.** A evidência sobre moradia é pontual: famílias pobres do Cadastro Único em condições precárias (SILVA; SOUSA, 2022), conjunto do Minha Casa Minha Vida com inserção urbana problemática (SOUZA; FERREIRA JÚNIOR, 2023), regularização fundiária de núcleo informal (CORRÊA ET AL., 2022; SILVA, 2025) e, sobretudo, as formas de morar criadas pela chegada de dezenas de milhares de migrantes do S11D (CASTRIOTA, 2024). Sobre trabalho, Moura et al. (2005) registra que o Sossego gerava cerca de 1.300 empregos e que a exigência de mão de obra local esbarrava na baixa qualificação; a subcontratação e seus limites para o desenvolvimento regional (FARIAS, 2008), a participação feminina na extração (SOUZA, 2022) e a qualidade de vida de mineiros em comunidades remotas (COSTA, 2008) completam um eixo pequeno. Não há série de formalização, setor e renda para a cidade.

**Economia mineral, royalties e finanças públicas.** O eixo mais volumoso fora da urbanização converge em três pontos: especialização produtiva e dependência (MATOS ET AL., 2014; RIBEIRO ET AL., 2014; MONTE-CARDOSO, 2018; ARAÚJO, 2023); CFEM abundante e aplicada de modo pouco estratégico ou pouco transparente (VIANA JÚNIOR, 2008; PINHEIRO, 2016; OLIVEIRA, 2021; CAITANO; MORALES, 2022; ASSUNCAO, 2022; MORAES, 2023); e o S11D como estratégia da Vale e do Estado (PADILHA, 2020; DIAS, 2025; CASTRO; PALHETA, 2025). A leitura neoextrativista (SANTOS, 2017; CASTRIOTA, 2024) é a moldura crítica dominante. Um grupo coeso do Instituto Tecnológico Vale mede licença social de operação, resiliência e percepção social da mineração com surveys (MATLABA ET AL., 2017; CRUZ ET AL., 2021; MATLABA ET AL., 2021; MATLABA ET AL., 2024).

**Conflitos agrários e meio ambiente.** O avanço do S11D desestrutura a produção camponesa e multiplica acampamentos em áreas de interesse mineral (CRUZ, 2017; SANTOS, 2017; SANTOS ET AL., 2021; MIRANDA; GOMES, 2023; FERREIRA; BRINGEL, 2025; SOUZA, 2024); é o contraponto rural da urbanização. Desmatamento, mudança de paisagem e a relação entre infraestrutura e desflorestamento desde 1984 (CORTEZ ET AL., 2019; FERNANDES, 2023), além de testes de detecção de mudança em Landsat na região (SIRAVENHA, 2017), são referências metodológicas diretas para a série de mancha aqui construída.

Cinco lacunas emergem dessa revisão e organizam a contribuição do artigo: (i) uma série anual da mancha urbana com método único, cruzada com a população; (ii) migração de data fixa, coortes de chegada e seletividade com microdados de 1991 a 2022; (iii) a trajetória populacional pré-1994 com fontes datadas e faixas de incerteza; (iv) condições domiciliares e desigualdade intraurbana por setor censitário entre 2010 e 2022; (v) densidade e forma urbana, com a elasticidade entre área construída e população.

## 3 Área de estudo e contexto mineral

Canaã dos Carajás (código IBGE 1502152) ocupa 3.147 km² no Sudeste Paraense, a sudoeste de Parauapebas, entre as serras que abrigam os depósitos de cobre do Sossego e de ferro da Serra Sul. A sede municipal está a cerca de 6,5° S e 49,9° O, numa janela de 26,6 por 22,2 km que este estudo adota como área de interesse para a série de mancha. O Quadro 1 sintetiza os marcos que estruturam a análise; todos foram conferidos em fonte primária ou na bibliografia verificada.

| Ano | Marco | Fonte |
|---|---|---|
| 1980 | Criação do GETAT (Decreto-lei 1.767) | (CARMO, 2023) |
| 1982–1985 | Assentamento dirigido nos CEDEREs I, II e III; 1.551 famílias assentadas, 816 títulos definitivos até 1985 | (CABRAL ET AL., 2011; CARMO, 2023) |
| 1988 | Parauapebas desmembrada de Marabá; o CEDERE II passa a Parauapebas | (CARMO, 2023) |
| 1991 | Censo: Parauapebas com 53.335 habitantes, incluindo o atual Canaã | IBGE, SIDRA t/200 |
| 1994 | Lei estadual 5.860 cria o município; instalação em 1997 | IBGE, Formação administrativa |
| 2002–2004 | Construção da mina do Sossego (Vale, cobre); operação em 2004 | (MOURA ET AL., 2005; CABRAL ET AL., 2011) |
| 2013–2016 | Construção do S11D (Vale, ferro); operação em dezembro de 2016 | (CIRNE; GIACOMAZZI, 2021; PADILHA, 2020) |
| 2022 | Censo: 77.079 habitantes, 69.332 urbanos | IBGE, SIDRA t/9923 |

O assentamento do GETAT é a origem material da cidade. O CEDERE II, implantado em 1982 no que é hoje a sede de Canaã, recebeu colonos em lotes de cerca de 50 ha; as fontes divergem sobre o escopo das 1.551 famílias assentadas entre 1982 e 1984 (se nos três núcleos ou apenas nos que hoje pertencem a Canaã), e apenas cerca de 10 % das famílias teriam permanecido nos lotes originais após 1985 (CABRAL ET AL., 2011). Convertidas em pessoas com o tamanho médio de domicílio da região em 1991 (4,76 moradores) como piso e 5,5 como teto, as famílias assentadas correspondem a algo entre 3,9 mil e 8,5 mil pessoas em 1985, conforme o cenário de escopo; esse é o único número que se pode oferecer para o assentamento, e ele é apresentado neste artigo apenas como faixa. Entre 1985 e 1996 a curva populacional é em U: esvaziamento dos lotes e recomposição por migração até a Contagem de 1996, que o SIDRA não publica para Canaã (o município só foi instalado em 1997) e que fontes secundárias registram em 11.139 habitantes (CABRAL ET AL., 2011). O Censo 2000 encontrou 10.922 pessoas, das quais 3.924 urbanas.

A mineração chegou em duas ondas. A mina do Sossego, primeira operação de cobre da Vale, foi construída entre 2002 e 2004 e a Contagem de 2007 já encontrou 23.757 habitantes, mais que o dobro de 2000. O S11D, maior projeto de minério de ferro da história da empresa, foi licenciado em 2012, construído entre 2013 e 2016 e entrou em operação em dezembro de 2016; o Censo 2022 encontrou 77.079 habitantes. A CFEM distribuída ao município, que não passava de R$ 26 milhões anuais até 2016, alcançou R$ 1,1 bilhão em 2021 e fez de Canaã, em 2021, o responsável por 13,3 % do PIB do Pará. A Figura 1 situa a série populacional nesses marcos.

<!-- fig: figuras/fig_01_populacao.png | Figura 1 — População residente de Canaã dos Carajás, 1985–2026, por tipo de fonte. Faixas ocre em 1985: conversão de famílias assentadas em pessoas (4,76–5,5 moradores por domicílio), em três cenários de escopo; losangos: citações secundárias; círculos vazados: estimativas anuais do IBGE, ancoradas no censo anterior e sistematicamente subestimadas; janelas sombreadas: construção das minas. Fonte: IBGE (Censos 1991–2022, Contagem 2007, Estimativas); CETEM (2011); PDP (2007); PLANO.md Fase 1b. -->


## 4 Dados e métodos

### 4.1 Fontes oficiais e agregados por setor

A série populacional e os indicadores municipais vêm da API do SIDRA (IBGE): Censos de 1970 a 2022 (tabelas 200, 202, 9923, 1552, 9514, 9605), Contagens de 1996 e 2007 (305, 793), estimativas anuais (6579), PIB dos Municípios (5938) e Cadastro Central de Empresas (6449). As receitas da CFEM de 2004 a 2026 vêm dos relatórios de distribuição da Agência Nacional de Mineração, lidos diretamente das páginas oficiais, e foram deflacionadas pelo IPCA de julho de cada ano para reais de julho de 2022. Os agregados do Universo por setor censitário (2010: 39 setores; 2022: 119) foram recortados das malhas oficiais e reprojetados para SIRGAS 2000 / UTM 22S (EPSG:31982), em que todas as áreas deste artigo são calculadas; os nomes de variáveis foram resolvidos contra os dicionários oficiais, nunca digitados de memória. A soma dos setores reproduz o total municipal do SIDRA em 2022 (77.079) e fica a 0,5 % dele em 2010.

### 4.2 Microdados da amostra e harmonização

Os microdados da amostra dos Censos de 1991, 2000, 2010 e 2022 foram lidos para o Pará inteiro a partir dos layouts oficiais e harmonizados num esquema único: sexo, idade, cor ou raça, nível de instrução em quatro classes, ocupação, posição na ocupação em seis classes, vínculo formal, setor de atividade em nove classes (CNAE-Dom 1.0 e 2.0 e seção CNAE em 2022), renda do trabalho e renda total deflacionadas para reais de julho de 2022, status migratório de data fixa (residência cinco anos antes, com os saltos de pergunta de cada questionário tratados), origem por município e UF, naturalidade, tempo de moradia e ano de chegada; para os domicílios, tipo, condição de ocupação, água, esgoto, lixo, energia (até 2010), internet (2010 e 2022), moradores por dormitório, renda domiciliar per capita e um índice de adequação (água da rede geral, esgoto por rede ou fossa séptica e lixo coletado). As geografias são a sede de Canaã (situação urbana), o município, Parauapebas (sede e município) e o Pará. Como Canaã só existe a partir de 1994, o Censo 1991 é usado por meio de Parauapebas, que então incluía o atual território de Canaã: a linha de base de 1991 é, portanto, de um superconjunto, e é rotulada assim em todas as tabelas. A população expandida reproduz o SIDRA com desvio nulo em 2000 e 2010 e de 0,3 % em 2022 (o Censo 2022 de acesso controlado exclui domicílios coletivos), e o número de domicílios difere do Universo em menos de 0,1 %.

### 4.3 Estimação e controle de revelação

Os erros-padrão foram obtidos por bootstrap de domicílios (Rao-Wu, 200 réplicas, estratificado por área de ponderação em 2022) e cada estimativa publicada leva coeficiente de variação e classe de precisão (boa até 15 %, cautela até 30 %, baixa acima). A amostra de Canaã é pequena (cerca de 1,9 mil pessoas em 2000, 2,6 mil em 2010 e 7,4 mil em 2022), o que limita os cruzamentos. Os microdados de 2022 são de acesso controlado, e o projeto aplica regras de controle de revelação alinhadas ao termo de compromisso: tamanho mínimo de célula (20 pessoas e 10 domicílios amostrais em 2022; 10 e 5 nos demais censos), contagens ponderadas arredondadas a 10, tamanhos amostrais só em faixas, no máximo duas dimensões temáticas cruzadas, nenhuma estimativa por área de ponderação, verificação de diferenciação entre município e sede (a área rural implícita também precisa cumprir o limiar) e supressão complementar, em que categorias pequenas são fundidas numa célula "outros" cujos constituintes ficam explícitos. Um verificador independente reconta todas as 20.458 células publicadas a partir dos microdados antes de qualquer saída chegar às tabelas e figuras. As razões e diferenças entre grupos apresentadas aqui foram derivadas dessas células com propagação de erro pelo método delta, supondo independência entre células, o que é conservador.

### 4.4 Sensoriamento remoto: a série anual da mancha urbana

A área construída da sede foi mapeada ano a ano numa grade fixa de 30 m (887 por 740 pixels, EPSG:31982) com 1.777 recortes de cenas Landsat 5, 7, 8 e 9 (coleção 2, nível 2), Sentinel-2 L2A e CBERS obtidos via catálogos STAC do Planetary Computer, do Element84 e do Brazil Data Cube, sem uso de plataformas em nuvem proprietárias. Para cada ano compôs-se a mediana da estação seca (junho a setembro, nuvem abaixo de 40 %), com máscara de qualidade, harmonização OLI para ETM+ segundo Roy et al. (2016) e uma composição de NDVI máximo da estação chuvosa para capturar a amplitude intersazonal, que separa o construído do solo exposto e do pasto seco. Quarenta e dois dos 43 anos têm 100 % dos pixels observados; 1984 tem 97 %. As 20 feições incluem as seis bandas, índices espectrais (NDVI, NDBI, MNDWI, BUI, BSI, IBI, NBR2), textura local, NDVI máximo da chuva, amplitude intersazonal e declividade do Copernicus DEM.

A classificação usou Random Forest treinado por era de sensor (TM/ETM+ 1984–2012; OLI 2013–2026; MSI 2017–2026 a 10 m), com rótulos de MapBiomas e do World Settlement Footprint para 2000 e 2010 e das Áreas Urbanizadas do IBGE para 2019 e 2022, negativos estratificados e loteamentos vazios como negativos explícitos, e uma amostra de pixels estáveis comum a todas as eras. A acurácia por validação cruzada em blocos de 3 km ficou entre 0,95 e 0,98. O pós-processamento aplica, nesta ordem, abertura morfológica para remover estradas de um pixel, maioria temporal em janela de três anos, persistência (um pixel só é selado depois de dois anos consecutivos como urbano, e só o núcleo selado é protegido de retração), máscara de mineração (lavra observada mais 1 km e concessões da ANM próximas à lavra), unidade mínima de 1 ha e encadeamento de 1 km ao núcleo para separar a sede contígua dos outros núcleos. A partir de 2022 os polígonos de loteamento sem construção das Áreas Urbanizadas 2022 são mantidos como classe separada.

A validação independente seguiu Olofsson et al. (2014) e Stehman (2014) em três épocas: 2009 (CBERS-2B HRC, 2,5 m, corregistrada por correlação de fase porque as cenas chegam com erro de georreferência de até 3 km), 2017 (CBERS-4 PAN5M, 5 m) e 2022 (CBERS-4A WPM, 2 m), com amostra aleatória estratificada e fotointerpretação de 50 pontos por estrato. A acurácia global ficou entre 0,984 e 0,996, com omissão do urbano próxima de zero e comissão de 15 a 20 % na franja (lotes terraplenados, pátios, chácaras). As áreas ajustadas pela matriz de erro, com intervalo de confiança de 95 %, são de 931 ± 176 ha em 2009, 2.260 ± 325 ha em 2017 e 2.573 ± 555 ha em 2022 para o urbano total; o fator entre área ajustada e área mapeada (0,79 a 0,87) foi interpolado entre as épocas validadas e mantido constante fora delas, e é aplicado a toda a série apresentada nas figuras. Antes de 1999 não há referência independente e a acurácia não é verificável. O limiar de probabilidade de 0,5 foi fixado antes da validação. A série própria diverge dos produtos globais na direção esperada: o MapBiomas superestima a área urbana da janela por um fator mediano de 4,1 e a mantém estagnada entre 1996 e 2014; o World Settlement Footprint Evolution acompanha a série própria até 2002 e depois subestima o crescimento; as Áreas Urbanizadas do IBGE de 2022 (2.139 ha na sede) ficam 8 % abaixo da área ajustada.

### 4.5 Desenho analítico

Os resultados combinam os três corpos de evidência em nove blocos: (a) a série populacional oficial, as estimativas anuais e as citações de terceiros, rotuladas por tipo de fonte; (b) a mancha anual contra a população da sede, com elasticidade área-população, densidade sobre a área construída e a razão do indicador ODS 11.3.1 entre a taxa de consumo de solo e a de crescimento populacional; (c) as coortes de chegada dos moradores não naturais; (d) o perfil dos migrantes de data fixa e dos não migrantes, com razões de seletividade; (e) a inserção ocupacional e, em particular, a inserção na cadeia produtiva da mineração, definida como extrativa mineral (seção B da CNAE, que inclui atividades de apoio à extração), construção (F) e indústria de transformação (C), com a ressalva de que fornecedores da mina em serviços e transporte não são identificáveis no CNAE-Dom, de modo que a cadeia ampliada é um limite inferior; (f) as condições dos domicílios segundo a presença de migrante recente e a desigualdade entre setores censitários da sede, situados pela distância ao núcleo de 1990 e pelo ano mediano de urbanização de seus pixels; (g) a comparação com Parauapebas e o Pará, com diferença-em-diferenças descritiva, e com grupos de municípios do Sudeste Paraense num painel de áreas mínimas comparáveis 2000–2022; (h) 1991 como linha de base pré-mineral; (i) PIB, CFEM e emprego formal.

### 4.6 Limitações

Cinco limitações devem ser declaradas. Primeira, a amostra censitária de Canaã é pequena e o controle de revelação suprime ou funde categorias, sobretudo na sede: o perfil detalhado é apresentado para o município, e a sede aparece nos agregados. Segunda, os migrantes de data fixa captam apenas quem chegou nos cinco anos anteriores a cada censo e sobreviveu no município até a data de referência; as coortes de chegada são sobreviventes, não fluxos. Terceira, a série de mancha tem comissão na franja e não pode ser validada antes de 1999; o ano de 2026 é o último da série e carece de confirmação temporal, sendo tratado como provisório. Quarta, as estimativas populacionais anuais do IBGE entre censos subestimaram sistematicamente o crescimento de Canaã (a Contagem de 2007 e o Censo 2022 encontraram cerca do dobro do estimado), o que afeta qualquer indicador per capita anual. Quinta, a reconstituição da população entre 1982 e 2000 depende de fontes secundárias parcialmente inconsistentes; ela é apresentada como faixa e não como série.

## 5 Resultados

### 5.1 A trajetória populacional

A Tabela 1 resume a série oficial. Canaã cresceu 9,4 % ao ano entre 2000 e 2010 e 9,2 % ao ano entre 2010 e 2022, ritmos que se decompõem em pulsos: 11,7 % ao ano entre o Censo 2000 e a Contagem de 2007, durante e logo após as obras do Sossego, e 4,0 % ao ano entre 2007 e 2010; a década de 2010 acrescentou 4,2 mil habitantes por ano. Entre a Contagem de 1996 (citação secundária) e o Censo 2000 a população foi estável ou levemente decrescente, o que é coerente com o esvaziamento dos lotes rurais descrito pela literatura. A população urbana passou de 3.924 (2000) para 20.727 (2010) e 69.332 (2022); a sede contígua, medida pelos setores urbanos cujo construído pertence à mancha principal, concentrava 67.915 pessoas em 2022, e a Vila Planalto, núcleo separado, outras 1.417.

**Tabela 1 — População residente de Canaã dos Carajás e taxas geométricas de crescimento, 1996–2026**

| Período | População inicial | População final | Taxa geométrica (% a.a.) | Acréscimo médio (hab./ano) |
|---|---|---|---|---|
| 2000–2007 | 10.922 | 23.757 | 11,7 | 1.834 |
| 2007–2010 | 23.757 | 26.716 | 4,0 | 986 |
| 2010–2022 | 26.716 | 77.079 | 9,2 | 4.197 |
| 2000–2010 | 10.922 | 26.716 | 9,4 | 1.579 |
| 1996–2000 (1996 = citação CETEM) | 11.139 | 10.922 | -0,5 | -54 |
| 2022–2026 (2026 = estimativa IBGE) | 77.079 | 92.311 | 4,6 | 3.808 |

Fonte: IBGE (Censos 2000, 2010 e 2022; Contagem 2007; Estimativas 2026); CETEM (2011) para 1996.

Nota: O SIDRA não publica a Contagem 1996 para Canaã (município instalado em 1997); o valor de 1996 é citação secundária.


### 5.2 A mancha urbana, 1984–2026

A Figura 2 mostra a série anual da área construída contígua da sede. O núcleo do CEDERE II tinha 8 ha em 1984 e 46 ha em 1990; em 2000 chegava a 139 ha mapeados (110 ha ajustados). O primeiro salto vem com as obras do Sossego: 504 ha em 2004 e 745 ha em 2007. A década seguinte é a de maior ritmo absoluto da série, 158 ha por ano entre 2004 e 2016, e o S11D encontra em 2016 uma cidade de 2.397 ha mapeados. A área cresce lentamente entre 2017 e 2022 (41 ha por ano) e volta a saltar depois de 2022, com 1.012 ha acrescidos até 2026, ano em que a sede alcança 3.656 ha mapeados e cerca de 3.200 ha ajustados; como 2026 não tem confirmação temporal, parte desse salto pode ser comissão. A Figura 3 mostra a sede em cinco cortes e a Figura 4 o primeiro ano urbano de cada pixel: mais da metade da sede de 2026 (52 %) foi construída entre o Sossego e o S11D. A expansão foi para oeste e sudoeste até 2004, para noroeste e sudoeste no ciclo Sossego–S11D e para sudoeste e norte depois do S11D; o centroide da mancha deslocou-se 1,1 km do núcleo histórico, rumo oeste-noroeste, e a forma tornou-se menos compacta depois de 2022, com o índice de proximidade caindo de 0,78 para 0,69.

<!-- fig: figuras/fig_02_mancha_serie.png | Figura 2 — Área construída contígua da sede de Canaã dos Carajás, 1984–2026 (acima: área mapeada, área ajustada pela acurácia com IC 95 % e MapBiomas como comparação; abaixo: acréscimo anual em hectares). Janelas sombreadas: construção do Sossego (2002–04) e do S11D (2013–16). O valor de 2026 é provisório (último ano da série, sem confirmação temporal). Fonte: Elaboração própria: série própria Landsat/Sentinel-2 (30 m), validada com CBERS; população IBGE. MapBiomas Col. 11 (CC-BY). -->


<!-- fig: figuras/fig_03_mapas_censos.png | Figura 3 — Área construída classificada (30 m) nos anos de 1990, 2000, 2010, 2022 e 2026; em cinza, a mancha do painel anterior. Hachura: loteamentos aprovados sem construção (Áreas Urbanizadas 2022). Fonte: Elaboração própria: série própria Landsat/Sentinel-2 (30 m), validada com CBERS; população IBGE. -->


<!-- fig: figuras/fig_04_ano_urbanizacao.png | Figura 4 — Primeiro ano em que cada pixel de 30 m da sede foi classificado como construído (série própria, 1984–2026), agrupado pelos ciclos minerais; cruz: centroide do núcleo de 1990. Fonte: Elaboração própria: série própria Landsat/Sentinel-2 (30 m), validada com CBERS; população IBGE. -->


### 5.3 Densidade, elasticidade e forma

A relação entre área e população mudou de sinal entre as duas décadas (Tabela 2, Tabela 3 e Figura 5). Entre 2000 e 2010 a área ajustada cresceu 22,8 % ao ano e a população da sede 18,1 %: elasticidade de 1,24, razão ODS 11.3.1 de 1,23, densidade caindo de 35,6 para 24,0 habitantes por hectare construído. A cidade se espraiou. Entre 2010 e 2022 a área cresceu 8,6 % ao ano e a população 10,4 %: elasticidade de 0,83, razão de 0,76, densidade subindo para 29,4 habitantes por hectare, com 10,5 domicílios por hectare e menos moradores por domicílio (3,55 para 2,79). A cidade adensou. No conjunto dos 22 anos a elasticidade é de 1,07, ou seja, a sede cresceu em área quase na mesma proporção em que cresceu em população.

**Tabela 2 — População, área construída e densidade da sede de Canaã dos Carajás nos anos censitários**

| Ano | População da sede | Área mapeada (ha) | Área ajustada (ha) ± IC 95 % | Densidade ajustada (hab./ha) | Domicílios/ha (ajust.) | Moradores/domicílio |
|---|---|---|---|---|---|---|
| 2000 | 3.924 | 139 | 110 ± 21 | 35,6 | — | — |
| 2010 | 20.668 | 1.076 | 860 ± 158 | 24,0 | 6,8 | 3,55 |
| 2022 | 67.915 | 2.644 | 2.311 ± 499 | 29,4 | 10,5 | 2,79 |

Fonte: Elaboração própria: série própria Landsat 30 m (E3b), validada com CBERS (Olofsson et al., 2014); população dos setores urbanos do Universo (IBGE).

Nota: Área ajustada = área mapeada corrigida pela acurácia (usuário/produtor) das épocas validadas (2009, 2017, 2022); em 2000 o fator é extrapolado.


**Tabela 3 — Elasticidade área construída–população da sede (área ajustada)**

| Período | Taxa da área (% a.a.) | Taxa da população (% a.a.) | Elasticidade área-população | Densidade inicial → final (hab./ha) |
|---|---|---|---|---|
| 2000–2010 | 22,8 | 18,1 | 1,24 | 35,6 → 24,0 |
| 2010–2022 | 8,6 | 10,4 | 0,83 | 24,0 → 29,4 |
| 2000–2022 | 14,8 | 13,8 | 1,07 | 35,6 → 29,4 |

Fonte: Elaboração própria (E3c, E5).

Nota: Elasticidade = Δln(área) / Δln(população); > 1 indica espraiamento (área cresce mais que a população), < 1 adensamento.


<!-- fig: figuras/fig_05_densidade.png | Figura 5 — Densidade populacional da sede sobre a área construída (esquerda; barras = IC 95 % da área ajustada) e razão entre a taxa de consumo de solo e a taxa de crescimento populacional (ODS 11.3.1, direita). Fonte: Elaboração própria: série própria Landsat/Sentinel-2 (30 m), validada com CBERS; população IBGE. -->


### 5.4 Quem chegou e quando

Dos 76,8 mil residentes de 2022, 58,9 mil não nasceram no município ou não moraram sempre nele. A Tabela 4 e a Figura 6 distribuem esses moradores pelo período de chegada. As coortes anteriores a 2002 são pequenas, cerca de 250 chegadas sobreviventes por ano. As obras do Sossego elevam o ritmo para 1,3 mil por ano; a operação do Sossego, para 1,8 mil; as obras do S11D, para 2,6 mil; e o período 2017–2022, para 4,5 mil por ano. Seis em cada dez moradores não naturais chegaram a partir de 2013. As coortes de chegada dos censos anteriores mostram o mesmo padrão em escala menor: em 2010, metade dos não naturais havia chegado entre 2005 e 2010, e um quinto durante as obras do Sossego.

**Tabela 4 — Residentes de Canaã dos Carajás em 2022 não naturais do município, por período de chegada**

| Período de chegada | Residentes em 2022 (arredondado) | % dos chegados | Chegados por ano | CV (%) |
|---|---|---|---|---|
| até 1984 (assentamento) | 940 | 1,6 | — | 14,8 |
| 1985–1994 (pré-município) | 2.480 | 4,2 | 248 | 7,7 |
| 1995–2001 (instalação) | 1.860 | 3,2 | 266 | 9,2 |
| 2002–2004 (obras do Sossego) | 4.030 | 6,8 | 1.343 | 7,7 |
| 2005–2012 (operação Sossego) | 14.210 | 24,1 | 1.776 | 4,2 |
| 2013–2016 (obras do S11D) | 10.300 | 17,5 | 2.575 | 5,2 |
| 2017–2022 (operação S11D) | 25.100 | 42,6 | 4.482 | 3,1 |

Fonte: Elaboração própria a partir dos microdados da amostra do Censo 2022 (IBGE; acesso controlado); estimativas aprovadas pelo controle de revelação.

Nota: Sobreviventes em 2022 de cada coorte (não o fluxo original); contagens arredondadas a 10. * CV 15–30 %; ** CV > 30 %.


<!-- fig: figuras/fig_06_coortes_chegada.png | Figura 6 — Esquerda: residentes de Canaã dos Carajás em 2022 não naturais do município, por ano de chegada (barras de erro: IC 95 %; anos com n insuficiente fundidos pelo controle de revelação e omitidos). Direita: distribuição por período de chegada nos Censos 2000, 2010 e 2022. Fonte: Elaboração própria a partir dos microdados da amostra dos Censos Demográficos (IBGE); estimativas aprovadas pelo controle de revelação. -->


A origem é majoritariamente paraense e maranhense. Entre os migrantes de data fixa de 2022, 57 % vinham de outro município do Pará, 21 % do Nordeste (18 % só do Maranhão), 8 % do Sudeste e 7 % de outros estados do Norte; Parauapebas responde sozinha por 13 % das origens, seguida de Tucuruí, Marabá, São Luís e Belém. A composição é estável desde 2000, com uma participação maranhense mais alta em 2010 (22 %), durante o auge das obras da década. Em 2022, 24,7 % da população era natural do município, 31,1 % de outro município paraense e 44,2 % de outra UF ou do exterior. A estrutura etária acompanha (Figura 7): a base larga de 1991 (44 % da população com menos de 15 anos em Parauapebas) dá lugar, em 2010 e 2022, a um perfil concentrado nos adultos de 20 a 39 anos, típico de cidade receptora de migrantes em idade ativa.

<!-- fig: figuras/fig_07_piramides.png | Figura 7 — Pirâmides etárias (% da população total): Parauapebas 1991 (amostra; inclui o atual Canaã), e Canaã dos Carajás 2000, 2010 e 2022 (Universo, SIDRA t/1552 e t/9514). Fonte: IBGE — Censos 1991 (amostra, estimativa própria), 2000, 2010 e 2022 (Universo). -->


### 5.5 Seletividade dos migrantes

A Tabela 5 e a Figura 8 comparam os migrantes de data fixa de 2022 (residiam em outro município em 2017) com os não migrantes. Os migrantes são mais jovens (28,2 contra 31,3 anos de idade média), têm mais superior completo entre os adultos de 25 anos ou mais (15,3 % contra 12,1 %) e menos pessoas sem o fundamental completo (23,5 % contra 29,3 %); entre os ocupados, têm mais carteira assinada (61,7 % contra 49,0 %) e menos trabalho por conta própria (17,2 % contra 21,1 %), e estão menos presentes na administração pública, educação e saúde (7,3 % contra 15,3 %). Todas essas diferenças são significativas a 95 %. A renda média do trabalho, porém, é igual (R$ 2.725 contra R$ 2.734), assim como a taxa de ocupação e a distribuição por sexo e cor. A seletividade positiva em escolaridade e formalidade não se traduz em prêmio salarial, o que sugere que os migrantes recentes preenchem postos formais de qualificação média na mesma escala salarial dos moradores antigos.

**Tabela 5 — Perfil de migrantes de data fixa (chegados em 2017–2022) e não migrantes, Canaã dos Carajás, 2022**

| Dimensão | Categoria | Migrantes (%) | Não migrantes (%) | Razão de seletividade | EP da razão | Diferença signif. (95 %) |
|---|---|---|---|---|---|---|
| Nível de instrução (25 anos ou mais) | Superior completo | 15,3 | 12,1 | 1,27 | 0,14 | sim |
| Nível de instrução (25 anos ou mais) | Sem instrução / fund. incompleto | 23,5 | 29,3 | 0,80 | 0,06 | sim |
| Ocupação (10 anos ou mais) | Sim | 56,7 | 54,9 | 1,03 | 0,03 | não |
| Vínculo formal | Sim | 64,2 | 59,6 | 1,08 | 0,04 | sim |
| Setor de atividade | Extrativa mineral | 12,0 | 9,8 | 1,22 | 0,16 | não |
| Setor de atividade | Construção | 16,1 | 13,3 | 1,20 | 0,11 | não |
| Setor de atividade | Serviços | 25,8 | 25,0 | 1,03 | 0,08 | não |
| Setor de atividade | Adm. pública, educação e saúde | 7,3 | 15,3 | 0,48 | 0,07 | sim |
| Posição na ocupação | Empregado com carteira | 61,7 | 49,0 | 1,26 | 0,05 | sim |
| Posição na ocupação | Conta própria | 17,2 | 21,1 | 0,82 | 0,09 | sim |
| Renda em salários mínimos | Mais de 10 SM | — | 0,8* | — | — | não |
| Renda em salários mínimos | Sem rendimento | 31,7 | 32,9 | 0,96 | 0,04 | não |
| Grupo etário | 25–39 | 35,8 | 32,3 | 1,11 | 0,05 | sim |
| Grupo etário | 5–14 (universo de 5 anos ou mais) | 19,4 | 19,9 | 0,98 | 0,06 | não |
| Sexo | Homens | 52,5 | 50,5 | 1,04 | 0,02 | não |
| Cor ou raça | Branca | 20,8 | 23,0 | 0,90 | 0,07 | não |
| Trabalha em outro município | Sim | 2,0* | 1,4* | 1,42 | 0,54 | não |
| Idade média (anos) | — | 28,2 | 31,3 | 0,90 | 0,02 | sim |
| Renda média do trabalho (R$ jul/2022) | — | 2.725 | 2.734 | 1,00 | 0,04 | não |

Fonte: Elaboração própria a partir dos microdados da amostra do Censo 2022 (IBGE; acesso controlado).

Nota: Razão de seletividade = proporção entre migrantes ÷ proporção entre não migrantes; erro-padrão pelo método delta (bootstrap de domicílios, 200 réplicas), supondo independência entre grupos. * CV 15–30 %; ** CV > 30 %.


<!-- fig: figuras/fig_08_seletividade.png | Figura 8 — Perfil dos migrantes de data fixa (residiam em outro município em 2017) e dos não migrantes, Canaã dos Carajás, 2022: proporção em cada categoria com IC 95 %; diferença em pontos percentuais (n.s. = não significativa a 95 %). Universos: pessoas de 5+ (sexo, idade, cor, naturalidade), 25+ (instrução), ocupados (setor, posição, formalidade). Fonte: Elaboração própria a partir dos microdados da amostra dos Censos Demográficos (IBGE); estimativas aprovadas pelo controle de revelação. -->


### 5.6 Inserção ocupacional e a cadeia produtiva da mineração

A estrutura ocupacional de Canaã foi refeita em duas décadas (Tabela 6, Figura 9). A agropecuária ocupava 55 % dos trabalhadores em 2000, 19 % em 2010 e 3 % em 2022. A extrativa mineral chegou a 7,4 % em 2010 e 10,4 % em 2022, proporção acima da de Parauapebas (7,8 %) e dez vezes a do Pará (1,0 %); a construção, a 12,2 % e 14,1 %; os serviços, de 5,7 % para 25,2 %. A formalização acompanhou: os ocupados com vínculo formal passaram de 7,1 % em 2000 para 41,6 % em 2010 e 60,9 % em 2022, contra 37,1 % no Pará e 59,2 % em Parauapebas, e o trabalho por conta própria caiu de 41 % para 20 %. A renda média do trabalho subiu de R$ 1.949 para R$ 2.732 em reais de 2022 e igualou a de Parauapebas.

**Tabela 6 — Ocupados por setor de atividade e indicadores de inserção, Canaã dos Carajás, Parauapebas e Pará, 2000–2022 (%)**

| Setor | Canaã 2000 | Canaã 2010 | Canaã 2022 | Parauapebas 2000 | Parauapebas 2010 | Parauapebas 2022 | Pará 2000 | Pará 2010 | Pará 2022 |
|---|---|---|---|---|---|---|---|---|---|
| Agropecuária | 55,2 | 19,3 | 3,4 | 14,4 | 5,0 | 2,5 | 28,9 | 26,1 | 14,2 |
| Extrativa mineral | — | 7,4 | 10,4 | 7,2 | 8,9 | 7,8 | 0,9 | 0,9 | 1,0 |
| Ind. de transformação | 4,0* | 4,5* | 6,6 | 9,2 | 5,5 | 6,5 | 11,0 | 6,5 | 6,3 |
| Construção | — | 12,2 | 14,1 | 7,8 | 15,9 | 12,4 | 5,2 | 6,9 | 8,4 |
| Comércio | 10,0 | 14,7 | 14,5 | 19,1 | 17,5 | 18,2 | 17,1 | 18,2 | 18,2 |
| Serviços | 5,7* | 16,4 | 25,2 | 17,9 | 19,6 | 25,1 | 15,2 | 14,9 | 23,2 |
| Adm. pública, educação e saúde | 13,0 | 11,9 | 13,0 | 14,5 | 10,9 | 13,5 | 12,9 | 13,6 | 16,4 |
| Serviços domésticos | 4,2* | 4,6 | 2,9 | 6,5 | 5,0 | 2,7 | 6,9 | 6,5 | 4,9 |
| Outras atividades | 3,4* | 8,9 | 9,8 | 3,1 | 11,7 | 11,3 | 1,9 | 6,5 | 7,4 |
| Outros (categorias fundidas pelo sigilo) | 4,3 | — | — | — | — | — | — | — | — |
| Ocupados com vínculo formal (%) | 7,1 | 41,6 | 60,9 | 28,6 | 57,1 | 59,2 | 18,0 | 31,7 | 37,1 |
| Empregados com carteira (%) | 7,1 | 34,9 | 52,6 | 28,6 | 51,6 | 51,5 | 18,0 | 25,0 | 26,1 |
| Conta própria (%) | 41,1 | 21,4 | 19,9 | 19,1 | 18,0 | 20,8 | 32,0 | 30,4 | 33,6 |
| Taxa de ocupação, 10 anos ou mais (%) | 46,1 | 52,5 | 55,4 | 49,5 | 52,3 | 51,7 | 44,8 | 47,9 | 43,1 |
| Renda média do trabalho (R$ jul/2022) | 1.949 | 2.274 | 2.732 | 2.381 | 2.590 | 2.729 | 1.801 | 1.918 | 2.066 |

Fonte: Elaboração própria a partir dos microdados da amostra dos Censos 2000, 2010 e 2022 (IBGE).

Nota: Setores harmonizados (CNAE-Dom 1.0/2.0 e seção CNAE 2022). Categorias com n insuficiente foram fundidas em 'Outros' pelo controle de revelação. * CV 15–30 %; ** CV > 30 %.


<!-- fig: figuras/fig_09_setores.png | Figura 9 — Ocupados por setor de atividade (CNAE harmonizada), Canaã dos Carajás, Parauapebas e Pará, Censos 2000, 2010 e 2022. Comércio e serviços agrega comércio, serviços, serviços domésticos e outras atividades; cinza: categorias fundidas pelo controle de revelação (Canaã 2000: extrativa + construção). Fonte: Elaboração própria a partir dos microdados da amostra dos Censos Demográficos (IBGE); estimativas aprovadas pelo controle de revelação. -->


A Tabela 12 e a Figura 15 examinam a inserção de migrantes e não migrantes na cadeia produtiva da mineração. Em 2022, 36,0 % dos migrantes de data fixa ocupados estavam na cadeia (extrativa, construção ou transformação), contra 29,1 % dos não migrantes: razão de seletividade de 1,23 (± 0,17), significativa. A diferença se distribui pelos três elos (extrativa 12,0 % contra 9,8 %; construção 16,1 % contra 13,3 %; transformação 7,9 % contra 6,0 %), com razões entre 1,20 e 1,32 que, isoladamente, não são significativas. Os migrantes de data fixa eram 28,6 % dos ocupados em 2022 e 33 % dos ocupados de cada elo da cadeia. Em 2010 a seletividade era maior e concentrada no núcleo: 11,2 % dos migrantes ocupados estavam na extrativa contra 5,4 % dos não migrantes (razão 2,10 ± 0,99), e metade dos trabalhadores da extrativa (51 %) havia chegado ao município nos cinco anos anteriores, contra um terço em 2022. A mão de obra da mina se "localizou" com o tempo, seja porque migrantes das primeiras coortes deixaram de contar como recentes, seja porque a operação do S11D passou a recrutar mais entre residentes. A origem importa: entre os migrantes de outras UFs ou do exterior, 41 % estavam na cadeia, sobretudo pela construção (19,9 %), contra 32 % dos migrantes intraestaduais e 29 % dos não migrantes. O vínculo com a cadeia é máximo entre quem mora no município há um a nove anos (32 a 34 % dos ocupados) e mínimo entre quem mora há dez a dezenove anos (26 %). Os trabalhadores da extrativa são o segmento mais qualificado e mais bem pago da cidade: 86 % têm o ensino médio completo ou mais (contra 62 % nos demais setores), 26 % têm superior completo, e a renda média do trabalho é de R$ 3.782, 45 % acima dos demais setores; a construção, elo em que os migrantes mais entram, paga R$ 2.171.

**Tabela 12 — Inserção de migrantes de data fixa e não migrantes na cadeia produtiva da mineração, Canaã dos Carajás, 2000–2022 (% dos ocupados de cada grupo)**

| Censo | Elo da cadeia | Migrantes (%) | Não migrantes (%) | Razão de seletividade | Diferença (p.p.) | Signif. 95 % | Migrantes no elo (%) |
|---|---|---|---|---|---|---|---|
| 2000 | extrativa mineral (B) | — | — | — | — | — | — |
| 2000 | construção (F) | — | — | — | — | — | — |
| 2000 | transformação (C) | 10,2** | 2,8* | 3,66 ± 3,08 | +7,4 | sim | 43,8 |
| 2000 | cadeia ampliada (B + F + C) (sem extrativa_mineral, construcao) | 10,2** | 7,4* | 1,38 ± 1,08 | +2,8 | não | 22,6 |
| 2010 | extrativa mineral (B) | 11,2* | 5,4* | 2,10 ± 0,99 | +5,9 | sim | 51,2 |
| 2010 | construção (F) | 12,4 | 12,1 | 1,03 ± 0,36 | +0,3 | não | 34,3 |
| 2010 | transformação (C) | 5,0* | 4,2* | 1,19 ± 0,72 | +0,8 | não | 38,0 |
| 2010 | cadeia ampliada (B + F + C) | 28,7 | 21,7 | 1,32 ± 0,34 | +7,0 | sim | 40,2 |
| 2022 | extrativa mineral (B) | 12,0 | 9,8 | 1,22 ± 0,31 | +2,2 | não | 33,0 |
| 2022 | construção (F) | 16,1 | 13,3 | 1,20 ± 0,22 | +2,7 | não | 32,4 |
| 2022 | transformação (C) | 7,9 | 6,0 | 1,32 ± 0,39 | +1,9 | não | 34,6 |
| 2022 | cadeia ampliada (B + F + C) | 36,0 | 29,1 | 1,23 ± 0,17 | +6,8 | sim | 33,1 |

Fonte: Elaboração própria a partir dos microdados da amostra dos Censos 2000, 2010 e 2022 (IBGE).

Nota: Cadeia = extrativa mineral (seção B, inclui atividades de apoio à extração) + construção (F) + indústria de transformação (C); fornecedores de serviços e transporte à mina não são identificáveis no CNAE-Dom, logo a cadeia ampliada é um limite inferior. Migrante = residia em outro município cinco anos antes. Razão = proporção entre migrantes ÷ proporção entre não migrantes (± IC 95 %, método delta). Participação dos migrantes no total de ocupados: 2000: 17,0 %; 2010: 33,6 %; 2022: 28,6 %. * CV 15–30 %; ** CV > 30 %; '—' = célula suprimida pelo controle de revelação.


<!-- fig: figuras/fig_15_cadeia_mineral.png | Figura 15 — Ocupados na cadeia produtiva da mineração (extrativa mineral, construção e indústria de transformação), Canaã dos Carajás. Esquerda: migrantes de data fixa e não migrantes por elo, 2010 e 2022 (IC 95 %; × = razão de seletividade; n.s. = não significativa). Centro: por origem do migrante, 2022. Direita: por tempo de moradia, 2022 (com menos de 1 ano, só a construção é publicável). Fornecedores de serviços e transporte à mina não são identificáveis no CNAE-Dom. Fonte: Elaboração própria a partir dos microdados da amostra dos Censos Demográficos (IBGE); estimativas aprovadas pelo controle de revelação. -->


### 5.7 Condições domiciliares

A infraestrutura domiciliar convergiu (Tabela 7, Figura 10). A água da rede geral atendia 2,4 % dos domicílios em 2000, 29,0 % em 2010 e 67,1 % em 2022; o esgoto por rede ou fossa séptica, 6,9 %, 36,2 % e 78,2 %; a coleta de lixo, 24,9 %, 84,6 % e 93,3 %; a internet, 10,8 % em 2010 e 93,3 % em 2022. Os domicílios adequados nos três serviços passaram de 10,2 % em 2010 para 56,1 % em 2022. Nesses indicadores os domicílios com e sem migrante recente não diferem. A diferença está na forma de morar: o aluguel passou de 4,0 % dos domicílios em 2000 para 25,9 % em 2010 e 31,5 % em 2022, e entre os domicílios com migrante recente chega a 51,1 %, contra 20,4 % nos demais; os domicílios com migrante recente têm mais moradores (3,32 contra 3,05), mais moradores por dormitório (2,01 contra 1,76) e o dobro da proporção com mais de três moradores por dormitório (8,0 % contra 3,8 %). A cessão pelo empregador, que abrigava 16 % dos domicílios com migrante em 2000, caiu para 4 % em 2022: a cidade absorveu a moradia dos trabalhadores por meio do mercado de aluguel, não de alojamentos de empresa.

**Tabela 7 — Condições dos domicílios particulares permanentes, por presença de migrante de data fixa, Canaã dos Carajás, 2000–2022**

| Indicador | 2000 c/ migr. | 2000 s/ migr. | 2010 c/ migr. | 2010 s/ migr. | 2022 c/ migr. | 2022 s/ migr. |
|---|---|---|---|---|---|---|
| Água da rede geral | — | 2,5** | 32,1 | 26,7 | 69,5 | 65,7 |
| Esgoto por rede ou fossa séptica | 10,0** | 5,9* | 38,1 | 34,9 | 76,7 | 79,1 |
| Lixo coletado | 33,3 | 22,4 | 84,1 | 84,9 | 94,4 | 92,6 |
| Energia elétrica | 76,3 | 58,0 | — | 98,4 | — | — |
| Internet no domicílio | — | — | 12,5 | 9,5 | 94,5 | 92,7 |
| Adequado (água + esgoto + lixo) | — | — | 11,6* | 9,2* | 56,6 | 55,8 |
| Alugado | 9,6** | 2,3** | 38,3 | 16,5 | 51,1 | 20,4 |
| Cedido pelo empregador | 16,3* | 4,8* | 3,6** | 2,7** | 4,2* | 3,4 |
| Mais de 3 moradores por dormitório | 8,2** | 10,7* | 11,5 | 5,6* | 8,0 | 3,8 |
| Apartamento | — | — | 4,0* | — | — | — |
| Renda domiciliar per capita média (R$ jul/2022) | 667 | 861 | 1.259 | 1.275 | 1.608 | 1.585 |
| Moradores por domicílio | 4,38 | 4,28 | 3,62 | 3,53 | 3,32 | 3,05 |
| Moradores por dormitório | 2,20 | 2,12 | 2,07 | 1,83 | 2,01 | 1,76 |

Fonte: Elaboração própria a partir dos microdados da amostra dos Censos 2000, 2010 e 2022 (IBGE).

Nota: Valores em % dos domicílios, salvo indicação. 'c/ migr.' = domicílio com ao menos um morador que residia em outro município cinco anos antes; 's/ migr.' = demais domicílios (os totais estão em data/processed/analise/condicoes_domiciliares). Energia não é investigada em 2022; internet só a partir de 2010. * CV 15–30 %; ** CV > 30 %. '—' = célula suprimida.


<!-- fig: figuras/fig_10_domicilios.png | Figura 10 — Condições dos domicílios particulares permanentes de Canaã dos Carajás, 2000–2022, segundo a presença de morador que residia em outro município cinco anos antes (barras: IC 95 %; células suprimidas omitidas). Fonte: Elaboração própria a partir dos microdados da amostra dos Censos Demográficos (IBGE); estimativas aprovadas pelo controle de revelação. -->


### 5.8 Desigualdade intraurbana

A Tabela 8 e a Figura 11 descem à escala do setor censitário da sede (24 setores em 2010, 88 em 2022), com cada setor situado pela distância ao núcleo de 1990 e pelo ano mediano em que seus pixels se tornaram construídos. Em 2010 a rede de esgoto era um privilégio do centro: a cobertura por setor tinha correlação de −0,82 com a distância ao núcleo e de −0,70 com a idade do tecido, com o decil inferior dos setores em 1,7 % e o superior em 64 %. Em 2022 a cobertura média ponderada de esgoto por rede subiu de 27 % para 56 % e o gradiente centro-periferia quase desapareceu (correlação −0,13), mas a dispersão continua alta: um décimo dos setores tem menos de 24 % de cobertura e outro décimo mais de 80 %. A água da rede geral, cuja cobertura média foi de 31 % para 64 %, inverteu o sinal do gradiente: em 2022 os setores mais distantes do núcleo e mais novos são os mais atendidos, porque os loteamentos recentes nascem com rede. A densidade líquida (habitantes por hectare construído) é o indicador mais desigual, com coeficiente de variação de 71 % entre setores em 2022 e correlação negativa com a distância e com a idade do tecido: os setores centrais e antigos são densos, os periféricos e novos, rarefeitos. A proporção de pretos e pardos cresce com a distância ao núcleo (correlação 0,34).

**Tabela 8 — Desigualdade intraurbana entre setores censitários da sede, 2010 e 2022**

| Indicador | Ano | Setores | Média pond. | P10 | P90 | CV (%) | ρ distância | ρ ano urb. |
|---|---|---|---|---|---|---|---|---|
| Água da rede geral (%) | 2010 | 24 | 30,6 | 11,3 | 45,6 | 81 | -0,18 | -0,02 |
| Esgoto rede geral (%) | 2010 | 24 | 27,2 | 1,7 | 64,1 | 75 | -0,82 | -0,70 |
| Lixo coletado (%) | 2010 | 24 | 97,9 | 95,8 | 100,0 | 2 | -0,48 | -0,63 |
| Energia elétrica (%) | 2010 | 24 | 99,9 | 99,5 | 100,0 | 0 | -0,20 | -0,40 |
| Rend. do responsável (R$ de 2010) | 2010 | 24 | 1.229,3 | 869,6 | 1.617,0 | 23 | -0,07 | -0,06 |
| Moradores por domicílio | 2010 | 24 | 3,6 | 3,1 | 3,9 | 8 | 0,42 | 0,40 |
| Densidade líquida (hab./ha construído) | 2010 | 24 | 37,2 | 12,3 | 72,0 | 56 | -0,56 | -0,59 |
| Água da rede geral (%) | 2022 | 85 | 63,8 | 27,6 | 90,8 | 40 | 0,39 | 0,33 |
| Esgoto rede geral (%) | 2022 | 86 | 55,9 | 23,6 | 79,8 | 42 | -0,13 | -0,16 |
| Lixo coletado (%) | 2022 | 87 | 84,8 | 71,4 | 94,7 | 21 | -0,05 | -0,09 |
| Moradores por domicílio | 2022 | 88 | 3,2 | 2,9 | 3,4 | 7 | 0,62 | 0,58 |
| Densidade líquida (hab./ha construído) | 2022 | 88 | 48,7 | 10,3 | 94,4 | 71 | -0,34 | -0,48 |
| Pretos e pardos (%) | 2022 | 87 | 77,3 | 69,0 | 83,4 | 7 | 0,34 | 0,31 |

Fonte: Elaboração própria a partir dos agregados por setor censitário do Universo (IBGE, 2010 e 2022), da série própria de mancha (ano de urbanização) e do núcleo histórico de 1990.

Nota: Setores 'da sede' = setores urbanos cujo construído mapeado pertence majoritariamente à mancha contígua (E3c). CV = coeficiente de variação entre setores; ρ = correlação de Spearman entre setores com a distância ao núcleo de 1990 e com o ano de urbanização; ano de urbanização = mediana do primeiro ano urbano dos pixels do setor. O esgoto de 2010 inclui rede pluvial; o de 2022 só rede geral.


<!-- fig: figuras/fig_11_setores_mapa.png | Figura 11 — Percentual de domicílios com água da rede geral e com esgoto por rede nos setores censitários da sede, 2010 e 2022 (classes fixas de 20 p.p.; ao fundo, a mancha construída de 2026). O esgoto de 2010 inclui rede pluvial. Fonte: IBGE — agregados por setor censitário (2010, 2022). -->


### 5.9 Comparação regional e linha de base de 1991

A Figura 12 e a Tabela 9 comparam Canaã com Parauapebas e com quatro grupos de municípios do Pará em áreas mínimas comparáveis, agrupados pelo porte da CFEM per capita: outros mineradores e não mineradores do Sudeste Paraense e, no restante do estado, mineradores e não mineradores. A imigração de data fixa cai em todos os grupos de comparação entre 2000 e 2022 (de 17 % para 7 % nos outros mineradores do Sudeste Paraense; de 22 % para 15 % em Parauapebas) e dobra em Canaã (14 % para 25 %). A inserção na extrativa vai de 1,5 % para 10,4 % dos ocupados em Canaã e permanece abaixo de 1,5 % em todos os grupos do Sudeste Paraense fora de Parauapebas; a população em domicílio alugado vai de 3 % para 28 %, contra 17 % nos comparáveis; a renda média do trabalho cresce 40 % em Canaã e entre 0 e 16 % nos grupos regionais. A população de Canaã cresceu 606 % entre 2000 e 2022, contra 274 % em Parauapebas e 31 a 39 % nos demais grupos. A diferença-em-diferenças descritiva em relação a Parauapebas entre 2000 e 2022 é de +21,6 pontos percentuais em migrantes de data fixa, +23,1 em ocupados formais, +64,4 em esgoto adequado e +14,3 em domicílios alugados, todas significativas a 95 %; a diferença em renda média do trabalho (+R$ 434) não é.

**Tabela 9 — Canaã dos Carajás e grupos de municípios comparáveis (Áreas Mínimas Comparáveis), 2000–2022**

| Indicador | Grupo | 2000 | 2010 | 2022 |
|---|---|---|---|---|
| Imigrantes de data fixa (%) | Canaã dos Carajás | 14,2 | 28,9 | 25,3 |
| Imigrantes de data fixa (%) | Parauapebas | 22,4 | 25,5 | 14,6 |
| Imigrantes de data fixa (%) | Sudeste Paraense — outros mineradores | 16,7 | 11,0 | 7,3 |
| Imigrantes de data fixa (%) | Sudeste Paraense — não mineradores | 21,0 | 10,5 | 7,2 |
| Imigrantes de data fixa (%) | Pará — mineradores (demais) | 8,5 | 6,5 | 5,8 |
| Imigrantes de data fixa (%) | Pará — não mineradores (demais) | 6,2 | 4,4 | 4,5 |
| Ocupados na extrativa (%) | Canaã dos Carajás | 1,5 | 7,4 | 10,4 |
| Ocupados na extrativa (%) | Parauapebas | 8,5 | 8,9 | 7,7 |
| Ocupados na extrativa (%) | Sudeste Paraense — outros mineradores | 0,5 | 1,2 | 1,2 |
| Ocupados na extrativa (%) | Sudeste Paraense — não mineradores | 0,1 | 0,2 | 0,2 |
| Ocupados na extrativa (%) | Pará — mineradores (demais) | 1,4 | 0,7 | 0,7 |
| Ocupados na extrativa (%) | Pará — não mineradores (demais) | 0,2 | 0,2 | 0,2 |
| Pop. em domicílio sem esgoto adequado (%) | Canaã dos Carajás | 92,9 | 66,1 | 40,3 |
| Pop. em domicílio sem esgoto adequado (%) | Parauapebas | 43,7 | 53,8 | 71,8 |
| Pop. em domicílio sem esgoto adequado (%) | Sudeste Paraense — outros mineradores | 82,1 | 83,3 | 89,0 |
| Pop. em domicílio sem esgoto adequado (%) | Sudeste Paraense — não mineradores | 94,8 | 91,4 | 95,3 |
| Pop. em domicílio sem esgoto adequado (%) | Pará — mineradores (demais) | 52,4 | 61,2 | 74,1 |
| Pop. em domicílio sem esgoto adequado (%) | Pará — não mineradores (demais) | 86,3 | 86,9 | 97,0 |
| Pop. em domicílio alugado (%) | Canaã dos Carajás | 3,2 | 23,1 | 28,0 |
| Pop. em domicílio alugado (%) | Parauapebas | 16,4 | 32,3 | 28,0 |
| Pop. em domicílio alugado (%) | Sudeste Paraense — outros mineradores | 7,7 | 13,8 | 17,2 |
| Pop. em domicílio alugado (%) | Sudeste Paraense — não mineradores | 5,7 | 11,9 | 16,9 |
| Pop. em domicílio alugado (%) | Pará — mineradores (demais) | 6,4 | 10,3 | 13,7 |
| Pop. em domicílio alugado (%) | Pará — não mineradores (demais) | 2,2 | 3,6 | 5,2 |
| Renda média do trabalho (R$ 2022) | Canaã dos Carajás | 1.949 | 2.274 | 2.734 |
| Renda média do trabalho (R$ 2022) | Parauapebas | 2.381 | 2.590 | 2.732 |
| Renda média do trabalho (R$ 2022) | Sudeste Paraense — outros mineradores | 1.788 | 1.903 | 2.079 |
| Renda média do trabalho (R$ 2022) | Sudeste Paraense — não mineradores | 1.826 | 2.033 | 1.786 |
| Renda média do trabalho (R$ 2022) | Pará — mineradores (demais) | 1.870 | 1.997 | 2.133 |
| Renda média do trabalho (R$ 2022) | Pará — não mineradores (demais) | 1.156 | 1.128 | 1.341 |
| População (var. % vs 2000) | Canaã dos Carajás | 0 | 145 | 606 |
| População (var. % vs 2000) | Parauapebas | 0 | 115 | 274 |
| População (var. % vs 2000) | Sudeste Paraense — outros mineradores | 0 | 31 | 31 |
| População (var. % vs 2000) | Sudeste Paraense — não mineradores | 0 | 39 | 37 |
| População (var. % vs 2000) | Pará — mineradores (demais) | 0 | 16 | 22 |
| População (var. % vs 2000) | Pará — não mineradores (demais) | 0 | 26 | 39 |

Fonte: Painel municipal 2000–2022 do projeto irmão migracoes-mineracao (microdados da amostra dos Censos; CFEM/ANM), médias ponderadas pela população.

Nota: Grupos por porte de CFEM per capita (lib.mineracao do projeto irmão). Municípios por grupo em 2022: Canaã dos Carajás: 1; Parauapebas: 1; Sudeste Paraense — outros mineradores: 29; Sudeste Paraense — não mineradores: 8; Pará — mineradores (demais): 54; Pará — não mineradores (demais): 50. Sudeste Paraense = mesorregião IBGE 1506 (39 municípios).


<!-- fig: figuras/fig_12_comparacao_regional.png | Figura 12 — Canaã dos Carajás, Parauapebas e grupos de municípios do Pará (Áreas Mínimas Comparáveis 2000–2022, médias ponderadas pela população; grupos por porte de CFEM per capita), Censos 2000, 2010 e 2022. Fonte: Painel municipal 2000–2022 do projeto irmão migracoes-mineracao (microdados da amostra dos Censos; ANM). -->


A Tabela 10 e a Figura 14 fecham o arco com a linha de base de 1991. Parauapebas, que então incluía o atual Canaã, era uma sociedade de fronteira: 43 % da população havia chegado nos cinco anos anteriores, 35 % dos ocupados estavam na agropecuária e 11 % na extrativa (a mina de ferro de Carajás já operava), 78 % dos adultos não tinham o fundamental completo, 21 % dos domicílios tinham água da rede e 62 % energia elétrica, e 44 % da população tinha menos de 15 anos. Canaã em 2000 era mais rural e mais pobre que essa média (55 % na agropecuária, 2,4 % com água da rede, 7 % de ocupados formais). Em 2022 a cidade tem 61 % de ocupados formais, 13 % de adultos com superior completo, 67 % de domicílios com água da rede e 93 % com lixo coletado. A mancha da sede em 1990 e 1991 media 46 e 62 ha.

**Tabela 10 — Linha de base pré-mineral: Parauapebas em 1991 (inclui o atual Canaã dos Carajás) e Canaã em 2000 e 2022**

| Indicador | Parauapebas 1991 (inclui Canaã) | Pará 1991 | Canaã 2000 | Canaã 2022 | Canaã sede 2022 |
|---|---|---|---|---|---|
| Migrantes de data fixa (%) | 42,9 | 12,5 | 16,1 | 27,8 | 29,2 |
| Naturais do município (%) | 18,7 | 67,7 | 28,5 | 24,7 | 24,0 |
| Naturais de outra UF (%) | 68,2 | 17,8 | 62,5 | — | — |
| Sem instrução / fund. incompleto, 25+ (%) | 78,3 | 77,5 | 86,0 | 27,8 | 24,8 |
| Superior completo, 25+ (%) | 1,8* | 2,8 | — | 12,9 | — |
| Taxa de ocupação 10+ (%) | 45,4 | 43,1 | 46,1 | 55,4 | 57,1 |
| Ocupados na agropecuária (%) | 34,7 | 35,0 | 55,2 | 3,4 | 1,2* |
| Ocupados na extrativa mineral (%) | 10,6 | 2,5 | — | 10,4 | — |
| Ocupados na construção (%) | 8,3 | 4,9 | — | 14,1 | — |
| Ocupados nos serviços (%) | 14,5 | 15,0 | 5,7* | 25,2 | 25,7 |
| Ocupados formais (%) | 35,9 | 29,4 | 7,1 | 60,9 | 62,5 |
| Domicílios com água da rede (%) | 20,7 | 40,0 | 2,4** | 67,1 | 71,9 |
| Esgoto adequado (%) | 22,8 | 29,2 | 6,9* | 78,2 | 81,5 |
| Lixo coletado (%) | 50,5 | 32,9 | 24,9 | 93,3 | 98,7 |
| Energia elétrica (%) | 62,1 | 66,1 | 62,2 | — | — |
| Domicílios alugados (%) | 10,9 | 8,9 | 4,0* | 31,5 | 34,4 |
| Mais de 3 moradores/dormitório (%) | 15,1 | 27,8 | 10,1 | 5,3 | — |
| População de 0–14 anos (%) | 43,7 | 42,9 | 36,7 | 27,2 | 26,8 |
| Homens (%) | 52,0 | 50,3 | 53,8 | 51,1 | 51,2 |
| Idade média (anos) | 20,6 | 22,2 | 24,0 | 27,8 | 27,5 |
| Moradores por domicílio | 4,8 | 5,2 | 4,3 | 3,1 | 3,2 |

Fonte: Elaboração própria a partir dos microdados da amostra dos Censos 1991, 2000 e 2022 (IBGE).

Nota: Em 1991 Canaã era localidade de Parauapebas: o perfil é de um superconjunto, não de um proxy externo. Renda de 1991 não é comparável (moeda pré-Real). '—' = célula suprimida ou não investigada. * CV 15–30 %; ** CV > 30 %.


<!-- fig: figuras/fig_14_baseline_1991.png | Figura 14 — Indicadores selecionados para Parauapebas em 1991 (município que então incluía o atual Canaã dos Carajás), Canaã em 2000 e Canaã em 2022 (IC 95 %). Células suprimidas pelo controle de revelação omitidas. Fonte: Elaboração própria a partir dos microdados da amostra dos Censos Demográficos (IBGE); estimativas aprovadas pelo controle de revelação. -->


### 5.10 Mineração, economia e o ritmo da cidade

A Tabela 11 e a Figura 13 relacionam o ritmo da expansão urbana com a economia mineral. O PIB municipal a preços correntes foi de R$ 70 milhões em 2002 para R$ 2,1 bilhões em 2010, R$ 10,7 bilhões em 2019 e R$ 35,0 bilhões em 2021, quando a participação de Canaã no PIB do Pará chegou a 13,3 %, recuando para 6,5 % em 2023 com a queda do preço do minério; o valor adicionado da indústria responde por 80 a 90 % do total desde 2010. A CFEM distribuída ao município ficou entre R$ 3 e 26 milhões anuais de 2004 a 2016 e saltou para R$ 178 milhões em 2018, R$ 676 milhões em 2020 e R$ 1,1 bilhão em 2021, em valores correntes; per capita, em reais de 2022, foram R$ 31 mil por habitante em 2021 (sobre a população estimada, subestimada). O emprego assalariado registrado no Cadastro Central de Empresas cresceu de 1,5 mil em 2007 para 8,0 mil em 2021.

**Tabela 11 — Indicadores econômicos de Canaã dos Carajás e área construída da sede, 2002–2023**

| Ano | População (IBGE) | PIB (R$ mi correntes) | PIB per capita (R$ correntes) | VA indústria (%) | VA adm. pública (%) | Part. no PIB do Pará (%) | CFEM (R$ mi correntes) | CFEM per capita (R$ jul/2022) | Assalariados CEMPRE | Área da sede (ha) |
|---|---|---|---|---|---|---|---|---|---|---|
| 2002 | 11.761 | 70 | 5.940 | 38,3 | 17,9 | 0,26 | — | — | — | 224 |
| 2004 | 13.035 | 465 | 35.681 | 72,9 | 4,5 | 1,25 | 3,5 | 734 | — | 504 |
| 2007 | 23.757 | 635 | 26.726 | 65,9 | 7,5 | 1,22 | 15,6 | 1.578 | 1.522 | 745 |
| 2010 | 26.716 | 2.120 | 79.357 | 81,3 | 3,5 | 2,56 | 16,7 | 1.286 | 3.251 | 1.076 |
| 2013 | 31.062 | 3.483 | 112.146 | 80,2 | 4,1 | 2,87 | 25,8 | 1.434 | 5.674 | 1.647 |
| 2016 | 34.853 | 2.396 | 68.750 | 59,2 | 13,0 | 1,73 | 19,4 | 757 | 7.048 | 2.397 |
| 2019 | 37.085 | 10.705 | 288.658 | 81,2 | 2,9 | 6,00 | 413,5 | 13.685 | 5.841 | 2.508 |
| 2021 | 39.103 | 34.988 | 894.763 | 89,6 | 1,2 | 13,31 | 1.114,1 | 31.359 | 8.030 | 2.597 |
| 2022 | 77.079 | 16.062 | 208.381 | — | — | 6,80 | 759,0 | 9.847 | — | 2.644 |
| 2023 | — | 16.622 | — | — | — | 6,53 | 445,7 | — | — | 2.773 |

Fonte: IBGE (PIB dos Municípios, t/5938; CEMPRE, t/6449; Estimativas de população); ANM (CFEM distribuída); série própria de mancha (E3b/E3c).

Nota: PIB e VA a preços correntes (VA setorial ainda não divulgado para 2022–2023); CFEM per capita deflacionada pelo IPCA de julho (jul/2022 = 100) e dividida pela população estimada do ano (subestimada em 2011–2021). CEMPRE disponível de 2006 a 2021; o pessoal da seção B (extrativa) é suprimido pelo IBGE por haver poucas unidades locais.


<!-- fig: figuras/fig_13_economia.png | Figura 13 — Área acrescida anualmente à sede (alto), CFEM distribuída ao município em R$ de julho de 2022 (meio) e PIB per capita a preços correntes (baixo), 2002–2026. Janelas sombreadas: construção das minas. Fonte: Elaboração própria: série própria Landsat/Sentinel-2 (30 m), validada com CBERS; população IBGE. ANM (CFEM); IBGE (PIB dos Municípios, estimativas de população); IPCA para o deflacionamento. -->


O que a Figura 13 torna visível é o descompasso entre os dois ciclos. O acréscimo anual de área construída concentra-se nas fases de obra (2002–2004 e 2013–2016) e no período pós-2022, quando a CFEM já é abundante; a CFEM, por sua vez, só se torna relevante a partir de 2018, dois anos depois do S11D entrar em operação. A correlação entre a CFEM em reais de 2022 e o acréscimo de área no mesmo ano é de −0,20 e permanece nula com defasagens de um e dois anos, tornando-se levemente positiva (+0,24) com três anos de defasagem. A cidade cresce nas obras; os royalties chegam depois.

## 6 Discussão

Os resultados dialogam com três debates. O primeiro é o da urbanização extensiva e da "não-cidade" de Carajás (MELO; CARDOSO, 2016; SANTOS, 2021; CARDOSO ET AL., 2017). A série de mancha mostra que Canaã tem, sim, uma cidade contígua, compacta em 2010 (índice de proximidade 0,78) e cada vez mais fragmentada depois de 2022, e que a expansão espacial foi comandada pelo calendário das obras, não pelo dos royalties. Essa sequência é a marca das cidades de grandes projetos: a fase de construção mobiliza contingentes de trabalhadores que a operação não absorve (MOURA ET AL., 2005; FARIAS, 2008; GODINHO, 2021), e a cidade que se forma para abrigá-los permanece depois que a obra termina. O padrão de espraiamento nos anos 2000 e adensamento nos anos 2010 sugere que a segunda onda, do S11D, foi absorvida em boa parte por uma cidade já traçada nos loteamentos abertos durante e depois do Sossego; o novo salto de área pós-2022, com a forma menos compacta, indica que a terceira fase, financiada pela CFEM e por um mercado imobiliário aquecido, reabre o espraiamento, na direção dos condomínios e loteamentos periféricos que Corrêa (2026) descreve.

O segundo debate é o da migração. A literatura afirmava o afluxo e a "cidade do imigrante" (SANCHES ET AL., 2025; MATLABA ET AL., 2019); os microdados o quantificam e o qualificam. A imigração de data fixa de Canaã dobrou entre 2000 e 2022 enquanto caía em todos os municípios comparáveis, e as coortes de chegada se alinham aos ciclos de investimento com precisão de poucos anos. Os migrantes recentes são positivamente selecionados em escolaridade e formalidade, o que contradiz a imagem de uma fronteira que atrai sobretudo mão de obra desqualificada, mas não obtêm prêmio salarial, e sua inserção na cadeia da mineração é maior que a dos residentes antigos por uma margem modesta (razão 1,23) e decrescente no tempo: em 2010 a mão de obra da extrativa era metade migrante recente, em 2022 um terço. Isso é consistente com a exigência de contratação local descrita por Moura et al. (2005) e com a formação, ao longo de duas décadas, de um mercado de trabalho local qualificado para a mina. A cadeia, entretanto, recruta migrantes de longa distância sobretudo pela construção, o elo mais precário e mais bem representado entre os migrantes de outras UFs, e a análise não alcança os fornecedores em serviços e transporte, de modo que a inserção total na economia mineral é subestimada.

O terceiro debate é o da moradia e da desigualdade. Castriota (2024) descreveu, em campo, as formas de morar criadas pelos migrantes do S11D; os censos mostram a escala: metade dos domicílios com migrante recente é alugada, o dobro da proporção dos demais, e a cessão pelo empregador, típica das company towns (RODRIGUES, 2001; JUAREZ, 2021), desapareceu. Canaã não é uma company town: é uma cidade de mercado, em que a empresa terceiriza a moradia ao aluguel. A convergência da infraestrutura entre 2000 e 2022 é real e, em parte, produto da CFEM aplicada em saneamento; mas a desigualdade entre setores persiste na forma de tecidos recentes com baixa cobertura de esgoto e alta rarefação, e de uma composição racial que se torna mais preta e parda à medida que se afasta do centro. A literatura sobre a CFEM (PINHEIRO, 2016; CAITANO; MORALES, 2022; ASSUNCAO, 2022) discute se os royalties são bem aplicados; os dados sugerem que a questão relevante é temporal: a cidade que precisava de infraestrutura cresceu antes que os royalties existissem, e os royalties chegaram a uma cidade que já estava construída.

## 7 Conclusão

Este artigo mediu a urbanização de Canaã dos Carajás com uma série anual de mancha urbana validada, microdados censitários harmonizados de quatro censos e agregados por setor, sob um único desenho analítico e com controle de revelação. A sede cresceu de 46 ha em 1990 para cerca de 3.200 ha em 2026, com o maior ritmo entre as duas minas; a elasticidade entre área e população inverteu-se entre as décadas; seis em cada dez moradores não naturais chegaram a partir de 2013; os migrantes recentes são mais escolarizados, mais formais, mais presentes na cadeia da mineração e muito mais frequentemente inquilinos, com a mesma renda dos residentes antigos; a infraestrutura convergiu enquanto o gradiente centro-periferia persiste nos tecidos novos; e a cidade cresceu no ritmo das obras, antes que os royalties existissem.

Três extensões são possíveis com os mesmos dados. A primeira é a reconstituição completa da trajetória populacional entre 1982 e 2000, com leitura do Plano Diretor de 2007 e dos registros administrativos da década de 1990, que este artigo apresentou apenas como faixa. A segunda é a atualização da série de mancha em 10 m com Sentinel-2 e a validação da franja pós-2022 com imagens CBERS-4A, para confirmar o salto de 2023–2026. A terceira é a identificação dos fornecedores da mina no setor de serviços, com dados administrativos de emprego formal, para medir a cadeia produtiva completa. Todos os dados públicos, o código e as figuras deste artigo estão disponíveis no repositório do projeto e no dashboard interativo que o acompanha; os microdados de acesso controlado não são redistribuídos, e toda estimativa publicada passou pelo controle de revelação descrito na seção 4.3.

## Disponibilidade de dados e código

Os agregados publicados (estimativas aprovadas pelo controle de revelação, série da mancha urbana, indicadores por setor), o código do pipeline e do painel interativo e este artigo estão em https://canaa-urbana.github.io e no repositório https://github.com/canaa-urbana/canaa-urbana.github.io, arquivado no Zenodo (DOI: https://doi.org/10.5281/zenodo.22699960; versão 1.0.0: https://doi.org/10.5281/zenodo.22699961), com código sob licença MIT e dados e textos sob CC BY 4.0. Os microdados dos Censos Demográficos não são redistribuídos; os de 2022 são de acesso controlado do IBGE.

## Declaração de uso de inteligência artificial

Este artigo foi produzido com assistência de inteligência artificial (Claude, Anthropic), sob supervisão integral do autor. A ferramenta foi utilizada nas seguintes etapas: (i) extração e harmonização programática dos microdados dos quatro censos a partir dos layouts oficiais do IBGE; (ii) cálculo das estatísticas descritivas, erros-padrão por bootstrap, razões de seletividade e elasticidades apresentados; (iii) construção do pipeline de sensoriamento remoto (composições anuais, classificação por Random Forest, pós-processamento e estimadores de área com correção por matriz de erro), com a fotointerpretação dos pontos de validação conduzida com apoio da ferramenta e conferida pelo autor; (iv) implementação e verificação independente das regras de controle de revelação; (v) busca e verificação de referências bibliográficas em fontes primárias (Crossref, DataCite, BDTD, Catálogo de Teses da CAPES, repositórios institucionais); (vi) geração das figuras e tabelas; (vii) redação de versões preliminares do texto a partir dos resultados computados.

São de responsabilidade exclusiva do autor: o desenho da pesquisa e das perguntas de investigação, todas as decisões metodológicas (definição das geografias e dos períodos de chegada, escolha do deflator, do limiar de classificação fixado a priori, das épocas de validação, dos limiares de revelação e da definição da cadeia produtiva da mineração), a interpretação dos resultados, a verificação final de cada referência citada em sua fonte primária, e a revisão e aprovação do texto final. O autor reafirma a responsabilidade integral pelo conteúdo científico deste artigo, incluindo eventuais erros remanescentes.

## Referências

ALMEIDA, Raphael Villela. Mineração e a reorganização do território em Canaã dos Carajás. 2017. Dissertação (Mestrado em População, território e estatísticas públicas) – Escola nacional de ciências estatísticas, 2017.

AMARAL, Anderson Vasconcellos. As paisagens de Canaã dos Carajás (PA): análise e evolução da paisagem na fronteira agropecuária e minerária. 2021. Dissertação (Mestrado em Geografia (geografia física)) – Universidade de são paulo, 2021.

ARAÚJO, Flávio Lacerda de. Sina de vagão: uma análise da dependência econômico-financeira nos municípios com matriz econômica de base mineral. 2023. Dissertação (Mestrado em Gestão Pública) – Universidade federal do Pará, 2023.

ASSUNCAO, Marcos Venancio Silva. O fundo municipal de desenvolvimento sustentável de Canaã dos Carajás: Uma análise comparativa com fundos de royalties subnacionais à luz do princípio do desenvolvimento sustentável e da justiça intergeracional. 2022. Dissertação (Mestrado em Direito, Políticas Públicas e Desenvolvimento Regional) – Centro universitário do estado do Pará, 2022.

BRINGEL, Fabiano de Oliveira; MACHADO, Brena Regina Lopes. Processos de migração e relação campo-cidade no entorno do Complexo Mínero-Industrial de Barcarena (PA). Revista Campo-Território, v. 15, n. 39 Dez., p. 391-420, 2020. DOI: 10.14393/rct153921.

CABRAL, Eugênia Rosa; ENRÍQUEZ, Maria Amélia Rodrigues da Silva; SANTOS, Dalva Vasconcelos dos. Canaã dos Carajás - do leite ao cobre: transformações estruturais do município após a implantação de uma grande mina. In: Recursos minerais & sustentabilidade territorial. v. 1: Grandes minas, p. 39-68, 2011.

CAITANO, Thamires Beatriz dos Santos; MORALES, Gundisalvo Piratoba. Potencial dos royalties minerais na promoção do desenvolvimento socioeconômico de municípios do estado do Pará, Brasil. Revista Brasileira de Gestão e Desenvolvimento Regional, v. 18, n. 3, 2022. DOI: 10.54399/rbgdr.v18i3.5861.

CARDOSO, Ana Cláudia Duarte; CÂNDIDO, Lucas Souto; MELO, Ana Carolina Campos de. Canaã dos Carajás: um laboratório sobre as circunstâncias da urbanização, na periferia global e no alvorecer do século XXI. Revista Brasileira de Estudos Urbanos e Regionais, v. 20, n. 1, p. 121, 2017. DOI: 10.22296/2317-1529.2018v20n1p121.

CARMO, Ednalva Lima. A CIDADE NA FRONTEIRA DA AMAZÔNIA: Mineração e produção do espaço em Canaã dos Carajás – Pará. 2023. Dissertação (Mestrado em Dinâmicas Territoriais e Sociedade na Amazônia) – Universidade federal do sul e sudeste do Pará, 2023.

CARMO, Ednalva Lima. Mineração e a produção do espaço urbano em Canaã dos Carajás-Pará. Revista Tocantinense de Geografia, v. 12, n. 28, p. 139-153, 2023. DOI: 10.20873/rtg.v12i28.16834.

CASTRIOTA, Rodrigo. HOUSING BEYOND THE METROPOLIS : Inhabiting Extractivism and Extensions in Urban Amazonia. International Journal of Urban and Regional Research, v. 48, n. 1, p. 32-52, 2024. DOI: 10.1111/1468-2427.13222.

CASTRIOTA, Rodrigo. “Aqui a vale é o Estado”: neoextrativismo e autoritarismo na cidade, no campo e na floresta na região de Carajás. Revista Brasileira de Estudos Urbanos e Regionais, v. 26, n. 1, 2024. DOI: 10.22296/2317-1529.rbeur.202408.

CASTRO, Antônio Orlando de; PALHETA, João Márcio. Circulação, transporte e logística na organização e gestão do território em Canaã dos Carajás. Confins, v. 68, 2025. DOI: 10.4000/14nli.

CHAGAS, Erika da Silva; SANTOS, Marcos Antônio Souza dos; MELLO, Andréa Hentz de. Dinâmica espaço-temporal da agropecuária em município com economia de base mineral na Amazônia brasileira. Geofronter, v. 10, p. e8311, 2024. DOI: 10.61389/geofronter.v10.8311.

CIRNE, Mariana Barbosa; GIACOMAZZI, Diego Busnello. Ferro Carajás s11d: participação social e processo dialético no licenciamento ambiental de mineração em Unidade de Conservação. Direito Ambiental e Sociedade, v. 11, n. 3, p. 277-295, 2021. DOI: 10.18226/22370021.v11.n3.13.

CORRÊA, Isabella Santos; SANTANA, Joana Valente; SANTOS, Laira Vasconcelos dos et al. Política de regularização fundiária urbana de interesse social no estado do Pará (2009-2018). O social em questão, v. 4, n. 53, 2022. DOI: 10.17771/pucrio.osq.58533.

CORRÊA, Leonardo Pantoja. DO ENCLAVE RESIDENCIAL ÀS CIDADES FRAGMENTADAS: Produção de Espaços Residenciais Fechados em Canaã dos Carajás, Marabá e Parauapebas, Pará. California Digital Library, 2026. DOI: 10.48321/d1ca512bdb.

CORTEZ, Hilquias Miranda; SÁ, Samy Cardoso; PEREIRA JÚNIOR, Antônio. Quantificação do desflorestamento no município de Canaã dos Carajás com o uso de geotecnologia em análise multitemporal. In: As multiplas visões do meio ambiente e os impactos ambientais, p. 12-32, 2019. DOI: 10.4322/978-85-455202-1-4-02.

COSTA, Silvana Dunham da. Mineworkers' quality of life in remote communities : a multiple case study in the Brazilian Amazon. 2008. DOI: 10.14288/1.0066394.

CRUZ, Thiago Martins da. Avanço da mineração e a resistência camponesa em Canaã dos Carajás. Caderno Eletrônico de Ciências Sociais, v. 5, n. 1, p. 94-114, 2017. DOI: 10.24305/cadecs.v5i1.2017.17773.

CRUZ, Thiago Leite; MATLABA, Valente José; MOTA, José Aroudo et al. Measuring the social license to operate of the mining industry in an Amazonian town: A case study of Canaã dos Carajás, Brazil. Resources Policy, v. 74, p. 101892, 2021. DOI: 10.1016/j.resourpol.2020.101892.

CRUZ, Leonardo de Oliveira. Migração e ocupações de maranhenses no sudeste do Pará: um estudo de caso a partir da moderna mineração em Parauapebas. 2022. Tese (Doutorado em Ciências sociais) – Universidade estadual paulista júlio de mesquita filho ( marília ), 2022.

DIAS, Anderson Saldanha. Os incentivos fiscais federais ao setor de mineração e sua contribuição para o desenvolvimento da Amazônia: o caso da Vale s11d em Canaã dos Carajás. 2025. Dissertação (Mestrado) – UFPA, 2025.

EMILIO, Mauro Emilio Costa Silva; JOÃO, Silvia Regina. A cidade da Vale s.a? Parauapebas, entre expansão urbana e periférica e a psicosfera da grande coorporação mineral the city of Vale s.a? Parauapebas, between urban and peripheral expansion and the psychosphere of the great mineral coorporation la ciudad de Vale s.a? Parauapebas, entre la expansión urbana y periférica y la psicosfera de la gran coorporación minera. Espaço em Revista, v. 27, n. 1, p. 342-365, 2025. DOI: 10.70261/er.v27i1.74892.

FARIAS, André Luis Assunção. Mineração, subcontração e desenvolvimento em paraubebpas e canaa dpos Carajás: Possibilidades e limites para a região sudeste do Pará. 2008. Tese (Doutorado em Desenvolvimento sustentável do trópico úmido) – Universidade federal do Pará, 2008.

FERNANDES, Patrícia Capanema Álvares. Natureza, infraestrutura, mineração e urbanização: cartografando interseções históricas na região de Carajás. In: Amazônia:, p. 93-114, 2023. DOI: 10.4322/978-85-7143-217-8.cap06.

FERREIRA, Rita de Kássia Pinheiro; BRINGEL, Fabiano de Oliveira. “Sobrevivendo ao Inferno”: mineração e luta pela terra em Canaã dos Carajás (PA) – o caso do Acampamento Oziel Alves do MST “Surviving Hell”: mining and the struggle for land in Canaã dos Carajás (PA) – the case of the MST Oziel Alves Camp “Sobreviviendo al infierno”: la minería y la lucha por la tierra en Canaã dos Carajás (PA) – el caso del Campamento Oziel Alves del MST. Revista da ANPEGE, v. 21, n. 45, 2025. DOI: 10.5418/ra2025.v21i45.19622.

FURTADO, Ana Maria Medeiros; PONTE, F.. Ocupação e impactos decorrentes da expansão urbana da cidade de Parauapebas, estado do Pará. Revista do Instituto Histórico e Geográfico do Pará, v. 1, n. 1, p. 123-134, 2014. DOI: 10.17553/2359-0831/ihgp.n1v1p123-134.

FURTADO, Layse Gomes; BRAGA PEREIRA, Carla; SILVA, Davi Farias da et al. Detecção de Mudanças do Uso e Cobertura do Solo no Município de Canaã dos Carajás, Pará. Revista Verde Grande: Geografia e Interdisciplinaridade, v. 5, n. 02, p. 116-131, 2023. DOI: 10.46551/rvg2675239520232116131.

GODINHO, A.P.. Fast urbanization and the commodities global market – The example of Parauapebas - Brazil. In: Research Tracks in Urbanism: Dynamics, Planning and Design in Contemporary Urban Territories, p. 35-41, 2021. DOI: 10.1201/9781003220855-5.

JUAREZ, Rodson. O espaço urbano como efeito do fordismo na Amazônia: O caso de Serra do Navio/AP / Urban space as an amazon fordism effect: Serra do Navio/Ap (Brazil) case. Brazilian Journal of Development, v. 7, n. 8, p. 76237-76254, 2021. DOI: 10.34117/bjdv7n8-036.

MACCHIAVELLO FERRADAS, Fiorella; CARVALHO DE CARVALHO, Larissa; REGINA GALVÃO, Lilyan. A urbanização como processo na implantação de grandes empreendimentos: Um olhar sobre fordlândia, porto de pecém e Carajás urbanization as a process in implementation of great enterprises: A look at fordlândia, port de pecém and Carajás. Revista Espaço e Geografia, v. 21, n. 2, 2022. DOI: 10.26512/2236-56562018e40198.

MACÊDO, Olinda; FREITAS, Felipe Bonfim; REIS, Raimundo Macedo dos et al. Prevalence and epidemiological characteristics of human immunodeficiency virus-1 infection in an iron mining area with intense migratory flow in Pará State, Brazilian amazon, 2005–2014. Brazilian Journal of Microbiology, v. 51, n. 4, p. 1737-1745, 2020. DOI: 10.1007/s42770-020-00361-7.

MATLABA, Valente José; MOTA, José Aroudo; MANESCHY, Maria Cristina et al. Social perception at the onset of a mining development in Eastern Amazonia, Brazil. Resources Policy, v. 54, p. 157-166, 2017. DOI: 10.1016/j.resourpol.2017.09.012.

MATLABA, Valente José; MANESCHY, Maria Cristina; FILIPE DOS SANTOS, Jorge et al. Socioeconomic dynamics of a mining town in Amazon: a case study from Canaã dos Carajás, Brazil. Mineral Economics, v. 32, n. 1, p. 75-90, 2019. DOI: 10.1007/s13563-018-0159-6.

MATLABA, Valente José; PEREIRA, Lorena Reis; MOTA, José Aroudo et al. Resilience Perception of a Mining Town in Eastern Amazonia: A Case Study of Canaã Dos Carajás, Brazil. Environmental Management, v. 67, n. 4, p. 698-716, 2021. DOI: 10.1007/s00267-020-01405-2.

MATLABA, Valente José; SANTOS, Jorge Filipe dos; MOTA, José Aroudo et al. Local social perception of mining in Parauapebas and Canaã dos Carajás in the eastern Amazonia, Brazil. Resources Policy, v. 96, p. 105237, 2024. DOI: 10.1016/j.resourpol.2024.105237.

MATOS, Aliny Soan de Jesus; GARCIA, Caísa Costa; PENA, Heriberto Wagner Amanajás. Estruturas economicas da região sudeste do estado do Pará, Amazônia-Brasil. Uma abordagem produtiva do municipio de Canaã dos Carajás. Observatório de la economía latinoamericana, 2014.

MEDEIROS, L.F.. Dinâmicas Territoriais e Produção do Espaço no Município de Canaã dos Carajás Antes e Depois da Chegada da Mineração. Boletim Amazônico de Geografia, v. 3, n. 5, p. 112-130, 2016. DOI: 10.17552/2358-7040/bag.v3n5p112-130.

MELO, Ana Carolina Campos de; CARDOSO, Ana Cláudia Duarte. O papel da grande mineração e sua interação com a dinâmica urbana em uma região de fronteira na Amazônia. Nova Economia, v. 26, n. spe, p. 1211-1243, 2016. DOI: 10.1590/0103-6351/3963.

MELO, Ana Carolina Campos de. O invisível em movimento um estudo sobre o urbano e suas possibilidades no Sudeste Paraense. 2020. Tese (Doutorado em Economia) – Universidade federal do Pará, 2020.

MIRANDA, Rogério Rego; GOMES, Lucas Ferreira. TERRITORIALIZAÇÃO CAMPONESA NO SUDESTE PARAENSE A PARTIR DOS ACAMPAMENTOS: o caso de Canaã dos Carajás-Pará. LA Referencia (Red Federada de Repositorios Institucionales de Publicaciones Científicas), 2023. DOI: 10.12957/geouerj.2023.73213.

MONTE-CARDOSO, Daniel. Mineração e subdesenvolvimento : impactos da atividade mineradora nos municípios de Canaã dos Carajás, Marabá e Parauapebas (2004 - 2015). 2018. Dissertação (Mestrado em Desenvolvimento econômico) – Universidade estadual de campinas, 2018.

MONTEIRO, Aline Cecília de Oliveira; GALLARDO, Nuria Pérez. Variações do índice de calor ao longo de duas décadas: Evidências em Canaã dos Carajás e suas implicações climáticas. Revista Políticas Públicas & Cidades, v. 14, n. 10, p. e3068, 2025. DOI: 10.23900/2359-1552v14n10-56-2025.

MORAES, Thiago Moraes de. COMPENSAÇÃO FINANCEIRA PELA EXPLORAÇÃO MINERAL NOS MUNICÍPIOS DO ESTADO DO PARÁ: uma proposta de instrumentalização do controle social sob uma visão sistêmica. 2023. Dissertação (Mestrado em Gestão Pública) – Universidade federal do Pará, 2023.

MOURA, Alexandro; NUNES, Jareston; MENEZES, João et al. Mina de cobre do Sossego da companhia Vale do rio doce - emprego e desenvolvimento para o Pará. Divisas para o Brasil. In: ABM Proceedings, p. 36-39, 2005. DOI: 10.5151/5463-5463-0010.

NASCIMENTO, Marcus Vinicius Brito. A dinâmica das áreas verdes em Canaã dos Carajás e 11 suas repercussões no espaço urbano. 2024. Dissertação (Mestrado em Planejamento e desenvolvimento regional e urbano na Amazônia) – Universidade federal do sul e sudeste do Pará, 2024.

NASCIMENTO NETO, Pedro Luiz do. Emancipação e crescimento de Canaã dos Carajás-PA: uma abordagem para o ensino de história local. Gnosis Carajás, v. 1, n. 2, p. e21008, 2021. DOI: 10.55723/gc.v1i2.14.

OLIVEIRA, Antonia Larissa Alves. CFEM e o desenvolvimento socioeconômico na Amazônia: uma análise dos municípios de Canaã dos Carajás (PA), Marabá (PA) e Parauapebas (PA). 2021. Dissertação (Mestrado em Planejamento e desenvolvimento regional e urbano na Amazônia) – Universidade federal do sul e sudeste do Pará, 2021.

OLOFSSON, Pontus; FOODY, Giles M.; HEROLD, Martin et al. Good practices for estimating area and assessing accuracy of land change. Remote Sensing of Environment, v. 148, p. 42–57, 2014. DOI: 10.1016/j.rse.2014.02.015.

PADILHA, Simone Cristina Contente. Estado, território e mineração no Brasil: o caso do Projeto S11D/Vale em Canaã dos Carajás-Pa. 2020. Tese (Doutorado em Ciências sociais em desenvolvimento, agricultura e sociedade) – Universidade federal rural do Rio de Janeiro, 2020.

PEREIRA, Raimundo Miguel dos Reis. Migração e desterritorialização: Sociabilidade afetada e exclusão social da força de trabalho migrante em Parauapebas-PA. Revista Contemporânea, v. 3, n. 8, p. 12512-12536, 2023. DOI: 10.56083/rcv3n8-142.

PINHEIRO, Leandro Andrei Lopes. Royalties da mineração em Canaã dos Carajás. 2016. Dissertação (Mestrado em Uso Sustentável de Recursos Naturais em Regiões Tropicais) – Instituto tecnológico Vale – desenvolvimento sustentável, 2016.

RIBEIRO, Igor Conceição; PEREIRA, José Danilo Santana; PENA, Heriberto Wagner Amanajás. Análise da dinâmica da estrutura produtiva do município de Canaã dos Carajás – Pará, Amazõnia-Brasil. Observatório de la economía latinoamericana, 2014.

RODRIGUES, Roberta Menezes. "Company Towns e mineração na Amazônia Oriental: especificidades, processos e transformações de um modelo urbanístico". 2001. Dissertação (Mestrado em Planejamento do desenvolvimento) – Universidade federal do Pará, 2001.

ROY, David P.; KOVALSKYY, Valeriy; ZHANG, Hankui K. et al. Characterization of Landsat-7 to Landsat-8 reflective wavelength and normalized difference vegetation index continuity. Remote Sensing of Environment, v. 185, p. 57–70, 2016. DOI: 10.1016/j.rse.2015.12.024.

SANCHES, Maria Clara Souza; RODRIGUES, Janine Stefani Mendes; NASCIMENTO, Bruno Jesus do. Canaã dos Carajás: Cidade do imigrante ou a cidade da mineração. In: Anais do XIII Coninter - Congresso Internacional Interdisciplinar em Sociais e Humanidades: Desenvolvimentos, mitos, ideias e projetos para um mundo em conflito, 2025. DOI: 10.29327/9786527212591.863432.

SANTOS, Sanmarie Rigaud dos. Conflitos agrários decorrentes da mineração: um estudo do Projeto Ferro Carajás S11D em Canaã dos Carajás/Pará. 2017. Dissertação (Mestrado em Direito agrário) – Universidade federal de goiás, 2017.

SANTOS, Rodrigo Salles Pereira dos. DESENVOLVIMENTO ECONÔMICO E MUDANÇA SOCIAL: a Vale e a mineração na Amazônia Oriental. Caderno CRH, v. 29, n. 77, p. 295-312, 2017. DOI: 10.9771/ccrh.v29i77.20004.

SANTOS, Marcelo Melo dos; CRUZ, Thiago Martins da; LOPES, Rafael Rodrigues. Mineração e conflitos pela posse da terra em Canaã dos Carajás: O caso do acampamento Planalto Serra Dourada. In: Ciência Política: Poder e Establishment, p. 153-164, 2021. DOI: 10.22533/at.ed.84021100214.

SANTOS, Rodrigo Castriota de Mello. Urbanização extensiva na Amazônia Oriental: escavando a não-cidade em Carajás. 2021. Tese (Doutorado em Economia) – Universidade federal de Minas Gerais, 2021.

SILVA, Manoel Alves da. Arranjos político-institucionais: a criação de novos municípios, novas estruturas de poder e as lideranças locais - a divisão territorial de Marabá na década de 1980. 2006. Tese (Doutorado em Desenvolvimento sustentável do trópico úmido) – Universidade federal do Pará, 2006.

SILVA, Fernando Flavio Lopes. Uso do território e implicações socioespaciais da mineração no município de Canaã dos carajas. 2016. Dissertação (Mestrado em Geografia) – Universidade federal do Pará, 2016.

SILVA, Daniel Nogueira; SOUSA, Rithielly Lira. As condições de moradia das famílias pobres em Canaã dos Carajás, uma cidade mineral da Amazônia. Revista de Políticas Públicas, v. 26, n. 1, p. 228-248, 2022. DOI: 10.18764/2178-2865.v26n1p228-248.

SILVA, Maria do Carmo Campos da. Regularização fundiária urbana no pós-regularização:o caso do núcleo urbano informal Paraíso das Águas na cidade de Canaã dos Carajás (PA), Brasil. Novos Cadernos NAEA, v. 28, n. 2, 2025. DOI: 10.18542/ncn.v28i2.18057.

SIRAVENHA, Ana Carolina Quintão. Avaliação de técnica semi-supervisionada de análise de vetor comprimido (C2VA) em imagens de satélites para detecção de mudanças de uso e cobertura da terra. 2017. Tese (Doutorado em Engenharia elétrica) – Universidade federal do Pará, 2017.

SOUSA, Karen H.; MATOS, Antonio Nilton; OLIVEIRA, Poliana et al. Volatilidade epidemiológica do hiv/aids em região mineraria da Amazônia. Revista ft, p. 30-31, 2024. DOI: 10.69849/revistaft/fa10202408092230.

SOUZA, Alyne Marcely Fernandes de. Mulheres no mercado de trabalho no setor extrativista mineral no município de Canaã dos Carajás, estado do Pará. 2022. Dissertação (Mestrado em Direito, Políticas Públicas e Desenvolvimento Regional) – Centro universitário do estado do Pará, 2022.

SOUZA, Marcus Vinicius Mariano de; FERREIRA JÚNIOR, Dionel Barbosa. Inserção urbana e desigualdades socioespaciais no programa Minha Casa Minha Vida. InterEspaço: Revista de Geografia e Interdisciplinaridade, 2023. DOI: 10.18764/2446-6549.e2023.11.

SOUZA, Michele Kely Moraes Santos. A urbanização de Parauapebas/PA : a cidade produzida pela mineração. 2024. Tese (Doutorado) – [s.l.], 2024.

SOUZA, Alcione Santos de. Conflitos pelo uso do território: camponeses e mineração no Estado do Pará. 2024. Tese (Doutorado em Geografia) – Universidade federal do rio grande do norte, 2024.

STEHMAN, Stephen V. Estimating area and map accuracy for stratified random sampling when the strata are different from the map classes. International Journal of Remote Sensing, v. 35, n. 13, p. 4923–4939, 2014. DOI: 10.1080/01431161.2014.930207.

TREVISAN, Ricardo; BRANDÃO, Simone Cristina Soares; REIS, Talita Rocha et al. Complexo Carajás, Amazônia: as pretensiosas pegadas urbanizadoras de um território. Ensayo: Revista de arquitectura, urbanismo y territorio, n. 6, p. 19-41, 2025. DOI: 10.18800/ensayo.202506.001.

VIANA JÚNIOR, Elias Marques. Royalties na mineração : uma ferramenta para o desenvolvimento regional da Amazônia oriental brasileira. 2008. Dissertação (Mestrado em Engenharia mineral) – Universidade federal de ouro preto, 2008.

