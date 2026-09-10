"""
Harmonização de atividade econômica (CNAE) entre os três censos — o que
destrava a regra 4 do CLAUDE.md (petróleo e gás nunca somados a minério).

2000 usa CNAE-Domiciliar 1.0 (`V4462`, 5 dígitos); 2010 usa CNAE-Domiciliar 2.0
(`V6471`, 5 dígitos); 2022 só traz a SEÇÃO agregada (`P1030`, 2 dígitos, '02' =
B Indústrias extrativas) -- não há como separar petróleo de minério dentro de
2022 pelo próprio Censo. Por isso a separação por substância em 2022 continua
dependendo de CFEM (ANM) x royalties (ANP), como já documentado em
`lib/mineracao.py`; mas em 2000 e 2010 o próprio Censo já permite excluir
petróleo e gás no nível individual, o que os dois códigos de 5 dígitos abaixo
fazem.

Conferido em `CnaeDom-Estrutura.xls` (2000, dentro de
`data/raw/2000/_docs/documentacao_2000.zip/Arquivos Auxiliares/`) e em
`CNAEDOM2.0_Estrutura 2010.xls` (2010, dentro de
`data/raw/2010/_docs/documentacao_2010.zip/Documentação/Anexos Auxiliares/`),
seção "C/B - INDÚSTRIAS EXTRATIVAS" de cada planilha.
"""

# Seção C (2000, CNAE-Dom 1.0) -- "INDÚSTRIAS EXTRATIVAS"
#   10 Extração de carvão mineral; 11 petróleo e gás; 12 minerais radioativos;
#   13 minerais metálicos; 14 minerais não-metálicos.
EXTRATIVA_SEM_PETROLEO_2000 = frozenset({
    "10000",  # extração de carvão mineral
    "12000",  # extração de minerais radioativos
    "13001",  # extração de minérios de metais preciosos
    "13002",  # extração de minerais metálicos, exceto preciosos e radioativos
    "14001",  # extração de pedras e outros materiais para construção
    "14002",  # extração de pedras preciosas e semipreciosas
    "14003",  # extração de outros minerais não-metálicos
    "14004",  # extração de minerais mal especificados
})
PETROLEO_GAS_2000 = frozenset({"11000"})  # extração de petróleo e gás natural

# Seção B (2010, CNAE-Dom 2.0) -- "INDÚSTRIAS EXTRATIVAS"
#   05 carvão; 06 petróleo e gás; 07 minerais metálicos; 08 minerais
#   não-metálicos; 09 atividades de apoio à extração de minerais.
EXTRATIVA_SEM_PETROLEO_2010 = frozenset({
    "05000",  # extração de carvão mineral
    "07001",  # extração de minérios de metais preciosos
    "07002",  # extração de minerais metálicos não especificados anteriormente
    "08001",  # extração de pedras, areia e argila
    "08002",  # extração de gemas (pedras preciosas e semipreciosas)
    "08009",  # extração de minerais não metálicos não especificados anteriormente
    "08999",  # extração de minerais não especificados
    "09000",  # atividades de apoio à extração de minerais
})
PETROLEO_GAS_2010 = frozenset({"06000"})  # extração de petróleo e gás natural

# 2022 (P1030): só a seção agregada. '02' = Seção B, Indústrias extrativas --
# mistura minério e petróleo/gás, não separável pelo próprio Censo (ver
# docstring do módulo e lib/mineracao.py::EXCLUIR_PETROLEO_GAS).
SECAO_EXTRATIVA_2022 = "02"


def eh_extrativa_sem_petroleo(serie, censo: int):
    """True para quem trabalha na extração mineral EXCLUINDO petróleo e gás,
    no `censo` pedido (2000 ou 2010 -- ver ressalva de 2022 na docstring do
    módulo). `serie` é a coluna de atividade bruta (`V4462` em 2000, `V6471`
    em 2010), como string."""
    alvo = {2000: EXTRATIVA_SEM_PETROLEO_2000, 2010: EXTRATIVA_SEM_PETROLEO_2010}[censo]
    return serie.str.strip().isin(alvo)


def eh_petroleo_gas(serie, censo: int):
    """True para quem trabalha em extração de petróleo e gás, no `censo`
    pedido (2000 ou 2010)."""
    alvo = {2000: PETROLEO_GAS_2000, 2010: PETROLEO_GAS_2010}[censo]
    return serie.str.strip().isin(alvo)
