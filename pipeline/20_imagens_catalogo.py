"""
E3a / Fase 3 passo 1 (PLANO.md) — AOI fixa e catálogo STAC das cenas
disponíveis sobre Canaã dos Carajás, de 1972 (Landsat MSS) a 2026
(Sentinel-2 / CBERS-4A WPM).

Nada é baixado aqui: o script só consulta os catálogos e grava um inventário
por cena (`data/interim/catalogo_cenas.parquet`), que E3b usa para escolher as
cenas de cada composição anual e as cenas de alta resolução de validação.

AOI (CLAUDE.md: sempre em CRS métrico para área/distância):
  - `aoi_municipio`: polígono municipal atual, IBGE Malhas API v4, qualidade
    máxima (o município foi criado em 1994; a AOI atual é aplicada
    retroativamente a todos os anos, inclusive 1979-1990 — nota metodológica
    obrigatória no artigo).
  - `aoi_sede`: janela da sede, bbox −49,99 / −6,60 / −49,75 / −6,40 (PLANO.md
    Fase 3), onde a mancha urbana é classificada.
  Ambos salvos em EPSG:31982 (SIRGAS 2000 / UTM 22S) e em 4326 (para o STAC e
  para o mapa do dashboard, que é WebMercator).

Catálogos consultados (todos sem conta; verificados em 09/09/2026):
  - Planetary Computer  `landsat-c2-l2` (TM/ETM+/OLI, 1984→), `landsat-c2-l1`
    (MSS 1972-1983), `sentinel-2-l2a` (2017→)
  - Element84 earth-search `sentinel-2-l2a` (redundância de S2)
  - INPE BDC `landsat-lgi-1` (MSS/TM históricos), `CB2B-HRC-L2-DN-1`,
    `CB4A-WPM-L4-DN-1`, `CB4A-WPM-PCA-FUSED-1`, `CB4-PAN5M-L4-DN-1`,
    `CB4-MUX-L4-DN-1`, `S2_L2A-1`

Uso:
    .venv/bin/python pipeline/20_imagens_catalogo.py
    .venv/bin/python pipeline/20_imagens_catalogo.py --resumo   # só reimprime
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from pystac_client import Client
from shapely.geometry import box, shape

BASE = Path(__file__).resolve().parent.parent
OUT_INTERIM = BASE / "data" / "interim"
OUT_GEO = BASE / "data" / "processed" / "geo"
OUT_WEB = BASE / "web" / "public" / "data" / "geo"
for d in (OUT_INTERIM, OUT_GEO, OUT_WEB):
    d.mkdir(parents=True, exist_ok=True)

MUNICIPIO = "1502152"
EPSG_METRICO = 31982
# Fase 3 do PLANO.md — janela da sede (oeste, sul, leste, norte)
BBOX_SEDE = (-49.99, -6.60, -49.75, -6.40)

CAT_PC = "https://planetarycomputer.microsoft.com/api/stac/v1"
CAT_E84 = "https://earth-search.aws.element84.com/v1"
CAT_BDC = "https://data.inpe.br/bdc/stac/v1"

# (rótulo, endpoint, coleção, intervalo de datas)
CONSULTAS = [
    ("PC/landsat-mss", CAT_PC, "landsat-c2-l1", "1972-01-01/1983-12-31"),
    ("PC/landsat-tm-oli", CAT_PC, "landsat-c2-l2", "1984-01-01/2026-12-31"),
    ("PC/sentinel-2", CAT_PC, "sentinel-2-l2a", "2015-06-01/2026-12-31"),
    ("E84/sentinel-2", CAT_E84, "sentinel-2-l2a", "2015-06-01/2026-12-31"),
    ("BDC/landsat-historico", CAT_BDC, "landsat-lgi-1", "1972-01-01/1990-12-31"),
    ("BDC/cbers2b-hrc", CAT_BDC, "CB2B-HRC-L2-DN-1", "2007-01-01/2011-12-31"),
    ("BDC/cbers4a-wpm", CAT_BDC, "CB4A-WPM-L4-DN-1", "2019-01-01/2026-12-31"),
    ("BDC/cbers4a-wpm-fused", CAT_BDC, "CB4A-WPM-PCA-FUSED-1", "2019-01-01/2026-12-31"),
    ("BDC/cbers4-pan5m", CAT_BDC, "CB4-PAN5M-L4-DN-1", "2014-01-01/2026-12-31"),
    ("BDC/cbers4-mux", CAT_BDC, "CB4-MUX-L4-DN-1", "2014-01-01/2026-12-31"),
    ("BDC/sentinel-2", CAT_BDC, "S2_L2A-1", "2017-01-01/2026-12-31"),
]

# Chaves de propriedade que variam entre catálogos — resolvidas por tentativa,
# nunca assumidas (o BDC não usa o mesmo vocabulário do PC/E84).
CHAVES_NUVEM = ("eo:cloud_cover", "cloud_cover", "cloudcover")
CHAVES_PLATAFORMA = ("platform", "constellation", "bdc:instrument")
CHAVES_INSTRUMENTO = ("instruments", "instrument", "bdc:instrument")
CHAVES_PATH = ("landsat:wrs_path", "wrs_path", "bdc:path", "path")
CHAVES_ROW = ("landsat:wrs_row", "wrs_row", "bdc:row", "row")
CHAVES_TILE = ("s2:mgrs_tile", "grid:code", "mgrs:grid_square", "bdc:tiles")


def _primeiro(props: dict, chaves) -> object | None:
    for k in chaves:
        v = props.get(k)
        if v not in (None, "", []):
            # `instruments`/`bdc:tiles` chegam como lista; o parquet precisa de escalar
            return ",".join(str(x) for x in v) if isinstance(v, list) else v
    return None


def aoi() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Polígono municipal (API v4) e janela da sede, em 4326 e 31982."""
    cache = OUT_GEO / "aoi_municipio_4326.json"
    if not cache.exists():
        url = (
            f"https://servicodados.ibge.gov.br/api/v4/malhas/municipios/{MUNICIPIO}"
            "?formato=application/vnd.geo+json&qualidade=maxima"
        )
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        cache.write_text(json.dumps(r.json()), encoding="utf-8")
    gj = json.loads(cache.read_text(encoding="utf-8"))
    mun = gpd.GeoDataFrame(
        {"nome": ["Canaã dos Carajás"], "codigo": [MUNICIPIO]},
        geometry=[shape(gj["features"][0]["geometry"])],
        crs=4326,
    )
    sede = gpd.GeoDataFrame(
        {"nome": ["Janela da sede"]}, geometry=[box(*BBOX_SEDE)], crs=4326
    )
    for nome, gdf in (("aoi_municipio", mun), ("aoi_sede", sede)):
        gdf.to_crs(EPSG_METRICO).to_parquet(OUT_GEO / f"{nome}_31982.parquet")
        gdf.to_file(OUT_WEB / f"{nome}.json", driver="GeoJSON")
    return mun, sede


def catalogar(bbox: tuple[float, float, float, float]) -> pd.DataFrame:
    linhas, falhas = [], []
    for rotulo, endpoint, colecao, datas in CONSULTAS:
        try:
            cliente = Client.open(endpoint)
            itens = list(
                cliente.search(collections=[colecao], bbox=list(bbox), datetime=datas).items()
            )
        except Exception as exc:  # catálogo fora do ar ou coleção renomeada
            falhas.append(f"{rotulo}: {type(exc).__name__}: {exc}")
            print(f"  ! {rotulo:24s} FALHOU — {type(exc).__name__}")
            continue
        for it in itens:
            p = it.properties
            linhas.append(
                {
                    "fonte": rotulo,
                    "endpoint": endpoint,
                    "colecao": colecao,
                    "item_id": it.id,
                    "datahora": pd.Timestamp(it.datetime),
                    "ano": it.datetime.year,
                    "mes": it.datetime.month,
                    "plataforma": _primeiro(p, CHAVES_PLATAFORMA),
                    "instrumento": _primeiro(p, CHAVES_INSTRUMENTO),
                    "nuvem": _primeiro(p, CHAVES_NUVEM),
                    "wrs_path": _primeiro(p, CHAVES_PATH),
                    "wrs_row": _primeiro(p, CHAVES_ROW),
                    "tile": _primeiro(p, CHAVES_TILE),
                    "n_assets": len(it.assets),
                    "href_json": it.get_self_href(),
                }
            )
        print(f"  · {rotulo:24s} {len(itens):5d} itens")
    if falhas:
        (OUT_INTERIM / "catalogo_cenas_falhas.txt").write_text("\n".join(falhas), "utf-8")
    df = pd.DataFrame(linhas)
    # `nuvem` chega como str em alguns catálogos do BDC
    df["nuvem"] = pd.to_numeric(df["nuvem"], errors="coerce")
    df["estacao_seca"] = df["mes"].between(6, 9)
    return df.sort_values(["ano", "datahora", "fonte"]).reset_index(drop=True)


def resumir(df: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por ano × fonte: quantas cenas, quantas em estação seca e
    quantas com nuvem < 20% — é o que E3b consulta para montar a composição."""
    g = df.groupby(["ano", "fonte"], as_index=False).agg(
        cenas=("item_id", "count"),
        secas=("estacao_seca", "sum"),
        nuvem_min=("nuvem", "min"),
        nuvem_mediana=("nuvem", "median"),
    )
    limpas = (
        df[(df["nuvem"] < 20) & df["estacao_seca"]]
        .groupby(["ano", "fonte"], as_index=False)
        .agg(secas_limpas=("item_id", "count"))
    )
    return g.merge(limpas, on=["ano", "fonte"], how="left").fillna({"secas_limpas": 0})


def main() -> None:
    print("AOI …")
    mun, sede = aoi()
    area_km2 = mun.to_crs(EPSG_METRICO).area.iloc[0] / 1e6
    print(f"  município: {area_km2:,.1f} km² (SIDRA t/4714: 3.146,821 km²)")
    print(f"  sede: bbox {BBOX_SEDE}")

    print("Catálogos STAC …")
    df = catalogar(BBOX_SEDE)
    df.to_parquet(OUT_INTERIM / "catalogo_cenas.parquet")
    resumo = resumir(df)
    resumo.to_parquet(OUT_GEO / "catalogo_cenas_resumo.parquet")

    print(f"\n{len(df):,} cenas, {df['ano'].min()}–{df['ano'].max()}")
    por_fonte = df.groupby("fonte").agg(
        cenas=("item_id", "count"), de=("ano", "min"), ate=("ano", "max")
    )
    print(por_fonte.to_string())
    anos_sem_landsat = sorted(
        set(range(1984, 2027))
        - set(df.loc[df["fonte"].str.contains("landsat|sentinel"), "ano"].unique())
    )
    print(f"\nanos 1984–2026 sem Landsat/Sentinel: {anos_sem_landsat or 'nenhum'}")
    otimas = df[(df["nuvem"] < 10) & df["estacao_seca"]]
    print(f"cenas estação seca com nuvem < 10%: {len(otimas):,}")


if __name__ == "__main__":
    if "--resumo" in sys.argv:
        df = pd.read_parquet(OUT_INTERIM / "catalogo_cenas.parquet")
        print(resumir(df).to_string())
    else:
        main()
