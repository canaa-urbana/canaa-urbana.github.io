"""
E3b / Fase 3 passo 3 (PLANO.md) — composições anuais da estação seca.

Lê os recortes de `21_baixar_cenas.py` (`data/interim/cenas/`) e grava, em
`data/interim/composicoes/`:

  comp30_<ano>.tif        1984–2026, Landsat TM/ETM+/OLI, 30 m: 6 bandas de
                          reflectância de superfície na escala ETM+ (int16 ×10000),
                          + n_obs (nº de observações válidas) + preenchido (0/1)
  ndvimax30_<ano>.tif     NDVI máximo da estação chuvosa (jan–abr), int16 ×10000
  comp10_<ano>.tif        2017–2026, Sentinel-2, 10 m, mesmas 6 bandas + n_obs
  ndvimax10_<ano>.tif     idem a 10 m
  mss30_<ano>.tif         1973 e 1982, Landsat MSS (green, red, nir08, nir09), marcos
  declividade30.tif       graus, do Copernicus DEM
  quicklook/<ano>.png     falsa-cor (swir1, nir, red) para inspeção visual
  composicoes.parquet     uma linha por composição: nº de cenas, datas reais,
                          sensores, fração de pixels com ≥1/≥3 obs, fração preenchida

Regras:
  · Máscara Landsat = QA_PIXEL bits 0–4 (fill, nuvem dilatada, cirro, nuvem,
    sombra) e faixa válida do C2 L2 (7273–43636 DN). Reflectância = DN·2,75e-5 − 0,2.
  · Máscara Sentinel-2 = SCL ∈ {0,1,3,8,9,10,11} (nodata, saturado, sombra,
    nuvens, cirro, neve). Reflectância = DN/10000 (BOA offset de 2022+ tratado:
    itens com `processing baseline ≥ 04.00` já vêm com offset -1000 aplicado
    pelo E84 nos COGs — verificado na leitura: valores em 0–10000).
  · Harmonização OLI→ETM+ (Roy et al. 2016, coeficientes OLS, como na
    implementação LandTrendr): ETM+ = a + b·OLI por banda. Aplicada a LC08/LC09
    e ao Sentinel-2 (MSI ≈ OLI; declarar no artigo).
  · Mediana por pixel e banda. Pixel sem observação no ano recebe a média das
    composições dos anos vizinhos (±1, ±2, ±3; flag `preenchido`) — sem gap-fill
    espacial, conforme a revisão do plano (2012 = só ETM+ SLC-off). O mesmo
    preenchimento vale para o NDVI máximo da chuva, que na Amazônia tem
    cobertura anual irregular (1995: nenhuma cena de chuva limpa).
    `--preencher` refaz só essa etapa.
  · 1984–1990: se a mediana de n_obs na janela for < 2, acrescenta cenas do
    ano anterior e do seguinte, registrando as datas reais usadas.

Uso:
    .venv/bin/python pipeline/22_compor_anual.py            # tudo
    .venv/bin/python pipeline/22_compor_anual.py 2010 2022  # só alguns anos
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.feicoes import declividade_graus  # noqa: E402
from lib.grade import GRADE10, GRADE30, Grade, agregar_3x3, escrever  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
CENAS = BASE / "data" / "interim" / "cenas"
OUT = BASE / "data" / "interim" / "composicoes"
(OUT / "quicklook").mkdir(parents=True, exist_ok=True)

ANOS_LANDSAT = range(1984, 2027)
ANOS_S2 = range(2017, 2027)
ESCALA = 10000
NODATA = -32768

# Roy et al. 2016 (Remote Sens. Environ. 185), OLI → ETM+ (OLS), na ordem
# blue, green, red, nir, swir1, swir2 — mesmos valores usados no LandTrendr.
ROY_INTERCEPTO = np.array([0.0183, 0.0123, 0.0123, 0.0448, 0.0306, 0.0116], dtype=np.float32)
ROY_INCLINACAO = np.array([0.8850, 0.9317, 0.9372, 0.8339, 0.8639, 0.9165], dtype=np.float32)

QA_BITS_RUINS = (1 << 0) | (1 << 1) | (1 << 2) | (1 << 3) | (1 << 4)
SCL_RUIM = np.array([0, 1, 3, 8, 9, 10, 11])


def _manifesto() -> pd.DataFrame:
    m = pd.read_parquet(CENAS / "manifesto.parquet")
    return m[m["gravado"]].copy()


def _ler(caminho: Path) -> tuple[np.ndarray, list[str], dict]:
    with rasterio.open(caminho) as src:
        return src.read(), list(src.descriptions), src.tags()


# ----------------------------------------------------------------------------
# Landsat
# ----------------------------------------------------------------------------

def _refl_landsat(arr: np.ndarray, nomes: list[str], plataforma: str) -> np.ndarray:
    """(7,H,W) uint16 → (6,H,W) float32 com NaN nos pixels mascarados."""
    qa = arr[nomes.index("qa_pixel")]
    ruim = (qa & QA_BITS_RUINS) != 0
    bandas = [arr[nomes.index(b)] for b in ("blue", "green", "red", "nir08", "swir16", "swir22")]
    out = np.empty((6,) + qa.shape, dtype=np.float32)
    for i, dn in enumerate(bandas):
        valido = (dn >= 7273) & (dn <= 43636) & ~ruim
        r = dn.astype(np.float32) * 2.75e-5 - 0.2
        out[i] = np.where(valido, r, np.nan)
    oli = "LANDSAT_8" in plataforma.upper() or "LANDSAT_9" in plataforma.upper() \
        or plataforma.upper() in ("LC08", "LC09")
    if oli:
        out = ROY_INTERCEPTO[:, None, None] + ROY_INCLINACAO[:, None, None] * out
    return out


def _empilhar_landsat(linhas: pd.DataFrame, grupo: str) -> tuple[np.ndarray, list[str]]:
    pilha, sensores = [], []
    for _, r in linhas.iterrows():
        arr, nomes, tags = _ler(CENAS / r["arquivo"])
        plat = tags.get("plataforma", str(r.get("plataforma", "")))
        if grupo == "landsat":
            pilha.append(_refl_landsat(arr, nomes, plat))
        else:  # chuva: só red, nir08, qa → NDVI
            qa = arr[nomes.index("qa_pixel")]
            ruim = (qa & QA_BITS_RUINS) != 0
            red = arr[nomes.index("red")].astype(np.float32) * 2.75e-5 - 0.2
            nir = arr[nomes.index("nir08")].astype(np.float32) * 2.75e-5 - 0.2
            ok = ~ruim & (arr[nomes.index("red")] >= 7273) & (arr[nomes.index("nir08")] >= 7273)
            with np.errstate(divide="ignore", invalid="ignore"):
                ndvi = (nir - red) / (nir + red)
            pilha.append(np.where(ok & np.isfinite(ndvi), ndvi, np.nan)[None].astype(np.float32))
        sensores.append(plat)
    return np.stack(pilha), sensores  # (n, b, H, W)


def _mediana(pilha: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    with np.errstate(all="ignore"):
        med = np.nanmedian(pilha, axis=0)
    n_obs = np.isfinite(pilha[:, 0]).sum(axis=0).astype(np.int16)
    return med, n_obs


def _gravar_comp(caminho: Path, med: np.ndarray, n_obs: np.ndarray, grade: Grade,
                 preenchido: np.ndarray | None, tags: dict) -> None:
    bandas = [np.where(np.isfinite(med[i]), np.round(med[i] * ESCALA), NODATA).astype(np.int16)
              for i in range(med.shape[0])]
    nomes = ["blue", "green", "red", "nir", "swir1", "swir2"][: med.shape[0]]
    bandas.append(n_obs.astype(np.int16))
    nomes.append("n_obs")
    if preenchido is not None:
        bandas.append(preenchido.astype(np.int16))
        nomes.append("preenchido")
    escrever(caminho, bandas, nomes, grade, nodata=NODATA, tags=tags)


def _gravar_ndvimax(caminho: Path, ndvi_max: np.ndarray, grade: Grade, tags: dict) -> None:
    b = np.where(np.isfinite(ndvi_max), np.round(ndvi_max * ESCALA), NODATA).astype(np.int16)
    escrever(caminho, [b], ["ndvi_max_chuva"], grade, nodata=NODATA, tags=tags)


def _quicklook(ano: int, med: np.ndarray, sufixo: str = "") -> None:
    """Falsa-cor swir1/nir/red com estiramento fixo (2–98 % por banda)."""
    from PIL import Image

    rgb = []
    for i in (4, 3, 2):
        b = med[i]
        lo, hi = np.nanpercentile(b, 2), np.nanpercentile(b, 98)
        rgb.append(np.clip((np.nan_to_num(b, nan=lo) - lo) / max(hi - lo, 1e-6), 0, 1) * 255)
    img = np.stack(rgb, axis=-1).astype(np.uint8)
    Image.fromarray(img).save(OUT / "quicklook" / f"{ano}{sufixo}.png")


def compor_landsat(ano: int, m: pd.DataFrame, registro: list[dict]) -> None:
    dest = OUT / f"comp30_{ano}.tif"
    seca = m[(m["grupo"] == "landsat") & (m["ano"] == ano)]
    anos_usados = [ano]
    if len(seca) == 0:
        print(f"  {ano}: sem cenas de estação seca")
        return
    pilha, sensores = _empilhar_landsat(seca, "landsat")
    med, n_obs = _mediana(pilha)
    if ano <= 1990 and np.median(n_obs) < 2:
        viz = m[(m["grupo"] == "landsat") & (m["ano"].isin([ano - 1, ano + 1]))]
        if len(viz):
            p2, s2 = _empilhar_landsat(viz, "landsat")
            pilha = np.concatenate([pilha, p2])
            sensores += s2
            anos_usados += sorted(viz["ano"].unique().tolist())
            med, n_obs = _mediana(pilha)
    datas = sorted(seca["data"].tolist())
    tags = {
        "ano": str(ano), "n_cenas": str(pilha.shape[0]), "datas": ",".join(datas),
        "anos_usados": ",".join(map(str, anos_usados)),
        "sensores": ",".join(sorted(set(sensores))), "harmonizacao": "Roy2016 OLI->ETM+",
        "escala": str(ESCALA),
    }
    _gravar_comp(dest, med, n_obs, GRADE30, np.zeros_like(n_obs), tags)
    _quicklook(ano, med)
    registro.append({
        "produto": "comp30", "ano": ano, "n_cenas": int(pilha.shape[0]), "datas": ",".join(datas),
        "sensores": ",".join(sorted(set(sensores))), "anos_usados": ",".join(map(str, anos_usados)),
        "frac_ge1": float((n_obs >= 1).mean()), "frac_ge3": float((n_obs >= 3).mean()),
        "n_obs_mediana": float(np.median(n_obs)),
    })
    print(f"  {ano}: {pilha.shape[0]:2d} cenas, n_obs mediana {np.median(n_obs):.0f}, "
          f"≥1 obs {100 * (n_obs >= 1).mean():.1f}%", flush=True)


def ndvimax_landsat(ano: int, m: pd.DataFrame, registro: list[dict]) -> None:
    dest = OUT / f"ndvimax30_{ano}.tif"
    chuva = m[(m["grupo"] == "landsat_chuva") & (m["ano"] == ano)]
    anos = [ano]
    if len(chuva) < 3:  # anos com poucas cenas de chuva: junta os vizinhos
        chuva = m[(m["grupo"] == "landsat_chuva") & (m["ano"].isin([ano - 1, ano, ano + 1]))]
        anos = sorted(chuva["ano"].unique().tolist())
    if len(chuva) == 0:
        return
    pilha, _ = _empilhar_landsat(chuva, "landsat_chuva")
    with np.errstate(all="ignore"):
        ndvi_max = np.nanmax(pilha[:, 0], axis=0)
    _gravar_ndvimax(dest, ndvi_max, GRADE30, {"ano": str(ano), "anos_usados": ",".join(map(str, anos)),
                                              "n_cenas": str(pilha.shape[0])})
    registro.append({"produto": "ndvimax30", "ano": ano, "n_cenas": int(pilha.shape[0]),
                     "anos_usados": ",".join(map(str, anos)),
                     "frac_ge1": float(np.isfinite(ndvi_max).mean())})


def preencher_lacunas(anos: list[int], prefixo: str, grade: Grade) -> dict[int, float]:
    """Pixels sem observação no ano ← média dos anos vizinhos com dado (±1, ±2, ±3).
    Serve para comp30/comp10 (6 bandas + n_obs [+ preenchido]) e para ndvimax30/10
    (1 banda): as bandas de valor são as que vêm antes de `n_obs`/`preenchido`."""
    comps = {a: OUT / f"{prefixo}_{a}.tif" for a in anos if (OUT / f"{prefixo}_{a}.tif").exists()}
    frac = {}
    cache: dict[int, np.ndarray] = {}
    original: dict[int, np.ndarray] = {}

    def ler(a):
        if a not in cache:
            with rasterio.open(comps[a]) as s:
                cache[a] = s.read().astype(np.float32)
                original[a] = cache[a][0] == NODATA
        return cache[a]

    for a in sorted(comps):
        with rasterio.open(comps[a]) as s:
            nomes, tags = list(s.descriptions), s.tags()
        nb = min([i for i, n in enumerate(nomes) if n in ("n_obs", "preenchido")] + [len(nomes)])
        arr = ler(a).copy()
        faltando = arr[0] == NODATA
        if not faltando.any():
            frac[a] = 0.0
            continue
        for dist in (1, 2, 3):
            viz = [v for v in (a - dist, a + dist) if v in comps]
            if not viz:
                continue
            soma = np.zeros((nb,) + arr.shape[1:], np.float32)
            cnt = np.zeros(arr.shape[1:], np.float32)
            for v in viz:
                av = ler(v)
                ok = ~original[v]  # só observação real do vizinho, nunca preenchimento
                soma[:, ok] += av[:nb, ok]
                cnt[ok] += 1
            alvo = faltando & (cnt > 0)
            for i in range(nb):
                arr[i][alvo] = soma[i][alvo] / cnt[alvo]
            faltando = arr[0] == NODATA
            if not faltando.any():
                break
        preenchido = original[a] & (arr[0] != NODATA)
        frac[a] = float(preenchido.mean())
        bandas = [arr[i].astype(np.int16) for i in range(nb)]
        for extra in ("n_obs", "preenchido"):
            if extra in nomes:
                bandas.append(preenchido.astype(np.int16) if extra == "preenchido" else ler(a)[nomes.index(extra)].astype(np.int16))
        tags["frac_preenchida"] = f"{frac[a]:.4f}"
        escrever(comps[a], bandas, nomes, grade, nodata=NODATA, tags=tags)
        cache[a] = np.stack(bandas).astype(np.float32)  # original[a] preservado
    return frac


def preencher_tudo(registro: list[dict]) -> None:
    print("preenchendo lacunas com anos vizinhos …", flush=True)
    for prefixo, grade, anos in (("comp30", GRADE30, list(ANOS_LANDSAT)), ("ndvimax30", GRADE30, list(ANOS_LANDSAT)),
                                 ("comp10", GRADE10, list(ANOS_S2)), ("ndvimax10", GRADE10, list(ANOS_S2))):
        frac = preencher_lacunas(anos, prefixo, grade)
        for r in registro:
            if r["produto"] == prefixo:
                r["frac_preenchida"] = frac.get(r["ano"], 0.0)
        if frac:
            pior = max(frac, key=frac.get)
            print(f"  {prefixo}: fração preenchida máx {frac[pior]:.1%} ({pior})", flush=True)


# ----------------------------------------------------------------------------
# Sentinel-2 (10 m)
# ----------------------------------------------------------------------------

def _refl_s2(arr: np.ndarray, nomes: list[str]) -> np.ndarray:
    scl = arr[nomes.index("scl")]
    ruim = np.isin(scl, SCL_RUIM)
    out = np.empty((6,) + scl.shape, dtype=np.float32)
    for i, b in enumerate(("blue", "green", "red", "nir", "swir16", "swir22")):
        dn = arr[nomes.index(b)]
        out[i] = np.where((dn > 0) & ~ruim, dn.astype(np.float32) / 10000.0, np.nan)
    # MSI ≈ OLI: mesma harmonização para a escala ETM+
    return ROY_INTERCEPTO[:, None, None] + ROY_INCLINACAO[:, None, None] * out


def compor_s2(ano: int, m: pd.DataFrame, registro: list[dict]) -> None:
    seca = m[(m["grupo"] == "s2") & (m["ano"] == ano)]
    if len(seca) == 0:
        return
    pilha = []
    for _, r in seca.iterrows():
        arr, nomes, _ = _ler(CENAS / r["arquivo"])
        pilha.append(_refl_s2(arr, nomes))
    pilha = np.stack(pilha)
    med, n_obs = _mediana(pilha)
    datas = sorted(seca["data"].tolist())
    tags = {"ano": str(ano), "n_cenas": str(len(datas)), "datas": ",".join(datas),
            "sensores": "Sentinel-2 MSI", "harmonizacao": "Roy2016 OLI->ETM+ (MSI~OLI)", "escala": str(ESCALA)}
    _gravar_comp(OUT / f"comp10_{ano}.tif", med, n_obs, GRADE10, None, tags)
    _quicklook(ano, med, "_s2")
    registro.append({"produto": "comp10", "ano": ano, "n_cenas": len(datas), "datas": ",".join(datas),
                     "sensores": "Sentinel-2 MSI", "anos_usados": str(ano),
                     "frac_ge1": float((n_obs >= 1).mean()), "frac_ge3": float((n_obs >= 3).mean()),
                     "n_obs_mediana": float(np.median(n_obs))})
    chuva = m[(m["grupo"] == "s2_chuva") & (m["ano"] == ano)]
    if len(chuva):
        pilha = []
        for _, r in chuva.iterrows():
            arr, nomes, _ = _ler(CENAS / r["arquivo"])
            scl = arr[nomes.index("scl")]
            ok = ~np.isin(scl, SCL_RUIM) & (arr[nomes.index("red")] > 0)
            red = arr[nomes.index("red")].astype(np.float32)
            nir = arr[nomes.index("nir")].astype(np.float32)
            with np.errstate(all="ignore"):
                ndvi = (nir - red) / (nir + red)
            pilha.append(np.where(ok & np.isfinite(ndvi), ndvi, np.nan))
        with np.errstate(all="ignore"):
            ndvi_max = np.nanmax(np.stack(pilha), axis=0)
        _gravar_ndvimax(OUT / f"ndvimax10_{ano}.tif", ndvi_max, GRADE10,
                        {"ano": str(ano), "n_cenas": str(len(chuva))})
        registro.append({"produto": "ndvimax10", "ano": ano, "n_cenas": len(chuva), "anos_usados": str(ano),
                         "frac_ge1": float(np.isfinite(ndvi_max).mean())})
    print(f"  S2 {ano}: {len(datas)} cenas, n_obs mediana {np.median(n_obs):.0f}", flush=True)


# ----------------------------------------------------------------------------

def compor_mss(m: pd.DataFrame, registro: list[dict]) -> None:
    for ano in sorted(m.loc[m["grupo"] == "mss", "ano"].unique()):
        sel = m[(m["grupo"] == "mss") & (m["ano"] == ano)]
        pilha = []
        for _, r in sel.iterrows():
            arr, nomes, _ = _ler(CENAS / r["arquivo"])
            qa = arr[nomes.index("qa_pixel")]
            ruim = (qa & QA_BITS_RUINS) != 0
            out = np.empty((4,) + qa.shape, np.float32)
            for i, b in enumerate(("green", "red", "nir08", "nir09")):
                dn = arr[nomes.index(b)].astype(np.float32)
                out[i] = np.where((dn > 0) & ~ruim, dn, np.nan)
            pilha.append(out)
        pilha = np.stack(pilha)
        med, n_obs = _mediana(pilha)
        bandas = [np.where(np.isfinite(med[i]), med[i], NODATA).astype(np.int16) for i in range(4)] + [n_obs]
        escrever(OUT / f"mss30_{int(ano)}.tif", bandas, ["green", "red", "nir08", "nir09", "n_obs"], GRADE30,
                 nodata=NODATA, tags={"ano": str(ano), "datas": ",".join(sorted(sel["data"])), "nivel": "L1 DN"})
        registro.append({"produto": "mss30", "ano": int(ano), "n_cenas": len(sel), "datas": ",".join(sorted(sel["data"])),
                         "sensores": "MSS", "anos_usados": str(ano), "frac_ge1": float((n_obs >= 1).mean())})
        print(f"  MSS {ano}: {len(sel)} cenas", flush=True)


def declividade() -> None:
    dest = OUT / "declividade30.tif"
    if dest.exists():
        return
    with rasterio.open(CENAS / "dem" / "copdem_30m.tif") as s:
        elev = s.read(1)
    escrever(dest, [declividade_graus(elev, 30.0)], ["declividade_graus"], GRADE30, nodata=None,
             tags={"fonte": "Copernicus DEM GLO-30"})


def main(anos: list[int] | None) -> None:
    m = _manifesto()
    registro: list[dict] = []
    declividade()
    anos_l = [a for a in ANOS_LANDSAT if anos is None or a in anos]
    print("Landsat 30 m …")
    for a in anos_l:
        compor_landsat(a, m, registro)
        ndvimax_landsat(a, m, registro)
    print("Sentinel-2 10 m …")
    for a in [a for a in ANOS_S2 if anos is None or a in anos]:
        compor_s2(a, m, registro)
    if anos is None:
        compor_mss(m, registro)
        preencher_tudo(registro)
    df = pd.DataFrame(registro)
    if anos is None:
        df.to_parquet(OUT / "composicoes.parquet", index=False)
    else:  # execução parcial: atualiza as linhas correspondentes
        p = OUT / "composicoes.parquet"
        if p.exists():
            antigo = pd.read_parquet(p)
            chave = antigo["produto"] + antigo["ano"].astype(str)
            df = pd.concat([antigo[~chave.isin(df["produto"] + df["ano"].astype(str))], df])
        df.to_parquet(p, index=False)
    print(df[df["produto"] == "comp30"][["ano", "n_cenas", "n_obs_mediana", "frac_ge1", "frac_ge3"]]
          .to_string(index=False))


if __name__ == "__main__":
    if "--preencher" in sys.argv:  # só o preenchimento, sobre composições já gravadas
        p = OUT / "composicoes.parquet"
        reg = pd.read_parquet(p).to_dict("records")
        preencher_tudo(reg)
        pd.DataFrame(reg).to_parquet(p, index=False)
    else:
        anos = [int(a) for a in sys.argv[1:] if a.isdigit()] or None
        main(anos)
