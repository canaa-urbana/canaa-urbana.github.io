"""
E3b / Fase 3 passo 5 (PLANO.md) — validação da mancha própria.

Quatro subcomandos:

  registrar  Corregistro das cenas de validação com a composição Landsat do ano
             (correlação de fase): o CBERS-2B HRC L2 chega deslocado 0,5–3 km.
             Cenas com residual ≥ 1,5 px ficam fora da validação.

  amostrar   Amostra aleatória estratificada por época (2022 → CBERS-4A WPM 2 m;
             2017 → CBERS-4 PAN5M 5 m; 2009 → CBERS-2B HRC 2,5 m, estação seca),
             estratos definidos pelo mapa classificado:
             urbano (classes 1–2), não urbano a ≤ 300 m do urbano (zona de erro),
             não urbano restante. Grava os pontos em
             data/processed/geo/validacao/pontos_<epoca>.parquet e montagens de
             recortes numerados (400 m × 400 m) em data/interim/validacao/ para
             fotointerpretação. O intérprete grava
             data/processed/geo/validacao/rotulos_<epoca>.json  {"id": "urbano"|"nao_urbano"|"incerto"}.

  avaliar    Matriz de confusão, acurácia global, do usuário e do produtor, e área
             urbana ajustada pelo erro com IC 95 % (Olofsson et al. 2014, estimador
             estratificado com pesos W_h = N_h/N) → validacao_acuracia.{json,csv}.
             Pontos "incerto" saem da matriz e são contados.

  comparar   Série própria × produtos prontos por ano: área e concordância (IoU)
             com MapBiomas 24 (Col. 11), WSF-Evolution (assentado ≤ ano), GHSL
             (fração ≥ 0,2 nas épocas), IBGE AU 2019/2022 e WSF2019
             → comparacao_serie_propria.{parquet,csv}.

Pré-1999 não há referência independente (o PLANO.md já prevê declarar isso);
a comparação com WSF-Evolution 1985–2015 é o que existe.

Uso:
    .venv/bin/python pipeline/24_validar_mancha.py registrar
    .venv/bin/python pipeline/24_validar_mancha.py amostrar
    .venv/bin/python pipeline/24_validar_mancha.py avaliar
    .venv/bin/python pipeline/24_validar_mancha.py comparar
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from PIL import Image, ImageDraw, ImageFont
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from scipy.ndimage import binary_dilation

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import referencias as R  # noqa: E402
from lib.grade import GRADE30, CRS_METRICO  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
CENAS = BASE / "data" / "interim" / "cenas"
MANCHA = BASE / "data" / "processed" / "geo" / "mancha_propria"
GEO = BASE / "data" / "processed" / "geo"
OUT_V = GEO / "validacao"
OUT_M = BASE / "data" / "interim" / "validacao"
for d in (OUT_V, OUT_M):
    d.mkdir(parents=True, exist_ok=True)

SEMENTE = 1502152
# Época 2009 (não 2010): as HRC de fev/2010 são de estação chuvosa e vêm sem
# máscara de nuvem; as de jul/2009 são limpas. O mapa validado é o do ano da imagem.
EPOCAS = {2022: {"papel": "wpm", "anos_ref": [2022, 2021, 2023], "res": 2.0},
          2017: {"papel": "pan5m", "anos_ref": [2017, 2018], "res": 5.0},
          2009: {"papel": "hrc", "anos_ref": [2009, 2008, 2010], "res": 2.5}}
DESLOC = OUT_M / "deslocamentos.json"  # corregistro por cena (registrar)
N_POR_ESTRATO = 50
ESTRATOS = {1: "urbano", 2: "nao_urbano_borda_300m", 3: "nao_urbano_restante"}
CHIP_M = 400  # lado do recorte em metros
CHIP_PX = 240  # lado do recorte em pixels na montagem
POR_LINHA, POR_COLUNA = 5, 4


def _mapa(ano: int) -> np.ndarray:
    with rasterio.open(MANCHA / f"mancha30_{ano}.tif") as s:
        return s.read(1)


def _estratos(ano: int) -> np.ndarray:
    cls = _mapa(ano)
    urb = np.isin(cls, [1, 2])
    r = 10
    yy, xx = np.ogrid[-r:r + 1, -r:r + 1]
    borda = binary_dilation(urb, structure=(xx ** 2 + yy ** 2) <= r ** 2) & ~urb
    e = np.zeros(cls.shape, np.uint8)
    e[urb] = 1
    e[borda] = 2
    e[(e == 0)] = 3
    e[cls == 3] = 0  # mineração fica fora da validação (curva separada)
    return e


def _cenas_ref(epoca: int) -> list[Path]:
    cfg = EPOCAS[epoca]
    m = pd.read_parquet(CENAS / "manifesto.parquet")
    m = m[m["gravado"] & (m["grupo"] == f"validacao/{cfg['papel']}") & m["ano"].isin(cfg["anos_ref"])]
    ordem = {a: i for i, a in enumerate(cfg["anos_ref"])}
    mes = pd.to_datetime(m["data"]).dt.month
    m = m.assign(prio=m["ano"].map(ordem), chuva=~mes.between(5, 10))
    m = m.sort_values(["prio", "chuva", "fracao_valida"], ascending=[True, True, False])
    d = _deslocamentos()
    cenas = [CENAS / a for a in m["arquivo"]]
    # só cenas corregistradas com residual < 1,5 px (ou sem registro estimado por falta de cobertura)
    return [p for p in cenas if p.stem not in d or d[p.stem].get("confiavel", False)]


def _deslocamentos() -> dict:
    return json.loads(DESLOC.read_text("utf-8")) if DESLOC.exists() else {}


def _src_transform(src, p: Path):
    """Transform da cena corrigido pelo deslocamento estimado em `registrar`."""
    d = _deslocamentos().get(p.stem)
    if not d or not d.get("aplicar"):
        return src.transform
    t = src.transform
    return rasterio.Affine(t.a, t.b, t.c + d["dx_m"], t.d, t.e, t.f + d["dy_m"])


def _ler_30m(p: Path, resampling=Resampling.average, corrigir: bool = True) -> np.ndarray:
    with rasterio.open(p) as src:
        kw = {"src_transform": _src_transform(src, p)} if corrigir else {}
        with WarpedVRT(src, crs=CRS_METRICO, transform=GRADE30.transform, width=GRADE30.largura,
                       height=GRADE30.altura, resampling=resampling, **kw) as v:
            return v.read(1).astype(np.float32)


def _cobertura(cenas: list[Path]) -> np.ndarray:
    """Máscara 30 m dos pixels cobertos por alguma cena de referência válida."""
    cob = np.zeros(GRADE30.shape, bool)
    for p in cenas:
        cob |= _ler_30m(p, Resampling.nearest) > 0
    return cob


def registrar() -> None:
    """Corregistro de cada cena de validação com a composição Landsat do mesmo
    ano (média de green/red/nir a 30 m) por correlação de fase (skimage), em
    duas passagens (estimar → aplicar → residual). O CBERS-2B HRC L2 é só
    corrigido por efemérides e chega deslocado 0,5–3 km; o CBERS-4A WPM L4 é
    ortorretificado (≈ 10 m). Deslocamentos < 0,5 pixel não são aplicados.
    Grava data/interim/validacao/deslocamentos.json (dx_m, dy_m, residual_px,
    aplicar) e a tabela em data/processed/geo/validacao/corregistro.csv."""
    from skimage.registration import phase_cross_correlation

    m = pd.read_parquet(CENAS / "manifesto.parquet")
    m = m[m["gravado"] & m["grupo"].str.startswith("validacao/")]
    res, linhas = _deslocamentos(), []
    for _, r in m.iterrows():
        p = CENAS / r["arquivo"]
        ano = int(r["ano"])
        with rasterio.open(BASE / "data" / "interim" / "composicoes" / f"comp30_{ano}.tif") as s:
            L = s.read()[1:4].astype(np.float32).mean(0)
        res[p.stem] = {"dx_m": 0.0, "dy_m": 0.0, "aplicar": False}
        DESLOC.write_text(json.dumps(res, indent=1), "utf-8")
        dx = dy = 0.0
        residual = None
        for passo in range(3):
            h = _ler_30m(p)
            ok = h > 0
            if ok.mean() < 0.05:
                break
            ys, xs = np.nonzero(ok)
            sl = (slice(ys.min() + 5, ys.max() - 5), slice(xs.min() + 5, xs.max() - 5))
            hh, ll = h[sl], L[sl]
            okk = (hh > 0) & np.isfinite(ll)
            hh = np.where(okk, hh, hh[okk].mean())
            ll = np.where(okk, ll, ll[okk].mean())
            hh = (hh - hh.mean()) / (hh.std() + 1e-6)
            ll = (ll - ll.mean()) / (ll.std() + 1e-6)
            shift, _, _ = phase_cross_correlation(ll, hh, upsample_factor=10)
            residual = float(np.hypot(*shift))
            if residual < 0.5:
                break
            dx += float(shift[1]) * 30
            dy -= float(shift[0]) * 30
            res[p.stem] = {"dx_m": dx, "dy_m": dy, "aplicar": True}
            DESLOC.write_text(json.dumps(res, indent=1), "utf-8")
        aplicar = bool(np.hypot(dx, dy) >= 15) and residual is not None and residual < 1.5
        res[p.stem] = {"dx_m": round(dx, 1), "dy_m": round(dy, 1), "residual_px": None if residual is None else round(residual, 2),
                       "aplicar": aplicar, "confiavel": residual is not None and residual < 1.5}
        DESLOC.write_text(json.dumps(res, indent=1), "utf-8")
        linhas.append({"cena": p.stem, "grupo": r["grupo"], "ano": ano, **res[p.stem]})
        print(f"  {p.stem[:40]:40s} dx {dx:8.0f} m  dy {dy:8.0f} m  residual {residual if residual is None else round(residual, 2)} px  aplicar={aplicar}")
    pd.DataFrame(linhas).to_csv(OUT_V / "corregistro.csv", index=False)


def _recorte(p: Path, x: float, y: float, lado_m: float, res: float) -> np.ndarray | None:
    n = int(lado_m / res)
    t = from_origin(x - lado_m / 2, y + lado_m / 2, res, res)
    with rasterio.open(p) as src:
        with WarpedVRT(src, crs=CRS_METRICO, transform=t, width=n, height=n, resampling=Resampling.bilinear,
                       src_transform=_src_transform(src, p)) as v:
            a = v.read().astype(np.float32)
    if (a[0] > 0).mean() < 0.9:
        return None
    return a


def _textura(a: np.ndarray) -> float:
    """Textura relativa do pan (desvio das diferenças horizontais / média):
    nuvem e névoa em cena sem máscara são lisas; o recorte mais texturizado
    entre as cenas do mesmo ano de referência é o mais limpo."""
    pan = a[0]
    return float(np.std(np.diff(pan, axis=1))) / max(float(pan.mean()), 1.0)


def _para_rgb(a: np.ndarray, nomes: list[str]) -> np.ndarray:
    def est(b):
        v = b[b > 0]
        if v.size == 0:
            return np.zeros_like(b, np.uint8)
        lo, hi = np.percentile(v, 1), np.percentile(v, 99)
        return (np.clip((b - lo) / max(hi - lo, 1e-6), 0, 1) * 255).astype(np.uint8)
    if a.shape[0] >= 4 and "red" in nomes:
        pan = a[nomes.index("pan")]
        r, g, b = a[nomes.index("red")], a[nomes.index("green")], a[nomes.index("blue")]
        med = (r + g + b) / 3 + 1e-6
        rgb = [est(r * pan / med), est(g * pan / med), est(b * pan / med)]
        return np.stack(rgb, -1)
    p = est(a[0])
    return np.stack([p, p, p], -1)


def amostrar() -> None:
    rng = np.random.default_rng(SEMENTE)
    fonte = None
    try:
        fonte = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
    except Exception:
        fonte = ImageFont.load_default()
    xs, ys = GRADE30.xy()
    for epoca, cfg in EPOCAS.items():
        cenas = _cenas_ref(epoca)
        if not cenas:
            print(f"{epoca}: sem cenas de referência baixadas")
            continue
        cob = _cobertura(cenas)
        est = _estratos(epoca)
        est[~cob] = 0
        N_h = {h: int((est == h).sum()) for h in ESTRATOS}
        linhas = []
        for h in ESTRATOS:
            idx = np.flatnonzero(est == h)
            if len(idx) == 0:
                continue
            sel = rng.choice(idx, min(N_POR_ESTRATO, len(idx)), replace=False)
            for i in sel:
                lin, col = divmod(int(i), GRADE30.largura)
                linhas.append({"estrato": h, "estrato_nome": ESTRATOS[h], "lin": lin, "col": col,
                               "x": float(xs[col]), "y": float(ys[lin]), "classe_mapa": int(_mapa(epoca)[lin, col])})
        pts = pd.DataFrame(linhas)
        pts = pts.sample(frac=1, random_state=SEMENTE).reset_index(drop=True)  # embaralha para o intérprete
        pts.insert(0, "id", [f"{epoca}_{i:03d}" for i in range(len(pts))])
        pts["N_h"] = pts["estrato"].map(N_h)
        pts["cena_ref"] = ""
        # montagens
        with rasterio.open(cenas[0]) as s:
            nomes = list(s.descriptions)
        chips = []
        anos_cena = {p: int(pd.read_parquet(CENAS / "manifesto.parquet").set_index("arquivo")
                            .loc[str(p.relative_to(CENAS)), "ano"]) for p in cenas}
        for k, r in pts.iterrows():
            chip = None
            for ano_ref in cfg["anos_ref"]:  # melhor textura entre as cenas do ano preferido
                cand = []
                for p in [q for q in cenas if anos_cena[q] == ano_ref]:
                    c = _recorte(p, r["x"], r["y"], CHIP_M, cfg["res"])
                    if c is not None:
                        cand.append((_textura(c), p, c))
                if cand:
                    tx, p, chip = max(cand, key=lambda t: t[0])
                    if tx < 0.02:  # tudo nublado neste ano: tenta o ano seguinte da lista
                        chip = None
                        continue
                    pts.loc[k, "cena_ref"] = p.stem
                    pts.loc[k, "textura"] = tx
                    break
            if chip is None:
                chips.append(None)
                continue
            img = Image.fromarray(_para_rgb(chip, nomes)).resize((CHIP_PX, CHIP_PX), Image.BILINEAR)
            d = ImageDraw.Draw(img)
            c = CHIP_PX / 2
            s = 30 / CHIP_M * CHIP_PX / 2  # meio pixel de 30 m
            d.rectangle([c - s, c - s, c + s, c + s], outline=(255, 255, 0), width=2)
            d.text((6, 4), r["id"], fill=(255, 255, 0), font=fonte)
            chips.append(img)
        pts = pts[[c is not None for c in chips]].reset_index(drop=True)
        chips = [c for c in chips if c is not None]
        por_pagina = POR_LINHA * POR_COLUNA
        for pg in range(0, len(chips), por_pagina):
            folha = Image.new("RGB", (POR_LINHA * CHIP_PX, POR_COLUNA * CHIP_PX), (20, 20, 20))
            for j, img in enumerate(chips[pg:pg + por_pagina]):
                folha.paste(img, ((j % POR_LINHA) * CHIP_PX, (j // POR_LINHA) * CHIP_PX))
            folha.save(OUT_M / f"montagem_{epoca}_{pg // por_pagina + 1:02d}.png")
        pts.to_parquet(OUT_V / f"pontos_{epoca}.parquet", index=False)
        print(f"{epoca}: {len(pts)} pontos ({pts['estrato'].value_counts().sort_index().to_dict()}), "
              f"N_h={N_h}, {len(range(0, len(chips), por_pagina))} montagens, cenas={[p.stem for p in cenas]}")


def _olofsson(pts: pd.DataFrame, px_ha: float = 0.09) -> dict:
    """Estimador estratificado de Olofsson et al. (2014) para 2 classes de mapa
    (urbano / não urbano) com 3 estratos de amostragem; classes de referência:
    urbano / não urbano."""
    pts = pts[pts["ref"].isin(["urbano", "nao_urbano"])].copy()
    pts["mapa"] = np.where(pts["classe_mapa"].isin([1, 2]), "urbano", "nao_urbano")
    N = pts.drop_duplicates("estrato").set_index("estrato")["N_h"]
    W = N / N.sum()
    n_h = pts.groupby("estrato").size()
    # proporção estimada de área em cada célula (mapa i, ref j): p_ij = Σ_h W_h · n_hij / n_h
    celulas = {}
    for i in ("urbano", "nao_urbano"):
        for j in ("urbano", "nao_urbano"):
            p = 0.0
            for h in N.index:
                sub = pts[pts["estrato"] == h]
                p += W[h] * ((sub["mapa"] == i) & (sub["ref"] == j)).sum() / n_h[h]
            celulas[(i, j)] = p
    oa = celulas[("urbano", "urbano")] + celulas[("nao_urbano", "nao_urbano")]
    p_map_u = celulas[("urbano", "urbano")] + celulas[("urbano", "nao_urbano")]
    p_ref_u = celulas[("urbano", "urbano")] + celulas[("nao_urbano", "urbano")]
    ua = celulas[("urbano", "urbano")] / p_map_u if p_map_u else float("nan")
    pa = celulas[("urbano", "urbano")] / p_ref_u if p_ref_u else float("nan")
    # variância da proporção de área da classe de referência "urbano" (eq. 10 de Olofsson 2014,
    # forma estratificada): V = Σ_h W_h² · p_h(1−p_h)/(n_h−1), p_h = fração de ref urbano no estrato h
    var = 0.0
    for h in N.index:
        sub = pts[pts["estrato"] == h]
        ph = (sub["ref"] == "urbano").mean()
        var += W[h] ** 2 * ph * (1 - ph) / max(len(sub) - 1, 1)
    ep = float(np.sqrt(var))
    area_total_ha = float(N.sum() * px_ha)
    var_oa = 0.0
    for h in N.index:
        sub = pts[pts["estrato"] == h]
        ph = (sub["mapa"] == sub["ref"]).mean()
        var_oa += W[h] ** 2 * ph * (1 - ph) / max(len(sub) - 1, 1)
    return {
        "n_pontos": int(len(pts)), "acuracia_global": round(float(oa), 4),
        "acuracia_global_ic95": round(1.96 * float(np.sqrt(var_oa)), 4),
        "usuario_urbano": round(float(ua), 4), "produtor_urbano": round(float(pa), 4),
        "area_mapa_urbano_ha": round(float(p_map_u * area_total_ha), 1),
        "area_ajustada_urbano_ha": round(float(p_ref_u * area_total_ha), 1),
        "area_ajustada_ic95_ha": round(float(1.96 * ep * area_total_ha), 1),
        "area_total_amostrada_ha": round(area_total_ha, 1),
        "matriz": {f"mapa_{i}|ref_{j}": int(((pts["mapa"] == i) & (pts["ref"] == j)).sum())
                   for i in ("urbano", "nao_urbano") for j in ("urbano", "nao_urbano")},
        "por_estrato": {ESTRATOS[h]: {"n": int(n_h[h]), "N_h": int(N[h]), "W_h": round(float(W[h]), 4),
                                      "acertos": int((pts.loc[pts["estrato"] == h, "mapa"] == pts.loc[pts["estrato"] == h, "ref"]).sum())}
                        for h in N.index},
    }


def avaliar() -> None:
    res, linhas = {}, []
    for epoca in EPOCAS:
        pp, rp = OUT_V / f"pontos_{epoca}.parquet", OUT_V / f"rotulos_{epoca}.json"
        if not (pp.exists() and rp.exists()):
            print(f"{epoca}: faltam pontos ou rótulos")
            continue
        pts = pd.read_parquet(pp)
        rot = json.loads(rp.read_text("utf-8"))
        pts["ref"] = pts["id"].map(rot).fillna("sem_rotulo")
        n_inc = int((pts["ref"] == "incerto").sum())
        n_sem = int((pts["ref"] == "sem_rotulo").sum())
        r = _olofsson(pts)
        r.update({"epoca": epoca, "referencia": EPOCAS[epoca]["papel"], "n_incertos": n_inc, "n_sem_rotulo": n_sem})
        res[str(epoca)] = r
        linhas.append({k: v for k, v in r.items() if not isinstance(v, dict)})
        pts.to_parquet(pp, index=False)
        print(f"{epoca}: OA {r['acuracia_global']:.3f} ± {r['acuracia_global_ic95']:.3f}, "
              f"UA {r['usuario_urbano']:.3f}, PA {r['produtor_urbano']:.3f}, "
              f"área mapa {r['area_mapa_urbano_ha']:.0f} ha, ajustada {r['area_ajustada_urbano_ha']:.0f} "
              f"± {r['area_ajustada_ic95_ha']:.0f} ha, incertos {n_inc}")
    (OUT_V / "validacao_acuracia.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), "utf-8")
    pd.DataFrame(linhas).to_csv(OUT_V / "validacao_acuracia.csv", index=False)


def _iou(a: np.ndarray, b: np.ndarray) -> float:
    u = (a | b).sum()
    return float((a & b).sum() / u) if u else float("nan")


def comparar() -> None:
    wsf = R.wsf_evolution()
    au = {2019: np.isin(R.areas_urbanizadas(2019), [1, 2]), 2022: np.isin(R.areas_urbanizadas(2022), [1, 2])}
    w19 = R.wsf2019() >= 0.5
    ghsl_epocas = [1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025, 2030]
    linhas = []
    for p in sorted(MANCHA.glob("mancha30_*.tif")):
        ano = int(p.stem.split("_")[1])
        with rasterio.open(p) as s:
            cls = s.read(1)
        prop = np.isin(cls, [1, 2])
        l = {"ano": ano, "area_propria_ha": float(prop.sum() * 0.09)}
        if 1985 <= ano <= 2025:
            mb = R.mapbiomas(ano) == 24
            l.update({"area_mapbiomas24_ha": float(mb.sum() * 0.09), "iou_mapbiomas24": _iou(prop, mb)})
        if 1985 <= ano <= 2015:
            w = (wsf > 0) & (wsf <= ano)
            l.update({"area_wsf_evo_ha": float(w.sum() * 0.09), "iou_wsf_evo": _iou(prop, w)})
        if ano in ghsl_epocas:
            g = R.ghsl(ano) >= 0.2
            l.update({"area_ghsl_frac20_ha": float(g.sum() * 0.09), "iou_ghsl": _iou(prop, g)})
        if ano in au:
            l.update({"area_ibge_au_ha": float(au[ano].sum() * 0.09), "iou_ibge_au": _iou(prop, au[ano])})
        if ano == 2019:
            l.update({"area_wsf2019_ha": float(w19.sum() * 0.09), "iou_wsf2019": _iou(prop, w19)})
        if 2017 <= ano <= 2025:
            f = R.mapbiomas10_frac24(ano) >= 0.5
            l.update({"area_mapbiomas10m_ha": float(f.sum() * 0.09), "iou_mapbiomas10m": _iou(prop, f)})
            p10 = MANCHA / f"mancha10_{ano}.tif"
            if p10.exists():
                with rasterio.open(p10) as s:
                    c10 = s.read(1)
                l["area_propria_10m_ha"] = float(np.isin(c10, [1, 2]).sum() * 0.01)
        linhas.append(l)
    df = pd.DataFrame(linhas)
    df.to_parquet(GEO / "comparacao_serie_propria.parquet", index=False)
    df.to_csv(GEO / "comparacao_serie_propria.csv", index=False)
    cols = [c for c in df.columns if c.startswith("area_")]
    print(df[["ano"] + cols].round(0).to_string(index=False))
    print(df[[c for c in df.columns if c.startswith("iou_") or c == "ano"]].round(3).dropna(how="all", axis=1).to_string(index=False))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "comparar"
    {"registrar": registrar, "amostrar": amostrar, "avaliar": avaliar, "comparar": comparar}[cmd]()
