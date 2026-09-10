"""
E3b / Fase 3 passo 4 (PLANO.md) — classificação própria da mancha urbana da
sede de Canaã dos Carajás, 1984–2026, Random Forest por era de sensor.

Entradas (tudo público): composições de `22_compor_anual.py`, referências de
`lib/referencias.py` (IBGE Áreas Urbanizadas 2019/2022, MapBiomas Col. 11 e
Col. 4 10 m, WSF-Evolution/WSF2019, máscara de mineração MapBiomas 30 ∪ ANM).

Eras e rótulos de treino (revisão crítica do plano: "treino por era de sensor
+ amostra de pixels estáveis comum a todas as eras"):
  tm_etm  1984–2012  Landsat 5/7  refs 2000 e 2010: urbano = MapBiomas 24 ∩ WSF-Evo
                     (ano de assentamento ≤ ano de referência), erodido 1 pixel;
                     não urbano = fora de 90 m de qualquer urbano MapBiomas/WSF, fora
                     da máscara de mineração, estratificado por classe MapBiomas.
  oli     2013–2026  Landsat 8/9  refs 2019 (AU 2019 revisada ∩ WSF2019|MB10m) e
                     2022 (AU 2022 ∩ MapBiomas 10 m classe 24); loteamentos vazios
                     (tipo IBGE) sem construção entram como negativos explícitos.
  msi10   2017–2026  Sentinel-2 10 m, ref 2022 (AU 2022 ∩ MapBiomas 10 m 24),
                     série secundária.
  Amostra estável (todas as eras, feições de 3 anos por era): urbano = AU 2022
  densa ∩ WSF-Evo ≤ 1990 ∩ MapBiomas 24 em 1995 e 2005; não urbano = floresta
  (3), pastagem (15) ou água (33) em TODOS os anos MapBiomas 1985–2025.
  A AU 2015 do IBGE não cobre Canaã (E3a) — a era OLI usa 2019 e 2022.

Modelo: RandomForest 500 árvores, class_weight balanced, min_samples_leaf 5;
validação cruzada por blocos espaciais de 3 km (5 dobras) reportada em
`modelos_rf.json` junto com OOB e importâncias. Limiar 0,5 na probabilidade.

Pós-processamento (ordem):
  1. maioria temporal em janela de 3 anos (1º ano: exige confirmação no 2º;
     último ano: bruto);
  2. persistência: pixel urbano em 2 anos consecutivos fica "selado" e não
     retrai depois (não retração só no núcleo selado);
  3. máscara de mineração: construído dentro dela vira classe 3 (curva separada);
  4. unidade mínima 1 ha (8-conectividade) e preenchimento de buracos ≤ 1 ha;
  5. separação sede contígua (classe 1: componentes ligados ao núcleo por
     encadeamento de 1 km, até 10 km do núcleo) × outros núcleos (classe 2);
  0. (antes de tudo) abertura 3×3 com restauração de borda em cada ano: tira
     rodovias/estradas de 1 pixel e pontinhos, que antes eram "selados" e
     encadeados à sede.
  6. a partir de 2022, loteamentos vazios da AU 2022 sem construção = classe 4.

Saídas:
  data/interim/classificacao/prob30_<ano>.tif, prob10_<ano>.tif  (0–100)
  data/processed/geo/mancha_propria/mancha30_<ano>.tif  classes 0–4 (uint8)
  data/processed/geo/mancha_propria/mancha30_<ano>.parquet  polígonos (classe, area_ha)
  data/processed/geo/mancha_propria/mancha10_<ano>.tif/.parquet  (2017–2026)
  data/processed/geo/mancha_propria/ano_urbanizacao30.tif  1º ano urbano por pixel
  data/processed/geo/mancha_propria/clareira_mss_<ano>.tif  marcos 1973/1982 (MSS)
  data/processed/geo/mancha_propria_anual.{parquet,csv}  área por ano × classe
  data/processed/geo/modelos_rf.json  métricas de treino/validação por era

Uso:
    .venv/bin/python pipeline/23_classificar_mancha.py            # tudo
    .venv/bin/python pipeline/23_classificar_mancha.py --so-pos   # só pós-processamento
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import shapes
from scipy.ndimage import binary_dilation, binary_erosion, distance_transform_edt, label
from shapely.geometry import shape as to_shape
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupKFold

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import referencias as R  # noqa: E402
from lib.feicoes import NOMES, calcular  # noqa: E402
from lib.grade import GRADE10, GRADE30, CRS_METRICO, Grade, escrever  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
COMP = BASE / "data" / "interim" / "composicoes"
OUT_I = BASE / "data" / "interim" / "classificacao"
OUT_P = BASE / "data" / "processed" / "geo" / "mancha_propria"
GEO = BASE / "data" / "processed" / "geo"
for d in (OUT_I, OUT_P):
    d.mkdir(parents=True, exist_ok=True)

ESCALA = 10000
NODATA = -32768
SEMENTE = 1502152
N_ARVORES = 500
LIMIAR = 50  # %
ERAS = {
    "tm_etm": {"anos": list(range(1984, 2013)), "refs": [2000, 2010], "estaveis": [1990, 2000, 2010]},
    "oli": {"anos": list(range(2013, 2027)), "refs": [2019, 2022], "estaveis": [2014, 2019, 2022]},
}
ANOS_S2 = list(range(2017, 2027))
CLASSES = {0: "nao_urbano", 1: "sede", 2: "outros_nucleos", 3: "construido_mineracao", 4: "loteamento_vazio"}

rng = np.random.default_rng(SEMENTE)


# ----------------------------------------------------------------------------
# feições
# ----------------------------------------------------------------------------

def _declividade(grade: Grade) -> np.ndarray:
    with rasterio.open(COMP / "declividade30.tif") as s:
        d = s.read(1)
    if grade.res == 10:
        d = np.repeat(np.repeat(d, 3, axis=0), 3, axis=1)
    return d


def feicoes(ano: int, res: int = 30) -> tuple[np.ndarray, np.ndarray]:
    """(n_feicoes, H, W) float32 e máscara de pixels válidos."""
    grade = GRADE30 if res == 30 else GRADE10
    with rasterio.open(COMP / f"comp{res}_{ano}.tif") as s:
        arr = s.read()
    refl = arr[:6].astype(np.float32)
    valido = refl[0] != NODATA
    refl = np.where(valido, refl / ESCALA, np.nan)
    p = COMP / f"ndvimax{res}_{ano}.tif"
    if p.exists():
        with rasterio.open(p) as s:
            nm = s.read(1).astype(np.float32)
        nm = np.where(nm == NODATA, np.nan, nm / ESCALA)
    else:
        nm = None
    f = calcular(refl, nm, _declividade(grade))
    # sem observação de chuva: amplitude desconhecida → 0 e ndvi_max = ndvi seca
    i_nm, i_amp, i_ndvi = NOMES.index("ndvi_max_chuva"), NOMES.index("ndvi_amplitude"), NOMES.index("ndvi")
    sem = ~np.isfinite(f[i_nm])
    f[i_nm][sem] = f[i_ndvi][sem]
    f[i_amp][sem] = 0.0
    f = np.nan_to_num(f, nan=0.0, posinf=0.0, neginf=0.0)
    return f, valido


# ----------------------------------------------------------------------------
# rótulos
# ----------------------------------------------------------------------------

def _erodir(m: np.ndarray, px: int = 1) -> np.ndarray:
    return binary_erosion(m, structure=np.ones((2 * px + 1, 2 * px + 1), bool))


def _dilatar(m: np.ndarray, px: int) -> np.ndarray:
    return binary_dilation(m, structure=np.ones((2 * px + 1, 2 * px + 1), bool))


def rotulos_referencia(ano: int, mascara: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """urbano (bool), nao_urbano (bool), classe MapBiomas (para estratificar)."""
    mb = R.mapbiomas(ano)
    wsf = R.wsf_evolution()
    if ano == 2022:
        au = R.areas_urbanizadas(2022)
        f24 = R.mapbiomas10_frac24(2022)
        urb = np.isin(au, [1, 2]) & (f24 >= 0.5)
        qualquer = np.isin(au, [1, 2, 4]) | (mb == 24)
        neg_extra = (au == 3) & (f24 < 0.2)
    elif ano == 2019:
        au = R.areas_urbanizadas(2019)
        w19 = R.wsf2019()
        f24 = R.mapbiomas10_frac24(2019)
        urb = np.isin(au, [1, 2]) & ((w19 >= 0.5) | (f24 >= 0.5))
        qualquer = np.isin(au, [1, 2, 4]) | (mb == 24)
        neg_extra = (au == 3) & (w19 < 0.2) & (f24 < 0.2)
    else:
        urb = (mb == 24) & (wsf > 0) & (wsf <= ano)
        qualquer = (mb == 24) | (wsf > 0)
        neg_extra = np.zeros_like(urb)
    urb = _erodir(urb, 1)
    nao = ~_dilatar(qualquer, 3) & ~np.isin(mb, [24, 30, 0]) & ~mascara
    nao |= neg_extra
    return urb, nao, mb


def rotulos_estaveis(mascara: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    au = R.areas_urbanizadas(2022)
    wsf = R.wsf_evolution()
    urb = (au == 1) & (wsf > 0) & (wsf <= 1990) & (R.mapbiomas(1995) == 24) & (R.mapbiomas(2005) == 24)
    urb = _erodir(urb, 1)
    floresta = np.ones(GRADE30.shape, bool)
    pasto = np.ones(GRADE30.shape, bool)
    agua = np.ones(GRADE30.shape, bool)
    for a in range(1985, 2026):
        mb = R.mapbiomas(a)
        floresta &= mb == 3
        pasto &= mb == 15
        agua &= mb == 33
    nao = (floresta | pasto | agua) & ~mascara & ~_dilatar(np.isin(au, [1, 2, 4]), 3)
    mb = R.mapbiomas(2022)
    return urb, nao, mb


def amostrar(urb: np.ndarray, nao: np.ndarray, mb: np.ndarray, n_pos: int, n_neg: int) -> tuple[np.ndarray, np.ndarray]:
    """Índices lineares de positivos e negativos; negativos com cota mínima por
    grupo MapBiomas (floresta / pastagem / outros) para cobrir a confusão dominante."""
    pos = np.flatnonzero(urb)
    pos = rng.choice(pos, min(n_pos, len(pos)), replace=False)
    grupos = {"floresta": np.isin(mb, [3, 4, 5, 6, 49]), "pastagem": mb == 15,
              "outros": ~np.isin(mb, [3, 4, 5, 6, 49, 15])}
    negs = []
    cota = n_neg // 3
    sobra = 0
    for nome, g in grupos.items():
        idx = np.flatnonzero(nao & g)
        k = min(cota + sobra, len(idx))
        sobra = cota + sobra - k
        if k:
            negs.append(rng.choice(idx, k, replace=False))
    return pos, np.concatenate(negs)


def _blocos(idx: np.ndarray, grade: Grade, tam_m: float = 3000) -> np.ndarray:
    lin, col = np.divmod(idx, grade.largura)
    n = int(tam_m / grade.res)
    return (lin // n) * 10000 + (col // n)


# ----------------------------------------------------------------------------
# treino por era
# ----------------------------------------------------------------------------

def montar_treino(era: str, mascara: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    cfg = ERAS[era]
    X, y, g, resumo = [], [], [], {}
    for ref in cfg["refs"]:
        urb, nao, mb = rotulos_referencia(ref, mascara)
        pos, neg = amostrar(urb, nao, mb, 6000, 12000)
        f, _ = feicoes(ref, 30)
        F = f.reshape(f.shape[0], -1).T
        X += [F[pos], F[neg]]
        y += [np.ones(len(pos), np.int8), np.zeros(len(neg), np.int8)]
        g += [_blocos(pos, GRADE30), _blocos(neg, GRADE30)]
        resumo[f"ref_{ref}"] = {"urbano_px_disponiveis": int(urb.sum()), "nao_px_disponiveis": int(nao.sum()),
                                "pos": int(len(pos)), "neg": int(len(neg))}
    urb_e, nao_e, mb_e = rotulos_estaveis(mascara)
    pos_e, neg_e = amostrar(urb_e, nao_e, mb_e, 1500, 3000)
    for a in cfg["estaveis"]:
        f, _ = feicoes(a, 30)
        F = f.reshape(f.shape[0], -1).T
        X += [F[pos_e], F[neg_e]]
        y += [np.ones(len(pos_e), np.int8), np.zeros(len(neg_e), np.int8)]
        g += [_blocos(pos_e, GRADE30), _blocos(neg_e, GRADE30)]
    resumo["estaveis"] = {"urbano_px": int(urb_e.sum()), "nao_px": int(nao_e.sum()), "pos": int(len(pos_e)),
                          "neg": int(len(neg_e)), "anos": cfg["estaveis"]}
    return np.vstack(X), np.concatenate(y), np.concatenate(g), resumo


def montar_treino_s2(mascara: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    au = R.areas_urbanizadas(2022, GRADE10)
    mb10 = R.ler_para_grade(R.PROD / "mapbiomas_col4_10m" / "mapbiomas_col4_10m_2022.tif", GRADE10)
    mb30 = np.repeat(np.repeat(R.mapbiomas(2022), 3, axis=0), 3, axis=1)
    masc10 = np.repeat(np.repeat(mascara, 3, axis=0), 3, axis=1)
    urb = _erodir(np.isin(au, [1, 2]) & (mb10 == 24), 1)
    qualquer = np.isin(au, [1, 2, 4]) | (mb10 == 24)
    nao = ~_dilatar(qualquer, 9) & ~np.isin(mb10, [24, 30, 0]) & ~masc10
    nao |= (au == 3) & (mb10 != 24)
    pos, neg = amostrar(urb, nao, mb30, 12000, 24000)
    f, _ = feicoes(2022, 10)
    F = f.reshape(f.shape[0], -1).T
    X = [F[pos], F[neg]]
    y = [np.ones(len(pos), np.int8), np.zeros(len(neg), np.int8)]
    g = [_blocos(pos, GRADE10), _blocos(neg, GRADE10)]
    # estáveis a 10 m (mesma definição, ampliada 3×3), anos 2018 e 2025
    urb_e, nao_e, _ = rotulos_estaveis(mascara)
    urb_e10 = np.repeat(np.repeat(urb_e, 3, axis=0), 3, axis=1) & (mb10 == 24)
    nao_e10 = np.repeat(np.repeat(nao_e, 3, axis=0), 3, axis=1)
    pos_e, neg_e = amostrar(urb_e10, nao_e10, mb30, 3000, 6000)
    for a in (2018, 2025):
        f, _ = feicoes(a, 10)
        F = f.reshape(f.shape[0], -1).T
        X += [F[pos_e], F[neg_e]]
        y += [np.ones(len(pos_e), np.int8), np.zeros(len(neg_e), np.int8)]
        g += [_blocos(pos_e, GRADE10), _blocos(neg_e, GRADE10)]
    resumo = {"ref_2022": {"urbano_px_disponiveis": int(urb.sum()), "nao_px_disponiveis": int(nao.sum()),
                           "pos": int(len(pos)), "neg": int(len(neg))},
              "estaveis": {"pos": int(len(pos_e)), "neg": int(len(neg_e)), "anos": [2018, 2025]}}
    return np.vstack(X), np.concatenate(y), np.concatenate(g), resumo


def _metricas(y: np.ndarray, p: np.ndarray) -> dict:
    tp = int(((p == 1) & (y == 1)).sum())
    fp = int(((p == 1) & (y == 0)).sum())
    fn = int(((p == 0) & (y == 1)).sum())
    tn = int(((p == 0) & (y == 0)).sum())
    oa = (tp + tn) / max(len(y), 1)
    ua = tp / max(tp + fp, 1)
    pa = tp / max(tp + fn, 1)
    f1 = 2 * ua * pa / max(ua + pa, 1e-9)
    return {"oa": round(oa, 4), "usuario_urbano": round(ua, 4), "produtor_urbano": round(pa, 4),
            "f1_urbano": round(f1, 4), "tp": tp, "fp": fp, "fn": fn, "tn": tn}


def treinar(X: np.ndarray, y: np.ndarray, g: np.ndarray, n_arvores: int = N_ARVORES) -> tuple[RandomForestClassifier, dict]:
    t0 = time.time()
    cv = GroupKFold(n_splits=5)
    pred = np.zeros(len(y), np.int8)
    for tr, te in cv.split(X, y, g):
        m = RandomForestClassifier(n_estimators=max(n_arvores // 2, 100), min_samples_leaf=5, class_weight="balanced",
                                   n_jobs=-1, random_state=SEMENTE)
        m.fit(X[tr], y[tr])
        pred[te] = (m.predict_proba(X[te])[:, 1] >= LIMIAR / 100).astype(np.int8)
    cv_met = _metricas(y, pred)
    rf = RandomForestClassifier(n_estimators=n_arvores, min_samples_leaf=5, class_weight="balanced",
                                oob_score=True, n_jobs=-1, random_state=SEMENTE)
    rf.fit(X, y)
    imp = dict(sorted(zip(NOMES, rf.feature_importances_.round(4).tolist()), key=lambda kv: -kv[1]))
    diag = {"n_amostras": int(len(y)), "n_urbano": int(y.sum()), "oob": round(float(rf.oob_score_), 4),
            "cv_blocos_3km": cv_met, "importancias": imp, "segundos": round(time.time() - t0, 1),
            "n_blocos": int(len(np.unique(g)))}
    return rf, diag


def prever(rf: RandomForestClassifier, ano: int, res: int) -> np.ndarray:
    f, valido = feicoes(ano, res)
    F = f.reshape(f.shape[0], -1).T
    prob = np.zeros(F.shape[0], np.float32)
    passo = 400_000
    for i in range(0, F.shape[0], passo):
        prob[i:i + passo] = rf.predict_proba(F[i:i + passo])[:, 1]
    prob = prob.reshape(f.shape[1:])
    prob = np.where(valido, np.round(prob * 100), 255).astype(np.uint8)
    grade = GRADE30 if res == 30 else GRADE10
    escrever(OUT_I / f"prob{res}_{ano}.tif", [prob], ["prob_urbano_pct"], grade, nodata=255,
             tags={"ano": str(ano), "limiar_pct": str(LIMIAR)})
    return prob


# ----------------------------------------------------------------------------
# pós-processamento
# ----------------------------------------------------------------------------

def _componentes(m: np.ndarray):
    return label(m, structure=np.ones((3, 3), bool))


def _remover_pequenos(m: np.ndarray, minimo_px: int) -> np.ndarray:
    lab, n = _componentes(m)
    if n == 0:
        return m
    tam = np.bincount(lab.ravel())
    tam[0] = 0
    return tam[lab] >= minimo_px


def _sem_linhas(m: np.ndarray) -> np.ndarray:
    """Remove feições lineares de 1 pixel (rodovias, cercas, estradas vicinais) e
    pontinhos isolados: abertura 3×3 seguida de restauração de 1 pixel de borda,
    restrita ao original — a mancha compacta mantém o contorno, a estrada some."""
    aberto = binary_erosion(m, structure=np.ones((3, 3), bool))
    aberto = binary_dilation(aberto, structure=np.ones((3, 3), bool))
    return m & binary_dilation(aberto, structure=np.ones((3, 3), bool))


def _preencher_buracos(m: np.ndarray, max_px: int) -> np.ndarray:
    lab, n = _componentes(~m)
    if n == 0:
        return m
    tam = np.bincount(lab.ravel())
    # o componente que toca a borda é o "fora"; buracos pequenos viram urbano
    borda = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    peq = (tam <= max_px)
    peq[borda] = False
    peq[0] = False
    return m | peq[lab]


def nucleo_xy() -> tuple[float, float]:
    g = R._au_gdf(2022)
    g = g[g["classe"] == 1]
    maior = g.loc[g.geometry.area.idxmax()].geometry
    c = maior.centroid
    return float(c.x), float(c.y)


def separar_sede(urb: np.ndarray, grade: Grade, nucleo: tuple[float, float]) -> np.ndarray:
    """1 = sede contígua (encadeamento de 1 km a partir do componente do núcleo,
    até 10 km do núcleo), 2 = outros núcleos."""
    lab, n = _componentes(urb)
    out = np.zeros(urb.shape, np.uint8)
    if n == 0:
        return out
    xs, ys = grade.xy()
    col = int((nucleo[0] - grade.x0) // grade.res)
    lin = int((grade.y1 - nucleo[1]) // grade.res)
    # componente do núcleo: o que contém o ponto ou o mais próximo a ≤ 3 km
    principal = lab[lin, col]
    if principal == 0:
        yy, xx = np.nonzero(urb)
        d = np.hypot(xs[xx] - nucleo[0], ys[yy] - nucleo[1])
        if d.min() > 3000:
            out[urb] = 2
            return out
        principal = lab[yy[d.argmin()], xx[d.argmin()]]
    sede = lab == principal
    X, Y = np.meshgrid(xs, ys)
    perto = np.hypot(X - nucleo[0], Y - nucleo[1]) <= 10000
    while True:  # encadeamento: componentes a ≤ 2 km da sede corrente (distância euclidiana)
        dist = distance_transform_edt(~sede) * grade.res
        alcance = (dist <= 1000) & urb & perto
        ids = np.unique(lab[alcance])
        novo = np.isin(lab, ids[ids > 0])
        if novo.sum() == sede.sum():
            break
        sede = novo
    out[urb] = 2
    out[sede] = 1
    return out


def pos_processar(prob: dict[int, np.ndarray], mascara: np.ndarray, grade: Grade, mmu_ha: float = 1.0,
                  buraco_ha: float = 1.0, lote_vazio: np.ndarray | None = None) -> tuple[dict[int, np.ndarray], pd.DataFrame]:
    anos = sorted(prob)
    px_ha = (grade.res ** 2) / 10000
    b = {a: _sem_linhas((prob[a] != 255) & (prob[a] >= LIMIAR)) for a in anos}
    # 1. maioria temporal (janela 3)
    bm = {}
    for i, a in enumerate(anos):
        if 0 < i < len(anos) - 1:
            s = b[anos[i - 1]].astype(np.int8) + b[a] + b[anos[i + 1]]
            bm[a] = s >= 2
        elif i == 0:  # 1º ano: sem ano anterior, exige confirmação no seguinte (tira o ruído de 1984)
            bm[a] = b[a] & b[anos[1]]
        else:  # último ano: fica o bruto (crescimento recente não pode ser confirmado ainda)
            bm[a] = b[a].copy()
    # 2. persistência ≥ 2 anos consecutivos → selado, sem retração
    selado = np.zeros(grade.shape, bool)
    final = {}
    for i, a in enumerate(anos):
        if i < len(anos) - 1:
            selado |= bm[a] & bm[anos[i + 1]]
        final[a] = bm[a] | selado
    nucleo = nucleo_xy()
    mmu_px = int(round(mmu_ha / px_ha))
    bur_px = int(round(buraco_ha / px_ha))
    saida, linhas = {}, []
    for a in anos:
        u = final[a]
        area_bruta = float(b[a].sum() * px_ha)
        mineracao = u & mascara
        u = u & ~mascara
        u = _remover_pequenos(u, mmu_px)
        u = _preencher_buracos(u, bur_px)
        cls = separar_sede(u, grade, nucleo)
        cls[mineracao & ~u] = 3
        if lote_vazio is not None and a >= 2022:
            cls[(lote_vazio) & (cls == 0)] = 4
        saida[a] = cls
        _, n_comp = _componentes(u)
        linhas.append({"ano": a, "area_bruta_ha": area_bruta,
                       "area_sede_ha": float((cls == 1).sum() * px_ha),
                       "area_outros_nucleos_ha": float((cls == 2).sum() * px_ha),
                       "area_construido_mineracao_ha": float((cls == 3).sum() * px_ha),
                       "area_loteamento_vazio_ha": float((cls == 4).sum() * px_ha),
                       "n_componentes": int(n_comp),
                       "frac_sem_dado": float((prob[a] == 255).mean())})
    return saida, pd.DataFrame(linhas)


def vetorizar(cls: np.ndarray, grade: Grade) -> gpd.GeoDataFrame:
    geoms, classes = [], []
    for c in (1, 2, 3, 4):
        m = (cls == c).astype(np.uint8)
        if not m.any():
            continue
        for geom, v in shapes(m, mask=m.astype(bool), transform=grade.transform, connectivity=8):
            geoms.append(to_shape(geom))
            classes.append(c)
    g = gpd.GeoDataFrame({"classe": classes, "nome": [CLASSES[c] for c in classes]}, geometry=geoms, crs=CRS_METRICO)
    g["area_ha"] = g.geometry.area / 10000
    return g


def gravar_serie(saida: dict[int, np.ndarray], grade: Grade, res: int) -> None:
    for a, cls in saida.items():
        escrever(OUT_P / f"mancha{res}_{a}.tif", [cls.astype(np.uint8)], ["classe"], grade, nodata=None,
                 tags={"ano": str(a), "classes": json.dumps(CLASSES, ensure_ascii=False)})
        vetorizar(cls, grade).to_parquet(OUT_P / f"mancha{res}_{a}.parquet")
    anos = sorted(saida)
    primeiro = np.zeros(grade.shape, np.int16)
    for a in reversed(anos):
        urb = np.isin(saida[a], [1, 2])
        primeiro[urb] = a
    escrever(OUT_P / f"ano_urbanizacao{res}.tif", [primeiro], ["primeiro_ano_urbano"], grade, nodata=0,
             tags={"nota": "0 = nunca urbano na série; classes 1 e 2 (sede e outros núcleos)"})


# ----------------------------------------------------------------------------
# marcos MSS (1973, 1982): clareira do núcleo, não mancha urbana
# ----------------------------------------------------------------------------

def marcos_mss() -> list[dict]:
    from skimage.filters import threshold_otsu

    nucleo = nucleo_xy()
    xs, ys = GRADE30.xy()
    X, Y = np.meshgrid(xs, ys)
    raio = np.hypot(X - nucleo[0], Y - nucleo[1])
    linhas = []
    for p in sorted(COMP.glob("mss30_*.tif")):
        ano = int(p.stem.split("_")[1])
        with rasterio.open(p) as s:
            arr = s.read().astype(np.float32)
        red, nir = arr[1], arr[2]
        ok = (red != NODATA) & (nir != NODATA)
        with np.errstate(all="ignore"):
            ndvi = np.where(ok, (nir - red) / (nir + red), np.nan)
        lim = float(threshold_otsu(ndvi[ok]))
        clareira = ok & (ndvi < lim)
        clareira = _remover_pequenos(clareira, 6)
        escrever(OUT_P / f"clareira_mss_{ano}.tif", [clareira.astype(np.uint8)], ["clareira"], GRADE30, nodata=None,
                 tags={"ano": str(ano), "limiar_ndvi_otsu": f"{lim:.3f}", "nivel": "MSS L1 DN",
                       "nota": "clareira/solo exposto (NDVI < Otsu), nao e mancha urbana"})
        linhas.append({"ano": ano, "limiar_ndvi_otsu": lim, "area_clareira_janela_ha": float(clareira.sum() * 0.09),
                       "area_clareira_3km_nucleo_ha": float((clareira & (raio <= 3000)).sum() * 0.09),
                       "frac_valida": float(ok.mean())})
    return linhas


# ----------------------------------------------------------------------------

def main(so_pos: bool = False) -> None:
    import joblib

    mascara = R.mascara_mineracao()
    diag = {}
    if not so_pos:
        for era, cfg in ERAS.items():
            print(f"era {era}: montando treino …", flush=True)
            X, y, g, resumo = montar_treino(era, mascara)
            rf, d = treinar(X, y, g)
            d["amostras"] = resumo
            diag[era] = d
            joblib.dump(rf, OUT_I / f"rf_{era}.joblib")
            print(f"  {len(y):,} amostras, OOB {d['oob']:.3f}, CV-blocos OA {d['cv_blocos_3km']['oa']:.3f} "
                  f"F1 {d['cv_blocos_3km']['f1_urbano']:.3f}", flush=True)
            for a in cfg["anos"]:
                if (COMP / f"comp30_{a}.tif").exists():
                    prever(rf, a, 30)
            print(f"  previstos {len(cfg['anos'])} anos", flush=True)
        print("era msi10 (Sentinel-2): montando treino …", flush=True)
        X, y, g, resumo = montar_treino_s2(mascara)
        rf, d = treinar(X, y, g, n_arvores=300)
        d["amostras"] = resumo
        diag["msi10"] = d
        joblib.dump(rf, OUT_I / "rf_msi10.joblib")
        print(f"  {len(y):,} amostras, OOB {d['oob']:.3f}, CV-blocos OA {d['cv_blocos_3km']['oa']:.3f}", flush=True)
        for a in ANOS_S2:
            if (COMP / f"comp10_{a}.tif").exists():
                prever(rf, a, 10)
                print(f"  S2 {a} previsto", flush=True)
        (GEO / "modelos_rf.json").write_text(json.dumps(diag, ensure_ascii=False, indent=2), "utf-8")

    print("pós-processamento 30 m …", flush=True)
    prob30 = {}
    for p in sorted(OUT_I.glob("prob30_*.tif")):
        with rasterio.open(p) as s:
            prob30[int(p.stem.split("_")[1])] = s.read(1)
    lote = R.areas_urbanizadas(2022) == 3
    saida30, tab30 = pos_processar(prob30, mascara, GRADE30, lote_vazio=lote)
    gravar_serie(saida30, GRADE30, 30)
    tab30["serie"] = "landsat_30m"

    print("pós-processamento 10 m …", flush=True)
    prob10 = {}
    for p in sorted(OUT_I.glob("prob10_*.tif")):
        with rasterio.open(p) as s:
            prob10[int(p.stem.split("_")[1])] = s.read(1)
    tabs = [tab30]
    if prob10:
        masc10 = np.repeat(np.repeat(mascara, 3, axis=0), 3, axis=1)
        lote10 = R.areas_urbanizadas(2022, GRADE10) == 3
        saida10, tab10 = pos_processar(prob10, masc10, GRADE10, lote_vazio=lote10)
        gravar_serie(saida10, GRADE10, 10)
        tab10["serie"] = "sentinel2_10m"
        tabs.append(tab10)
    tab = pd.concat(tabs, ignore_index=True)
    tab.to_parquet(GEO / "mancha_propria_anual.parquet", index=False)
    tab.to_csv(GEO / "mancha_propria_anual.csv", index=False)

    marcos = marcos_mss()
    if marcos:
        pd.DataFrame(marcos).to_parquet(GEO / "marcos_mss.parquet", index=False)
        print("marcos MSS:", marcos)
    print(tab[tab["serie"] == "landsat_30m"][["ano", "area_bruta_ha", "area_sede_ha", "area_outros_nucleos_ha",
                                                "area_construido_mineracao_ha", "n_componentes"]].round(1).to_string(index=False))


if __name__ == "__main__":
    main(so_pos="--so-pos" in sys.argv)
