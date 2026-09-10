"""
Feições espectrais/texturais para a classificação da mancha urbana (E3b).

Entrada: composição anual com 6 bandas de reflectância de superfície na escala
ETM+ (blue, green, red, nir, swir1, swir2; float 0–1), o NDVI máximo da estação
chuvosa do mesmo ano e a declividade. Saída: matriz (n_feicoes, H, W) float32
com os nomes em `NOMES`.

Índices (todos adimensionais):
  NDVI  = (nir − red)/(nir + red)
  NDBI  = (swir1 − nir)/(swir1 + nir)                       Zha et al. 2003
  MNDWI = (green − swir1)/(green + swir1)                    Xu 2006
  BUI   = NDBI − NDVI                                        He et al. 2010
  BSI   = ((swir1 + red) − (nir + blue)) / ((swir1 + red) + (nir + blue))  Rikimaru et al. 2002
  IBI   = (NDBI − (SAVI + MNDWI)/2) / (NDBI + (SAVI + MNDWI)/2)             Xu 2008
  NBR2  = (swir1 − swir2)/(swir1 + swir2)  (separa solo exposto seco de telhado/asfalto)
Textura: desvio-padrão local (3×3 e 5×5) de NIR e de NDBI — substitui a GLCM
prevista no PLANO.md (mesma informação de heterogeneidade, 100× mais barato).
Intersazonal (ajuste da revisão crítica do plano): `ndvi_max_chuva` e
`ndvi_amplitude` = ndvi_max_chuva − ndvi_seca; área construída tem amplitude
baixa, pasto/solo exposto tem amplitude alta.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import uniform_filter

BANDAS = ["blue", "green", "red", "nir", "swir1", "swir2"]
NOMES = (
    BANDAS
    + ["ndvi", "ndbi", "mndwi", "bui", "bsi", "ibi", "nbr2"]
    + ["std3_nir", "std5_nir", "std3_ndbi", "std5_ndbi"]
    + ["ndvi_max_chuva", "ndvi_amplitude", "declividade"]
)


def _norm(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        r = (a - b) / (a + b)
    return np.where(np.isfinite(r), r, 0.0).astype(np.float32)


def _std_local(a: np.ndarray, k: int) -> np.ndarray:
    a = a.astype(np.float32)
    m = uniform_filter(a, k, mode="reflect")
    m2 = uniform_filter(a * a, k, mode="reflect")
    return np.sqrt(np.maximum(m2 - m * m, 0)).astype(np.float32)


def calcular(refl: np.ndarray, ndvi_max_chuva: np.ndarray | None, declividade: np.ndarray) -> np.ndarray:
    """refl: (6, H, W) float em 0–1, NaN onde não há observação."""
    blue, green, red, nir, swir1, swir2 = [refl[i].astype(np.float32) for i in range(6)]
    ndvi = _norm(nir, red)
    ndbi = _norm(swir1, nir)
    mndwi = _norm(green, swir1)
    bui = ndbi - ndvi
    bsi = _norm(swir1 + red, nir + blue)
    savi = np.where((nir + red + 0.5) != 0, (nir - red) / (nir + red + 0.5) * 1.5, 0).astype(np.float32)
    ibi = _norm(ndbi, (savi + mndwi) / 2)
    nbr2 = _norm(swir1, swir2)
    if ndvi_max_chuva is None:
        ndvi_max_chuva = np.full_like(ndvi, np.nan)
    ndvi_max_chuva = ndvi_max_chuva.astype(np.float32)
    amp = ndvi_max_chuva - ndvi
    feats = [
        blue, green, red, nir, swir1, swir2,
        ndvi, ndbi, mndwi, bui, bsi, ibi, nbr2,
        _std_local(np.nan_to_num(nir), 3), _std_local(np.nan_to_num(nir), 5),
        _std_local(ndbi, 3), _std_local(ndbi, 5),
        ndvi_max_chuva, amp, declividade.astype(np.float32),
    ]
    out = np.stack(feats).astype(np.float32)
    assert out.shape[0] == len(NOMES)
    return out


def declividade_graus(elev: np.ndarray, res: float) -> np.ndarray:
    gy, gx = np.gradient(elev.astype(np.float32), res)
    return np.degrees(np.arctan(np.hypot(gx, gy))).astype(np.float32)
