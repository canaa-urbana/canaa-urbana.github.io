"""Códigos, nomes e regiões das 27 UFs — usado por todos os parsers e pela análise.

Fonte: IBGE (Divisão Territorial Brasileira), conferido nos layouts oficiais dos
três censos (todos usam o mesmo código de 2 dígitos por UF, ver plano §1.1/§1.2).
"""

UF_NOME = {
    "11": "Rondônia", "12": "Acre", "13": "Amazonas", "14": "Roraima", "15": "Pará",
    "16": "Amapá", "17": "Tocantins", "21": "Maranhão", "22": "Piauí", "23": "Ceará",
    "24": "Rio Grande do Norte", "25": "Paraíba", "26": "Pernambuco", "27": "Alagoas",
    "28": "Sergipe", "29": "Bahia", "31": "Minas Gerais", "32": "Espírito Santo",
    "33": "Rio de Janeiro", "35": "São Paulo", "41": "Paraná", "42": "Santa Catarina",
    "43": "Rio Grande do Sul", "50": "Mato Grosso do Sul", "51": "Mato Grosso",
    "52": "Goiás", "53": "Distrito Federal",
}

UF_SIGLA = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR",
    "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}

UF_REGIAO = {
    **{c: "Norte" for c in ["11", "12", "13", "14", "15", "16", "17"]},
    **{c: "Nordeste" for c in ["21", "22", "23", "24", "25", "26", "27", "28", "29"]},
    **{c: "Sudeste" for c in ["31", "32", "33", "35"]},
    **{c: "Sul" for c in ["41", "42", "43"]},
    **{c: "Centro-Oeste" for c in ["50", "51", "52", "53"]},
}

UFS = sorted(UF_NOME)  # 27 códigos, ordem canônica usada em todas as matrizes OD

# Sigla FTP do IBGE por UF (Censo 2000): pastas nomeadas pela sigla, exceto SP.
FTP_SIGLA_2000 = dict(UF_SIGLA)

# Censo 2010: SP é dividido em SP1 ("outras", exceto RM de São Paulo) e SP2_RM
# (Região Metropolitana de São Paulo) — os dois juntos cobrem o estado inteiro.
FTP_PASTAS_2010 = {c: [s] for c, s in UF_SIGLA.items() if s != "SP"}
FTP_PASTAS_2010["35"] = ["SP1", "SP2_RM"]

# Código de UF usado NAS VARIÁVEIS DE MIGRAÇÃO do Censo 2000 (V4210/V4230/V4260)
# — um esquema sequencial 01-27 PRÓPRIO dessas variáveis, diferente do código de
# UF de 2 dígitos (11-53) usado em todo o resto do arquivo (inclusive V0102).
# Conferido em Arquivos Auxiliares/Estrutura Migração V4210,V4260.xls e
# .../V4230.xls (idênticas nas duas). Código 29 = "Brasil sem especificação";
# 30+ = países estrangeiros (não usado neste projeto, tratado como não-Brasil).
UF_CODIGO_MIGRACAO_2000 = {
    "01": "11", "02": "12", "03": "13", "04": "14", "05": "15", "06": "16", "07": "17",
    "08": "21", "09": "22", "10": "23", "11": "24", "12": "25", "13": "26", "14": "27",
    "15": "28", "16": "29", "17": "31", "18": "32", "19": "33", "20": "35", "21": "41",
    "22": "42", "23": "43", "24": "50", "25": "51", "26": "52", "27": "53",
}
