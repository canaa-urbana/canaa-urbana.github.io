"""
E3a / Fase 3 passos 2 (parte) e 6 (PLANO.md) — produtos de mancha urbana já
prontos, recortados para a AOI de Canaã dos Carajás. Nenhuma classificação
própria aqui (isso é E3b); esta etapa entrega a série de referência contra a
qual a classificação própria será comparada e validada.

Produtos (URLs conferidas em 09/09/2026, todas HTTP 200):
  1. **Legenda oficial MapBiomas Coleção 11** (CSV de códigos/hex publicado em
     `brasil.mapbiomas.org/downloads/codigos-de-legenda/`) →
     `web/src/legend/mapbiomas.json`. Exigência do CLAUDE.md: as cores das
     camadas temáticas vêm da legenda oficial, não da paleta Ardósia, e nenhum
     código de classe é digitado de memória.
  2. **MapBiomas Coleção 11** (30 m, anual 1985-2025), classe 24 Área
     Urbanizada e 30 Mineração — recorte por `/vsicurl` sobre o GeoTIFF Brasil
     (BigTIFF tiled: lê-se só a janela da AOI, não os ~650 MB do arquivo).
  3. **MapBiomas 10 m Sentinel Coleção 4** (2016-2025) — mesma técnica.
  4. **GHS-BUILT-S R2023A** (100 m, épocas 1975-2030, Mollweide): a AOI
     municipal cruza a divisa das tiles R10_C13 e R10_C14 — ambas são baixadas
     e mosaicadas.
  5. **WSF-Evolution** (30 m, ano de primeira detecção 1985-2015) e **WSF2019**
     (10 m): tiles 2°×2° `-52_-8` e `-50_-8`.
  6. **IBGE Áreas Urbanizadas** 2015, 2019, 2019 revisado e 2022 (com densidade
     e tipo), + os estilos `.qml` oficiais, recortados para o município.
  7. **TerraClass Amazônia** — sem URL direta (formulário web em
     terraclass.gov.br); se o usuário baixar os ZIP para
     `data/externo/terraclass/`, o script os incorpora. Ausência não bloqueia.

Saídas: rasters/vetores recortados em `data/interim/produtos/` (fora do git),
vetores para o dashboard em `web/public/data/geo/`, e um manifesto de
proveniência em `data/processed/geo/produtos_prontos.parquet` (fonte, URL,
data de acesso, licença) — usado nas atribuições do mapa e no artigo.

Uso:
    .venv/bin/python pipeline/25_produtos_prontos.py            # tudo
    .venv/bin/python pipeline/25_produtos_prontos.py mapbiomas  # só um bloco
"""
from __future__ import annotations

import io
import json
import sys
import zipfile
from datetime import date
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import requests
from rasterio.merge import merge
from rasterio.windows import from_bounds

BASE = Path(__file__).resolve().parent.parent
DL = BASE / "data" / "interim" / "_produtos_dl"
OUT = BASE / "data" / "interim" / "produtos"
OUT_GEO = BASE / "data" / "processed" / "geo"
OUT_WEB = BASE / "web" / "public" / "data" / "geo"
OUT_LEGEND = BASE / "web" / "src" / "legend"
for d in (DL, OUT, OUT_GEO, OUT_WEB, OUT_LEGEND):
    d.mkdir(parents=True, exist_ok=True)

MUNICIPIO = "1502152"
EPSG_METRICO = 31982
HOJE = date.today().isoformat()

MB_LEGENDA = (
    "https://brasil.mapbiomas.org/wp-content/uploads/sites/3/2026/08/"
    "legend_code_mapbiomas_brazil_collection_11.csv"
)
MB_30M = (
    "https://storage.googleapis.com/mapbiomas-public/initiatives/brasil/collection11/"
    "lulc/coverage/brazil_coverage/brazil_coverage-col11_{ano}.tif"
)
MB_10M = (
    "https://storage.googleapis.com/mapbiomas-public/initiatives/brasil/lulc_10m/"
    "collection4/coverage/brazil_coverage/brazil_coverage-col4_10m_{ano}.tif"
)
MB_ANOS_30M = range(1985, 2026)
MB_ANOS_10M = range(2017, 2026)  # a Col.4 10 m começa em 2017 (2016 devolve 404)

GHSL = (
    "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_S_GLOBE_R2023A/"
    "GHS_BUILT_S_E{ano}_GLOBE_R2023A_54009_100/V1-0/tiles/"
    "GHS_BUILT_S_E{ano}_GLOBE_R2023A_54009_100_V1_0_{tile}.zip"
)
GHSL_EPOCAS = list(range(1975, 2031, 5))
GHSL_TILES = ["R10_C13", "R10_C14"]  # a AOI municipal cruza a divisa em x = −5.041.000 m

WSF_EVO = "https://download.geoservice.dlr.de/WSF_EVO/files/WSFevolution_v1_{tile}.tif"
WSF_2019 = "https://download.geoservice.dlr.de/WSF2019/files/WSF2019_v1_{tile}.tif"
WSF_TILES = ["-52_-8", "-50_-8"]

AU_BASE = (
    "https://geoftp.ibge.gov.br/organizacao_do_territorio/tipologias_do_territorio/"
    "areas_urbanizadas_do_brasil/"
)
AU_ARQUIVOS = {
    "2015": AU_BASE + "2015/Shape/AreasUrbanizadasDoBrasil_2015.zip",
    "2019": AU_BASE + "2019/Shapefile/AreasUrbanizadas2019_Brasil.zip",
    "2019_revisado": AU_BASE + "2022/Shapefile/AreasUrbanizadas_2019_Brasil_Revisado.zip",
    "2022": AU_BASE + "2022/Shapefile/AreasUrbanizadas2022_Brasil.zip",
}
AU_QML = {
    "2022_densidade_tipo": AU_BASE + "2022/Shapefile/AreasUrbanizadas2022_Densidade_Tipo.qml",
    "2022_comparacao": AU_BASE + "2022/Shapefile/AreasUrbanizadas2022_Comparacao.qml",
}

MANIFESTO: list[dict] = []


def registrar(produto: str, url: str, arquivo: Path | None, obs: str = "") -> None:
    MANIFESTO.append(
        {
            "produto": produto,
            "url": url,
            "arquivo": str(arquivo.relative_to(BASE)) if arquivo else "",
            "bytes": arquivo.stat().st_size if arquivo and arquivo.exists() else 0,
            "acessado_em": HOJE,
            "observacao": obs,
        }
    )


def baixar(url: str, destino: Path, timeout: int = 900) -> Path:
    """Download com cache em disco — nunca rebaixa o que já existe."""
    if destino.exists() and destino.stat().st_size > 0:
        return destino
    with requests.get(url, timeout=timeout, stream=True) as r:
        r.raise_for_status()
        tmp = destino.with_suffix(destino.suffix + ".parcial")
        with open(tmp, "wb") as f:
            for bloco in r.iter_content(1 << 20):
                f.write(bloco)
        tmp.rename(destino)
    return destino


def aoi_municipio() -> gpd.GeoDataFrame:
    p = OUT_GEO / "aoi_municipio_31982.parquet"
    if not p.exists():
        raise SystemExit("Rode antes: pipeline/20_imagens_catalogo.py (gera a AOI)")
    return gpd.read_parquet(p)


# ---------------------------------------------------------------- MapBiomas
def legenda_mapbiomas() -> pd.DataFrame:
    csv = DL / "legend_code_mapbiomas_col11.csv"
    baixar(MB_LEGENDA, csv)
    # o CSV vem em UTF-8 servido sem BOM; acentos já corretos em utf-8
    leg = pd.read_csv(csv, encoding="utf-8")
    leg.columns = ["class_id", "classe_pt", "classe_en", "hex"]
    (OUT_LEGEND / "mapbiomas.json").write_text(
        json.dumps(
            {
                "fonte": "MapBiomas Brasil, Coleção 11 — códigos de legenda oficiais",
                "url": MB_LEGENDA,
                "acessado_em": HOJE,
                "classes": leg.to_dict("records"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    leg.to_parquet(OUT_GEO / "mapbiomas_legenda_col11.parquet")
    registrar("MapBiomas Col.11 — legenda", MB_LEGENDA, OUT_LEGEND / "mapbiomas.json")
    print(f"  legenda: {len(leg)} classes → web/src/legend/mapbiomas.json")
    return leg


def recortar_vsicurl(url: str, destino: Path, bounds4326: tuple) -> Path | None:
    """Lê pela janela da AOI direto do COG remoto (sem baixar o arquivo todo)."""
    if destino.exists() and destino.stat().st_size > 0:
        return destino
    try:
        with rasterio.open("/vsicurl/" + url) as src:
            win = from_bounds(*bounds4326, src.transform)
            arr = src.read(1, window=win)
            perfil = src.profile | {
                "height": arr.shape[0],
                "width": arr.shape[1],
                "transform": src.window_transform(win),
                "compress": "deflate",
                "tiled": True,
                "BIGTIFF": "IF_SAFER",
            }
            perfil.pop("blockxsize", None)
            perfil.pop("blockysize", None)
        with rasterio.open(destino, "w", **perfil) as dst:
            dst.write(arr, 1)
    except Exception as exc:
        print(f"    ! {url.rsplit('/', 1)[-1]}: {type(exc).__name__}: {str(exc)[:80]}")
        return None
    return destino


def mapbiomas(mun: gpd.GeoDataFrame) -> None:
    legenda_mapbiomas()
    b = tuple(mun.to_crs(4326).total_bounds)
    for rotulo, molde, anos, sub in (
        ("Col.11 30 m", MB_30M, MB_ANOS_30M, "mapbiomas_col11"),
        ("Col.4 10 m", MB_10M, MB_ANOS_10M, "mapbiomas_col4_10m"),
    ):
        d = OUT / sub
        d.mkdir(parents=True, exist_ok=True)
        ok = 0
        for ano in anos:
            url = molde.format(ano=ano)
            alvo = recortar_vsicurl(url, d / f"{sub}_{ano}.tif", b)
            if alvo:
                ok += 1
                registrar(f"MapBiomas {rotulo}", url, alvo, f"ano {ano}, recorte AOI municipal")
        print(f"  MapBiomas {rotulo}: {ok}/{len(list(anos))} anos recortados → {d.name}/")


# --------------------------------------------------------------------- GHSL
def ghsl(mun: gpd.GeoDataFrame) -> None:
    d = OUT / "ghsl"
    d.mkdir(parents=True, exist_ok=True)
    mun_moll = mun.to_crs("ESRI:54009")
    ok = 0
    for ano in GHSL_EPOCAS:
        saida = d / f"ghs_built_s_{ano}.tif"
        if saida.exists():
            ok += 1
            continue
        partes = []
        for tile in GHSL_TILES:
            url = GHSL.format(ano=ano, tile=tile)
            try:
                z = baixar(url, DL / Path(url).name)
                nome_tif = Path(url).name.replace(".zip", ".tif")
                partes.append(f"/vsizip/{z}/{nome_tif}")
            except Exception as exc:
                print(f"    ! GHSL {ano} {tile}: {type(exc).__name__}")
        if not partes:
            continue
        srcs = [rasterio.open(p) for p in partes]
        arr, transform = merge(srcs, bounds=tuple(mun_moll.total_bounds))
        perfil = srcs[0].profile | {
            "height": arr.shape[1],
            "width": arr.shape[2],
            "transform": transform,
            "compress": "deflate",
        }
        for s in srcs:
            s.close()
        with rasterio.open(saida, "w", **perfil) as dst:
            dst.write(arr)
        registrar("GHS-BUILT-S R2023A", GHSL.format(ano=ano, tile="|".join(GHSL_TILES)), saida,
                  f"época {ano}, mosaico de 2 tiles, recorte AOI municipal")
        ok += 1
    print(f"  GHSL: {ok}/{len(GHSL_EPOCAS)} épocas → ghsl/")


# ---------------------------------------------------------------------- WSF
def wsf(mun: gpd.GeoDataFrame) -> None:
    d = OUT / "wsf"
    d.mkdir(parents=True, exist_ok=True)
    b = tuple(mun.to_crs(4326).total_bounds)
    for rotulo, molde, sub in (
        ("WSF-Evolution", WSF_EVO, "wsf_evolution"),
        ("WSF2019", WSF_2019, "wsf2019"),
    ):
        partes = []
        for tile in WSF_TILES:
            url = molde.format(tile=tile)
            try:
                partes.append(baixar(url, DL / Path(url).name))
                registrar(rotulo, url, DL / Path(url).name, f"tile {tile}")
            except Exception as exc:
                print(f"    ! {rotulo} {tile}: {type(exc).__name__}")
        if not partes:
            continue
        srcs = [rasterio.open(p) for p in partes]
        arr, transform = merge(srcs, bounds=b)
        perfil = srcs[0].profile | {
            "height": arr.shape[1],
            "width": arr.shape[2],
            "transform": transform,
            "compress": "deflate",
        }
        for s in srcs:
            s.close()
        saida = d / f"{sub}.tif"
        with rasterio.open(saida, "w", **perfil) as dst:
            dst.write(arr)
        print(f"  {rotulo}: mosaico {arr.shape[1]}×{arr.shape[2]} → wsf/{saida.name}")


# ----------------------------------------------- IBGE Áreas Urbanizadas
def areas_urbanizadas(mun: gpd.GeoDataFrame) -> None:
    d = OUT / "areas_urbanizadas"
    d.mkdir(parents=True, exist_ok=True)
    mun_4326 = mun.to_crs(4326)
    for rotulo, url in AU_ARQUIVOS.items():
        z = DL / Path(url).name
        try:
            baixar(url, z)
        except Exception as exc:
            print(f"    ! AU {rotulo}: {type(exc).__name__}")
            continue
        with zipfile.ZipFile(z) as zf:
            shps = [n for n in zf.namelist() if n.lower().endswith(".shp")]
        if not shps:
            print(f"    ! AU {rotulo}: sem .shp no zip")
            continue
        # 2015 vem repartido em dois shapefiles (concentrações ≥ 300 mil e de
        # 100 a 300 mil hab.) — leia todos, nunca só o primeiro
        partes = [gpd.read_file(f"zip://{z}!{s}", mask=mun_4326) for s in shps]
        partes = [g for g in partes if len(g)]
        if not partes:
            print(f"    ! AU {rotulo}: nenhum polígono sobre o município "
                  f"({len(shps)} shapefile(s) lidos) — produto não cobre Canaã neste ano")
            registrar(f"IBGE Áreas Urbanizadas {rotulo}", url, None,
                      "sem cobertura de Canaã dos Carajás neste recorte do produto")
            continue
        # `mask=` faz o recorte espacial no driver, sem carregar o Brasil inteiro
        gdf = gpd.GeoDataFrame(pd.concat(partes, ignore_index=True), crs=partes[0].crs)
        gdf = gdf.to_crs(EPSG_METRICO)
        gdf = gdf[gdf.intersects(mun.union_all())]
        gdf["area_ha"] = gdf.geometry.area / 1e4
        gdf.to_parquet(d / f"areas_urbanizadas_{rotulo}.parquet")
        gdf.to_crs(4326).to_file(OUT_WEB / f"areas_urbanizadas_{rotulo}.json", driver="GeoJSON")
        registrar(f"IBGE Áreas Urbanizadas {rotulo}", url, d / f"areas_urbanizadas_{rotulo}.parquet",
                  f"{len(gdf)} polígonos no município, {gdf['area_ha'].sum():,.1f} ha")
        print(f"  AU {rotulo:14s} {len(gdf):3d} polígonos  {gdf['area_ha'].sum():9,.1f} ha")
    for rotulo, url in AU_QML.items():
        try:
            baixar(url, OUT_LEGEND.parent / "legend" / f"ibge_au_{rotulo}.qml")
            registrar("IBGE AU — estilo oficial", url, OUT_LEGEND / f"ibge_au_{rotulo}.qml")
        except Exception as exc:
            print(f"    ! QML {rotulo}: {type(exc).__name__}")


# --------------------------------------------------------------- TerraClass
def terraclass(mun: gpd.GeoDataFrame) -> None:
    origem = BASE / "data" / "externo" / "terraclass"
    if not origem.exists() or not any(origem.iterdir()):
        print("  TerraClass: nada em data/externo/terraclass/ — download é por "
              "formulário web (terraclass.gov.br); pendência para o usuário")
        return
    d = OUT / "terraclass"
    d.mkdir(parents=True, exist_ok=True)
    b = tuple(mun.to_crs(4326).total_bounds)
    for tif in sorted(origem.rglob("*.tif")):
        with rasterio.open(tif) as src:
            bb = b if src.crs.to_epsg() == 4326 else tuple(mun.to_crs(src.crs).total_bounds)
            win = from_bounds(*bb, src.transform)
            arr = src.read(1, window=win)
            perfil = src.profile | {
                "height": arr.shape[0], "width": arr.shape[1],
                "transform": src.window_transform(win), "compress": "deflate",
            }
        with rasterio.open(d / tif.name, "w", **perfil) as dst:
            dst.write(arr, 1)
        registrar("TerraClass Amazônia", "terraclass.gov.br (formulário web)", d / tif.name)
        print(f"  TerraClass: {tif.name} recortado")


def main() -> None:
    blocos = sys.argv[1:] or ["mapbiomas", "ghsl", "wsf", "au", "terraclass"]
    mun = aoi_municipio()
    print(f"AOI municipal: {mun.area.iloc[0] / 1e6:,.1f} km²\n")
    if "mapbiomas" in blocos:
        print("MapBiomas …")
        mapbiomas(mun)
    if "ghsl" in blocos:
        print("GHSL …")
        ghsl(mun)
    if "wsf" in blocos:
        print("WSF …")
        wsf(mun)
    if "au" in blocos:
        print("IBGE Áreas Urbanizadas …")
        areas_urbanizadas(mun)
    if "terraclass" in blocos:
        print("TerraClass …")
        terraclass(mun)

    if MANIFESTO:
        man = pd.DataFrame(MANIFESTO)
        alvo = OUT_GEO / "produtos_prontos.parquet"
        if alvo.exists():
            man = pd.concat([pd.read_parquet(alvo), man]).drop_duplicates(
                subset=["produto", "url"], keep="last"
            )
        man.to_parquet(alvo)
        print(f"\nmanifesto: {len(man)} entradas → {alvo.relative_to(BASE)}")


if __name__ == "__main__":
    main()
