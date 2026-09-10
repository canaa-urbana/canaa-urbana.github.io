"""
E3b / Fase 3 passo 2 (PLANO.md) — recortes das cenas sobre a janela da sede,
lidos por janela (COG) direto na grade fixa de `lib/grade.py`.

Nada aqui é microdado; tudo é imagem pública. Saída em `data/interim/cenas/`
(fora do git):

  landsat/<item_id>.tif        6 bandas SR + QA_PIXEL, 30 m, estação seca (jun–set)
  landsat_chuva/<item_id>.tif  red, nir08, QA_PIXEL, 30 m, estação chuvosa (jan–abr)
                               — só para o NDVI máximo intersazonal
  s2/<item_id>.tif             blue, green, red, nir, swir16, swir22, SCL, 10 m, jun–set
  s2_chuva/<item_id>.tif       red, nir, SCL, 10 m, jan–abr
  mss/<item_id>.tif            green, red, nir08, nir09, QA_PIXEL, 30 m (marcos 1973/1982)
  validacao/<fonte>/<item_id>.tif   CBERS-2B HRC 2,5 m, CBERS-4 PAN5M 5 m,
                               CBERS-4A WPM (pan 2 m + MS 8 m) — cenas de referência
  dem/copdem_30m.tif           Copernicus DEM GLO-30 (declividade em 22_compor_anual)
  manifesto.parquet            uma linha por arquivo (fonte, ano, data, bandas,
                               fração válida, bytes, tempo)

Seleção por ano (catálogo de `20_imagens_catalogo.py`):
  Landsat seca: nuvem < 40 %, até MAX_LANDSAT cenas por (path,row) por ano,
    ordenadas por tier (T1 antes de T2) e nuvem. A janela cruza as linhas
    WRS 064/065 dos paths 223/224, então uma cena cobre só parte dela — a
    composição mediana de `22_compor_anual.py` junta os pedaços.
  Landsat chuva: nuvem < 70 %, até MAX_LANDSAT cenas por (path,row).
  Sentinel-2 (Element84, sem conta): uma cena por data, até MAX_S2 por ano.
  Cenas de validação: todas as HRC que intersectam a janela (2008–2010); a
    melhor WPM por ano 2020–2026 e a melhor PAN5M por ano 2014–2019.

Uso:
    .venv/bin/python pipeline/21_baixar_cenas.py               # tudo (resumível)
    .venv/bin/python pipeline/21_baixar_cenas.py landsat s2    # só alguns grupos
    .venv/bin/python pipeline/21_baixar_cenas.py --manifesto   # reimprime resumo
Grupos: landsat landsat_chuva s2 s2_chuva mss validacao dem
"""
from __future__ import annotations

import json
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
import planetary_computer as pc
import requests
from rasterio.enums import Resampling
from shapely.geometry import box, shape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.grade import GRADE10, GRADE30, Grade, escrever, ler_para_grade  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
CATALOGO = BASE / "data" / "interim" / "catalogo_cenas.parquet"
OUT = BASE / "data" / "interim" / "cenas"
OUT.mkdir(parents=True, exist_ok=True)
MANIFESTO = OUT / "manifesto.parquet"
FALHAS = OUT / "falhas.jsonl"

BBOX_SEDE = (-49.99, -6.60, -49.75, -6.40)
MAX_LANDSAT = 6  # por (path,row) por ano — 4 combinações cobrem a janela
MAX_S2 = 8  # por ano
THREADS = 6

BANDAS_LANDSAT = ["blue", "green", "red", "nir08", "swir16", "swir22", "qa_pixel"]
BANDAS_LANDSAT_CHUVA = ["red", "nir08", "qa_pixel"]
BANDAS_S2 = ["blue", "green", "red", "nir", "swir16", "swir22", "scl"]
BANDAS_S2_CHUVA = ["red", "nir", "scl"]
BANDAS_MSS = ["green", "red", "nir08", "nir09", "qa_pixel"]

_sessao = requests.Session()


def _item(href_json: str, assinar: bool) -> dict:
    for tent in range(4):
        try:
            r = _sessao.get(href_json, timeout=90)
            r.raise_for_status()
            it = r.json()
            return pc.sign(it) if assinar else it
        except Exception:
            if tent == 3:
                raise
            time.sleep(2 * (tent + 1))
    raise RuntimeError("inalcançável")


def _fracao_valida(a: np.ndarray, nodata=0) -> float:
    return float((a != nodata).mean())


def _registrar(linhas: list[dict]) -> None:
    if not linhas:
        return
    df = pd.DataFrame(linhas)
    if MANIFESTO.exists():
        antigo = pd.read_parquet(MANIFESTO)
        df = pd.concat([antigo[~antigo["arquivo"].isin(df["arquivo"])], df], ignore_index=True)
    df.sort_values(["grupo", "ano", "data"]).to_parquet(MANIFESTO, index=False)


def _falha(grupo: str, item_id: str, exc: Exception) -> None:
    with FALHAS.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"grupo": grupo, "item_id": item_id, "erro": repr(exc)[:300]}) + "\n")


# ----------------------------------------------------------------------------
# seleção de cenas
# ----------------------------------------------------------------------------

def catalogo() -> pd.DataFrame:
    c = pd.read_parquet(CATALOGO)
    c["tier"] = c["item_id"].str.extract(r"_(T[12])$", expand=False).fillna("T9")
    c["data"] = c["datahora"].dt.date.astype(str)
    c["chuva"] = c["mes"].between(1, 4)
    c["tile"] = c["tile"].astype(str).str.replace("MGRS-", "", regex=False)
    return c


def selecionar_landsat(c: pd.DataFrame, chuva: bool) -> pd.DataFrame:
    d = c[(c["fonte"] == "PC/landsat-tm-oli")]
    d = d[d["chuva"]] if chuva else d[d["estacao_seca"]]
    d = d[d["nuvem"] < (70 if chuva else 40)]
    d = d.sort_values(["ano", "wrs_path", "wrs_row", "tier", "nuvem"])
    return d.groupby(["ano", "wrs_path", "wrs_row"]).head(MAX_LANDSAT)


def selecionar_s2(c: pd.DataFrame, chuva: bool) -> pd.DataFrame:
    d = c[c["fonte"] == "E84/sentinel-2"]
    d = d[d["chuva"]] if chuva else d[d["estacao_seca"]]
    d = d[d["nuvem"] < (70 if chuva else 40)]
    # a janela cruza os tiles MGRS 22MFT/22MFU: uma cena por (data, tile) — o E84
    # lista reprocessamentos da mesma órbita — e até MAX_S2 DATAS por ano
    d = d.sort_values(["ano", "data", "tile", "nuvem"]).drop_duplicates(["data", "tile"])
    por_data = d.groupby(["ano", "data"], as_index=False)["nuvem"].mean().sort_values(["ano", "nuvem"])
    datas = por_data.groupby("ano").head(MAX_S2)["data"]
    return d[d["data"].isin(datas)].sort_values(["ano", "data"])


def selecionar_mss(c: pd.DataFrame) -> pd.DataFrame:
    return c[(c["fonte"] == "PC/landsat-mss") & (c["nuvem"] < 30)]


def selecionar_validacao(c: pd.DataFrame) -> pd.DataFrame:
    partes = []
    hrc = c[c["fonte"] == "BDC/cbers2b-hrc"].copy()
    hrc["papel"] = "hrc"
    partes.append(hrc)
    wpm = c[(c["fonte"] == "BDC/cbers4a-wpm") & (c["nuvem"].fillna(0) < 30)].copy()
    wpm = wpm.sort_values(["ano", "nuvem"]).groupby("ano").head(1)
    wpm["papel"] = "wpm"
    partes.append(wpm)
    pan = c[(c["fonte"] == "BDC/cbers4-pan5m") & (c["nuvem"].fillna(0) < 30) & (c["ano"] <= 2019)].copy()
    pan = pan.sort_values(["ano", "nuvem"]).groupby("ano").head(1)
    pan["papel"] = "pan5m"
    partes.append(pan)
    return pd.concat(partes, ignore_index=True)


# ----------------------------------------------------------------------------
# download por cena
# ----------------------------------------------------------------------------

def _baixar_multibanda(row: pd.Series, grupo: str, bandas: list[str], grade: Grade,
                       assinar: bool, resamp_por_banda: dict | None = None) -> dict | None:
    destino = OUT / grupo / f"{row.item_id}.tif"
    if destino.exists():
        return None
    t0 = time.time()
    it = _item(row.href_json, assinar)
    arrays = []
    for b in bandas:
        if b not in it["assets"]:
            raise KeyError(f"asset {b} ausente em {row.item_id}")
        rs = (resamp_por_banda or {}).get(b, Resampling.nearest)
        arrays.append(ler_para_grade(it["assets"][b]["href"], grade, rs))
    ref = arrays[0]
    fv = _fracao_valida(ref)
    if fv < 0.02:  # cena tangencia a janela — não vale gravar
        return {
            "grupo": grupo, "arquivo": str(destino.relative_to(OUT)), "item_id": row.item_id,
            "fonte": row.fonte, "ano": int(row.ano), "data": row.data, "plataforma": row.plataforma,
            "nuvem": float(row.nuvem) if pd.notna(row.nuvem) else None, "bandas": ",".join(bandas),
            "fracao_valida": fv, "bytes": 0, "segundos": time.time() - t0, "gravado": False,
        }
    tags = {
        "item_id": row.item_id, "fonte": row.fonte, "datahora": str(row.datahora),
        "plataforma": str(row.plataforma), "nuvem_cena": str(row.nuvem),
        "wrs_path": str(row.wrs_path), "wrs_row": str(row.wrs_row),
    }
    escrever(destino, arrays, bandas, grade, nodata=0, tags=tags)
    return {
        "grupo": grupo, "arquivo": str(destino.relative_to(OUT)), "item_id": row.item_id,
        "fonte": row.fonte, "ano": int(row.ano), "data": row.data, "plataforma": row.plataforma,
        "nuvem": float(row.nuvem) if pd.notna(row.nuvem) else None, "bandas": ",".join(bandas),
        "fracao_valida": fv, "bytes": destino.stat().st_size, "segundos": time.time() - t0,
        "gravado": True,
    }


def _grade_nativa(bounds_cena, res: float) -> Grade:
    """Grade na resolução nativa da cena de validação, recortada à janela."""
    import math

    xmin, ymin, xmax, ymax = GRADE30.bounds
    bx0, by0, bx1, by1 = bounds_cena
    x0 = max(xmin, math.floor(bx0 / res) * res)
    x1 = min(xmax, math.ceil(bx1 / res) * res)
    y0 = max(ymin, math.floor(by0 / res) * res)
    y1 = min(ymax, math.ceil(by1 / res) * res)
    if x1 <= x0 or y1 <= y0:
        raise ValueError("sem interseção")
    return Grade(res, x0, y1, int(round((x1 - x0) / res)), int(round((y1 - y0) / res)))


def _baixar_validacao(row: pd.Series) -> dict | None:
    import rasterio
    from rasterio.warp import transform_bounds

    grupo = f"validacao/{row.papel}"
    destino = OUT / grupo / f"{row.item_id}.tif"
    if destino.exists():
        return None
    t0 = time.time()
    it = _item(row.href_json, False)
    assets = it["assets"]
    if row.papel == "hrc":
        bandas = {"pan": ("BAND1", 2.5)}
    elif row.papel == "pan5m":
        bandas = {"pan": ("BAND1", 5.0)}
    else:  # wpm: pan 2 m + 4 bandas MS 8 m, tudo gravado a 2 m (MS reamostrado nearest)
        bandas = {"pan": ("BAND0", 2.0), "blue": ("BAND1", 2.0), "green": ("BAND2", 2.0),
                  "red": ("BAND3", 2.0), "nir": ("BAND4", 2.0)}
    primeiro = next(iter(bandas.values()))[0]
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"):
        with rasterio.open(assets[primeiro]["href"]) as src:
            b = transform_bounds(src.crs, "EPSG:31982", *src.bounds)
    res = next(iter(bandas.values()))[1]
    try:
        grade = _grade_nativa(b, res)
    except ValueError:
        return {"grupo": grupo, "arquivo": str(destino.relative_to(OUT)), "item_id": row.item_id,
                "fonte": row.fonte, "ano": int(row.ano), "data": row.data, "plataforma": row.plataforma,
                "nuvem": float(row.nuvem) if pd.notna(row.nuvem) else None, "bandas": "",
                "fracao_valida": 0.0, "bytes": 0, "segundos": time.time() - t0, "gravado": False}
    arrays, nomes = [], []
    for nome, (asset, _) in bandas.items():
        arrays.append(ler_para_grade(assets[asset]["href"], grade, Resampling.nearest))
        nomes.append(nome)
    fv = _fracao_valida(arrays[0])
    if fv < 0.05:
        gravado = False
    else:
        escrever(destino, arrays, nomes, grade, nodata=0,
                 tags={"item_id": row.item_id, "fonte": row.fonte, "datahora": str(row.datahora)})
        gravado = True
    return {"grupo": grupo, "arquivo": str(destino.relative_to(OUT)), "item_id": row.item_id,
            "fonte": row.fonte, "ano": int(row.ano), "data": row.data, "plataforma": row.plataforma,
            "nuvem": float(row.nuvem) if pd.notna(row.nuvem) else None, "bandas": ",".join(nomes),
            "fracao_valida": fv, "bytes": destino.stat().st_size if gravado else 0,
            "segundos": time.time() - t0, "gravado": gravado}


def baixar_dem() -> dict | None:
    destino = OUT / "dem" / "copdem_30m.tif"
    if destino.exists():
        return None
    from pystac_client import Client

    t0 = time.time()
    cl = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)
    itens = list(cl.search(collections=["cop-dem-glo-30"], bbox=list(BBOX_SEDE)).items())
    if not itens:
        raise RuntimeError("COP-DEM sem itens sobre a janela")
    # mosaico simples: máximo (os tiles não se sobrepõem; fora do tile é nodata)
    acc = None
    for it in itens:
        a = ler_para_grade(it.assets["data"].href, GRADE30, Resampling.bilinear, dtype="float32")
        acc = a if acc is None else np.where(np.isfinite(a) & (a != 0), a, acc)
    escrever(destino, [acc], ["elevacao_m"], GRADE30, nodata=None,
             tags={"fonte": "Copernicus DEM GLO-30 (Planetary Computer cop-dem-glo-30)",
                   "itens": ",".join(i.id for i in itens)})
    return {"grupo": "dem", "arquivo": "dem/copdem_30m.tif", "item_id": ",".join(i.id for i in itens),
            "fonte": "PC/cop-dem-glo-30", "ano": 2021, "data": "", "plataforma": "TanDEM-X",
            "nuvem": None, "bandas": "elevacao_m", "fracao_valida": 1.0,
            "bytes": destino.stat().st_size, "segundos": time.time() - t0, "gravado": True}


# ----------------------------------------------------------------------------

def _executar(tarefas, fn, rotulo: str) -> None:
    linhas, n_ok, n_falha = [], 0, 0
    t0 = time.time()
    with ThreadPoolExecutor(THREADS) as ex:
        futs = {ex.submit(fn, row): row for row in tarefas}
        for i, f in enumerate(as_completed(futs), start=1):
            row = futs[f]
            try:
                r = f.result()
                if r is not None:
                    linhas.append(r)
                    n_ok += 1
            except Exception as exc:
                n_falha += 1
                _falha(rotulo, row.item_id, exc)
            if i % 25 == 0 or i == len(futs):
                _registrar(linhas)
                linhas = []
                print(f"  {rotulo}: {i}/{len(futs)} ({n_falha} falhas, {time.time() - t0:,.0f}s)", flush=True)
    _registrar(linhas)


def main(grupos: list[str]) -> None:
    c = catalogo()
    planos = {
        "landsat": (selecionar_landsat(c, False),
                    lambda r: _baixar_multibanda(r, "landsat", BANDAS_LANDSAT, GRADE30, True)),
        "landsat_chuva": (selecionar_landsat(c, True),
                          lambda r: _baixar_multibanda(r, "landsat_chuva", BANDAS_LANDSAT_CHUVA, GRADE30, True)),
        "s2": (selecionar_s2(c, False),
               lambda r: _baixar_multibanda(r, "s2", BANDAS_S2, GRADE10, False)),
        "s2_chuva": (selecionar_s2(c, True),
                     lambda r: _baixar_multibanda(r, "s2_chuva", BANDAS_S2_CHUVA, GRADE10, False)),
        "mss": (selecionar_mss(c),
                lambda r: _baixar_multibanda(r, "mss", BANDAS_MSS, GRADE30, True)),
        "validacao": (selecionar_validacao(c), _baixar_validacao),
    }
    if "dem" in grupos:
        print("dem …")
        try:
            r = baixar_dem()
            _registrar([r] if r else [])
        except Exception as exc:
            _falha("dem", "copdem", exc)
            traceback.print_exc()
    for g in grupos:
        if g not in planos:
            continue
        sel, fn = planos[g]
        print(f"{g}: {len(sel)} cenas selecionadas", flush=True)
        _executar([r for _, r in sel.iterrows()], fn, g)
    reconciliar()
    resumo()


def reconciliar() -> None:
    """Arquivos gravados mas ausentes do manifesto (ex.: execução interrompida
    entre dois registros) entram lidos das tags do próprio GeoTIFF."""
    import rasterio

    m = pd.read_parquet(MANIFESTO) if MANIFESTO.exists() else pd.DataFrame(columns=["arquivo"])
    conhecidos = set(m["arquivo"])
    novos = []
    for tif in OUT.rglob("*.tif"):
        rel = str(tif.relative_to(OUT))
        if rel in conhecidos or tif.name.endswith(".tmp.tif") or rel.startswith("dem/"):
            continue
        with rasterio.open(tif) as src:
            t = src.tags()
            fv = float((src.read(1) != 0).mean())
            bandas = ",".join(d or "" for d in src.descriptions)
        dh = pd.Timestamp(t.get("datahora")) if t.get("datahora") else None
        novos.append({"grupo": str(Path(rel).parent), "arquivo": rel, "item_id": t.get("item_id", tif.stem),
                      "fonte": t.get("fonte"), "ano": dh.year if dh is not None else None,
                      "data": str(dh.date()) if dh is not None else "", "plataforma": t.get("plataforma"),
                      "nuvem": float(t["nuvem_cena"]) if t.get("nuvem_cena") not in (None, "None", "nan") else None,
                      "bandas": bandas, "fracao_valida": fv, "bytes": tif.stat().st_size, "segundos": None,
                      "gravado": True})
    if novos:
        print(f"reconciliação: {len(novos)} arquivos acrescentados ao manifesto")
        _registrar(novos)


def resumo() -> None:
    if not MANIFESTO.exists():
        print("sem manifesto")
        return
    m = pd.read_parquet(MANIFESTO)
    m = m[m["gravado"]]
    g = m.groupby("grupo").agg(arquivos=("arquivo", "count"), de=("ano", "min"), ate=("ano", "max"),
                               mb=("bytes", lambda s: s.sum() / 1e6),
                               fv_media=("fracao_valida", "mean"))
    print(g.round(2).to_string())
    la = m[m["grupo"] == "landsat"].groupby("ano").size()
    print("landsat seca por ano:", la.to_dict())
    if FALHAS.exists():
        print(f"falhas registradas: {sum(1 for _ in FALHAS.open())} (ver {FALHAS})")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--manifesto" in sys.argv:
        reconciliar()
        resumo()
    else:
        main(args or ["dem", "landsat", "s2", "landsat_chuva", "s2_chuva", "mss", "validacao"])
