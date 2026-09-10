"""
Camadas de referência na grade de 30 m da sede (E3b): rótulos de treino,
máscara de mineração e produtos de comparação. Tudo público; nada de microdado.

  areas_urbanizadas(ano)  IBGE AU 2019 (revisado) / 2022 rasterizadas:
                          1 densa, 2 pouco densa, 3 loteamento vazio, 4 outros equipamentos
  mapbiomas(ano)          Col. 11, 30 m, classe MapBiomas por pixel (nearest)
  mapbiomas10(ano)        Col. 4, 10 m, fração da classe 24 por célula de 30 m
  wsf_evolution()         ano de assentamento WSF-Evo (1985–2015; 0 = nunca)
  wsf2019()               fração construída WSF2019 (10 m → 30 m)
  ghsl(epoca)             fração construída GHS-BUILT-S (m² por célula de 100 m → fração)
  mascara_mineracao()     MapBiomas 30 (união 1985–2025) dilatada 1 km ∪ concessões de
                          lavra ANM/SIGMINE (WFS, fase 'CONCESSÃO DE LAVRA' e
                          'LAVRA GARIMPEIRA') restritas a <= 3 km da lavra observada,
                          menos os polígonos de área urbanizada da AU 2022 — gravada em data/processed/geo/mascara_mineracao_30m.tif
                          e os polígonos ANM em data/processed/geo/anm_lavra.parquet
"""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
import requests
from rasterio.enums import Resampling
from rasterio.features import rasterize
from scipy.ndimage import binary_dilation

from .grade import GRADE10, GRADE30, CRS_METRICO, Grade, agregar_3x3, escrever, ler_para_grade

BASE = Path(__file__).resolve().parent.parent.parent
PROD = BASE / "data" / "interim" / "produtos"
GEO = BASE / "data" / "processed" / "geo"

AU_CLASSES = {("Densa", "Área urbanizada"): 1, ("Pouco densa", "Área urbanizada"): 2,
              ("Loteamento vazio", "Loteamento vazio"): 3,
              ("Densa", "Outros equipamentos urbanos"): 4, ("Pouco densa", "Outros equipamentos urbanos"): 4}

ANM_URL = ("https://geo.anm.gov.br/arcgis/rest/services/SIGMINE/dados_anm/MapServer/0/query"
           "?where=UF%3D%27PA%27+AND+(FASE%3D%27CONCESS%C3%83O+DE+LAVRA%27+OR+FASE%3D%27LAVRA+GARIMPEIRA%27)"
           "&geometry=-50.5,-6.8,-49.6,-6.2&geometryType=esriGeometryEnvelope&inSR=4326"
           "&outFields=PROCESSO,ANO,FASE,NOME,SUBS,AREA_HA&returnGeometry=true&outSR=4326&f=geojson")


def _au_gdf(ano: int) -> gpd.GeoDataFrame:
    nome = {2019: "areas_urbanizadas_2019_revisado.parquet", 2022: "areas_urbanizadas_2022.parquet"}[ano]
    g = gpd.read_parquet(PROD / "areas_urbanizadas" / nome).to_crs(CRS_METRICO)
    g["classe"] = [AU_CLASSES.get((d, t), 0) for d, t in zip(g["Densidade"], g["Tipo"])]
    return g


def areas_urbanizadas(ano: int, grade: Grade = GRADE30) -> np.ndarray:
    g = _au_gdf(ano)
    g = g[g["classe"] > 0]
    # loteamento vazio por último não sobrescreve área urbanizada (ordem: 4,3,2,1 → 1 vence)
    shapes = [(geom, int(c)) for geom, c in sorted(zip(g.geometry, g["classe"]), key=lambda x: -x[1])]
    return rasterize(shapes, out_shape=grade.shape, transform=grade.transform, fill=0, dtype="uint8",
                     all_touched=False)


def mapbiomas(ano: int, grade: Grade = GRADE30) -> np.ndarray:
    return ler_para_grade(PROD / "mapbiomas_col11" / f"mapbiomas_col11_{ano}.tif", grade, Resampling.nearest)


def mapbiomas10_frac24(ano: int) -> np.ndarray:
    a = ler_para_grade(PROD / "mapbiomas_col4_10m" / f"mapbiomas_col4_10m_{ano}.tif", GRADE10, Resampling.nearest)
    return agregar_3x3((a == 24).astype(np.float32), np.mean)


def wsf_evolution() -> np.ndarray:
    return ler_para_grade(PROD / "wsf" / "wsf_evolution.tif", GRADE30, Resampling.nearest)


def wsf2019() -> np.ndarray:
    a = ler_para_grade(PROD / "wsf" / "wsf2019.tif", GRADE10, Resampling.nearest)
    return agregar_3x3((a > 0).astype(np.float32), np.mean)


def ghsl(epoca: int) -> np.ndarray:
    a = ler_para_grade(PROD / "ghsl" / f"ghs_built_s_{epoca}.tif", GRADE30, Resampling.bilinear, dtype="float32")
    a = np.where(a >= 65535, 0, a)
    return np.clip(a / 10000.0, 0, 1)  # m² construídos por célula de 100 m → fração


def anm_lavra() -> gpd.GeoDataFrame:
    dest = GEO / "anm_lavra.parquet"
    if dest.exists():
        return gpd.read_parquet(dest)
    r = requests.get(ANM_URL, timeout=120)
    r.raise_for_status()
    gj = r.json()
    g = gpd.GeoDataFrame.from_features(gj["features"], crs=4326).to_crs(CRS_METRICO)
    g["acessado_em"] = "2026-09-10"
    g.to_parquet(dest)
    return g


def mascara_mineracao(regravar: bool = False) -> np.ndarray:
    dest = GEO / "mascara_mineracao_30m.tif"
    if dest.exists() and not regravar:
        with rasterio.open(dest) as s:
            return s.read(1).astype(bool)
    uniao = np.zeros(GRADE30.shape, bool)
    for ano in range(1985, 2026):
        uniao |= mapbiomas(ano) == 30
    raio_px = int(round(1000 / 30))
    yy, xx = np.ogrid[-raio_px:raio_px + 1, -raio_px:raio_px + 1]
    disco = (xx ** 2 + yy ** 2) <= raio_px ** 2
    mb_dil = binary_dilation(uniao, structure=disco)
    try:
        anm = anm_lavra()
        anm_r = rasterize([(g, 1) for g in anm.geometry], out_shape=GRADE30.shape,
                          transform=GRADE30.transform, fill=0, dtype="uint8").astype(bool)
        # a concessão é limite jurídico (a de cobre da Vale tem 97,8 mil ha): só conta
        # como mineração a parte a ≤ 3 km de lavra observada pelo MapBiomas
        r3 = int(round(3000 / 30))
        yy3, xx3 = np.ogrid[-r3:r3 + 1, -r3:r3 + 1]
        anm_r &= binary_dilation(uniao, structure=(xx3 ** 2 + yy3 ** 2) <= r3 ** 2)
        origem = f"MapBiomas 30 (1985–2025) dilatado 1 km ∪ concessões de lavra ANM ({len(anm)} processos) a <= 3 km da lavra observada"
    except Exception as exc:  # ANM fora do ar: fica só o MapBiomas, declarado
        anm_r = np.zeros(GRADE30.shape, bool)
        origem = f"MapBiomas 30 (1985–2025) dilatado 1 km (ANM indisponível: {type(exc).__name__})"
    masc = mb_dil | anm_r
    au = areas_urbanizadas(2022)
    masc &= ~np.isin(au, [1, 2, 4])  # a sede nunca entra na máscara
    escrever(dest, [masc.astype(np.uint8)], ["mascara_mineracao"], GRADE30, nodata=None,
             tags={"origem": origem, "frac_mapbiomas30": f"{uniao.mean():.4f}", "frac_mascara": f"{masc.mean():.4f}"})
    (GEO / "mascara_mineracao_30m.json").write_text(json.dumps({
        "origem": origem, "area_ha": float(masc.sum() * 0.09), "area_mapbiomas30_ha": float(uniao.sum() * 0.09),
        "area_anm_ha": float(anm_r.sum() * 0.09)}, ensure_ascii=False, indent=2), "utf-8")
    return masc
