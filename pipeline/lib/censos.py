"""
Harmonização dos quatro censos (1991, 2000, 2010, 2022) para o projeto
urban-canaa — Fase 2 do PLANO.md (E2).

Este módulo é a ÚNICA fonte dos mapeamentos código → categoria harmonizada.
Todo código citado aqui foi conferido nesta sessão (2026-09-10) contra a
documentação oficial do IBGE lida em `data/interim/`:
  - 1991: `censo1991/docs/Dicionario_1991.xls` (aba Layout) e
    `CODIGO_ATIVIDADE.TXT`;
  - 2000: `censo2000_docs/Documentaá∆o.txt` (conversão do .doc oficial) e
    `Arquivos Auxiliares/CnaeDom-Estrutura.xls`;
  - 2010: `Documentação/Layout/Layout_microdados_Amostra.xls` e
    `Anexos Auxiliares/Atividade CNAE_DOM 2.0 2010.xls`;
  - 2022: `layouts_2022/{PESS,DOMI}.json` (exportado de `Layout Microdados
    CD2022 - acesso Controlado.xlsx`).

Nenhuma posição de coluna aparece aqui — só códigos de categoria. Posições
vêm dos layouts JSON (`lib.fwf`) ou do cabeçalho do CSV (2022) / DBF (1991).

Geografias do projeto:
  - Canaã dos Carajás (1502152) — sede urbana (situação = urbana) e município;
  - Parauapebas (1505536) — comparação em todos os anos e PROXY de 1991 (Canaã
    foi emancipada de Parauapebas em 1994; em 1991 a sede era o distrito de
    Canaã dentro de Parauapebas, não separável nos microdados);
  - Pará (UF 15) — referência regional.
"""
from __future__ import annotations

import pandas as pd

CANAA = "1502152"
PARAUAPEBAS = "1505536"
UF_PA = "15"

# Município de 1991 (4 dígitos no DBF = dígitos 3-6 do código de 7) -> código de 7
# dígitos, conferido em `DTB Municipios 1991.xls` (DTB do próprio pacote de 1991).
MUNICIPIOS_1991 = {"0553": PARAUAPEBAS, "0420": "1504208", "0277": "1502772"}

# Categorias harmonizadas ----------------------------------------------------------

SEXO = {"1": "M", "2": "F"}

COR_RACA = {"1": "branca", "2": "preta", "3": "amarela", "4": "parda", "5": "indigena", "9": "ignorado"}

# Nível de instrução compatível com V6400 (2010) / P0770 (2022); em 2000 e 1991
# reconstruído a partir de anos de estudo (V4300 / EDANOEST) — regra do IBGE:
# 0-7 anos = sem instrução e fundamental incompleto; 8-10 = fundamental completo
# e médio incompleto; 11-14 = médio completo e superior incompleto; 15+ = superior
# completo; 20/30 (2000) e 20/30 (1991) = não determinado / alfabetização.
NIVEL_INSTRUCAO = {
    "1": "sem_instrucao_fund_incompleto",
    "2": "fund_completo_medio_incompleto",
    "3": "medio_completo_sup_incompleto",
    "4": "superior_completo",
    "5": "nao_determinado",
}


def nivel_por_anos_estudo(anos: pd.Series) -> pd.Series:
    a = pd.to_numeric(anos, errors="coerce")
    out = pd.Series(pd.NA, index=anos.index, dtype="object")
    out[a <= 7] = "sem_instrucao_fund_incompleto"
    out[(a >= 8) & (a <= 10)] = "fund_completo_medio_incompleto"
    out[(a >= 11) & (a <= 14)] = "medio_completo_sup_incompleto"
    out[(a >= 15) & (a <= 17)] = "superior_completo"
    out[a.isin([20, 30])] = "nao_determinado"
    return out


# Posição na ocupação (trabalho principal), harmonizada em 6 classes.
POSICAO_2022 = {  # P1020
    "01": "empregado_com_carteira", "02": "empregado_sem_carteira",
    "03": "empregado_com_carteira", "04": "empregado_sem_carteira",   # domésticos
    "05": "empregado_com_carteira", "06": "empregado_sem_carteira",   # setor público celetista
    "07": "militar_estatutario", "08": "empregador", "09": "conta_propria",
    "10": "nao_remunerado",
}
POSICAO_2010 = {  # V6930
    "1": "empregado_com_carteira", "2": "militar_estatutario", "3": "empregado_sem_carteira",
    "4": "conta_propria", "5": "empregador", "6": "nao_remunerado", "7": "nao_remunerado",
}
POSICAO_2000 = {  # V0447 (2000 não separa militar/estatutário: cai em "com carteira")
    "1": "empregado_com_carteira", "2": "empregado_sem_carteira",
    "3": "empregado_com_carteira", "4": "empregado_sem_carteira",
    "5": "empregador", "6": "conta_propria", "7": "nao_remunerado", "8": "nao_remunerado",
    "9": "nao_remunerado",
}
# 1991: POSOCUP x CARTASS (1 sim / 3 não tem / 2 não sabe / 4 não empregado)
POSICAO_1991_EMPREGADO = {1, 2, 4, 6, 8}   # volante, parceiro-empregado, doméstico-empregado, privado, estatal
POSICAO_1991 = {7: "militar_estatutario", 3: "conta_propria", 5: "conta_propria", 9: "conta_propria",
                10: "empregador", 11: "nao_remunerado"}

FORMAL = {"empregado_com_carteira", "militar_estatutario"}

# Setor de atividade harmonizado (9 classes). Chave = seção (2022) ou divisão
# (2 primeiros dígitos do código CNAE-Dom, 2000/2010) ou ATIVISET/ATIVIDAD (1991).
SETORES = ["agropecuaria", "extrativa_mineral", "transformacao", "construcao", "comercio",
           "servicos", "adm_publica_educacao_saude", "domestico", "outras_atividades"]

SETOR_2022 = {  # P1030 (seção CNAE 2.0 codificada 01-22)
    "01": "agropecuaria", "02": "extrativa_mineral", "03": "transformacao", "04": "outras_atividades",
    "05": "outras_atividades", "06": "construcao", "07": "comercio", "08": "servicos", "09": "servicos",
    "10": "servicos", "11": "servicos", "12": "servicos", "13": "servicos", "14": "servicos",
    "15": "adm_publica_educacao_saude", "16": "adm_publica_educacao_saude",
    "17": "adm_publica_educacao_saude", "18": "servicos", "19": "servicos", "20": "domestico",
    "21": "outras_atividades", "22": "outras_atividades",
}


def _faixa(d: int, faixas: list[tuple[int, int, str]]) -> str:
    for lo, hi, rot in faixas:
        if lo <= d <= hi:
            return rot
    return "outras_atividades"


# CNAE-Dom 2.0 (2010, V6471 5 dígitos): divisão = 2 primeiros dígitos
_DIV_2010 = [(1, 3, "agropecuaria"), (5, 9, "extrativa_mineral"), (10, 33, "transformacao"),
             (35, 39, "outras_atividades"), (41, 43, "construcao"), (45, 48, "comercio"), (49, 82, "servicos"),
             (84, 88, "adm_publica_educacao_saude"), (90, 96, "servicos"), (97, 97, "domestico"),
             (99, 99, "outras_atividades")]
# CNAE-Dom 1.0 (2000, V4462 5 dígitos): divisão = 2 primeiros dígitos
_DIV_2000 = [(1, 5, "agropecuaria"), (10, 14, "extrativa_mineral"), (15, 37, "transformacao"),
             (40, 41, "outras_atividades"), (45, 45, "construcao"), (50, 53, "comercio"), (55, 74, "servicos"),
             (75, 75, "adm_publica_educacao_saude"), (80, 85, "adm_publica_educacao_saude"),
             (90, 93, "servicos"), (95, 95, "domestico"), (99, 99, "outras_atividades")]


def setor_por_cnae(codigo: pd.Series, censo: int) -> pd.Series:
    """Setor harmonizado a partir do código CNAE-Dom de 5 dígitos (2000/2010)."""
    faixas = {2000: _DIV_2000, 2010: _DIV_2010}[censo]
    s = codigo.astype("string").str.strip()
    div = pd.to_numeric(s.str[:2], errors="coerce")
    out = div.map(lambda d: _faixa(int(d), faixas) if pd.notna(d) else pd.NA)
    return out.where(s.str.len() > 0, pd.NA)


# 1991: ATIVISET (setor) refinado por ATIVIDAD para extração mineral (050-059,
# conferido em CODIGO_ATIVIDADE.TXT: 050 pedras/mat. construção ... 058 minerais
# metálicos, 059 mal definidas) — em ATIVISET a extração mineral cai em
# "4 outras atividades industriais".
def setor_1991(ativiset: pd.Series, atividad: pd.Series, posocup: pd.Series) -> pd.Series:
    st = pd.to_numeric(ativiset, errors="coerce")
    at = pd.to_numeric(atividad, errors="coerce")
    po = pd.to_numeric(posocup, errors="coerce")
    out = pd.Series(pd.NA, index=ativiset.index, dtype="object")
    out[st == 1] = "agropecuaria"
    out[st == 2] = "transformacao"
    out[st == 3] = "construcao"
    out[st == 4] = "outras_atividades"
    out[st == 5] = "comercio"
    out[st.isin([6, 7, 8])] = "servicos"
    out[st.isin([9, 10])] = "adm_publica_educacao_saude"
    out[st == 11] = "outras_atividades"
    out[(at >= 50) & (at <= 59)] = "extrativa_mineral"
    out[po.isin([4, 5])] = "domestico"
    return out


# Faixas de renda total (pessoal) em salários mínimos — comum aos 4 censos.
RENDA_SM_FAIXAS = ["sem_rendimento", "ate_1_2", "1_2_a_1", "1_a_2", "2_a_3", "3_a_5", "5_a_10", "mais_de_10"]


def faixa_renda_sm(renda_sm: pd.Series) -> pd.Series:
    r = pd.to_numeric(renda_sm, errors="coerce")
    out = pd.Series(pd.NA, index=renda_sm.index, dtype="object")
    out[r == 0] = "sem_rendimento"
    out[(r > 0) & (r <= 0.5)] = "ate_1_2"
    out[(r > 0.5) & (r <= 1)] = "1_2_a_1"
    out[(r > 1) & (r <= 2)] = "1_a_2"
    out[(r > 2) & (r <= 3)] = "2_a_3"
    out[(r > 3) & (r <= 5)] = "3_a_5"
    out[(r > 5) & (r <= 10)] = "5_a_10"
    out[r > 10] = "mais_de_10"
    return out


# 1991: RTONOMIF já vem em faixas de SM (o IBGE fez a conversão pelo salário
# mínimo da época) — recodificada para as mesmas faixas acima.
RENDA_SM_1991 = {1: "ate_1_2", 2: "ate_1_2", 3: "1_2_a_1", 4: "1_2_a_1", 5: "1_a_2", 6: "1_a_2",
                 7: "1_a_2", 8: "2_a_3", 9: "3_a_5", 10: "5_a_10", 11: "mais_de_10", 12: "mais_de_10",
                 13: "mais_de_10", 14: "sem_rendimento"}

# Faixas etárias quinquenais (pirâmide) e grandes grupos.
def faixa_etaria(idade: pd.Series, largura: int = 5, topo: int = 80) -> pd.Series:
    i = pd.to_numeric(idade, errors="coerce")
    lo = (i // largura * largura).clip(upper=topo)
    lab = lo.map(lambda x: pd.NA if pd.isna(x) else (f"{int(x):02d}_{int(x)+largura-1:02d}" if x < topo else f"{topo}_mais"))
    return lab


def grupo_etario(idade: pd.Series) -> pd.Series:
    i = pd.to_numeric(idade, errors="coerce")
    out = pd.Series(pd.NA, index=idade.index, dtype="object")
    out[i <= 14] = "00_14"
    out[(i >= 15) & (i <= 24)] = "15_24"
    out[(i >= 25) & (i <= 39)] = "25_39"
    out[(i >= 40) & (i <= 59)] = "40_59"
    out[i >= 60] = "60_mais"
    return out


def faixa_tempo_moradia(anos: pd.Series) -> pd.Series:
    a = pd.to_numeric(anos, errors="coerce")
    out = pd.Series(pd.NA, index=anos.index, dtype="object")
    out[a < 1] = "menos_1"
    out[(a >= 1) & (a <= 4)] = "1_a_4"
    out[(a >= 5) & (a <= 9)] = "5_a_9"
    out[(a >= 10) & (a <= 19)] = "10_a_19"
    out[a >= 20] = "20_mais"
    return out


# Domicílios -----------------------------------------------------------------------
CONDICAO_OCUPACAO_2022 = {"1": "proprio", "2": "proprio", "3": "alugado", "4": "cedido_empregador",
                          "5": "cedido_outro", "6": "cedido_outro", "7": "outra"}
CONDICAO_OCUPACAO_2010 = {"1": "proprio", "2": "proprio", "3": "alugado", "4": "cedido_empregador",
                          "5": "cedido_outro", "6": "outra"}
CONDICAO_OCUPACAO_2000 = CONDICAO_OCUPACAO_2010  # V0205: mesmas 6 categorias
CONDICAO_OCUPACAO_1991 = {1: "proprio", 2: "proprio", 3: "alugado", 4: "cedido_empregador",
                          5: "cedido_outro", 6: "outra"}

TIPO_DOMICILIO_2022 = {"11": "casa", "12": "casa", "13": "apartamento", "14": "comodo", "15": "outro", "16": "outro"}
TIPO_DOMICILIO_2010 = {"11": "casa", "12": "casa", "13": "apartamento", "14": "comodo", "15": "outro"}
TIPO_DOMICILIO_2000 = {"1": "casa", "2": "apartamento", "3": "comodo"}
TIPO_DOMICILIO_1991 = {1: "casa", 2: "casa", 3: "casa", 4: "apartamento", 5: "apartamento", 6: "apartamento", 7: "comodo"}


def faixa_densidade(dens: pd.Series) -> pd.Series:
    d = pd.to_numeric(dens, errors="coerce")
    out = pd.Series(pd.NA, index=dens.index, dtype="object")
    out[d <= 1] = "ate_1"
    out[(d > 1) & (d <= 2)] = "1_a_2"
    out[(d > 2) & (d <= 3)] = "2_a_3"
    out[d > 3] = "mais_de_3"
    return out


def adequacao(agua: pd.Series, esgoto: pd.Series, lixo: pd.Series) -> pd.Series:
    """Índice reconstruído de adequação (água rede + esgoto rede/fossa séptica +
    lixo coletado): 'adequada' = os três; 'semi_adequada' = 1 ou 2; 'inadequada'
    = nenhum. NA se algum componente for NA."""
    comp = pd.concat([agua, esgoto, lixo], axis=1)
    n = comp.sum(axis=1, min_count=3)
    out = pd.Series(pd.NA, index=agua.index, dtype="object")
    out[n == 3] = "adequada"
    out[(n >= 1) & (n <= 2)] = "semi_adequada"
    out[n == 0] = "inadequada"
    return out


REGIAO_UF = {
    **{c: "Norte" for c in ["11", "12", "13", "14", "15", "16", "17"]},
    **{c: "Nordeste" for c in ["21", "22", "23", "24", "25", "26", "27", "28", "29"]},
    **{c: "Sudeste" for c in ["31", "32", "33", "35"]},
    **{c: "Sul" for c in ["41", "42", "43"]},
    **{c: "Centro-Oeste" for c in ["50", "51", "52", "53"]},
}


def regiao_origem(uf_origem: pd.Series, uf_atual: pd.Series, tipo: pd.Series) -> pd.Series:
    """Região de origem do migrante de data fixa: 'mesma_uf' (intraestadual),
    região do Brasil para interestadual, 'exterior' para internacional."""
    out = pd.Series(pd.NA, index=uf_origem.index, dtype="object")
    out[tipo == "intraestadual"] = "mesma_uf"
    inter = tipo == "interestadual"
    out[inter] = uf_origem[inter].map(REGIAO_UF)
    out[tipo == "internacional"] = "exterior"
    return out
