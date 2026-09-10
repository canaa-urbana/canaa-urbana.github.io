"""
Supressão de célula para publicação — regra 2 do CLAUDE.md (acesso controlado).

Nenhuma tabela ou figura publicada em `artigos/` ou `output/` pode expor uma célula
(cruzamento de categorias) sustentada por menos de `LIMIAR_CELULA` observações
amostrais, mesmo que o valor esteja expandido pelo peso — N amostral pequeno é o
risco de identificação, não a magnitude da população estimada.

Uso:
    from lib.publicacao import LIMIAR_CELULA, marcar_supressao, resumo_supressao

    tab = tab.assign(**marcar_supressao(tab, col_n="n_amostral"))
    tab.loc[tab["suprimido"], ["valor", "n_expandido"]] = pd.NA
"""
from pathlib import Path

import pandas as pd

LIMIAR_CELULA = 20


def marcar_supressao(df: pd.DataFrame, col_n: str = "n_amostral") -> pd.Series:
    """Série booleana `suprimido` — True onde `col_n` < LIMIAR_CELULA (inclusive
    NaN, tratado como supressão por ausência de contagem)."""
    n = pd.to_numeric(df[col_n], errors="coerce")
    return (n < LIMIAR_CELULA) | n.isna()


def aplicar_supressao(
    df: pd.DataFrame, cols_valor: list[str], col_n: str = "n_amostral"
) -> pd.DataFrame:
    """Retorna cópia de `df` com `suprimido` adicionada e `cols_valor` zerados
    (NaN) nas linhas suprimidas — a forma pronta para gravar em `tabelas/`."""
    out = df.copy()
    out["suprimido"] = marcar_supressao(out, col_n)
    out.loc[out["suprimido"], cols_valor] = pd.NA
    return out


def resumo_supressao(df: pd.DataFrame) -> dict:
    """Conta linhas suprimidas vs. total — para log/relatório de `04_validar.py`."""
    if "suprimido" not in df.columns:
        return {"total": len(df), "suprimidas": 0, "pct": 0.0}
    total = len(df)
    supr = int(df["suprimido"].sum())
    return {"total": total, "suprimidas": supr, "pct": 100 * supr / total if total else 0.0}


def varrer_diretorio(diretorio: Path, col_n: str = "n_amostral") -> list[dict]:
    """Varre todo `.csv`/`.parquet` sob `diretorio` (tipicamente `artigos/*/tabelas/`)
    e falha (retorna violações) se alguma linha tiver `col_n` < LIMIAR_CELULA com
    algum valor numérico não nulo em coluna que não seja `suprimido`/`n_amostral`/
    `n_expandido`. Usado por `04_validar.py`."""
    violacoes = []
    diretorio = Path(diretorio)
    for f in list(diretorio.rglob("*.csv")) + list(diretorio.rglob("*.parquet")):
        df = pd.read_csv(f) if f.suffix == ".csv" else pd.read_parquet(f)
        if col_n not in df.columns:
            continue
        supr = marcar_supressao(df, col_n)
        cols_dado = [
            c for c in df.columns
            if c not in {col_n, "n_expandido", "suprimido", col_n.replace("n_amostral", "n")}
        ]
        vazadas = df.loc[supr, cols_dado].notna().any(axis=1)
        if vazadas.any():
            violacoes.append({
                "arquivo": str(f),
                "linhas_vazadas": int(vazadas.sum()),
            })
    return violacoes
