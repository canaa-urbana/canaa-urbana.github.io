"""
Cliente genérico para a API SIDRA/Agregados do IBGE (E1 — Fase 1 do PLANO.md).

Em vez de fixar à mão o código de cada variável/classificação por tabela
(risco de esquecer uma categoria ou usar o nome errado), `fetch_tabela()`
consulta primeiro `.../agregados/{id}/metadados` e monta a URL de valores
pedindo `v/allxp` (todas as variáveis, exceto percentuais) e `c{id}/all`
para cada classificação da tabela — cobre a tabela inteira sem exigir
conhecimento prévio do esquema.

Grava, por tabela, em `data/processed/ibge/`:
    {tabela}_bruto.json   resposta crua da API (auditoria/reprodutibilidade)
    {tabela}.parquet      tidy: uma linha por célula, colunas D*N renomeadas
                           para os nomes das classificações + `valor`
    _index.parquet        catálogo de todas as chamadas desta sessão:
                           tabela, nome, url, nivel, localidade, data_acesso,
                           n_linhas

Regra de sigilo: estes dados são agregados públicos do IBGE — nunca
microdados — por isso não passam pelo gate de revelação (`disclosure_check.py`).
"""
from __future__ import annotations

import datetime as _dt
import json
import time
from pathlib import Path

import pandas as pd
import requests

BASE = Path(__file__).resolve().parent.parent.parent
OUT = BASE / "data" / "processed" / "ibge"
OUT.mkdir(parents=True, exist_ok=True)

META_URL = "https://servicodados.ibge.gov.br/api/v3/agregados/{tabela}/metadados"
VALUES_URL = "https://apisidra.ibge.gov.br/values/t/{tabela}/{nivel}/{codigo}/{resto}"

_SUPRIMIDOS = {"X", "...", "-", "..", "NA", ""}


def metadados(tabela: int) -> dict:
    r = requests.get(META_URL.format(tabela=tabela), timeout=30)
    r.raise_for_status()
    return r.json()


def montar_url(
    tabela: int, nivel: str, codigo: str, meta: dict,
    periodos: str = "all", classificacoes: dict[int, str] | None = None,
) -> str:
    """`classificacoes` permite restringir categorias por id (ex.: {1: "1,2"}
    para só urbana/rural em vez de "all", quando a tabela tem categorias
    demais e a API rejeita `all` em alguma delas)."""
    partes = [f"v/allxp", f"p/{periodos}"]
    for c in meta.get("classificacoes", []):
        cid = c["id"]
        cats = (classificacoes or {}).get(cid, "all")
        partes.append(f"c{cid}/{cats}")
    return VALUES_URL.format(tabela=tabela, nivel=nivel, codigo=codigo, resto="/".join(partes))


def fetch_tabela(
    tabela: int, nivel: str = "n6", codigo: str = "1502152",
    periodos: str = "all", classificacoes: dict[int, str] | None = None,
    nome_saida: str | None = None, pausa: float = 0.3,
) -> pd.DataFrame:
    """Baixa uma tabela inteira (todas as variáveis e classificações) para
    uma localidade, grava bruto+tidy e devolve o DataFrame tidy.
    Levanta `requests.HTTPError` se a API rejeitar a URL (ex.: nível
    territorial incompatível) — o chamador decide como tratar."""
    meta = metadados(tabela)
    url = montar_url(tabela, nivel, codigo, meta, periodos, classificacoes)
    r = requests.get(url, timeout=90)
    r.raise_for_status()
    dados = r.json()
    time.sleep(pausa)

    nome = nome_saida or f"t{tabela}"
    (OUT / f"{nome}_bruto.json").write_text(
        json.dumps({"url": url, "resposta": dados}, ensure_ascii=False), encoding="utf-8"
    )

    if not dados or len(dados) < 2:
        df = pd.DataFrame()
    else:
        cabecalho, linhas = dados[0], dados[1:]
        registros = []
        for row in linhas:
            valor_raw = row.get("V")
            valor = None if valor_raw in _SUPRIMIDOS else _to_num(valor_raw)
            rec = {"valor": valor, "unidade": row.get("MN")}
            for chave, rotulo in cabecalho.items():
                if chave.endswith("C") and chave not in ("NC", "MC"):
                    base = chave[:-1]
                    rec[f"{cabecalho.get(base + 'N', base)}_codigo"] = row.get(chave)
                elif chave.endswith("N") and chave not in ("NN", "MN"):
                    rec[cabecalho[chave]] = row.get(chave)
            registros.append(rec)
        df = pd.DataFrame(registros)
        df.attrs["nome_tabela"] = meta.get("nome", "")
        df.attrs["url"] = url
        df.to_parquet(OUT / f"{nome}.parquet", index=False)

    _registrar_indice(tabela, meta.get("nome", ""), url, nivel, codigo, len(df))
    return df


def _to_num(v: str):
    try:
        if "." in v or "," in v:
            return float(v.replace(",", "."))
        return int(v)
    except (ValueError, AttributeError):
        return v


def _registrar_indice(tabela, nome, url, nivel, codigo, n_linhas) -> None:
    idx_path = OUT / "_index.parquet"
    linha = pd.DataFrame([{
        "tabela": tabela, "nome": nome, "url": url, "nivel": nivel,
        "localidade": codigo, "data_acesso": _dt.date.today().isoformat(),
        "n_linhas": n_linhas,
    }])
    if idx_path.exists():
        atual = pd.read_parquet(idx_path)
        atual = atual[~((atual["tabela"] == tabela) & (atual["localidade"] == codigo))]
        linha = pd.concat([atual, linha], ignore_index=True)
    linha.to_parquet(idx_path, index=False)
