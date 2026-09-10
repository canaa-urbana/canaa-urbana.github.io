"""Checagens de consistência do projeto.

Uso:
    .venv/bin/python pipeline/validate.py --smoke   # E0: ambiente, caminhos, libs, APIs
    .venv/bin/python pipeline/validate.py --e3a     # E3a: catálogo STAC, produtos prontos, série anual
    .venv/bin/python pipeline/validate.py --e2      # E2: microdados × SIDRA, tabelas publicadas, gate
    .venv/bin/python pipeline/validate.py --e4      # E4: referências verificadas, matriz, citações
    .venv/bin/python pipeline/validate.py --e3b     # E3b: composições, RF, validação, comparação
    .venv/bin/python pipeline/validate.py --e3c     # E3c: estatísticas da mancha e camadas web
    .venv/bin/python pipeline/validate.py --e5      # E5: tabelas analíticas, tabelas e figuras do artigo
    .venv/bin/python pipeline/validate.py --e6      # E6: artigo (citações, referências, figuras, DOCX/PDF)
    .venv/bin/python pipeline/validate.py --e7      # E7: dados do painel × gate, sigilo em web/, paleta, build
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "pipeline"))


def _ok(msg: str) -> None:
    print(f"  [ok] {msg}")


def _fail(msg: str) -> None:
    print(f"  [FALHA] {msg}")


def smoke() -> int:
    falhas = 0
    print("1. Pacotes Python")
    for m in ["pandas", "pyarrow", "duckdb", "geopandas", "rasterio", "rioxarray", "pystac_client",
              "planetary_computer", "odc.stac", "sklearn", "statsmodels", "matplotlib", "dbfread"]:
        try:
            importlib.import_module(m)
            _ok(m)
        except Exception as e:  # noqa: BLE001
            _fail(f"{m}: {e}")
            falhas += 1

    print("2. Caminhos de dados (symlinks)")
    for p, must in [
        (BASE / "data/raw/microdados_local/microdados_censo_amostra_2010_txt/PA/Amostra_Pessoas_15.txt", True),
        (next(iter(sorted((BASE / "data/raw/microdados_local").glob("microdados_censo_amostra_2022_csv_*"))), BASE / "data/raw/microdados_local/microdados_censo_amostra_2022_csv") / "15/Pessoas_15_controlado.csv", True),
        (BASE / "data/raw/zeitmaschine/Microdados_Censo_Demografico_2000_Amostra/PA/Pes15.txt", False),
        (BASE / "data/raw/zeitmaschine/Microdados_Censo_Demografico_1991_Amostra", False),
    ]:
        if p.exists():
            _ok(str(p.relative_to(BASE)))
        else:
            (_fail if must else print)(f"{'' if must else '  [aviso] '}{p.relative_to(BASE)} ausente"
                                       + ("" if must else " (volume externo desmontado?)"))
            falhas += int(must)

    print("3. Layouts oficiais")
    for f in ["2000_pessoas", "2000_domicilios", "2000_familias", "2010_pessoas", "2010_domicilios"]:
        p = BASE / "data/interim/layouts" / f"{f}.json"
        if p.exists():
            n = len(json.loads(p.read_text()))
            _ok(f"{f}: {n} variáveis")
        else:
            _fail(f"{f}.json ausente")
            falhas += 1

    print("4. Libs reutilizadas")
    for m in ["lib.fwf", "lib.migracao", "lib.seletividade", "lib.deflator", "lib.ardosia_palette",
              "disclosure_rules"]:
        try:
            importlib.import_module(m)
            _ok(m)
        except Exception as e:  # noqa: BLE001
            _fail(f"{m}: {e}")
            falhas += 1
    try:
        from lib.fwf import load_layout
        lay = load_layout(2010, "pessoas")
        nomes = {c["nome"] for c in lay}
        for v in ["V0002", "V0011", "V1006", "V0010", "V0626", "V6264", "V6400", "V6527"]:
            assert v in nomes, v
        _ok("layout 2010 pessoas contém V0002/V0011/V1006/V0010/V0626/V6264/V6400/V6527")
    except Exception as e:  # noqa: BLE001
        _fail(f"layout 2010: {e}")
        falhas += 1

    print("5. APIs externas (GET curto)")
    import requests
    for url in [
        "https://servicodados.ibge.gov.br/api/v1/localidades/municipios/1502152",
        "https://apisidra.ibge.gov.br/values/t/9923/n6/1502152/v/93/p/all/c1/0",
        "https://data.inpe.br/bdc/stac/v1/",
        "https://planetarycomputer.microsoft.com/api/stac/v1/",
    ]:
        try:
            r = requests.get(url, timeout=30)
            (_ok if r.status_code == 200 else _fail)(f"{r.status_code} {url}")
            falhas += int(r.status_code != 200)
        except Exception as e:  # noqa: BLE001
            _fail(f"{url}: {e}")
            falhas += 1

    print("6. Ferramentas externas")
    import shutil
    for t in ["node", "soffice", "pdftotext", "unzip", "git"]:
        (_ok if shutil.which(t) else _fail)(t)
        falhas += int(not shutil.which(t))

    print(f"\nResultado: {'OK' if falhas == 0 else f'{falhas} falha(s)'}")
    return 1 if falhas else 0


def e3a() -> int:
    """E3a — catálogo de cenas, produtos prontos e série anual MapBiomas."""
    import pandas as pd
    import geopandas as gpd

    falhas = 0
    GEO = BASE / "data" / "processed" / "geo"

    print("1. AOI")
    aoi = GEO / "aoi_municipio_31982.parquet"
    if aoi.exists():
        km2 = gpd.read_parquet(aoi).area.iloc[0] / 1e6
        # SIDRA t/4714 (E1): 3.146,821 km². A malha da API v4 é generalizada;
        # tolerância de 1% cobre a generalização sem esconder AOI errada.
        desvio = abs(km2 - 3146.821) / 3146.821 * 100
        (_ok if desvio < 1 else _fail)(f"área da AOI {km2:,.1f} km² × SIDRA 3.146,8 km² (desvio {desvio:.2f}%)")
        falhas += int(desvio >= 1)
    else:
        _fail("aoi_municipio_31982.parquet ausente — rode 20_imagens_catalogo.py")
        falhas += 1

    print("2. Catálogo STAC")
    cat = BASE / "data" / "interim" / "catalogo_cenas.parquet"
    if cat.exists():
        c = pd.read_parquet(cat)
        _ok(f"{len(c):,} cenas, {c['ano'].min()}–{c['ano'].max()}, {c['fonte'].nunique()} fontes")
        vazios = sorted(set(range(1984, 2026)) - set(c["ano"].unique()))
        (_ok if not vazios else _fail)(f"anos 1984–2025 sem cena: {vazios or 'nenhum'}")
        falhas += int(bool(vazios))
        secas = c[(c["nuvem"] < 20) & c["estacao_seca"]].groupby("ano").size()
        magros = sorted(a for a in range(1984, 2026) if secas.get(a, 0) < 3)
        (_ok if not magros else _fail)(
            f"anos com < 3 cenas de estação seca e nuvem < 20%: {magros or 'nenhum'}")
        falhas += int(bool(magros))
    else:
        _fail("catalogo_cenas.parquet ausente")
        falhas += 1

    print("3. Série anual MapBiomas")
    serie = GEO / "mancha_mapbiomas_anual.parquet"
    if serie.exists():
        df = pd.read_parquet(serie)
        sede = df[df["recorte"] == "sede"].sort_values("ano")
        faltando = sorted(set(range(1985, 2026)) - set(sede["ano"]))
        (_ok if not faltando else _fail)(f"anos 1985–2025 na série: {41 - len(faltando)}/41")
        falhas += int(bool(faltando))
        # produto de terceiros: retração de mais de 2% em um ano é sinal de
        # ruído de classificação, não de demolição — reportar, não bloquear
        quedas = sede[sede["area_urbanizada_var_pct"] < -2]
        _ok(f"quedas anuais > 2%: {len(quedas)} {quedas['ano'].tolist()}")
    else:
        _fail("mancha_mapbiomas_anual.parquet ausente — rode 26_estatisticas_mancha.py")
        falhas += 1

    print("4. Produtos prontos e camadas do dashboard")
    man = GEO / "produtos_prontos.parquet"
    if man.exists():
        m = pd.read_parquet(man)
        _ok(f"manifesto com {len(m)} entradas, {m['produto'].nunique()} produtos")
    else:
        _fail("produtos_prontos.parquet ausente")
        falhas += 1
    web = BASE / "web" / "public" / "data" / "geo"
    n_mancha = len(list(web.glob("mancha_mapbiomas_*.json")))
    (_ok if n_mancha == 41 else _fail)(f"camadas anuais do slider: {n_mancha}/41")
    falhas += int(n_mancha != 41)
    leg = BASE / "web" / "src" / "legend" / "mapbiomas.json"
    if leg.exists():
        classes = json.loads(leg.read_text(encoding="utf-8"))["classes"]
        por_id = {c["class_id"]: c for c in classes}
        ok = 24 in por_id and "rban" in por_id[24]["classe_pt"] and por_id[24]["hex"].startswith("#")
        (_ok if ok else _fail)(f"legenda MapBiomas: {len(classes)} classes, 24 = {por_id.get(24, {}).get('classe_pt')}")
        falhas += int(not ok)
    else:
        _fail("web/src/legend/mapbiomas.json ausente")
        falhas += 1

    print(f"\nResultado: {'OK' if falhas == 0 else f'{falhas} falha(s)'}")
    return 1 if falhas else 0


def e2() -> int:
    """E2 — microdados: parquets harmonizados, população expandida × SIDRA por situação,
    domicílios × universo por setor, tabelas publicadas + gate."""
    import subprocess

    import pandas as pd

    falhas = 0
    INTERIM = BASE / "data/interim/microdados"
    IBGE = BASE / "data/processed/ibge"

    print("1. Parquets harmonizados (data/interim/microdados)")
    for censo in (1991, 2000, 2010, 2022):
        for nome in ("pessoas", "domicilios"):
            f = INTERIM / f"{nome}_{censo}.parquet"
            if f.exists():
                _ok(f"{f.name}")
            else:
                _fail(f"{f.name} ausente — rode 12_microdados.py")
                falhas += 1
    if falhas:
        return falhas

    print("2. População expandida × SIDRA (Canaã; Parauapebas em 1991)")
    t202 = pd.read_parquet(IBGE / "t202_pop_distrito.parquet")
    t9923 = pd.read_parquet(IBGE / "t9923_situacao_2022.parquet")
    oficial = {}
    for ano in ("2000", "2010"):
        sub = t202[(t202["Ano_codigo"] == ano) & (t202["Sexo_codigo"] == "0")]
        oficial[int(ano)] = {r["Situação do domicílio"].lower(): r["valor"] for _, r in sub.iterrows()}
    oficial[2022] = {r["Situação do domicílio"].lower(): r["valor"] for _, r in t9923.iterrows()}
    try:
        import requests
        r = requests.get("https://apisidra.ibge.gov.br/values/t/200/n6/1505536/v/93/p/1991/c1/0/c2/0/c58/0", timeout=30)
        v = [x for x in r.json()[1:] if x.get("D3C") == "1991"]
        oficial[1991] = {"total": float(v[0]["V"])} if v else {}
    except Exception as e:  # noqa: BLE001
        print(f"  [aviso] SIDRA t/200 Parauapebas 1991 indisponível ({e})")
        oficial[1991] = {}
    for censo, mun in ((1991, "1505536"), (2000, "1502152"), (2010, "1502152"), (2022, "1502152")):
        p = pd.read_parquet(INTERIM / f"pessoas_{censo}.parquet", columns=["mun", "situacao", "peso"])
        p = p[p["mun"] == mun]
        est = {"total": p["peso"].sum(), "urbana": p.loc[p["situacao"] == "urbana", "peso"].sum(),
               "rural": p.loc[p["situacao"] == "rural", "peso"].sum()}
        for sit, ofc in oficial.get(censo, {}).items():
            if sit not in est or ofc is None or ofc != ofc:
                continue
            desvio = 100 * (est[sit] - ofc) / ofc
            # a amostra harmonizada exclui domicílios coletivos/improvisados: tolerância 3 %
            (_ok if abs(desvio) <= 3 else _fail)(f"{censo} {sit}: amostra {est[sit]:,.0f} × SIDRA {ofc:,.0f} (desvio {desvio:+.2f}%)")
            falhas += int(abs(desvio) > 3)

    print("3. Domicílios particulares permanentes × universo (setores)")
    for censo, f, col in ((2010, "setores_2010_indicadores.parquet", None), (2022, "setores_2022_indicadores.parquet", None)):
        s = pd.read_parquet(BASE / "data/processed/setores" / f)
        pref = ["domicilios_particulares_ocupados", "domicilios_particulares_permanentes"]
        cand = [c for c in pref if c in s.columns] or [c for c in s.columns if "domic" in c.lower()]
        if not cand:
            print(f"  [aviso] {f}: sem coluna de domicílios ({list(s.columns)[:8]}...)")
            continue
        ofc = float(pd.to_numeric(s[cand[0]], errors="coerce").sum())
        d = pd.read_parquet(INTERIM / f"domicilios_{censo}.parquet", columns=["mun", "peso"])
        est = d.loc[d["mun"] == "1502152", "peso"].sum()
        desvio = 100 * (est - ofc) / ofc
        (_ok if abs(desvio) <= 5 else _fail)(f"{censo}: amostra {est:,.0f} × universo ({cand[0]}) {ofc:,.0f} (desvio {desvio:+.2f}%)")
        falhas += int(abs(desvio) > 5)

    print("4. Tabelas publicadas e gate")
    est_f = BASE / "data/processed/microdados/estimativas.parquet"
    if not est_f.exists():
        _fail("estimativas.parquet ausente — rode 13_migracao_perfil.py")
        return falhas + 1
    e = pd.read_parquet(est_f)
    _ok(f"{len(e):,} linhas; censos {sorted(e['censo'].unique())}; geografias {sorted(e['geografia'].unique())}")
    cls = e["classe_precisao"].value_counts(normalize=True).mul(100).round(1).to_dict()
    _ok(f"classes de precisão (% das estimativas): {cls}")
    for censo, g in e.groupby("censo"):
        cv_med = g.loc[g["estatistica"] == "proporcao", "cv"].median()
        _ok(f"{censo}: CV mediano das proporções {cv_med:.1f} %; {(g['classe_precisao'] == 'baixa').mean() * 100:.1f} % em classe baixa")
    r = subprocess.run([sys.executable, str(BASE / "pipeline/verify_gate.py")], capture_output=True, text=True)
    (_ok if r.returncode == 0 else _fail)(f"verify_gate.py: {'aprovado' if r.returncode == 0 else 'REPROVADO'}")
    falhas += int(r.returncode != 0)
    if r.returncode:
        print(r.stdout[-2000:])

    print(f"\nResultado E2: {'OK' if falhas == 0 else f'{falhas} falha(s)'}")
    return 1 if falhas else 0


def e4() -> int:
    """E4: toda referência tem verificado_em e campos mínimos; slugs únicos; BibTeX e matriz
    coerentes; toda citação `slug` da síntese existe na base."""
    import re

    falhas = 0
    print("=== E4: bibliografia ===")
    refs = json.loads((BASE / "artigo/bibliografia/referencias.json").read_text())["referencias"]
    slugs = [r["slug"] for r in refs]
    ok = len(slugs) == len(set(slugs))
    (_ok if ok else _fail)(f"{len(refs)} referências; slugs únicos: {ok}")
    falhas += int(not ok)
    obrig = ("slug", "tipo", "autores", "ano", "titulo", "verificado_em", "abnt", "camada", "eixos")
    sem = [r["slug"] for r in refs if any(not r.get(k) for k in obrig)]
    (_ok if not sem else _fail)(f"campos obrigatórios ({', '.join(obrig)}) — faltando em {sem[:5]}")
    falhas += int(bool(sem))
    sem_url = [r["slug"] for r in refs if not re.match(r"https?://", r["verificado_em"])]
    (_ok if not sem_url else _fail)(f"verificado_em começa por URL em todas — exceções: {sem_url[:5]}")
    falhas += int(bool(sem_url))
    bib = (BASE / "artigo/bibliografia/referencias.bib").read_text()
    n_bib = len(re.findall(r"^@\w+\{", bib, flags=re.M))
    (_ok if n_bib == len(refs) else _fail)(f"referencias.bib: {n_bib} entradas")
    falhas += int(n_bib != len(refs))
    doc = (BASE / "docs/revisao_bibliografica.md").read_text()
    sintese, _, matriz = doc.partition("<!-- MATRIZ:INICIO -->")
    cit = set(re.findall(r"`([a-z][a-z0-9-]+\d{4}[a-z0-9]*)`", sintese))
    faltam = sorted(c for c in cit if c not in set(slugs))
    (_ok if not faltam else _fail)(f"síntese cita {len(cit)} slugs; inexistentes: {faltam}")
    falhas += int(bool(faltam))
    na_matriz = set(re.findall(r"`([a-z][a-z0-9-]+\d{4}[a-z0-9]*)`", matriz))
    fora = sorted(set(slugs) - na_matriz)
    (_ok if not fora else _fail)(f"matriz cobre {len(na_matriz)} referências; fora da matriz: {fora[:5]}")
    falhas += int(bool(fora))
    print(f"\nResultado E4: {'OK' if falhas == 0 else f'{falhas} falha(s)'}")
    return 1 if falhas else 0


def e3b() -> int:
    """E3b — composições anuais, classificação própria, validação e comparação."""
    import pandas as pd

    falhas = 0
    GEO = BASE / "data" / "processed" / "geo"
    COMP = BASE / "data" / "interim" / "composicoes"

    print("1. Composições anuais")
    reg = COMP / "composicoes.parquet"
    if reg.exists():
        c = pd.read_parquet(reg)
        c30 = c[c["produto"] == "comp30"]
        faltando = sorted(set(range(1984, 2027)) - set(c30["ano"]))
        (_ok if not faltando else _fail)(f"comp30 1984–2026: {len(c30)}/43 (faltam {faltando or 'nenhum'})")
        falhas += int(bool(faltando))
        # 1984 é o 1º ano da série TM (97,2% observado, 2,8% preenchido com 1985): tolerância 95%
        ruins = c30[c30["frac_ge1"] < 0.95]
        (_ok if ruins.empty else _fail)(f"anos com < 95% dos pixels observados antes do preenchimento: {ruins['ano'].tolist() or 'nenhum'}")
        falhas += int(not ruins.empty)
        if "frac_preenchida" in c30:
            _ok(f"fração preenchida com anos vizinhos: máx {c30['frac_preenchida'].max():.3%} ({int(c30.loc[c30['frac_preenchida'].idxmax(), 'ano'])})")
        c10 = c[c["produto"] == "comp10"]
        (_ok if len(c10) == 10 else _fail)(f"comp10 Sentinel-2 2017–2026: {len(c10)}/10")
        falhas += int(len(c10) != 10)
    else:
        _fail("composicoes.parquet ausente — rode 22_compor_anual.py")
        falhas += 1

    print("2. Modelos e classificação")
    mj = GEO / "modelos_rf.json"
    if mj.exists():
        d = json.loads(mj.read_text("utf-8"))
        for era, v in d.items():
            cv = v["cv_blocos_3km"]
            ok = cv["oa"] >= 0.85 and cv["f1_urbano"] >= 0.75
            (_ok if ok else _fail)(f"{era}: OOB {v['oob']:.3f}, CV-blocos OA {cv['oa']:.3f} F1 {cv['f1_urbano']:.3f} (n={v['n_amostras']:,})")
            falhas += int(not ok)
    else:
        _fail("modelos_rf.json ausente — rode 23_classificar_mancha.py")
        falhas += 1
    serie = GEO / "mancha_propria_anual.parquet"
    if serie.exists():
        t = pd.read_parquet(serie)
        t30 = t[t["serie"] == "landsat_30m"].sort_values("ano")
        faltando = sorted(set(range(1984, 2027)) - set(t30["ano"]))
        (_ok if not faltando else _fail)(f"série própria 30 m: {len(t30)}/43 anos")
        falhas += int(bool(faltando))
        # a não retração vale para o núcleo selado (urbano em 2 anos consecutivos); pixels de um
        # ano só (maioria temporal) podem sair, e um componente pode migrar sede ↔ outros núcleos.
        # Falha só se o urbano total (sede + outros) cair mais de 5% e mais de 10 ha num ano.
        tot = t30["area_sede_ha"] + t30["area_outros_nucleos_ha"]
        d = tot.diff()
        quedas = t30.loc[(d < -10) & (d < -0.05 * tot.shift()), "ano"].tolist()
        pequenas = t30.loc[(d < -0.5), "ano"].tolist()
        (_ok if not quedas else _fail)(f"retrações do urbano total > 5% e > 10 ha: {quedas or 'nenhuma'} "
                                        f"(retrações pequenas de pixels não selados: {pequenas or 'nenhuma'})")
        falhas += int(bool(quedas))
        rasters = len(list((GEO / "mancha_propria").glob("mancha30_*.tif")))
        vetores = len(list((GEO / "mancha_propria").glob("mancha30_*.parquet")))
        (_ok if rasters == 43 and vetores == 43 else _fail)(f"rasters/vetores 30 m por ano: {rasters}/{vetores}")
        falhas += int(not (rasters == 43 and vetores == 43))
        sede22 = float(t30.loc[t30["ano"] == 2022, "area_sede_ha"].iloc[0])
        _ok(f"sede 2022: {sede22:,.0f} ha (IBGE AU 2022 área urbanizada: 2.139 ha; comparação em comparacao_serie_propria)")
    else:
        _fail("mancha_propria_anual.parquet ausente")
        falhas += 1
    masc = GEO / "mascara_mineracao_30m.json"
    if masc.exists():
        m = json.loads(masc.read_text("utf-8"))
        _ok(f"máscara de mineração: {m['area_ha']:,.0f} ha ({m['origem']})")
    else:
        _fail("mascara_mineracao_30m.json ausente")
        falhas += 1

    print("3. Validação e comparação")
    va = GEO / "validacao" / "validacao_acuracia.json"
    if va.exists():
        v = json.loads(va.read_text("utf-8"))
        for ep, r in v.items():
            ok = r["acuracia_global"] >= 0.85
            (_ok if ok else _fail)(f"{ep} ({r['referencia']}): OA {r['acuracia_global']:.3f} ± {r['acuracia_global_ic95']:.3f}, "
                                   f"UA {r['usuario_urbano']:.3f} PA {r['produtor_urbano']:.3f}, n={r['n_pontos']}, incertos {r['n_incertos']}")
            falhas += int(not ok)
    else:
        _fail("validacao_acuracia.json ausente — rode 24_validar_mancha.py amostrar/avaliar")
        falhas += 1
    cp = GEO / "comparacao_serie_propria.parquet"
    if cp.exists():
        c = pd.read_parquet(cp)
        for ano in (2019, 2022):
            r = c[c["ano"] == ano]
            if not r.empty and "iou_ibge_au" in r:
                iou = float(r["iou_ibge_au"].iloc[0])
                # a AU do IBGE exclui a franja pouco densa e os equipamentos; a série própria tem
                # ~15% de comissão na franja (validação independente). IoU < 0,5 sinalizaria erro grosseiro.
                (_ok if iou >= 0.5 else _fail)(f"IoU própria × IBGE AU {ano}: {iou:.3f} "
                                              f"(própria {float(r['area_propria_ha'].iloc[0]):,.0f} ha × AU {float(r['area_ibge_au_ha'].iloc[0]):,.0f} ha)")
                falhas += int(iou < 0.5)
        w = c.dropna(subset=["iou_wsf_evo"]) if "iou_wsf_evo" in c else pd.DataFrame()
        if not w.empty:
            _ok(f"IoU × WSF-Evolution 1985–2015: mediana {w['iou_wsf_evo'].median():.3f}, mín {w['iou_wsf_evo'].min():.3f} ({int(w.loc[w['iou_wsf_evo'].idxmin(), 'ano'])})")
        if "area_mapbiomas24_ha" in c:
            mb = c.dropna(subset=["area_mapbiomas24_ha"])
            razao = (mb["area_mapbiomas24_ha"] / mb["area_propria_ha"]).median()
            _ok(f"razão MapBiomas 24 / própria (mediana 1985–2025): {razao:.2f} — viés reportado, não erro")
    else:
        _fail("comparacao_serie_propria.parquet ausente — rode 24_validar_mancha.py comparar")
        falhas += 1

    print(f"\nResultado: {'OK' if falhas == 0 else f'{falhas} falha(s)'}")
    return 1 if falhas else 0


def e3c() -> int:
    """E3c — estatísticas da mancha própria e camadas do dashboard."""
    import re

    import pandas as pd

    falhas = 0
    GEO = BASE / "data" / "processed" / "geo"
    WEB = BASE / "web" / "public" / "data"

    def chk(ok: bool, msg: str) -> None:
        nonlocal falhas
        (_ok if ok else _fail)(msg)
        falhas += int(not ok)

    print("1. Série anual")
    p = GEO / "estatisticas_mancha.parquet"
    if not p.exists():
        _fail("estatisticas_mancha.parquet ausente — rode 26_estatisticas_mancha.py propria")
        return 1
    a = pd.read_parquet(p).sort_values("ano")
    chk(a["ano"].tolist() == list(range(1984, 2027)), f"anos 1984–2026: {len(a)}/43")
    tot = a["area_urbana_total_ha"]
    quedas = a.loc[(tot.diff() < -10) & (tot.diff() < -0.05 * tot.shift()), "ano"].tolist()
    chk(not quedas, f"urbano total sem retração > 5% e > 10 ha: {quedas or 'nenhuma'}")
    chk(a["fator_ajuste"].between(0.7, 1.0).all(),
        f"fator de ajuste em [0,7; 1,0]: {a['fator_ajuste'].min():.3f}–{a['fator_ajuste'].max():.3f}")
    v = a[a["ajuste_origem"] == "validado"]["ano"].tolist()
    chk(v == [2009, 2017, 2022], f"épocas validadas na série: {v}")
    chk(a["area_sede_ajustada_ic95_ha"].gt(0).all(), "IC 95% da área ajustada presente em todos os anos")
    r22 = a[a["ano"] == 2022].iloc[0]
    au22 = 2139.3  # IBGE AU 2022, Tipo "Área urbanizada" (docs/qa/E3a.md, E3b.md)
    _ok(f"sede 2022: mapeada {r22['area_sede_ha']:,.0f} ha ({(r22['area_sede_ha'] / au22 - 1) * 100:+.0f}% × AU 2022), "
        f"ajustada {r22['area_sede_ajustada_ha']:,.0f} ± {r22['area_sede_ajustada_ic95_ha']:,.0f} ha "
        f"({(r22['area_sede_ajustada_ha'] / au22 - 1) * 100:+.0f}%) — desvio relatado")
    mb = a.dropna(subset=["mapbiomas24_janela_ha"])
    corr = mb["area_urbana_total_ha"].corr(mb["mapbiomas24_janela_ha"])
    razao = (mb["mapbiomas24_janela_ha"] / mb["area_urbana_total_ha"]).median()
    _ok(f"MapBiomas 24 × própria 1985–2025: correlação {corr:.2f}, razão mediana {razao:.2f} (viés relatado)")

    print("2. Censos, períodos e direção")
    c = pd.read_parquet(GEO / "estatisticas_mancha_censos.parquet").set_index("ano")
    for ano in (2010, 2022):
        fr = c.loc[ano, "pop_sede"] / c.loc[ano, "pop_urbana_sidra"]
        chk(0.95 <= fr <= 1.0, f"{ano}: população da sede pelos setores = {fr:.1%} da urbana SIDRA")
    chk(c["densidade_ajustada_hab_ha"].between(5, 100).all(),
        "densidade ajustada da sede em 5–100 hab/ha: " +
        ", ".join(f"{i} {x:.1f}" for i, x in c["densidade_ajustada_hab_ha"].items()))
    per = pd.read_parquet(GEO / "estatisticas_mancha_periodos.parquet")
    ods = per.dropna(subset=["ods_11_3_1_razao"])
    chk(len(ods) == 2, "ODS 11.3.1 nos dois intervalos censitários: " +
        ", ".join(f"{r.periodo} {r.ods_11_3_1_razao:.2f}" for r in ods.itertuples()))
    d = pd.read_parquet(GEO / "expansao_direcao.parquet")
    somas = d.groupby("periodo")["participacao_pct"].sum()
    chk(((somas - 100).abs() < 0.5).all(), f"octantes somam 100% em cada período ({len(somas)} períodos)")
    sm = pd.read_parquet(BASE / "data" / "processed" / "setores" / "setores_mancha.parquet")
    chk(set(sm["ano"]) == {2010, 2022}, f"setores × mancha: {len(sm)} setores em 2010 e 2022")

    print("3. Camadas web")
    man = json.loads((WEB / "geo" / "camadas.json").read_text("utf-8"))
    faltando = []
    for cam in man["camadas"]:
        for ano in cam.get("anos", [None]):
            f = WEB / (cam["arquivo"].format(ano=ano) if ano is not None else cam["arquivo"])
            if not f.exists():
                faltando.append(str(f.relative_to(WEB)))
    chk(not faltando, f"camadas.json: {len(man['camadas'])} camadas, arquivos ausentes: {faltando[:5] or 'nenhum'}")
    n30 = len(list((WEB / "geo" / "mancha").glob("mancha_propria_*.json")))
    n10 = len(list((WEB / "geo" / "mancha").glob("mancha_propria10_*.json")))
    chk(n30 == 43 and n10 == 10, f"manchas por ano: 30 m {n30}/43, 10 m {n10}/10")
    img = WEB / "geo" / "img"
    cont = {k: len(list(img.glob(f"{k}_*.webp"))) for k in ("landsat", "s2", "mss")}
    chk(cont == {"landsat": 86, "s2": 10, "mss": 2}, f"imagens WebP: {cont}")
    w, s_, e, n = -49.99, -6.60, -49.75, -6.40
    fora = []
    for f in sorted((WEB / "geo" / "mancha").glob("*.json")):
        gj = json.loads(f.read_text("utf-8"))
        xs = [pt[0] for ft in gj["features"] for pt in _pontos(ft["geometry"])]
        ys = [pt[1] for ft in gj["features"] for pt in _pontos(ft["geometry"])]
        if xs and not (w - 0.01 <= min(xs) and max(xs) <= e + 0.01 and s_ - 0.01 <= min(ys) and max(ys) <= n + 0.01):
            fora.append(f.name)
    chk(not fora, f"vetores da mancha dentro da janela da sede em 4326: {fora or 'todos'}")
    for cam in man["camadas"]:
        if cam["tipo"] == "image":
            cx = [p[0] for p in cam["coordenadas"]]
            cy = [p[1] for p in cam["coordenadas"]]
            ok = abs(min(cx) - w) < 0.01 and abs(max(cx) - e) < 0.01 and abs(min(cy) - s_) < 0.01 and abs(max(cy) - n) < 0.01
            chk(ok, f"{cam['id']}: cantos da imagem na janela ({min(cx):.3f}, {min(cy):.3f}, {max(cx):.3f}, {max(cy):.3f})")
    maior_json = max((f.stat().st_size for f in (WEB / "geo" / "mancha").glob("mancha_propria_*.json")))
    maior_img = max(f.stat().st_size for f in img.glob("*.webp"))
    total = sum(f.stat().st_size for f in (WEB / "geo").rglob("*") if f.is_file())
    chk(maior_json < 300e3 and maior_img < 2e6 and total < 60e6,
        f"orçamento: maior mancha 30 m {maior_json / 1e3:.0f} KB (< 300), maior imagem {maior_img / 1e6:.2f} MB (< 2), "
        f"total geo {total / 1e6:.1f} MB (< 60)")
    # toda cor do manifesto vem de uma fonte declarada (Ardósia, MapBiomas, .qml IBGE)
    css = (BASE / "web" / "src" / "styles" / "ardosia.css").read_text("utf-8")
    fontes = {h.lower() for h in re.findall(r"#[0-9A-Fa-f]{6}", css)}
    fontes |= {c["hex"].lower() for c in json.loads((BASE / "web" / "src" / "legend" / "mapbiomas.json").read_text("utf-8"))["classes"]}
    qml = (BASE / "web" / "src" / "legend" / "ibge_au_2022_densidade_tipo.qml").read_text("utf-8")
    fontes |= {"#{:02x}{:02x}{:02x}".format(*map(int, m)) for m in re.findall(r"(\d{1,3}),(\d{1,3}),(\d{1,3}),\d{1,3}", qml)}
    from lib.legendas import cores_oficiais
    fontes |= cores_oficiais()  # inclui a rampa de vermelhos derivada da classe 24
    cores = set(re.findall(r"#[0-9a-fA-F]{6}", json.dumps(man)))
    alheias = sorted(h for h in cores if h.lower() not in fontes)
    chk(not alheias, f"cores do manifesto com fonte declarada: {len(cores)} cores, sem fonte: {alheias or 'nenhuma'}")
    est = json.loads((WEB / "estatisticas_mancha.json").read_text("utf-8"))
    s22 = next(r for r in est["serie"] if r["ano"] == 2022)
    chk(abs(s22["area_sede_ha"] - r22["area_sede_ha"]) < 0.01 and len(est["serie"]) == 43,
        f"estatisticas_mancha.json confere com o parquet (sede 2022 = {s22['area_sede_ha']:,.2f} ha)")

    print(f"\nResultado: {'OK' if falhas == 0 else f'{falhas} falha(s)'}")
    return 1 if falhas else 0


def e5() -> int:
    """E5 — análise e figuras do artigo: tabelas analíticas, tabelas markdown, figuras Ardósia e índice."""
    import re

    import pandas as pd

    falhas = 0
    AN = BASE / "data" / "processed" / "analise"
    TAB = BASE / "artigo" / "tabelas"
    FIG = BASE / "artigo" / "figuras"

    def chk(ok: bool, msg: str) -> None:
        nonlocal falhas
        (_ok if ok else _fail)(msg)
        falhas += int(not ok)

    print("=== E5: análise e figuras ===")
    esperados = ["serie_populacao", "populacao_taxas", "mancha_populacao_anual", "elasticidade_area_populacao", "mancha_cfem_correlacao",
                 "mancha_cfem_periodos", "coortes_chegada", "coortes_chegada_anual", "perfil_migrantes", "perfil_por_periodo_chegada",
                 "insercao_ocupacional", "setor_cruzamentos", "condicoes_domiciliares", "setores_sede_indicadores", "desigualdade_intraurbana",
                 "comparacao_geografias", "dif_em_dif_descritiva", "painel_amc_grupos", "baseline_1991", "economia_anual",
                 "cadeia_mineral_migrantes", "cadeia_mineral_base_migrantes", "cadeia_mineral_por_origem_coorte", "cadeia_mineral_perfil_extrativa"]
    faltam = [n for n in esperados if not (AN / f"{n}.parquet").exists() or not (AN / f"{n}.csv").exists()]
    chk(not faltam, f"{len(esperados)} tabelas analíticas (parquet + csv) — faltando: {faltam}")
    if faltam:
        return 1
    # 1. série populacional coerente com o SIDRA (E1)
    s = pd.read_parquet(AN / "serie_populacao.parquet")
    mun = s[(s.recorte == "município") & (s.tipo_fonte == "oficial_censo")].set_index("ano").valor
    chk(mun.get(2000) == 10922 and mun.get(2010) == 26716 and mun.get(2022) == 77079, "âncoras censitárias 2000/2010/2022 = SIDRA")
    chk(set(s.tipo_fonte) >= {"oficial_censo", "oficial_contagem", "estimativa_ibge", "citacao_terceiro", "estimativa_propria"},
        "série populacional rotulada por tipo de fonte (oficial / estimativa IBGE / citação / estimativa própria)")
    ep = s[s.tipo_fonte == "estimativa_propria"]
    chk(ep.valor.isna().all() and ep.valor_min.notna().all() and ep.valor_max.notna().all(), "estimativas próprias só como faixa (min–max), nunca valor pontual")
    # 2. elasticidade e densidade batem com E3c
    el = pd.read_parquet(AN / "elasticidade_area_populacao.parquet")
    per = pd.read_parquet(BASE / "data/processed/geo/estatisticas_mancha_periodos.parquet").set_index("periodo")
    e1 = el[(el.periodo == "2000–2010") & (el.area == "mapeada")].elasticidade_area_pop.iloc[0]
    chk(abs(e1 - per.loc["2000-2010", "ods_11_3_1_razao"]) < 0.05,
        f"elasticidade 2000–2010 (mapeada) {e1:.2f} ≈ razão ODS 11.3.1 de E3c {per.loc['2000-2010', 'ods_11_3_1_razao']:.2f}")
    chk(el.elasticidade_area_pop.between(0.3, 3).all(), "elasticidades em [0,3; 3]")
    # 3. estimativas amostrais: nenhuma contagem exata (todas múltiplas de 10), CV/classe presentes
    for nome in ("coortes_chegada", "insercao_ocupacional", "condicoes_domiciliares"):
        d = pd.read_parquet(AN / f"{nome}.parquet")
        cont = d[d.get("estatistica", pd.Series("proporcao", index=d.index)) == "contagem"].valor if "estatistica" in d else pd.Series([], dtype=float)
        chk((cont % 10 == 0).all(), f"{nome}: contagens em múltiplos de 10 ({len(cont)} valores)")
        chk(d.classe.notna().all() and d.cv.notna().all(), f"{nome}: CV e classe de precisão em todas as {len(d)} linhas")
    cad = pd.read_parquet(AN / "cadeia_mineral_migrantes.parquet")
    chk((cad.ocupados_elo_arred.dropna() % 10 == 0).all(), "cadeia mineral: totais por elo arredondados a 10")
    chk(cad.ep_razao.notna().sum() > 0 and (cad.razao_seletividade.dropna() > 0).all(), "cadeia mineral: razões de seletividade com erro-padrão")
    pf = pd.read_parquet(AN / "perfil_migrantes.parquet")
    ok = pf.dropna(subset=["razao_seletividade"])
    chk((ok.ep_razao > 0).all(), f"perfil_migrantes: EP da razão > 0 em {len(ok)} razões")
    # 4. desigualdade intraurbana: setores da sede = E3c
    st = pd.read_parquet(AN / "setores_sede_indicadores.parquet")
    sm = pd.read_parquet(BASE / "data/processed/setores/setores_mancha.parquet")
    for ano in (2010, 2022):
        n_e3c = int(((sm.ano == ano) & (sm.pertence == "sede")).sum())
        chk(int((st.ano == ano).sum()) == n_e3c, f"setores da sede {ano}: {int((st.ano == ano).sum())} = {n_e3c} (E3c)")
    chk(st.ano_urbanizacao_mediano.between(1984, 2026).all(), "ano de urbanização mediano por setor em 1984–2026")
    # 5. painel regional: Canaã e Parauapebas isolados, grupos com ≥ 5 municípios, sem n amostral
    pg = pd.read_parquet(AN / "painel_amc_grupos.parquet")
    chk("n_amostral" not in pg.columns, "painel AMC sem contagens amostrais")
    grp = pg[pg.censo == 2022].set_index("grupo").n_municipios_amc
    chk((grp.drop(["Canaã dos Carajás", "Parauapebas"], errors="ignore") >= 5).all(), f"grupos de comparação com ≥ 5 municípios: {grp.to_dict()}")
    # 6. tabelas markdown
    tabs = sorted(TAB.glob("tab_*.md"))
    chk(len(tabs) >= 12, f"{len(tabs)} tabelas markdown em artigo/tabelas")
    sem_fonte = [t.name for t in tabs if "Fonte:" not in t.read_text()]
    chk(not sem_fonte, f"toda tabela com 'Fonte:' — exceções: {sem_fonte}")
    # 7. figuras: PNG + SVG + índice com resumo (alt) e fonte; sem hex fora da paleta nos SVG
    idx = json.loads((FIG / "figuras.json").read_text())
    chk(len(idx) >= 15, f"{len(idx)} figuras no índice")
    faltam = [d["arquivo"] for d in idx if not (FIG / d["arquivo"]).exists() or not (FIG / d["svg"]).exists()]
    chk(not faltam, f"PNG e SVG presentes para todas — faltando: {faltam}")
    chk(all(d.get("resumo") and d.get("fonte") and d.get("legenda") for d in idx), "todas as figuras com legenda, fonte e resumo textual (alt)")
    from lib import ardosia_palette as P
    paleta = {v.lower() for k, v in vars(P).items() if isinstance(v, str) and v.startswith("#")}
    paleta |= {c.lower() for c in P.VIZ_SEQUENTIAL + P.VIZ_DIVERGING + [P.VIZ_MUTED]}
    paleta |= {c["solid"].lower() for c in P.STATUS.values()} | {c["bg"].lower() for c in P.STATUS.values()} | {c["fg"].lower() for c in P.STATUS.values()}
    # exceção decidida pelo usuário (10/09/2026): classes de uso do solo com as cores oficiais MapBiomas/IBGE
    from lib.legendas import cores_oficiais
    paleta |= cores_oficiais()
    fora = {}
    for d in idx:
        svg = (FIG / d["svg"]).read_text(errors="ignore")
        hexes = {h.lower() for h in re.findall(r"#[0-9a-fA-F]{6}\b", svg)}
        extra = sorted(h for h in hexes if h not in paleta and h not in {"#ffffff", "#000000"})
        if extra:
            fora[d["svg"]] = extra
    chk(not fora, f"hex fora da paleta Ardósia ∪ legendas oficiais MapBiomas/IBGE nos SVG: {fora if fora else 'nenhum'}")
    # 8. gate
    chk((BASE / "data/processed/.gate_ok").exists(), ".gate_ok presente (rodar disclosure_check.py após mudar data/processed)")
    print(f"\nResultado E5: {'OK' if falhas == 0 else f'{falhas} falha(s)'}")
    return 1 if falhas else 0


def e6() -> int:
    """E6 — artigo: texto, citações resolvidas, referências verificadas, figuras/tabelas presentes, DOCX e PDF."""
    import re

    falhas = 0
    ART = BASE / "artigo"

    def chk(ok: bool, msg: str) -> None:
        nonlocal falhas
        (_ok if ok else _fail)(msg)
        falhas += int(not ok)

    print("=== E6: artigo ===")
    for f in ("texto.md", "texto_resolvido.md", "artigo.docx", "artigo.pdf", "citadas.json"):
        chk((ART / f).exists(), f"artigo/{f} presente")
    if falhas:
        return 1
    txt = (ART / "texto.md").read_text(encoding="utf-8")
    res = (ART / "texto_resolvido.md").read_text(encoding="utf-8")
    for sec in ("## Resumo", "## Abstract", "## 1 Introdução", "## 2 Revisão de literatura", "## 3 Área de estudo", "## 4 Dados e métodos",
                "### 4.3 Estimação e controle de revelação", "### 4.4 Sensoriamento remoto", "### 4.6 Limitações", "## 5 Resultados",
                "## 6 Discussão", "## 7 Conclusão", "## Declaração de uso de inteligência artificial", "## Referências"):
        chk(sec in txt, f"seção presente: {sec}")
    chk(not re.search(r"<cite[t]?:|<!--\s*(tab|fig):\s*(tab|fig)_", res), "nenhum marcador <cite>/tab/fig pendente no texto resolvido")
    refs = json.loads((ART / "bibliografia/referencias.json").read_text())["referencias"]
    refs += json.loads((ART / "bibliografia/referencias_metodologicas.json").read_text())["referencias"]
    por = {r["slug"]: r for r in refs}
    citadas = json.loads((ART / "citadas.json").read_text())
    chk(all(s in por for s in citadas), f"{len(citadas)} obras citadas, todas em referencias*.json")
    chk(all(re.match(r"https?://", por[s]["verificado_em"]) for s in citadas), "toda obra citada tem verificado_em com URL")
    sec_ref = res.split("## Referências", 1)[1]
    n_ref = sum(1 for l in sec_ref.splitlines() if l.strip() and re.match(r"^[A-ZÁ-Ú][A-ZÁ-Ú' \-]+,", l.strip()))
    chk(n_ref == len(citadas), f"lista de referências com {n_ref} entradas = {len(citadas)} citadas")
    slugs_cit = set(re.findall(r"<cite[t]?:([^>]+)>", txt))
    todos = {s.strip() for grupo in slugs_cit for s in grupo.split(";")}
    chk(todos == set(citadas), "conjunto de slugs no texto.md = citadas.json")
    figs = re.findall(r"<!-- fig: (fig_\S+) -->", txt)
    tabs = re.findall(r"<!-- tab: (tab_\S+) -->", txt)
    idx = {d["arquivo"].removesuffix(".png") for d in json.loads((ART / "figuras/figuras.json").read_text())}
    chk(set(figs) <= idx and all((ART / "figuras" / f"{f}.png").exists() for f in figs), f"{len(figs)} figuras citadas existem")
    chk(len(figs) == len(set(figs)) and len(figs) == len(idx), f"todas as {len(idx)} figuras do índice usadas exatamente uma vez")
    chk(all((ART / "tabelas" / f"{t}.md").exists() for t in tabs), f"{len(tabs)} tabelas citadas existem")
    todas_tabs = {p.stem for p in (ART / "tabelas").glob("tab_*.md")}
    chk(set(tabs) == todas_tabs, f"todas as {len(todas_tabs)} tabelas usadas: faltam {sorted(todas_tabs - set(tabs))}")
    for i in range(1, len(tabs) + 1):
        chk(f"Tabela {i}" in txt, f"Tabela {i} mencionada no corpo")
    for i in range(1, len(figs) + 1):
        chk(f"Figura {i}" in txt, f"Figura {i} mencionada no corpo")
    decl = (ART / "bibliografia/declaracao_ia_padrao.md").read_text()
    chk("responsabilidade integral pelo conteúdo científico" in " ".join(txt.split()) and "responsabilidade integral pelo conteúdo científico" in " ".join(decl.split()), "declaração de IA reaproveitada do texto padrão")
    pdf = ART / "artigo.pdf"
    chk(pdf.stat().st_mtime >= (ART / "artigo.docx").stat().st_mtime - 5 and (ART / "artigo.docx").stat().st_mtime >= (ART / "texto.md").stat().st_mtime,
        "artigo.docx e artigo.pdf mais novos que texto.md")
    try:
        import subprocess
        info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
        pags = int(re.search(r"Pages:\s+(\d+)", info).group(1))
        chk(pags >= 20, f"PDF com {pags} páginas")
    except Exception as e:  # noqa: BLE001
        _ok(f"pdfinfo indisponível ({e}); páginas não conferidas")
    palavras = len(res.split("## Referências")[0].split())
    chk(palavras >= 6000, f"corpo do texto com {palavras} palavras")
    print(f"\nResultado E6: {'OK' if falhas == 0 else f'{falhas} falha(s)'}")
    return 1 if falhas else 0


def e7() -> int:
    """E7 — painel: dados web aprovados pelo gate e sem drift, nada de microdado/CSV em web/public,
    auditoria de hex (paleta Ardósia ∪ cores de legenda declaradas no manifesto), build atualizado."""
    import hashlib
    import re

    import pandas as pd

    import disclosure_rules as R

    falhas = 0
    WEB = BASE / "web"
    PUB = WEB / "public"
    PAINEL = PUB / "data" / "painel"
    PROC = BASE / "data" / "processed"

    def chk(ok: bool, msg: str) -> None:
        nonlocal falhas
        (_ok if ok else _fail)(msg)
        falhas += int(not ok)

    def sha(p: Path) -> str:
        return hashlib.sha256(p.read_bytes()).hexdigest()

    print("=== E7: dados do painel ===")
    man_p = PAINEL / "_manifesto.json"
    chk(man_p.exists(), "web/public/data/painel/_manifesto.json presente (rode pipeline/60_dados_web.py)")
    if not man_p.exists():
        return 1
    man = json.loads(man_p.read_text("utf-8"))
    carimbo = json.loads((PROC / ".gate_ok").read_text("utf-8"))
    chk(man["versao_gate"] == carimbo["versao_dados"],
        f"dados web exportados sob o carimbo vigente ({man['versao_gate']} = {carimbo['versao_dados']})")
    drift = [a for a, h in man["arquivos"].items() if not (PUB / a).exists() or sha(PUB / a) != h]
    chk(not drift, f"{len(man['arquivos'])} arquivos do painel batem com o manifesto (sem edição manual)" +
        (f" — divergentes: {drift[:5]}" if drift else ""))
    # cada tabela analítica exportada vem de um parquet aprovado, com o mesmo número de linhas
    aprovados = carimbo["arquivos"]
    faltam, linhas_dif = [], []
    for j in sorted((PAINEL / "analise").glob("*.json")):
        pq = f"analise/{j.stem}.parquet"
        if pq not in aprovados:
            faltam.append(j.name)
            continue
        if len(json.loads(j.read_text("utf-8"))) != len(pd.read_parquet(PROC / pq)):
            linhas_dif.append(j.name)
    chk(not faltam, "toda tabela de painel/analise tem origem carimbada em data/processed/analise" + (f" — sem origem: {faltam}" if faltam else ""))
    chk(not linhas_dif, "tabelas do painel com o mesmo número de linhas da origem" + (f" — {linhas_dif}" if linhas_dif else ""))

    print("=== E7: sigilo em web/public ===")
    est = json.loads((PAINEL / "estimativas.json").read_text("utf-8"))
    cols = set(est["col"]) | set(est["dic"])
    proib = {c.lower() for c in R.COLUNAS_PROIBIDAS}
    chk(not (cols & proib), "estimativas.json sem coluna proibida (R5)")
    chk(not any(c == "n" or (c.startswith("n_") and not c.endswith("_faixa")) for c in cols),
        "estimativas.json sem contagem amostral exata (R3: só faixas)")
    faixas_ok = {rot for _, _, rot in R.FAIXAS_N} | {""}
    chk(set(est["dic"]["n_faixa"]) <= faixas_ok and set(est["dic"]["n_dom_faixa"]) <= faixas_ok, "faixas de n válidas")
    i_cont = est["dic"]["estatistica"].index("contagem")
    cont = [v for k, v in zip(est["col"]["estatistica"], est["col"]["valor"]) if k == i_cont and v is not None]
    chk(all(abs(v / R.ARREDONDAMENTO - round(v / R.ARREDONDAMENTO)) < 1e-9 for v in cont),
        f"{len(cont)} contagens ponderadas múltiplas de {R.ARREDONDAMENTO} (R2)")
    chk(len(est["col"]["valor"]) == len(pd.read_parquet(PROC / "microdados" / "estimativas.parquet")),
        "estimativas.json com as mesmas linhas do parquet aprovado")
    proibidos = [p.relative_to(WEB).as_posix() for p in PUB.rglob("*")
                 if p.is_file() and p.name != "robots.txt" and (p.suffix.lower() in {".csv", ".txt", ".dbf", ".parquet", ".sas"} or
                                     re.search(r"(microdados|interim|_controlado|pessoas_|domicilios_)", p.name.lower()))]
    chk(not proibidos, "nenhum CSV/TXT/DBF/parquet ou arquivo de microdado em web/public" + (f" — {proibidos[:5]}" if proibidos else ""))
    chk(sha(PUB / "artigo" / "artigo.pdf") == sha(BASE / "artigo" / "artigo.pdf"), "PDF do painel = artigo/artigo.pdf")

    print("=== E7: paleta ===")
    hexre = re.compile(r"#[0-9a-fA-F]{6}\b")
    permitidos = {h.upper() for h in hexre.findall((WEB / "src" / "styles" / "ardosia.css").read_text("utf-8"))}
    # tokens do tema escuro e cinzas de ênfase documentados na skill (references/palette.md)
    permitidos |= {"#B4B2A9", "#A9BEC9", "#C08066", "#E0BCAC", "#A7BFB4", "#6C8F80", "#212A2F", "#EDEAE4",
                   "#9AA6AC", "#3A4348", "#7E8A90", "#171B1E"}
    legendas = {h.upper() for h in hexre.findall((PUB / "data" / "geo" / "camadas.json").read_text("utf-8"))}
    for f in (WEB / "src" / "legend").glob("*"):
        legendas |= {h.upper() for h in hexre.findall(f.read_text("utf-8", errors="ignore"))}
    fora = {}
    for f in (WEB / "src").rglob("*"):
        if f.suffix not in {".ts", ".tsx", ".css"} or "legend" in f.parts:
            continue
        t = f.read_text("utf-8")
        achados = {h.upper() for h in hexre.findall(t)}
        for r_, g_, b_ in re.findall(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", t):
            if (r_, g_, b_) != ("0", "0", "0"):
                achados.add(f"#{int(r_):02X}{int(g_):02X}{int(b_):02X}")
        ruins = achados - permitidos - legendas
        if ruins:
            fora[f.relative_to(WEB).as_posix()] = sorted(ruins)
    chk(not fora, f"nenhum hex fora da paleta Ardósia/legendas oficiais em web/src ({len(permitidos)} tokens)" +
        (f" — {fora}" if fora else ""))

    print("=== E7: build ===")
    dist = WEB / "dist" / "index.html"
    chk(dist.exists(), "web/dist/index.html presente (npm run build)")
    if dist.exists():
        mais_novo = max(p.stat().st_mtime for p in (WEB / "src").rglob("*") if p.is_file())
        chk(dist.stat().st_mtime >= mais_novo, "build mais novo que o código-fonte")
        chk((WEB / "dist" / "data" / "painel" / "_manifesto.json").exists(), "dados copiados para o build")
        html = dist.read_text("utf-8")
        chk('src="./' in html or "src='./" in html or 'href="./' in html, "caminhos relativos no build (GitHub Pages)")
    print(f"\nResultado E7: {'OK' if falhas == 0 else f'{falhas} falha(s)'}")
    return 1 if falhas else 0


def _pontos(geom: dict):
    """Todos os vértices de uma geometria GeoJSON (Polygon/MultiPolygon/LineString/Point)."""
    def rec(c):
        if isinstance(c[0], (int, float)):
            yield c
        else:
            for x in c:
                yield from rec(x)
    yield from rec(geom["coordinates"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--e3a", action="store_true")
    ap.add_argument("--e3b", action="store_true")
    ap.add_argument("--e3c", action="store_true")
    ap.add_argument("--e2", action="store_true")
    ap.add_argument("--e4", action="store_true")
    ap.add_argument("--e5", action="store_true")
    ap.add_argument("--e6", action="store_true")
    ap.add_argument("--e7", action="store_true")
    args = ap.parse_args()
    if args.smoke:
        sys.exit(smoke())
    if args.e3a:
        sys.exit(e3a())
    if args.e3b:
        sys.exit(e3b())
    if args.e3c:
        sys.exit(e3c())
    if args.e2:
        sys.exit(e2())
    if args.e4:
        sys.exit(e4())
    if args.e5:
        sys.exit(e5())
    if args.e6:
        sys.exit(e6())
    if args.e7:
        sys.exit(e7())
    ap.print_help()
