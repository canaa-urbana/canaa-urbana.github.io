"""
E3c / Fase 3 passo 7 (PLANO.md) — camadas do dashboard em `web/public/data/geo/`.

Tudo aqui é produto de sensoriamento remoto ou dado público (nenhum microdado):

  vetores (GeoJSON 4326, coordenadas com 5 casas ≈ 1 m, simplificados com
  tolerância de meio pixel a 30 m, 1 pixel a 10 m e 40 m no MSS, para tirar o degrau do raster):
    mancha/mancha_propria_<ano>.json    1984–2026, classes 1 sede, 2 outros núcleos,
                                        3 construído em mineração, 4 loteamento vazio
    mancha/mancha_propria10_<ano>.json  2017–2026, série secundária Sentinel-2
    expansao_ano_urbanizacao.json       1º ano urbano (classes 1–2), um polígono por ano
    mineracao_mascara.json              máscara de mineração (MapBiomas 30 + 1 km ∪ ANM)
    anm_lavra.json                      concessões de lavra ANM/SIGMINE (recorte da AOI municipal)
    clareira_mss_<ano>.json             1973 e 1982 (MSS, clareira NDVI < Otsu)
    osm_vias.json                       rodovias principais e ferrovia (OpenStreetMap, Overpass)
    osm_ferrovia.json                   Ramal Ferroviário do Sudeste do Pará (S11D–Parauapebas),
                                        consulta regional (AOI municipal + ~15 km)
    osm_rodovias_regiao.json            rodovias trunk/primary/secondary na mesma janela regional
    nucleo_historico.json               centroide da sede de 1990
    wsf_evolution.json                  WSF-Evolution (DLR) — 1º ano assentado por pixel, 1985–2015
    wsf2019.json                        World Settlement Footprint 2019 (DLR, 10 m), classe única
    ghsl/ghsl_<ano>.json                GHSL GHS-BUILT-S R2023A (JRC, 100 m), 1975–2030,
                                        classes de fração construída (5–20/20–40/40–60/≥60 %)

  imagens (WebP com alfa, pré-projetadas em EPSG:3857 para `image` source do MapLibre):
    img/landsat_<ano>_cor.webp          1984–2026, cor natural (red/green/blue)
    img/landsat_<ano>_falsacor.webp     1984–2026, SWIR1/NIR/red (construído em magenta)
    img/s2_<ano>_cor.webp               2017–2026, Sentinel-2 10 m
    img/mss_<ano>_falsacor.webp         1973 e 1982 (NIR/red/green, DN, estiramento por ano)
  O estiramento é FIXO por sensor (percentis 2–98 do conjunto de anos, na escala
  ETM+ harmonizada de `22_compor_anual.py`; um para Landsat, outro para
  Sentinel-2): mudança de cor entre anos do mesmo sensor é mudança da superfície,
  não do contraste.

  manifesto:
    camadas.json   id, título, tipo, arquivo (com {ano}), anos, cores com a fonte
                   de cada cor (legenda MapBiomas Col. 11, estilo .qml oficial do
                   IBGE, tokens Ardósia), coordenadas das imagens, atribuição e licença.

Uso:
    .venv/bin/python pipeline/27_tiles_camadas.py            # tudo
    .venv/bin/python pipeline/27_tiles_camadas.py vetores    # só vetores
    .venv/bin/python pipeline/27_tiles_camadas.py imagens    # só imagens
    .venv/bin/python pipeline/27_tiles_camadas.py produtos   # só produtos externos (WSF/GHSL/OSM regional)
    .venv/bin/python pipeline/27_tiles_camadas.py manifesto  # só camadas.json
"""
from __future__ import annotations

import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import requests
import shapely
from PIL import Image
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.features import shapes
from rasterio.warp import calculate_default_transform, reproject, transform_bounds
from shapely.geometry import shape as to_shape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.grade import GRADE10, GRADE30, CRS_METRICO  # noqa: E402
from lib.legendas import ibge_qml, mapbiomas_hex, rampa_urbana  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
GEO = BASE / "data" / "processed" / "geo"
MANCHA = GEO / "mancha_propria"
COMP = BASE / "data" / "interim" / "composicoes"
PRODUTOS = BASE / "data" / "interim" / "produtos"
WEB = BASE / "web" / "public" / "data"
WEB_GEO = WEB / "geo"
WEB_M = WEB_GEO / "mancha"
WEB_IMG = WEB_GEO / "img"
WEB_GHSL = WEB_GEO / "ghsl"
for d in (WEB_M, WEB_IMG, WEB_GHSL):
    d.mkdir(parents=True, exist_ok=True)

NODATA = -32768
ESCALA = 10000
CLASSES = {1: "sede", 2: "outros_nucleos", 3: "construido_mineracao", 4: "loteamento_vazio"}
PRECISAO = 1e-5  # graus ≈ 1,1 m
SIMPLIF_30, SIMPLIF_10 = 15.0, 10.0  # metros (meio pixel a 30 m; 1 pixel a 10 m)
SIMPLIF_MSS = 40.0  # MSS tem 60–80 m nativos
NUCLEO_RAIO_M, NUCLEO_MAX_HA = 1000.0, 100.0  # clareira do núcleo do assentamento (MSS)
WEBP_Q = 80
EPSG_WEB = CRS.from_epsg(3857)
OVERPASS = "https://overpass-api.de/api/interpreter"
OVERPASS_ALT = "https://overpass.kumi.systems/api/interpreter"
ACESSO = "2026-09-10"
# GHSL GHS-BUILT-S: fração construída da célula (valor / ESCALA_GHSL m² por célula de 100x100 m)
ESCALA_GHSL = 10000
CLASSES_GHSL = [(1, 0.05, 0.20), (2, 0.20, 0.40), (3, 0.40, 0.60), (4, 0.60, 1.01)]


# ----------------------------------------------------------------------------
# utilidades
# ----------------------------------------------------------------------------

def _gravar_geojson(gdf: gpd.GeoDataFrame, destino: Path) -> int:
    """GeoJSON 4326 com coordenadas arredondadas; devolve bytes gravados."""
    g = gdf.to_crs(4326).copy()
    g["geometry"] = shapely.set_precision(g.geometry.values, PRECISAO)
    g = g[~g.geometry.is_empty]
    for c in g.columns:
        if c != "geometry" and pd.api.types.is_float_dtype(g[c]):
            g[c] = g[c].round(2)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(g.to_json(drop_id=True, separators=(",", ":")), "utf-8")
    return destino.stat().st_size


def _vetorizar(arr: np.ndarray, transform, valores: dict[int, str] | None = None) -> gpd.GeoDataFrame:
    geoms, vals = [], []
    for geom, v in shapes(arr.astype(np.int32), mask=arr > 0, transform=transform, connectivity=8):
        geoms.append(to_shape(geom))
        vals.append(int(v))
    return gpd.GeoDataFrame({"valor": vals}, geometry=geoms, crs=CRS_METRICO)


def _dissolver_simplificar(g: gpd.GeoDataFrame, por: str, tol: float) -> gpd.GeoDataFrame:
    if g.empty:
        return g
    area = g.assign(area_ha=g.geometry.area / 1e4).groupby(por)["area_ha"].sum()
    d = g.dissolve(by=por, as_index=False)
    d["geometry"] = d.geometry.simplify(tol, preserve_topology=True)
    d["area_ha"] = d[por].map(area)  # área do raster, não do polígono simplificado
    return d


# ----------------------------------------------------------------------------
# vetores
# ----------------------------------------------------------------------------

def manchas(res: int) -> dict[int, int]:
    tam = {}
    tol = SIMPLIF_30 if res == 30 else SIMPLIF_10
    sufixo = "" if res == 30 else "10"
    for p in sorted(MANCHA.glob(f"mancha{res}_*.tif")):
        ano = int(p.stem.split("_")[1])
        with rasterio.open(p) as s:
            cls, tr = s.read(1), s.transform
        g = _vetorizar(cls, tr).rename(columns={"valor": "classe"})
        g = _dissolver_simplificar(g, "classe", tol)
        g["nome"] = g["classe"].map(CLASSES)
        g["ano"] = ano
        tam[ano] = _gravar_geojson(g[["ano", "classe", "nome", "area_ha", "geometry"]],
                                   WEB_M / f"mancha_propria{sufixo}_{ano}.json")
    return tam


def expansao() -> int:
    with rasterio.open(MANCHA / "ano_urbanizacao30.tif") as s:
        a, tr = s.read(1), s.transform
    g = _vetorizar(np.where(a > 0, a, 0), tr).rename(columns={"valor": "ano_urbanizacao"})
    g = _dissolver_simplificar(g, "ano_urbanizacao", SIMPLIF_30)
    return _gravar_geojson(g[["ano_urbanizacao", "area_ha", "geometry"]], WEB_GEO / "expansao_ano_urbanizacao.json")


def apoio() -> dict[str, int]:
    tam = {}
    with rasterio.open(GEO / "mascara_mineracao_30m.tif") as s:
        m, tr = s.read(1), s.transform
    g = _dissolver_simplificar(_vetorizar(m, tr), "valor", SIMPLIF_30)
    tam["mineracao_mascara"] = _gravar_geojson(g[["area_ha", "geometry"]], WEB_GEO / "mineracao_mascara.json")

    anm = gpd.read_parquet(GEO / "anm_lavra.parquet").to_crs(CRS_METRICO)
    aoi = gpd.read_parquet(GEO / "aoi_municipio_31982.parquet")
    anm = gpd.clip(anm, aoi)
    anm["geometry"] = anm.geometry.simplify(20, preserve_topology=True)
    anm["area_ha_no_municipio"] = anm.geometry.area / 1e4
    cols = [c for c in ("PROCESSO", "FASE", "NOME", "SUBS", "AREA_HA", "area_ha_no_municipio") if c in anm.columns]
    tam["anm_lavra"] = _gravar_geojson(anm[cols + ["geometry"]], WEB_GEO / "anm_lavra.json")

    # Clareiras MSS (NDVI < Otsu): quase tudo é desmatamento agropecuário (≈ 18 mil ha em 1982).
    # Classe 1 = núcleo do assentamento: partes a até NUCLEO_RAIO_M do núcleo histórico e menores que
    # NUCLEO_MAX_HA (exclui o grande contínuo de pastagem que encosta no núcleo); classe 2 = demais
    # clareiras. Regra geométrica simples, declarada no manifesto.
    est = json.loads((WEB / "estatisticas_mancha.json").read_text("utf-8"))["nucleo_historico"]
    ponto_nucleo = gpd.GeoSeries(gpd.points_from_xy([est["lon"]], [est["lat"]]), crs=4326).to_crs(CRS_METRICO).iloc[0]
    for p in sorted(MANCHA.glob("clareira_mss_*.tif")):
        ano = int(p.stem.split("_")[-1])
        with rasterio.open(p) as s:
            c, tr = s.read(1), s.transform
        g = _dissolver_simplificar(_vetorizar(c, tr), "valor", SIMPLIF_MSS).explode(index_parts=False).reset_index(drop=True)
        g["area_ha"] = g.geometry.area / 1e4
        perto = g.geometry.distance(ponto_nucleo) <= NUCLEO_RAIO_M
        # antes do CEDERE II (1982) não há núcleo: em 1973 tudo é "demais clareiras"
        g["classe"] = np.where(perto & (g["area_ha"] < NUCLEO_MAX_HA) & (ano >= 1982), 1, 2)
        g["ano"] = ano
        tam[f"clareira_mss_{ano}"] = _gravar_geojson(g[["ano", "classe", "area_ha", "geometry"]], WEB_GEO / f"clareira_mss_{ano}.json")
        print(f"  clareira MSS {ano}: núcleo {g.loc[g.classe == 1, 'area_ha'].sum():.1f} ha, demais {g.loc[g.classe == 2, 'area_ha'].sum():.0f} ha")

    nuc = gpd.GeoDataFrame({"nome": ["Núcleo histórico (centroide da sede em 1990)"]},
                           geometry=gpd.points_from_xy([est["lon"]], [est["lat"]]), crs=4326)
    tam["nucleo_historico"] = _gravar_geojson(nuc, WEB_GEO / "nucleo_historico.json")

    tam["osm_vias"] = osm_vias()
    return tam


def _overpass(query: str) -> dict:
    """POST em Overpass com retentativa no espelho kumi.systems se o principal falhar."""
    ultimo = None
    for url in (OVERPASS, OVERPASS_ALT):
        try:
            r = requests.post(url, data={"data": query}, timeout=180,
                              headers={"User-Agent": "urban-canaa (pesquisa acadêmica)"})
            r.raise_for_status()
            return r.json()
        except Exception as exc:  # noqa: BLE001 — qualquer falha de rede/HTTP tenta o espelho
            ultimo = exc
    raise RuntimeError(f"Overpass indisponível em {OVERPASS} e {OVERPASS_ALT}: {ultimo}")


def _linhas_overpass(dados: dict, tipo_de) -> gpd.GeoDataFrame:
    from shapely.geometry import LineString

    linhas = []
    for el in dados.get("elements", []):
        pts = [(p["lon"], p["lat"]) for p in el.get("geometry", [])]
        if len(pts) < 2:
            continue
        t = el.get("tags", {})
        linhas.append({"osm_id": el["id"], "tipo": tipo_de(t), "nome": t.get("name", ""),
                       "ref": t.get("ref", ""), "geometry": LineString(pts)})
    return gpd.GeoDataFrame(linhas, crs=4326)


def osm_vias() -> int:
    """Rodovias principais e ferrovia na janela da sede, via Overpass (ODbL).
    Guarda cópia em data/processed/geo/osm_vias.parquet com a data de acesso."""
    cache = GEO / "osm_vias.parquet"
    if not cache.exists():
        w, s_, e, n = transform_bounds(CRS_METRICO, "EPSG:4326", *GRADE30.bounds)
        q = (f"[out:json][timeout:120];("
             f'way["highway"~"^(motorway|trunk|primary|secondary|tertiary)$"]({s_},{w},{n},{e});'
             f'way["railway"="rail"]({s_},{w},{n},{e}););out geom;')
        dados = _overpass(q)
        g = _linhas_overpass(dados, lambda t: "ferrovia" if "railway" in t else t.get("highway")).to_crs(CRS_METRICO)
        g["acessado_em"] = ACESSO
        g.to_parquet(cache)
    g = gpd.read_parquet(cache)
    g["geometry"] = g.geometry.simplify(5, preserve_topology=True)
    return _gravar_geojson(g[["tipo", "nome", "ref", "geometry"]], WEB_GEO / "osm_vias.json")


def _bbox_regiao(buffer_m: float = 15000) -> tuple[float, float, float, float]:
    """Bbox 4326 da AOI municipal + margem, para consultas Overpass de infraestrutura regional
    (o Ramal Ferroviário do Sudeste do Pará passa a oeste da sede, fora da janela da sede)."""
    aoi = gpd.read_parquet(GEO / "aoi_municipio_31982.parquet")
    poligono = aoi.union_all().buffer(buffer_m)
    return transform_bounds(CRS_METRICO, "EPSG:4326", *poligono.bounds)


def osm_ferrovia() -> int | None:
    """Ramal Ferroviário do Sudeste do Pará (S11D–Parauapebas), via Overpass (ODbL).
    Consulta a bbox regional (AOI municipal + ~15 km), não a janela da sede — `osm_vias()`
    não encontra ferrovia porque ela não passa pela sede. Pula com aviso se o Overpass falhar."""
    cache = GEO / "osm_ferrovia.parquet"
    if not cache.exists():
        w, s_, e, n = _bbox_regiao()
        q = f'[out:json][timeout:180];way["railway"~"^(rail|construction)$"]({s_},{w},{n},{e});out geom;'
        try:
            dados = _overpass(q)
        except Exception as exc:
            print(f"osm_ferrovia: Overpass indisponível, pulando ({exc})")
            return None
        g = _linhas_overpass(dados, lambda t: t.get("railway", "rail"))
        if g.empty:
            print("osm_ferrovia: nenhum elemento retornado pelo Overpass")
            return None
        g = g.to_crs(CRS_METRICO)
        g["acessado_em"] = ACESSO
        g.to_parquet(cache)
    g = gpd.read_parquet(cache)
    g["geometry"] = g.geometry.simplify(5, preserve_topology=True)
    return _gravar_geojson(g[["tipo", "nome", "ref", "geometry"]], WEB_GEO / "osm_ferrovia.json")


def osm_rodovias_regiao() -> int | None:
    """Rodovias trunk/primary/secondary (p.ex. PA-160, PA-275) na bbox regional, via Overpass
    (ODbL). Complementa `osm_vias()` (só a janela da sede). Pula com aviso se o Overpass falhar."""
    cache = GEO / "osm_rodovias_regiao.parquet"
    if not cache.exists():
        w, s_, e, n = _bbox_regiao()
        q = f'[out:json][timeout:180];way["highway"~"^(trunk|primary|secondary)$"]({s_},{w},{n},{e});out geom;'
        try:
            dados = _overpass(q)
        except Exception as exc:
            print(f"osm_rodovias_regiao: Overpass indisponível, pulando ({exc})")
            return None
        g = _linhas_overpass(dados, lambda t: t.get("highway"))
        if g.empty:
            print("osm_rodovias_regiao: nenhum elemento retornado pelo Overpass")
            return None
        g = g.to_crs(CRS_METRICO)
        g["acessado_em"] = ACESSO
        g.to_parquet(cache)
    g = gpd.read_parquet(cache)
    g["geometry"] = g.geometry.simplify(5, preserve_topology=True)
    return _gravar_geojson(g[["tipo", "nome", "ref", "geometry"]], WEB_GEO / "osm_rodovias_regiao.json")


# ----------------------------------------------------------------------------
# produtos externos de comparação (WSF, GHSL) — reprojetados para a grade do projeto
# ----------------------------------------------------------------------------

def _reprojetar_local(caminho: Path, grade, resampling: Resampling, dtype) -> np.ndarray:
    """Lê a banda 1 de um raster local inteiro (produtos pequenos) e reprojeta para `grade`."""
    with rasterio.open(caminho) as s:
        arr = s.read(1).astype(dtype)
        src_crs, src_tr = s.crs, s.transform
    dst = np.zeros(grade.shape, dtype)
    reproject(arr, dst, src_transform=src_tr, src_crs=src_crs,
              dst_transform=grade.transform, dst_crs=CRS_METRICO, resampling=resampling)
    return dst


def produtos_wsf() -> dict[str, int]:
    """WSF-Evolution e WSF 2019 (DLR/EOC, CC BY 4.0), reamostrados por vizinho mais próximo
    (dado categórico: ano de assentamento / máscara binária) para a grade do projeto."""
    tam = {}
    ano = _reprojetar_local(PRODUTOS / "wsf" / "wsf_evolution.tif", GRADE30, Resampling.nearest, np.int32)
    # 0 = nunca assentado (codificação de nodata do produto, não um ano real)
    g = _vetorizar(ano, GRADE30.transform).rename(columns={"valor": "ano"})
    g = _dissolver_simplificar(g, "ano", SIMPLIF_30)
    tam["wsf_evolution"] = _gravar_geojson(g[["ano", "area_ha", "geometry"]], WEB_GEO / "wsf_evolution.json")

    wsf19 = _reprojetar_local(PRODUTOS / "wsf" / "wsf2019.tif", GRADE10, Resampling.nearest, np.uint8)
    # assentamento = 255 (valor padrão do produto); alguns pixels isolados vêm como 1 (artefato de
    # borda da reprojeção original, < 0,001% da cena) — tratados como assentados (valor != 0)
    classe = np.where(wsf19 > 0, 1, 0).astype(np.int32)
    g2 = _vetorizar(classe, GRADE10.transform).rename(columns={"valor": "classe"})
    g2 = _dissolver_simplificar(g2, "classe", SIMPLIF_10)
    tam["wsf2019"] = _gravar_geojson(g2[["classe", "area_ha", "geometry"]], WEB_GEO / "wsf2019.json")
    return tam


def _grade_100m() -> tuple:
    """Grade auxiliar de 100 m em EPSG:31982, alinhada a múltiplos de 100 m, cobrindo a janela
    da sede (bounds de GRADE30) — para o GHSL, que não deve ser reamostrado para 30 m."""
    xmin, ymin, xmax, ymax = GRADE30.bounds
    x0, x1 = math.floor(xmin / 100) * 100, math.ceil(xmax / 100) * 100
    y0, y1 = math.floor(ymin / 100) * 100, math.ceil(ymax / 100) * 100
    tr = rasterio.transform.from_origin(x0, y1, 100, 100)
    return tr, int((x1 - x0) / 100), int((y1 - y0) / 100)


def produtos_ghsl() -> dict[str, int]:
    """GHSL GHS-BUILT-S R2023A (JRC, CC BY 4.0): superfície construída (m²/célula de 100 m),
    reprojetada de ESRI:54009 (Mollweide) para EPSG:31982 a 100 m, classificada por fração
    construída e vetorizada dissolvida por classe, sem simplificação (célula já quadrada)."""
    tam = {}
    tr100, w100, h100 = _grade_100m()
    for p in sorted((PRODUTOS / "ghsl").glob("ghs_built_s_*.tif")):
        ano = int(p.stem.split("_")[-1])
        with rasterio.open(p) as s:
            arr = s.read(1).astype(np.float32)
            src_crs, src_tr, nodata = s.crs, s.transform, s.nodata
        arr = np.where(arr == nodata, np.nan, arr)
        dst = np.full((h100, w100), np.nan, np.float32)
        reproject(arr, dst, src_transform=src_tr, src_crs=src_crs, dst_transform=tr100, dst_crs=CRS_METRICO,
                  resampling=Resampling.bilinear, src_nodata=np.nan, dst_nodata=np.nan)
        frac = np.nan_to_num(dst / ESCALA_GHSL, nan=0.0)
        classe = np.zeros((h100, w100), np.int32)
        for c, lo, hi in CLASSES_GHSL:
            classe[(frac >= lo) & (frac < hi)] = c
        g = _vetorizar(classe, tr100).rename(columns={"valor": "classe"})
        if g.empty:
            continue
        g = _dissolver_simplificar(g, "classe", 0.0)
        tam[f"ghsl_{ano}"] = _gravar_geojson(g[["classe", "area_ha", "geometry"]], WEB_GHSL / f"ghsl_{ano}.json")
    return tam


def produtos() -> dict[str, int]:
    """WSF, GHSL e infraestrutura regional (OSM) — camadas de comparação do dashboard."""
    tam = {}
    tam.update(produtos_wsf())
    tam.update(produtos_ghsl())
    r = osm_ferrovia()
    if r is not None:
        tam["osm_ferrovia"] = r
    r = osm_rodovias_regiao()
    if r is not None:
        tam["osm_rodovias_regiao"] = r
    return tam


# ----------------------------------------------------------------------------
# imagens
# ----------------------------------------------------------------------------

def _destino_3857(grade) -> tuple:
    tr, w, h = calculate_default_transform(CRS_METRICO, EPSG_WEB, grade.largura, grade.altura,
                                           *grade.bounds, resolution=grade.res)
    # cantos em lon/lat na ordem do MapLibre: sup-esq, sup-dir, inf-dir, inf-esq
    x0, y1 = tr.c, tr.f
    x1, y0 = x0 + w * tr.a, y1 + h * tr.e
    import pyproj

    t = pyproj.Transformer.from_crs(EPSG_WEB, "EPSG:4326", always_xy=True)
    cantos = [list(t.transform(x, y)) for x, y in ((x0, y1), (x1, y1), (x1, y0), (x0, y0))]
    cantos = [[round(a, 6), round(b, 6)] for a, b in cantos]
    return tr, w, h, cantos


def _para_3857(bandas: np.ndarray, valido: np.ndarray, grade, tr, w, h) -> tuple[np.ndarray, np.ndarray]:
    out = np.zeros((bandas.shape[0], h, w), np.float32)
    for i in range(bandas.shape[0]):
        reproject(bandas[i].astype(np.float32), out[i], src_transform=grade.transform, src_crs=CRS_METRICO,
                  dst_transform=tr, dst_crs=EPSG_WEB, resampling=Resampling.bilinear,
                  src_nodata=np.nan, dst_nodata=np.nan)
    alfa = np.zeros((h, w), np.uint8)
    reproject(valido.astype(np.uint8) * 255, alfa, src_transform=grade.transform, src_crs=CRS_METRICO,
              dst_transform=tr, dst_crs=EPSG_WEB, resampling=Resampling.nearest)
    return out, alfa


def _estirar(b: np.ndarray, lo: float, hi: float, gama: float = 1.0) -> np.ndarray:
    x = np.clip((b - lo) / (hi - lo), 0, 1) ** (1 / gama)
    return np.nan_to_num(x * 255).astype(np.uint8)


def _salvar_webp(rgb: list[np.ndarray], alfa: np.ndarray, destino: Path) -> int:
    img = Image.fromarray(np.dstack(rgb + [alfa]), "RGBA")
    img.save(destino, "WEBP", quality=WEBP_Q, method=6)
    return destino.stat().st_size


def _ler_comp(p: Path) -> tuple[np.ndarray, np.ndarray]:
    with rasterio.open(p) as s:
        a = s.read()[:6].astype(np.float32)
    valido = a[0] != NODATA
    return np.where(valido, a / ESCALA, np.nan), valido


def estiramento_fixo(prefixo: str) -> dict[str, tuple[float, float]]:
    """Percentis 2–98 por banda sobre uma amostra de todos os anos (escala ETM+)."""
    rng = np.random.default_rng(1502152)
    amostras = {i: [] for i in range(6)}
    for p in sorted(COMP.glob(f"{prefixo}_*.tif")):
        a, v = _ler_comp(p)
        idx = rng.choice(np.flatnonzero(v), min(20000, int(v.sum())), replace=False)
        for i in range(6):
            amostras[i].append(a[i].ravel()[idx])
    nomes = ["blue", "green", "red", "nir", "swir1", "swir2"]
    return {nomes[i]: (float(np.nanpercentile(np.concatenate(amostras[i]), 2)),
                       float(np.nanpercentile(np.concatenate(amostras[i]), 98))) for i in range(6)}


def imagens() -> dict:
    info = {"landsat": {}, "s2": {}, "mss": {}}
    est = estiramento_fixo("comp30")
    tr, w, h, cantos30 = _destino_3857(GRADE30)
    info["landsat"]["coordenadas"] = cantos30
    info["landsat"]["estiramento"] = est
    tamanhos = {}
    for p in sorted(COMP.glob("comp30_*.tif")):
        ano = int(p.stem.split("_")[1])
        a, v = _ler_comp(p)
        b, alfa = _para_3857(a, v, GRADE30, tr, w, h)
        idx = {"blue": 0, "green": 1, "red": 2, "nir": 3, "swir1": 4, "swir2": 5}
        cor = [_estirar(b[idx[k]], *est[k], gama=1.3) for k in ("red", "green", "blue")]
        falsa = [_estirar(b[idx[k]], *est[k]) for k in ("swir1", "nir", "red")]
        tamanhos[f"landsat_{ano}_cor"] = _salvar_webp(cor, alfa, WEB_IMG / f"landsat_{ano}_cor.webp")
        tamanhos[f"landsat_{ano}_falsacor"] = _salvar_webp(falsa, alfa, WEB_IMG / f"landsat_{ano}_falsacor.webp")
    info["landsat"]["dimensoes_px"] = [w, h]

    tr10, w10, h10, cantos10 = _destino_3857(GRADE10)
    info["s2"]["coordenadas"] = cantos10
    # estiramento próprio do Sentinel-2: mesmo harmonizado, o Sen2Cor sai 0,015–0,03 mais claro
    # que o LaSRC no visível e no SWIR (docs/qa/E3c.md); fixo entre os anos de S2
    est = estiramento_fixo("comp10")
    info["s2"]["estiramento"] = est
    for p in sorted(COMP.glob("comp10_*.tif")):
        ano = int(p.stem.split("_")[1])
        a, v = _ler_comp(p)
        b, alfa = _para_3857(a, v, GRADE10, tr10, w10, h10)
        cor = [_estirar(b[k], *est[n], gama=1.3) for k, n in ((2, "red"), (1, "green"), (0, "blue"))]
        tamanhos[f"s2_{ano}_cor"] = _salvar_webp(cor, alfa, WEB_IMG / f"s2_{ano}_cor.webp")
    info["s2"]["dimensoes_px"] = [w10, h10]

    info["mss"]["coordenadas"] = cantos30
    for p in sorted(COMP.glob("mss30_*.tif")):
        ano = int(p.stem.split("_")[1])
        with rasterio.open(p) as s:
            m = s.read()[:4].astype(np.float32)
        v = m[0] != NODATA
        m = np.where(v, m, np.nan)
        b, alfa = _para_3857(m, v, GRADE30, tr, w, h)
        # MSS L1 em DN: estiramento por ano (não comparável radiometricamente)
        rgb = [_estirar(b[i], np.nanpercentile(b[i], 2), np.nanpercentile(b[i], 98)) for i in (2, 1, 0)]
        tamanhos[f"mss_{ano}_falsacor"] = _salvar_webp(rgb, alfa, WEB_IMG / f"mss_{ano}_falsacor.webp")
    info["tamanhos"] = tamanhos
    (WEB_IMG / "_imagens.json").write_text(json.dumps(info, indent=1), "utf-8")
    return info


# ----------------------------------------------------------------------------
# manifesto e cores (lidas das fontes, nunca digitadas)
# ----------------------------------------------------------------------------

def _mapbiomas_hex(cid: int) -> str:
    return mapbiomas_hex(cid)


def _ibge_qml(rotulo: str) -> dict:
    """Preenchimento e contorno do símbolo da regra `rotulo` no .qml oficial da AU 2022."""
    return ibge_qml(rotulo)


def _ardosia() -> dict[str, str]:
    css = (BASE / "web" / "src" / "styles" / "ardosia.css").read_text("utf-8")
    return dict(re.findall(r"--([a-z0-9-]+):\s*(#[0-9A-Fa-f]{6})", css))


def manifesto() -> None:
    ard = _ardosia()
    img = json.loads((WEB_IMG / "_imagens.json").read_text("utf-8"))
    anos30 = sorted(int(p.stem.split("_")[-1]) for p in WEB_M.glob("mancha_propria_*.json"))
    anos10 = sorted(int(p.stem.split("_")[-1]) for p in WEB_M.glob("mancha_propria10_*.json"))
    anos_mss = sorted(int(p.stem.split("_")[1]) for p in WEB_IMG.glob("mss_*_falsacor.webp"))
    anos_s2 = sorted(int(p.stem.split("_")[1]) for p in WEB_IMG.glob("s2_*_cor.webp"))
    lot = _ibge_qml("Loteamento vazio")
    # escalas da classe urbana (ano de urbanização, WSF, GHSL): vermelhos derivados da classe 24 do
    # MapBiomas (decisão do usuário, 10/09/2026), do mais escuro (mais antigo) ao mais claro
    seq = rampa_urbana(5)
    FONTE_RAMPA = "MapBiomas Col. 11, classe 24 — rampa de vermelhos derivada (lib/legendas.rampa_urbana)"
    atrib_landsat = "Landsat 5/7/8/9 Collection 2 Level-2 (USGS/NASA), via Microsoft Planetary Computer"
    atrib_propria = ("Classificação própria (Random Forest), a partir de " + atrib_landsat +
                     "; D. P. Sobreira, 2026")
    camadas = [
        {"id": "mancha_propria", "titulo": "Mancha urbana (classificação própria, 30 m)", "tipo": "geojson",
         "arquivo": "geo/mancha/mancha_propria_{ano}.json", "anos": anos30, "propriedade_classe": "classe",
         "legenda": [
             {"classe": 1, "rotulo": "Sede (mancha contígua)", "cor": _mapbiomas_hex(24), "opacidade": 0.75,
              "fonte_cor": "MapBiomas Col. 11, classe 24"},
             {"classe": 2, "rotulo": "Outros núcleos", "cor": _mapbiomas_hex(24), "opacidade": 0.4,
              "fonte_cor": "MapBiomas Col. 11, classe 24 (opacidade reduzida)"},
             {"classe": 3, "rotulo": "Construído em área de mineração", "cor": _mapbiomas_hex(30),
              "opacidade": 0.75, "fonte_cor": "MapBiomas Col. 11, classe 30"},
             {"classe": 4, "rotulo": "Loteamento vazio (IBGE AU 2022)", "cor": lot["preenchimento"],
              "contorno": lot["contorno"], "fonte_cor": "IBGE, AreasUrbanizadas2022_Densidade_Tipo.qml"}],
         "atribuicao": atrib_propria, "licenca": "CC BY 4.0",
         "notas": "Áreas mapeadas (brutas); a série ajustada pelo erro está em estatisticas_mancha.json."},
        {"id": "mancha_propria10", "titulo": "Mancha urbana (Sentinel-2, 10 m, série secundária)",
         "tipo": "geojson", "arquivo": "geo/mancha/mancha_propria10_{ano}.json", "anos": anos10,
         "propriedade_classe": "classe", "legenda_de": "mancha_propria",
         "atribuicao": "Classificação própria a partir de Copernicus Sentinel-2 L2A (ESA), via Element84 "
                       "Earth Search; D. P. Sobreira, 2026", "licenca": "CC BY 4.0"},
        {"id": "expansao", "titulo": "Ano de urbanização (1º ano urbano do pixel)", "tipo": "geojson",
         "arquivo": "geo/expansao_ano_urbanizacao.json", "propriedade": "ano_urbanizacao",
         "rampa": seq, "fonte_cor": FONTE_RAMPA + "; mais escuro = mais antigo", "dominio": [anos30[0], anos30[-1]],
         "atribuicao": atrib_propria, "licenca": "CC BY 4.0"},
        {"id": "mineracao_mascara", "titulo": "Máscara de mineração", "tipo": "geojson",
         "arquivo": "geo/mineracao_mascara.json", "cor": _mapbiomas_hex(30), "opacidade": 0.15,
         "fonte_cor": "MapBiomas Col. 11, classe 30",
         "atribuicao": "MapBiomas Col. 11 (classe 30, 1985–2025) + ANM/SIGMINE", "licenca": "CC BY 4.0"},
        {"id": "anm_lavra", "titulo": "Concessões de lavra (ANM)", "tipo": "geojson",
         "arquivo": "geo/anm_lavra.json", "contorno": ard["ard-pedra"], "fonte_cor": "Ardósia --ard-pedra",
         "atribuicao": f"ANM, SIGMINE (acesso {ACESSO})", "licenca": "dado público (ANM)"},
        {"id": "clareira_mss", "titulo": "Clareiras em imagem MSS (1973, 1982): núcleo do assentamento e demais",
         "tipo": "geojson", "arquivo": "geo/clareira_mss_{ano}.json", "anos": anos_mss, "propriedade_classe": "classe",
         "legenda": [
             {"classe": 1, "rotulo": "Núcleo do assentamento (1982; clareira a até 1 km do núcleo histórico, < 100 ha)",
              "cor": _mapbiomas_hex(24), "opacidade": 0.85, "fonte_cor": "MapBiomas Col. 11, classe 24"},
             {"classe": 2, "rotulo": "Demais clareiras (agropecuária)", "cor": _mapbiomas_hex(21), "opacidade": 0.6,
              "fonte_cor": "MapBiomas Col. 11, classe 21 (mosaico de usos)"}],
         "notas": "Clareira = NDVI abaixo do limiar de Otsu na cena MSS; separação núcleo/demais por regra geométrica "
                  "(distância ao núcleo histórico e área). Não é mancha urbana classificada. LIMITAÇÃO (QA E7): as cenas "
                  "MSS são Tier 2 (duas L1GS, sem pontos de controle), com erro de posição de centenas de metros a ~1 km "
                  "entre si, e a de out/1982 tem muitos cúmulos — parte das 'clareiras' são nuvens e sombras. Serve só "
                  "como marco visual, não para comparar com a série TM/OLI.",
         "atribuicao": "Landsat 1/4 MSS Collection 2 Level-1 (USGS), via Microsoft Planetary Computer",
         "licenca": "domínio público (USGS)"},
        {"id": "osm_vias", "titulo": "Rodovias e ferrovia", "tipo": "geojson", "arquivo": "geo/osm_vias.json",
         "propriedade_classe": "tipo", "cor": ard["ard-grafite"], "cor_ferrovia": ard["ard-tinta"],
         "fonte_cor": "Ardósia --ard-grafite / --ard-tinta",
         "atribuicao": f"© contribuidores do OpenStreetMap (acesso {ACESSO})", "licenca": "ODbL 1.0"},
        {"id": "nucleo_historico", "titulo": "Núcleo histórico", "tipo": "geojson",
         "arquivo": "geo/nucleo_historico.json", "cor": ard["ard-tinta"], "fonte_cor": "Ardósia --ard-tinta",
         "atribuicao": atrib_propria, "licenca": "CC BY 4.0"},
        {"id": "landsat_cor", "titulo": "Landsat — cor natural (composição mediana jun–set)", "tipo": "image",
         "arquivo": "geo/img/landsat_{ano}_cor.webp", "anos": anos30, "coordenadas": img["landsat"]["coordenadas"],
         "atribuicao": atrib_landsat, "licenca": "domínio público (USGS)"},
        {"id": "landsat_falsacor", "titulo": "Landsat — falsa-cor SWIR1/NIR/vermelho", "tipo": "image",
         "arquivo": "geo/img/landsat_{ano}_falsacor.webp", "anos": anos30,
         "coordenadas": img["landsat"]["coordenadas"], "atribuicao": atrib_landsat,
         "licenca": "domínio público (USGS)"},
        {"id": "s2_cor", "titulo": "Sentinel-2 — cor natural (10 m)", "tipo": "image",
         "arquivo": "geo/img/s2_{ano}_cor.webp", "anos": anos_s2, "coordenadas": img["s2"]["coordenadas"],
         "atribuicao": "Contém dados modificados Copernicus Sentinel (2017–2026), via Element84 Earth Search",
         "licenca": "Copernicus (uso livre com atribuição)"},
        {"id": "mss_falsacor", "titulo": "Landsat MSS (1973, 1982), exibida em tons de cinza", "tipo": "image",
         "arquivo": "geo/img/mss_{ano}_falsacor.webp", "anos": anos_mss, "coordenadas": img["mss"]["coordenadas"],
         "atribuicao": "Landsat 1/4 MSS Collection 2 Level-1 (USGS), via Microsoft Planetary Computer",
         "licenca": "domínio público (USGS)"},
    ]
    # produtos externos de comparação (WSF, GHSL) — só entram se produtos_wsf()/produtos_ghsl() rodaram
    if (WEB_GEO / "wsf_evolution.json").exists():
        anos_wsf = sorted({ft["properties"]["ano"]
                           for ft in json.loads((WEB_GEO / "wsf_evolution.json").read_text("utf-8"))["features"]})
        camadas.append({
            "id": "wsf_evolution", "titulo": "WSF-Evolution — 1º ano assentado (DLR)", "tipo": "geojson",
            "arquivo": "geo/wsf_evolution.json", "propriedade": "ano", "rampa": seq,
            "fonte_cor": FONTE_RAMPA + " (mesma rampa do ano de urbanização, para comparação)", "dominio": [1985, 2015],
            "atribuicao": "DLR/EOC, World Settlement Footprint Evolution (Marconcini et al., 2021)",
            "licenca": "CC BY 4.0", "origem_etapa": "produtos externos",
            "notas": f"Anos com feição na janela: {anos_wsf[0]}–{anos_wsf[-1]} ({len(anos_wsf)} anos). "
                     "0 (nunca assentado) é a codificação de nodata do produto, não um ano."})
    if (WEB_GEO / "wsf2019.json").exists():
        camadas.append({
            "id": "wsf2019", "titulo": "World Settlement Footprint 2019 (10 m)", "tipo": "geojson",
            "arquivo": "geo/wsf2019.json", "cor": seq[3],
            "fonte_cor": FONTE_RAMPA + " (tom claro)",
            "atribuicao": "DLR/EOC, World Settlement Footprint 2019 (Marconcini et al., 2020)",
            "licenca": "CC BY 4.0", "origem_etapa": "produtos externos"})
    anos_ghsl = sorted(int(p.stem.split("_")[-1]) for p in WEB_GHSL.glob("ghsl_*.json"))
    if anos_ghsl:
        ghsl_cores = rampa_urbana(4)[::-1]  # classe 1 (pouco construído) clara → classe 4 escura
        camadas.append({
            "id": "ghsl", "titulo": "GHSL GHS-BUILT-S — superfície construída (100 m)", "tipo": "geojson",
            "arquivo": "geo/ghsl/ghsl_{ano}.json", "anos": anos_ghsl, "propriedade_classe": "classe",
            "legenda": [
                {"classe": 1, "rotulo": "5–20 % construído", "cor": ghsl_cores[0],
                 "fonte_cor": FONTE_RAMPA},
                {"classe": 2, "rotulo": "20–40 % construído", "cor": ghsl_cores[1],
                 "fonte_cor": FONTE_RAMPA},
                {"classe": 3, "rotulo": "40–60 % construído", "cor": ghsl_cores[2],
                 "fonte_cor": FONTE_RAMPA},
                {"classe": 4, "rotulo": "≥ 60 % construído", "cor": ghsl_cores[3],
                 "fonte_cor": FONTE_RAMPA}],
            "atribuicao": "JRC, GHS-BUILT-S R2023A (Pesaresi & Politis, 2023)", "licenca": "CC BY 4.0",
            "origem_etapa": "produtos externos",
            "notas": "Grade própria de 100 m (não reamostrada para 30 m). As épocas de 2025 e 2030 são "
                     "projeções do JRC, não observações."})
    if (WEB_GEO / "osm_ferrovia.json").exists():
        camadas.append({
            "id": "osm_ferrovia", "titulo": "Ramal Ferroviário do Sudeste do Pará", "tipo": "geojson",
            "arquivo": "geo/osm_ferrovia.json", "propriedade_classe": "tipo", "cor": ard["ard-tinta"],
            "fonte_cor": "Ardósia --ard-tinta", "atribuicao": f"© contribuidores do OpenStreetMap (acesso {ACESSO})",
            "licenca": "ODbL 1.0",
            "notas": "Consulta regional (AOI municipal + ~15 km); a ferrovia S11D–Parauapebas passa a "
                     "oeste da sede, fora da janela de `osm_vias`."})
    if (WEB_GEO / "osm_rodovias_regiao.json").exists():
        camadas.append({
            "id": "osm_rodovias_regiao", "titulo": "Rodovias regionais (trunk/primary/secondary)",
            "tipo": "geojson", "arquivo": "geo/osm_rodovias_regiao.json", "propriedade_classe": "tipo",
            "cor": ard["ard-grafite"], "fonte_cor": "Ardósia --ard-grafite",
            "atribuicao": f"© contribuidores do OpenStreetMap (acesso {ACESSO})", "licenca": "ODbL 1.0",
            "notas": "Consulta regional (AOI municipal + ~15 km), complementa `osm_vias` (janela da sede)."})
    # camadas herdadas de E1/E3a, referenciadas para o dashboard ter um só manifesto
    for arq, tit, atr in (
        ("geo/mancha_mapbiomas_{ano}.json", "MapBiomas Col. 11 — classe 24 (comparação)",
         "MapBiomas Brasil, Coleção 11"),
        ("geo/areas_urbanizadas_2019_revisado.json", "IBGE Áreas Urbanizadas 2019 (revisado)", "IBGE"),
        ("geo/areas_urbanizadas_2022.json", "IBGE Áreas Urbanizadas 2022", "IBGE"),
        ("geo/setores_2010.json", "Setores censitários 2010", "IBGE, Censo 2010"),
        ("geo/setores_2022.json", "Setores censitários 2022", "IBGE, Censo 2022"),
        ("geo/aoi_municipio.json", "Limite municipal", "IBGE, Malhas API v4"),
        ("geo/aoi_sede.json", "Janela de análise da sede", "definição do projeto"),
    ):
        entrada = {"id": Path(arq).stem.replace("_{ano}", ""), "titulo": tit, "tipo": "geojson",
                   "arquivo": arq, "atribuicao": atr, "origem_etapa": "E1/E3a"}
        if "{ano}" in arq:
            entrada["anos"] = sorted(int(p.stem.split("_")[-1]) for p in WEB_GEO.glob("mancha_mapbiomas_*.json"))
            entrada["cor"] = _mapbiomas_hex(24)
            entrada["fonte_cor"] = "MapBiomas Col. 11, classe 24"
        camadas.append(entrada)
    # legenda oficial (Densidade/Tipo) da AU 2022, lida do .qml do IBGE
    au22 = next(c for c in camadas if c["id"] == "areas_urbanizadas_2022")
    au22["legenda"] = [
        {"propriedade": prop, "valor": valor, "rotulo": rotulo, "cor": cor["preenchimento"],
         "contorno": cor["contorno"], "fonte_cor": "IBGE, AreasUrbanizadas2022_Densidade_Tipo.qml"}
        for prop, valor, rotulo, cor in (
            (p, v, r, _ibge_qml(r)) for p, v, r in (
                ("Densidade", "Densa", "Densa"), ("Densidade", "Pouco densa", "Pouco densa"),
                ("Densidade", "Loteamento vazio", "Loteamento vazio"),
                ("Tipo", "Outros equipamentos urbanos", "Outros equipamentos"),
                ("Tipo", "Vazio intraurbano", "Vazio intraurbano")))]
    # grupo temático de cada camada, para agrupar o seletor do dashboard
    grupos = {
        "mancha_propria": "mancha", "mancha_propria10": "mancha", "expansao": "mancha",
        "clareira_mss": "mancha", "nucleo_historico": "mancha",
        "mancha_mapbiomas": "comparacao", "areas_urbanizadas_2019_revisado": "comparacao",
        "areas_urbanizadas_2022": "comparacao", "wsf_evolution": "comparacao", "wsf2019": "comparacao",
        "ghsl": "comparacao",
        "setores_2010": "setores", "setores_2022": "setores",
        "aoi_municipio": "limites", "aoi_sede": "limites",
        "mineracao_mascara": "mineracao_infra", "anm_lavra": "mineracao_infra", "osm_vias": "mineracao_infra",
        "osm_ferrovia": "mineracao_infra", "osm_rodovias_regiao": "mineracao_infra",
        "landsat_cor": "imagens", "landsat_falsacor": "imagens", "s2_cor": "imagens", "mss_falsacor": "imagens",
    }
    for c in camadas:
        c["grupo"] = grupos[c["id"]]
    # confere que todo arquivo citado existe
    faltando = []
    for c in camadas:
        anos = c.get("anos", [None])
        for a in anos:
            f = WEB / c["arquivo"].format(ano=a) if a is not None else WEB / c["arquivo"]
            if not f.exists():
                faltando.append(str(f.relative_to(WEB)))
    if faltando:
        raise SystemExit(f"manifesto cita arquivos ausentes: {faltando[:10]}")
    (WEB_GEO / "camadas.json").write_text(json.dumps(
        {"gerado_em": ACESSO, "crs_vetores": "EPSG:4326", "crs_imagens": "EPSG:3857 (cantos em lon/lat)",
         "camadas": camadas}, ensure_ascii=False, indent=1), "utf-8")
    print(f"camadas.json: {len(camadas)} camadas, todos os arquivos citados existem")


def resumo_tamanhos() -> None:
    def mb(glob):
        return sum(p.stat().st_size for p in WEB_GEO.glob(glob)) / 1e6
    print(f"  mancha 30 m: {mb('mancha/mancha_propria_*.json'):.2f} MB | 10 m: {mb('mancha/mancha_propria10_*.json'):.2f} MB")
    print(f"  imagens: landsat cor {mb('img/landsat_*_cor.webp'):.1f} MB, falsa-cor {mb('img/landsat_*_falsacor.webp'):.1f} MB, "
          f"s2 {mb('img/s2_*.webp'):.1f} MB, mss {mb('img/mss_*.webp'):.2f} MB")
    print(f"  total web/public/data/geo: {sum(p.stat().st_size for p in WEB_GEO.rglob('*') if p.is_file()) / 1e6:.1f} MB")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "tudo"
    if cmd in ("vetores", "tudo"):
        t30 = manchas(30)
        print(f"mancha 30 m: {len(t30)} anos, {sum(t30.values()) / 1e6:.2f} MB (máx {max(t30.values()) / 1e3:.0f} KB)")
        t10 = manchas(10)
        print(f"mancha 10 m: {len(t10)} anos, {sum(t10.values()) / 1e6:.2f} MB (máx {max(t10.values()) / 1e3:.0f} KB)")
        print(f"expansão: {expansao() / 1e3:.0f} KB")
        print({k: f"{v / 1e3:.0f} KB" for k, v in apoio().items()})
    if cmd in ("imagens", "tudo"):
        info = imagens()
        t = info["tamanhos"]
        print(f"imagens: {len(t)} arquivos, {sum(t.values()) / 1e6:.1f} MB, maior {max(t, key=t.get)} "
              f"{max(t.values()) / 1e6:.2f} MB")
    if cmd in ("produtos", "tudo"):
        tp = produtos()
        print(f"produtos: {len(tp)} arquivos, {sum(tp.values()) / 1e6:.2f} MB — "
              f"{', '.join(f'{k} {v / 1e3:.0f} KB' for k, v in tp.items())}")
    if cmd in ("manifesto", "tudo"):
        manifesto()
    resumo_tamanhos()
