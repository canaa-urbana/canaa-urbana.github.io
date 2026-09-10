"""Leitura genérica de arquivos de largura fixa a partir dos layouts em JSON
gerados por `scripts/00c_layouts.py`. Nenhuma posição de coluna é escrita à mão
fora daquele parser — este módulo só consome o resultado (mesma convenção do
projeto irmão migracoes-br, regra "nenhuma posição de coluna escrita à mão").
"""
import json
from pathlib import Path
from typing import Iterator

import pandas as pd

LAYOUTS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "interim" / "layouts"


def load_layout(censo: int, registro: str) -> list[dict]:
    p = LAYOUTS_DIR / f"{censo}_{registro}.json"
    if not p.exists():
        raise FileNotFoundError(
            f"layout {p} não existe — rode scripts/00c_layouts.py antes de parsear dados"
        )
    return json.loads(p.read_text())


def colspecs_para(layout: list[dict], campos: list[str]) -> tuple[list[tuple[int, int]], list[str]]:
    """Monta (colspecs, nomes) na ORDEM DE `campos` para os campos pedidos."""
    by_nome = {c["nome"]: c for c in layout}
    faltando = [f for f in campos if f not in by_nome]
    if faltando:
        disponiveis = sorted(by_nome)
        raise KeyError(
            f"variáveis não encontradas no layout: {faltando}\n"
            f"(primeiras disponíveis: {disponiveis[:20]}...)"
        )
    colspecs = [(by_nome[f]["start0"], by_nome[f]["end"]) for f in campos]
    return colspecs, list(campos)


def ler_fwf(
    path: str | Path,
    censo: int,
    registro: str,
    campos: list[str],
    encoding: str = "latin-1",
    chunksize: int | None = None,
) -> pd.DataFrame | Iterator[pd.DataFrame]:
    """Lê um arquivo de largura fixa selecionando só `campos`, todos como string.

    Retorna um DataFrame (chunksize=None) ou um iterador de DataFrames
    (chunksize=N) — usar iterador para os arquivos grandes (SP, MG, BA...).
    Valores em branco (todos espaços) viram string vazia; a conversão para
    numérico/categórico fica a cargo do parser específico de cada censo.
    """
    layout = load_layout(censo, registro)
    colspecs, nomes = colspecs_para(layout, campos)
    kwargs = dict(
        colspecs=colspecs,
        names=nomes,
        dtype=str,
        encoding=encoding,
        na_filter=False,
    )
    if chunksize:
        kwargs["chunksize"] = chunksize
    return pd.read_fwf(path, **kwargs)


def to_num(serie: pd.Series) -> pd.Series:
    """Converte uma coluna string (com brancos/espaços = ausente) para numérico."""
    s = serie.str.strip()
    return pd.to_numeric(s.replace("", pd.NA), errors="coerce")
