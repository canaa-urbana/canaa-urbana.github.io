"""
Grade raster fixa da janela da sede de Canaã dos Carajás (E3b, Fase 3).

Toda a série própria (composições, classificações, máscaras, validação) vive em
UMA grade de 30 m em EPSG:31982 (SIRGAS 2000 / UTM 22S), alinhada a múltiplos
de 30 m, cobrindo a `aoi_sede` de `20_imagens_catalogo.py`. A grade de 10 m
(Sentinel-2, série secundária) tem a MESMA origem e 3×3 pixels por célula de
30 m, de modo que agregar 10 m → 30 m é uma média de blocos exata, sem
reamostragem.

Regra do CLAUDE.md: áreas sempre em CRS métrico. Aqui o pixel de 30 m tem
exatamente 900 m² e o de 10 m, 100 m²; mesmo assim os totais publicados em
`26_estatisticas_mancha.py` são calculados sobre polígonos vetorizados.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.transform import Affine, from_origin
from rasterio.vrt import WarpedVRT

BASE = Path(__file__).resolve().parent.parent.parent
EPSG_METRICO = 31982
CRS_METRICO = CRS.from_epsg(EPSG_METRICO)


@dataclass(frozen=True)
class Grade:
    res: float
    x0: float
    y1: float  # canto superior esquerdo (norte)
    largura: int
    altura: int

    @property
    def transform(self) -> Affine:
        return from_origin(self.x0, self.y1, self.res, self.res)

    @property
    def shape(self) -> tuple[int, int]:
        return (self.altura, self.largura)

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        return (
            self.x0,
            self.y1 - self.altura * self.res,
            self.x0 + self.largura * self.res,
            self.y1,
        )

    def perfil(self, count: int, dtype: str, nodata=None, **extra) -> dict:
        p = dict(
            driver="GTiff",
            width=self.largura,
            height=self.altura,
            count=count,
            dtype=dtype,
            crs=CRS_METRICO,
            transform=self.transform,
            compress="deflate",
            predictor=2 if dtype.startswith(("int", "uint")) else 3,
            tiled=True,
            blockxsize=256,
            blockysize=256,
            nodata=nodata,
        )
        p.update(extra)
        return p

    def xy(self) -> tuple[np.ndarray, np.ndarray]:
        """Coordenadas dos centros de pixel (metros)."""
        xs = self.x0 + (np.arange(self.largura) + 0.5) * self.res
        ys = self.y1 - (np.arange(self.altura) + 0.5) * self.res
        return xs, ys


def _grade_sede() -> tuple[Grade, Grade]:
    import geopandas as gpd

    sede = gpd.read_parquet(BASE / "data" / "processed" / "geo" / "aoi_sede_31982.parquet")
    xmin, ymin, xmax, ymax = sede.total_bounds
    x0 = math.floor(xmin / 30) * 30
    x1 = math.ceil(xmax / 30) * 30
    y0 = math.floor(ymin / 30) * 30
    y1 = math.ceil(ymax / 30) * 30
    g30 = Grade(30.0, x0, y1, int((x1 - x0) / 30), int((y1 - y0) / 30))
    g10 = Grade(10.0, x0, y1, g30.largura * 3, g30.altura * 3)
    return g30, g10


GRADE30, GRADE10 = _grade_sede()


def ler_para_grade(
    href: str,
    grade: Grade,
    resampling: Resampling = Resampling.nearest,
    banda: int = 1,
    dtype=None,
) -> np.ndarray:
    """Lê UMA banda de um COG remoto (ou arquivo local) já reprojetada e
    recortada na grade — leitura por janela, nunca o arquivo inteiro."""
    with rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        GDAL_HTTP_MAX_RETRY="4",
        GDAL_HTTP_RETRY_DELAY="2",
        GDAL_HTTP_TIMEOUT="120",
        VSI_CACHE="TRUE",
    ):
        with rasterio.open(href) as src:
            with WarpedVRT(
                src,
                crs=CRS_METRICO,
                transform=grade.transform,
                width=grade.largura,
                height=grade.altura,
                resampling=resampling,
            ) as vrt:
                arr = vrt.read(banda)
    return arr if dtype is None else arr.astype(dtype)


def agregar_3x3(a: np.ndarray, func=np.nanmean) -> np.ndarray:
    """10 m → 30 m por blocos 3×3 (a grade de 10 m é exatamente 3× a de 30 m)."""
    h, w = a.shape
    return func(a.reshape(h // 3, 3, w // 3, 3), axis=(1, 3))


def escrever(caminho: Path, bandas: list[np.ndarray], nomes: list[str], grade: Grade,
             nodata=None, tags: dict | None = None) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    dtype = np.result_type(*[b.dtype for b in bandas]).name
    tmp = caminho.with_suffix(".tmp.tif")
    with rasterio.open(tmp, "w", **grade.perfil(len(bandas), dtype, nodata)) as dst:
        for i, (b, n) in enumerate(zip(bandas, nomes), start=1):
            dst.write(b.astype(dtype), i)
            dst.set_band_description(i, n)
        if tags:
            dst.update_tags(**tags)
    tmp.replace(caminho)


def ler_local(caminho: Path) -> tuple[np.ndarray, list[str], dict]:
    with rasterio.open(caminho) as src:
        return src.read(), list(src.descriptions), src.tags()
