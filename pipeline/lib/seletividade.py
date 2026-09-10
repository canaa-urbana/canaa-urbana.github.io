"""
Seletividade migratória e decomposição de diferenciais de renda —
Oaxaca-Blinder ponderado e regressão RIF (plano §4/§6, Artigos 1 e 3).
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm


def indice_seletividade(pct_grupo: pd.Series, pct_referencia: pd.Series) -> pd.Series:
    """Índice de seletividade de Lee (1966): razão entre a composição (%) de
    um subgrupo migrante e a composição (%) da população de referência.
    >1 = sobre-representação (seleção positiva); <1 = sub-representação.
    """
    return pct_grupo / pct_referencia


def oaxaca_blinder(
    df: pd.DataFrame,
    col_renda_log: str,
    col_grupo: str,
    grupo_a,
    grupo_b,
    covariaveis: list[str],
    col_peso: str = "peso",
) -> dict:
    """Decomposição de Oaxaca-Blinder (duas vias, ponderada) do diferencial
    médio de `col_renda_log` (deve já estar em log) entre `grupo_a` (ex.:
    migrantes) e `grupo_b` (ex.: não migrantes) de `col_grupo`.

    Retorna o hiato total e sua partição em componente "dotações"
    (explicado pelas covariáveis observadas) e "coeficientes" (retorno
    diferencial às mesmas covariáveis — a parte não explicada).
    """
    a = df[df[col_grupo] == grupo_a].dropna(subset=[col_renda_log, *covariaveis, col_peso])
    b = df[df[col_grupo] == grupo_b].dropna(subset=[col_renda_log, *covariaveis, col_peso])

    def _wls(d):
        X = sm.add_constant(d[covariaveis].astype(float))
        w = d[col_peso].astype(float)
        return sm.WLS(d[col_renda_log].astype(float), X, weights=w).fit()

    mod_a, mod_b = _wls(a), _wls(b)

    xbar_a = np.append(1.0, np.average(a[covariaveis], weights=a[col_peso], axis=0))
    xbar_b = np.append(1.0, np.average(b[covariaveis], weights=b[col_peso], axis=0))

    hiato_total = float(xbar_a @ mod_a.params - xbar_b @ mod_b.params)
    dotacoes = float((xbar_a - xbar_b) @ mod_b.params)
    coeficientes = float(xbar_b @ (mod_a.params - mod_b.params))
    interacao = float((xbar_a - xbar_b) @ (mod_a.params - mod_b.params))

    return {
        "hiato_total": hiato_total,
        "componente_dotacoes": dotacoes,
        "componente_coeficientes": coeficientes,
        "componente_interacao": interacao,
        "pct_explicado_por_dotacoes": 100 * dotacoes / hiato_total if hiato_total else float("nan"),
        "n_grupo_a": len(a),
        "n_grupo_b": len(b),
        "modelo_a": mod_a,
        "modelo_b": mod_b,
    }


def rif_renda(renda: pd.Series, peso: pd.Series, quantil: float = 0.5) -> pd.Series:
    """Recentered Influence Function (Firpo, Fortin & Lemieux, 2009) para um
    quantil da distribuição de renda — usada para decompor diferenciais em
    pontos específicos da distribuição (não só na média), ex.: RIF do Artigo
    3 comparando migrantes e não-migrantes na mediana e nos decis extremos.
    """
    d = pd.DataFrame({"renda": renda, "peso": peso}).dropna().sort_values("renda")
    peso_acum = d["peso"].cumsum() / d["peso"].sum()
    idx = (peso_acum >= quantil).idxmax()
    q_valor = d.loc[idx, "renda"]

    # densidade no quantil por kernel gaussiano (regra de Silverman)
    n_eff = d["peso"].sum() ** 2 / (d["peso"] ** 2).sum()  # tamanho de amostra efetivo
    sigma = np.sqrt(np.average((d["renda"] - np.average(d["renda"], weights=d["peso"])) ** 2, weights=d["peso"]))
    h = 1.06 * sigma * n_eff ** (-1 / 5)
    kernel = np.exp(-0.5 * ((d["renda"] - q_valor) / h) ** 2) / (h * np.sqrt(2 * np.pi))
    densidade = float(np.average(kernel, weights=d["peso"]))

    rif = q_valor + (quantil - (d["renda"] <= q_valor).astype(float)) / max(densidade, 1e-12)
    return pd.Series(rif.values, index=d.index).reindex(renda.index)
