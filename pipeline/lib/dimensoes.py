"""
Dimensões, universos e cruzamentos publicáveis — fonte única usada por
`13_migracao_perfil.py` (publicação) e por `disclosure_check.py` (verificação
independente das contagens amostrais). Regra R4: no máximo 2 dimensões
temáticas por tabela; geografia, censo e universo não contam como dimensão.

Toda categoria publicável está listada aqui (`cats`); uma categoria fora da
lista nunca entra numa tabela. Colunas derivadas (faixas, binários "sim/nao",
flag de domicílio com migrante recente) são criadas por `preparar()` a partir
dos parquets harmonizados de `data/interim/microdados/`.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from lib import censos as C

SIM_NAO = ["sim", "nao"]

# Universos (filtro aplicado antes da dimensão). Chave -> (nível, expressão)
UNIVERSOS = {
    "pessoas": ("pessoas", None),
    "pessoas_5mais": ("pessoas", "idade >= 5"),
    "pessoas_10mais": ("pessoas", "idade >= 10"),
    "pessoas_25mais": ("pessoas", "idade >= 25"),
    "ocupados": ("pessoas", "ocupado == True"),
    "com_rendimento": ("pessoas", "idade >= 10 and renda_total > 0"),
    "migrantes_5anos": ("pessoas", "migrante == 'migrante'"),
    "migrantes_internos": ("pessoas", "tipo_mig_5anos in ['intraestadual', 'interestadual']"),
    "chegados": ("pessoas", "ano_chegada == ano_chegada"),   # not NaN
    "domicilios": ("domicilios", None),
}

PERIODOS_CHEGADA = ["ate_1984", "1985_1994", "1995_2001", "2002_2004", "2005_2012", "2013_2016", "2017_2022"]
ANOS_CHEGADA = [str(a) for a in range(1970, 2023)]

DIMENSOES: dict[str, dict] = {
    # --- pessoas ---
    "sexo": dict(col="sexo", universo="pessoas", cats=["M", "F"]),
    "faixa_etaria": dict(col="faixa_etaria", universo="pessoas",
                         cats=[f"{a:02d}_{a+4:02d}" for a in range(0, 80, 5)] + ["80_mais"]),
    "grupo_etario": dict(col="grupo_etario", universo="pessoas", cats=["00_14", "15_24", "25_39", "40_59", "60_mais"]),
    "cor_raca": dict(col="cor_raca", universo="pessoas", cats=["branca", "preta", "parda", "amarela", "indigena", "ignorado"]),
    "nivel_instrucao": dict(col="nivel_instrucao", universo="pessoas_25mais", cats=list(C.NIVEL_INSTRUCAO.values())),
    "ocupado": dict(col="ocupado_cat", universo="pessoas_10mais", cats=SIM_NAO),
    "posicao": dict(col="posicao", universo="ocupados",
                    cats=["empregado_com_carteira", "empregado_sem_carteira", "militar_estatutario", "conta_propria",
                          "empregador", "nao_remunerado"]),
    "formal": dict(col="formal_cat", universo="ocupados", cats=SIM_NAO),
    "setor": dict(col="setor", universo="ocupados", cats=C.SETORES),
    "extrativa_mineral": dict(col="extrativa_cat", universo="ocupados", cats=SIM_NAO),
    "renda_sm_faixa": dict(col="renda_sm_faixa", universo="pessoas_10mais", cats=C.RENDA_SM_FAIXAS),
    "tipo_mig_5anos": dict(col="tipo_mig_5anos", universo="pessoas_5mais",
                           cats=["nao_migrante", "intraestadual", "interestadual", "internacional"]),
    "migrante": dict(col="migrante", universo="pessoas_5mais", cats=["migrante", "nao_migrante"]),
    "origem_regiao": dict(col="origem_regiao", universo="migrantes_5anos",
                          cats=["mesma_uf", "Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste", "exterior"]),
    "origem_uf": dict(col="origem_uf", universo="migrantes_internos", cats=sorted(C.REGIAO_UF), nominal=True),
    "origem_mun": dict(col="origem_mun", universo="migrantes_internos", cats=None, nominal=True),  # cats abertas (códigos IBGE)
    "naturalidade": dict(col="naturalidade", universo="pessoas", cats=["municipio", "mesma_uf", "outra_uf", "exterior"]),
    "tempo_moradia_faixa": dict(col="tempo_moradia_faixa", universo="pessoas", cats=["menos_1", "1_a_4", "5_a_9", "10_a_19", "20_mais"]),
    "periodo_chegada": dict(col="periodo_chegada", universo="chegados", cats=PERIODOS_CHEGADA),
    "ano_chegada": dict(col="ano_chegada_cat", universo="chegados", cats=ANOS_CHEGADA),
    "retorno": dict(col="retorno_cat", universo="pessoas_5mais", cats=SIM_NAO),
    "trabalha_outro_mun": dict(col="trabalha_outro_cat", universo="ocupados", cats=SIM_NAO),
    # --- domicílios ---
    "tem_migrante_recente": dict(col="tem_migrante_recente", universo="domicilios", cats=SIM_NAO),
    "tipo_domicilio": dict(col="tipo", universo="domicilios", cats=["casa", "apartamento", "comodo", "outro"]),
    "condicao_ocupacao": dict(col="condicao_ocupacao", universo="domicilios",
                              cats=["proprio", "alugado", "cedido_empregador", "cedido_outro", "outra"]),
    "agua_rede": dict(col="agua_rede_cat", universo="domicilios", cats=SIM_NAO),
    "esgoto_adequado": dict(col="esgoto_cat", universo="domicilios", cats=SIM_NAO),
    "lixo_coletado": dict(col="lixo_cat", universo="domicilios", cats=SIM_NAO),
    "energia": dict(col="energia_cat", universo="domicilios", cats=SIM_NAO),
    "internet": dict(col="internet_cat", universo="domicilios", cats=SIM_NAO),
    "adequacao": dict(col="adequacao", universo="domicilios", cats=["adequada", "semi_adequada", "inadequada"]),
    "densidade_faixa": dict(col="densidade_faixa", universo="domicilios", cats=["ate_1", "1_a_2", "2_a_3", "mais_de_3"]),
    "renda_dom_pc_faixa": dict(col="renda_dom_pc_faixa", universo="domicilios", cats=C.RENDA_SM_FAIXAS),
}

# Preferência de fusão na supressão secundária (R8): quando uma categoria pequena
# precisa ser somada a outra para formar 'outros', escolhe-se o vizinho ordinal
# (dimensões em ORDINAIS, pela ordem de `cats`) ou o parceiro semântico em FUSAO;
# só na falta dos dois cai na menor categoria restante. Evita, por exemplo, que
# 'internacional' arraste 'nao_migrante' ou que 'exterior' engula 'municipio'.
ORDINAIS = {"faixa_etaria", "grupo_etario", "nivel_instrucao", "renda_sm_faixa", "tempo_moradia_faixa",
            "periodo_chegada", "ano_chegada", "densidade_faixa", "renda_dom_pc_faixa", "adequacao"}
FUSAO = {
    "tipo_mig_5anos": {"internacional": "interestadual"},
    "naturalidade": {"exterior": "outra_uf"},
    "origem_regiao": {"exterior": "Sul", "Sul": "Centro-Oeste", "Centro-Oeste": "Sudeste", "Norte": "Nordeste"},
    "posicao": {"empregador": "nao_remunerado", "nao_remunerado": "empregador",
                "militar_estatutario": "empregado_com_carteira"},
    "setor": {"domestico": "servicos", "outras_atividades": "servicos", "transformacao": "outras_atividades",
              "extrativa_mineral": "construcao", "agropecuaria": "outras_atividades"},
    "cor_raca": {"ignorado": "amarela", "amarela": "indigena", "indigena": "preta"},
    "condicao_ocupacao": {"outra": "cedido_outro", "cedido_empregador": "cedido_outro", "cedido_outro": "alugado"},
    "tipo_domicilio": {"outro": "comodo", "comodo": "apartamento", "apartamento": "casa"},
}

# Cruzamentos publicados (dim1 x dim2). O universo é a interseção dos dois.
CRUZAMENTOS = (
    [("migrante", d) for d in ["sexo", "grupo_etario", "cor_raca", "nivel_instrucao", "ocupado", "posicao",
                               "formal", "setor", "extrativa_mineral", "renda_sm_faixa", "trabalha_outro_mun",
                               "naturalidade"]]
    + [("tipo_mig_5anos", "grupo_etario"), ("tipo_mig_5anos", "setor"), ("sexo", "faixa_etaria"),
       ("setor", "posicao"), ("periodo_chegada", "setor"), ("periodo_chegada", "naturalidade"),
       ("periodo_chegada", "origem_regiao"), ("tempo_moradia_faixa", "setor"), ("setor", "sexo"),
       ("extrativa_mineral", "posicao"), ("extrativa_mineral", "nivel_instrucao")]
    + [("tem_migrante_recente", d) for d in ["tipo_domicilio", "condicao_ocupacao", "agua_rede", "esgoto_adequado",
                                             "lixo_coletado", "energia", "internet", "adequacao", "densidade_faixa",
                                             "renda_dom_pc_faixa"]]
)

# Médias/medianas publicadas: (variável, universo, dimensão de desagregação ou None)
MEDIAS = [
    ("idade", "pessoas", None), ("idade", "pessoas", "migrante"),
    ("renda_total_r2022", "com_rendimento", None), ("renda_total_r2022", "com_rendimento", "migrante"),
    ("renda_total_r2022", "com_rendimento", "setor"),
    ("renda_trabalho_r2022", "ocupados", None), ("renda_trabalho_r2022", "ocupados", "migrante"),
    ("renda_trabalho_r2022", "ocupados", "setor"), ("renda_trabalho_r2022", "ocupados", "extrativa_mineral"),
    ("tempo_moradia", "pessoas", None), ("tempo_moradia", "pessoas", "setor"),
    ("renda_dom_pc_r2022", "domicilios", None), ("renda_dom_pc_r2022", "domicilios", "tem_migrante_recente"),
    ("densidade_dormitorio", "domicilios", None), ("densidade_dormitorio", "domicilios", "tem_migrante_recente"),
    ("moradores", "domicilios", None), ("moradores", "domicilios", "tem_migrante_recente"),
]


def _sim_nao(s: pd.Series) -> pd.Series:
    out = pd.Series(pd.NA, index=s.index, dtype="object")
    out[s == True] = "sim"   # noqa: E712  (boolean com NA)
    out[s == False] = "nao"  # noqa: E712
    return out


def periodo_chegada(ano: pd.Series) -> pd.Series:
    a = pd.to_numeric(ano, errors="coerce")
    bins = [-np.inf, 1984, 1994, 2001, 2004, 2012, 2016, 2022]
    return pd.cut(a, bins=bins, labels=PERIODOS_CHEGADA).astype("object")


def preparar(pessoas: pd.DataFrame, domicilios: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Adiciona as colunas derivadas usadas pelas dimensões. Não altera os parquets."""
    p = pessoas.copy()
    p["faixa_etaria"] = C.faixa_etaria(p["idade"])
    p["grupo_etario"] = C.grupo_etario(p["idade"])
    p["ocupado_cat"] = _sim_nao(p["ocupado"])
    p["formal_cat"] = _sim_nao(p["formal"])
    p["extrativa_cat"] = _sim_nao(p["extrativa_mineral"])
    p["retorno_cat"] = _sim_nao(p["retorno"].astype("boolean"))
    p["trabalha_outro_cat"] = _sim_nao(p["trabalha_outro_mun"])
    p["migrante"] = pd.Series(pd.NA, index=p.index, dtype="object")
    p.loc[p["tipo_mig_5anos"].isin(["intraestadual", "interestadual", "internacional"]), "migrante"] = "migrante"
    p.loc[p["tipo_mig_5anos"] == "nao_migrante", "migrante"] = "nao_migrante"
    p["origem_regiao"] = C.regiao_origem(p["origem_uf"], p["uf"], p["tipo_mig_5anos"])
    p["tempo_moradia_faixa"] = C.faixa_tempo_moradia(p["tempo_moradia"])
    p["periodo_chegada"] = periodo_chegada(p["ano_chegada"])
    p["ano_chegada_cat"] = p["ano_chegada"].map(lambda a: str(int(a)) if pd.notna(a) else pd.NA)

    d = domicilios.copy()
    mig_dom = (p.loc[p["migrante"] == "migrante", "controle"].astype(str)).unique()
    d["tem_migrante_recente"] = np.where(d["controle"].astype(str).isin(mig_dom), "sim", "nao")
    d["agua_rede_cat"] = _sim_nao(d["agua_rede"])
    d["esgoto_cat"] = _sim_nao(d["esgoto_adequado"])
    d["lixo_cat"] = _sim_nao(d["lixo_coletado"])
    d["energia_cat"] = _sim_nao(d["energia"])
    d["internet_cat"] = _sim_nao(d["internet"])
    d["densidade_faixa"] = C.faixa_densidade(d["densidade_dormitorio"])
    d["renda_dom_pc_faixa"] = C.faixa_renda_sm(d["renda_dom_pc_sm"])
    return p, d


def mascara_universo(df: pd.DataFrame, universo: str) -> np.ndarray:
    nivel, expr = UNIVERSOS[universo]
    if expr is None:
        return np.ones(len(df), dtype=bool)
    return df.eval(expr).fillna(False).to_numpy(dtype=bool)


def nivel_universo(universo: str) -> str:
    return UNIVERSOS[universo][0]


def mascara_categoria(df: pd.DataFrame, dim: str, cat: str) -> np.ndarray:
    col = DIMENSOES[dim]["col"]
    return (df[col].astype("object") == cat).fillna(False).to_numpy(dtype=bool)


def universo_cruzamento(dim1: str, dim2: str | None) -> str:
    """Universo de um cruzamento = o mais restritivo dos dois (ordem de restrição
    explícita, para nunca depender de qual dimensão vem primeiro)."""
    ordem = ["pessoas", "pessoas_5mais", "pessoas_10mais", "pessoas_25mais", "com_rendimento",
             "ocupados", "chegados", "migrantes_5anos", "migrantes_internos", "domicilios"]
    u1 = DIMENSOES[dim1]["universo"]
    if dim2 is None:
        return u1
    u2 = DIMENSOES[dim2]["universo"]
    if nivel_universo(u1) != nivel_universo(u2):
        raise ValueError(f"cruzamento entre níveis diferentes: {dim1} x {dim2}")
    return max(u1, u2, key=ordem.index)


def geografia_mascara(df: pd.DataFrame, geografia: str, geografias: dict) -> np.ndarray:
    mun, sit = geografias[geografia]
    m = np.ones(len(df), dtype=bool)
    if mun is not None:
        m &= (df["mun"] == mun).to_numpy()
    if sit is not None:
        m &= (df["situacao"] == sit).to_numpy()
    return m
