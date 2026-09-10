"""
E3a / Fase 3 passo 6 (parte) (PLANO.md) — série anual de área urbanizada e de
mineração a partir dos produtos prontos recortados em `25_produtos_prontos.py`,
e vetorização por ano para o slider do dashboard.

O que sai daqui (tudo referente a **produtos de terceiros**; a série da
classificação própria vem em E3b e será comparada com esta):

  - `data/processed/geo/mancha_mapbiomas_anual.parquet` / `.csv`: uma linha por
    ano 1985-2025 × recorte (município inteiro | janela da sede) com área em ha
    e km² das classes 24 (Área Urbanizada), 30 (Mineração), 21/25 (mosaico e
    outras áreas não vegetadas, usadas como contexto), Δ absoluto e %, taxa
    geométrica anual, e densidade (hab/ha) nos anos censitários.
  - `web/public/data/geo/mancha_mapbiomas_{ano}.json`: polígonos da classe 24
    por ano, na janela da sede, em 4326 (camada do slider).
  - `web/public/data/mancha_anual.json`: a série, já no formato que os KPIs e
    o gráfico de linha do dashboard consomem.
  - `data/processed/geo/comparacao_produtos.parquet`: área urbanizada segundo
    MapBiomas × GHSL × WSF-Evolution × IBGE Áreas Urbanizadas nos anos em que
    dois ou mais coincidem — a tabela de "validação de magnitude" do artigo.

Áreas sempre calculadas em EPSG:31982 (CLAUDE.md), nunca em graus. O pixel do
MapBiomas é 30 m nominais em 4326; a área é obtida reprojetando os polígonos
vetorizados, não multiplicando contagem de pixels por 900 m².

E3c acrescentou a parte da **classificação própria** (`main_propria`), que lê
`mancha_propria_anual.parquet` e os rasters de `23_classificar_mancha.py`:

  - `data/processed/geo/estatisticas_mancha.{parquet,csv}`: uma linha por ano
    1984-2026 — área da sede contígua, outros núcleos, construído em mineração,
    loteamento vazio (ha e km²), Δ absoluto e %, área ajustada pelo erro de
    mapeamento (fator área ajustada / área mapeada das épocas validadas em
    `24_validar_mancha.py`, interpolado linearmente entre 2009, 2017 e 2022 e
    mantido constante fora delas) com IC 95 %, série de 10 m, MapBiomas 24 na
    mesma janela, população (município e urbana), densidades, forma (raio
    equivalente, distância média ao núcleo histórico, índice de proximidade de
    Angel et al. 2010, deslocamento do centroide) e qualidade do ano (sensor,
    nº de cenas, fração preenchida, situação da validação).
  - `data/processed/geo/estatisticas_mancha_periodos.{parquet,csv}`: taxa
    geométrica anual, ha/ano e participação na área final por período mineral e
    intercensitário, com o indicador ODS 11.3.1 (razão entre a taxa de consumo de
    solo e a taxa de crescimento populacional, UN-Habitat) nos intervalos
    censitários.
  - `data/processed/geo/estatisticas_mancha_censos.{parquet,csv}`: densidade
    bruta e ajustada (hab/ha, dom/ha) nos anos censitários, com população e
    domicílios da sede somados dos setores urbanos do Universo (2010, 2022) que
    se sobrepõem à sede mapeada; 2000 sem malha digital (população urbana SIDRA).
  - `data/processed/geo/expansao_direcao.{parquet,csv}`: área acrescida por
    octante (a partir do centroide da sede de 1990) e por período.
  - `data/processed/setores/setores_mancha.parquet`: por setor 2010/2022, área
    construída mapeada, fração construída e densidade líquida (hab/ha construído).
  - `web/public/data/estatisticas_mancha.json` e `web/public/data/setores_mancha.json`.

Uso:
    .venv/bin/python pipeline/26_estatisticas_mancha.py            # tudo
    .venv/bin/python pipeline/26_estatisticas_mancha.py mapbiomas  # só a parte E3a
    .venv/bin/python pipeline/26_estatisticas_mancha.py propria    # só a parte E3c
"""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape

BASE = Path(__file__).resolve().parent.parent
PROD = BASE / "data" / "interim" / "produtos"
OUT_GEO = BASE / "data" / "processed" / "geo"
OUT_WEB = BASE / "web" / "public" / "data"
OUT_WEB_GEO = OUT_WEB / "geo"
for d in (OUT_GEO, OUT_WEB_GEO):
    d.mkdir(parents=True, exist_ok=True)

EPSG_METRICO = 31982
BBOX_SEDE = (-49.99, -6.60, -49.75, -6.40)

# Classes MapBiomas de interesse — os códigos vêm da legenda oficial baixada em
# 25_produtos_prontos.py, conferidos contra ela em `_conferir_legenda()`.
CLASSES = {24: "area_urbanizada", 30: "mineracao", 21: "mosaico_de_usos", 25: "outras_nao_veg"}

# População do município nos anos censitários e estimativas (E1, SIDRA)
POP_ARQUIVOS = {
    "censos": OUT_GEO.parent / "ibge" / "t9923_situacao_2022.parquet",
    "estimativas": OUT_GEO.parent / "ibge" / "t6579_estimativas_2001_2026.parquet",
}


def _conferir_legenda() -> None:
    p = OUT_GEO / "mapbiomas_legenda_col11.parquet"
    if not p.exists():
        raise SystemExit("Rode antes: pipeline/25_produtos_prontos.py mapbiomas")
    leg = pd.read_parquet(p).set_index("class_id")["classe_pt"].to_dict()
    esperado = {24: "urbaniz", 30: "mineraç", 21: "mosaico", 25: "não veget"}
    for cid, fragmento in esperado.items():
        nome = str(leg.get(cid, "")).lower()
        if fragmento.lower() not in nome:
            raise SystemExit(
                f"Legenda MapBiomas mudou: classe {cid} = {leg.get(cid)!r}, "
                f"esperado conter {fragmento!r}. Revisar CLASSES."
            )
    print(f"  legenda conferida: 24={leg[24]}, 30={leg[30]}")


def vetorizar(tif: Path, classe: int, recorte: str) -> gpd.GeoDataFrame:
    """Polígonos de uma classe MapBiomas, em EPSG:31982."""
    with rasterio.open(tif) as src:
        if recorte == "sede":
            from rasterio.windows import from_bounds

            win = from_bounds(*BBOX_SEDE, src.transform)
            arr = src.read(1, window=win)
            transform = src.window_transform(win)
        else:
            arr = src.read(1)
            transform = src.transform
        crs = src.crs
    mask = arr == classe
    if not mask.any():
        return gpd.GeoDataFrame({"classe": []}, geometry=[], crs=EPSG_METRICO)
    geoms = [
        shape(g) for g, v in shapes(mask.astype(np.uint8), mask=mask, transform=transform) if v == 1
    ]
    gdf = gpd.GeoDataFrame(
        {"classe": [classe] * len(geoms)}, geometry=geoms, crs=crs
    ).to_crs(EPSG_METRICO)
    gdf["area_ha"] = gdf.geometry.area / 1e4
    return gdf


def serie_mapbiomas() -> pd.DataFrame:
    d = PROD / "mapbiomas_col11"
    tifs = sorted(d.glob("mapbiomas_col11_*.tif"))
    if not tifs:
        raise SystemExit("Sem recortes MapBiomas — rode 25_produtos_prontos.py mapbiomas")
    linhas = []
    for tif in tifs:
        ano = int(tif.stem.rsplit("_", 1)[-1])
        for recorte in ("municipio", "sede"):
            reg = {"ano": ano, "recorte": recorte}
            for cid, nome in CLASSES.items():
                gdf = vetorizar(tif, cid, recorte)
                reg[f"{nome}_ha"] = float(gdf["area_ha"].sum())
                reg[f"{nome}_n_poligonos"] = int(len(gdf))
                if cid == 24 and recorte == "sede" and len(gdf):
                    # camada do slider: só a classe 24 na janela da sede
                    gdf.to_crs(4326).to_file(
                        OUT_WEB_GEO / f"mancha_mapbiomas_{ano}.json", driver="GeoJSON"
                    )
            linhas.append(reg)
        print(f"  {ano}: sede {linhas[-1]['area_urbanizada_ha']:7.1f} ha urbanizado, "
              f"{linhas[-1]['mineracao_ha']:8.1f} ha mineração")
    df = pd.DataFrame(linhas).sort_values(["recorte", "ano"])
    for col in ("area_urbanizada_ha", "mineracao_ha"):
        g = df.groupby("recorte")[col]
        df[col.replace("_ha", "_km2")] = df[col] / 100
        df[col.replace("_ha", "_delta_ha")] = g.diff()
        df[col.replace("_ha", "_var_pct")] = g.pct_change() * 100
    return df.reset_index(drop=True)


def taxa_geometrica(df: pd.DataFrame, coluna: str = "area_urbanizada_ha") -> pd.DataFrame:
    """Taxa geométrica anual entre marcos (assentamento→hoje e por período
    mineral): (Vf/Vi)^(1/n) − 1."""
    marcos = [(1985, 1994), (1994, 2004), (2004, 2016), (2016, 2025), (1985, 2025)]
    out = []
    for recorte, sub in df.groupby("recorte"):
        s = sub.set_index("ano")[coluna]
        for a0, a1 in marcos:
            if a0 in s.index and a1 in s.index and s[a0] > 0:
                out.append(
                    {
                        "recorte": recorte,
                        "periodo": f"{a0}-{a1}",
                        "ha_inicio": s[a0],
                        "ha_fim": s[a1],
                        "taxa_geometrica_aa_pct": ((s[a1] / s[a0]) ** (1 / (a1 - a0)) - 1) * 100,
                    }
                )
    return pd.DataFrame(out)


def comparacao_produtos(df_mb: pd.DataFrame) -> pd.DataFrame:
    """Área urbanizada (município) segundo cada produto, para a tabela de
    validação de magnitude. GHSL é superfície construída (m² por pixel de
    100 m), não mancha — a conversão é declarada na coluna `natureza`."""
    linhas = []
    sede_mb = df_mb[df_mb["recorte"] == "municipio"].set_index("ano")
    for ano in sede_mb.index:
        linhas.append(
            {"produto": "MapBiomas Col.11", "ano": int(ano), "natureza": "classe 24 (mancha)",
             "area_ha": float(sede_mb.loc[ano, "area_urbanizada_ha"])}
        )
    # GHSL — soma da superfície construída (m²/pixel) → ha
    for tif in sorted((PROD / "ghsl").glob("ghs_built_s_*.tif")):
        ano = int(tif.stem.rsplit("_", 1)[-1])
        with rasterio.open(tif) as src:
            a = src.read(1).astype("float64")
            a = np.where(a == src.nodata, 0, a) if src.nodata is not None else a
        linhas.append({"produto": "GHS-BUILT-S R2023A", "ano": ano,
                       "natureza": "superfície construída (m²)", "area_ha": float(a.sum()) / 1e4})
    # WSF-Evolution — o valor do pixel é o ano de primeira detecção; acumulado
    evo = PROD / "wsf" / "wsf_evolution.tif"
    if evo.exists():
        with rasterio.open(evo) as src:
            a = src.read(1)
            px_m2 = abs(src.transform.a) * abs(src.transform.e) * (111_320**2) * np.cos(
                np.deg2rad(6.5)
            ) if src.crs.to_epsg() == 4326 else abs(src.transform.a * src.transform.e)
        for ano in range(1985, 2016):
            n = int(((a >= 1985) & (a <= ano)).sum())
            linhas.append({"produto": "WSF-Evolution", "ano": ano,
                           "natureza": "ano de 1ª detecção (acumulado)",
                           "area_ha": n * px_m2 / 1e4})
    # IBGE Áreas Urbanizadas
    for p in sorted((PROD / "areas_urbanizadas").glob("areas_urbanizadas_*.parquet")):
        rot = p.stem.replace("areas_urbanizadas_", "")
        gdf = gpd.read_parquet(p)
        linhas.append({"produto": f"IBGE Áreas Urbanizadas {rot}",
                       "ano": int(rot[:4]), "natureza": "vetor interpretado (mancha)",
                       "area_ha": float(gdf["area_ha"].sum())})
    return pd.DataFrame(linhas).sort_values(["produto", "ano"]).reset_index(drop=True)


def diagnostico(df: pd.DataFrame, comp: pd.DataFrame) -> pd.DataFrame:
    """Consistência da série MapBiomas como *série anual*.

    A classe 24 do MapBiomas sobre Canaã cresce até meados dos anos 1990 e
    depois congela por quase duas décadas (ver `docs/qa/E3a.md`): é um mapa
    urbano quase estático, não uma detecção anual. Este bloco quantifica isso
    para que E3b e o artigo citem o número, em vez da impressão visual:
      - `anos_estagnados`: anos em que |Δ| < 0,5% da área do ano anterior;
      - `razao_wsf`: MapBiomas ÷ WSF-Evolution no mesmo ano (divergência de
        magnitude entre os produtos de referência).
    """
    sede = df[df["recorte"] == "sede"].set_index("ano")
    est = sede.index[(sede["area_urbanizada_var_pct"].abs() < 0.5)].tolist()
    blocos = []
    for ano in est:
        if blocos and ano == blocos[-1][-1] + 1:
            blocos[-1].append(ano)
        else:
            blocos.append([ano])
    maior = max(blocos, key=len) if blocos else []

    mun = df[df["recorte"] == "municipio"].set_index("ano")["area_urbanizada_ha"]
    wsf = comp[comp["produto"] == "WSF-Evolution"].set_index("ano")["area_ha"]
    ghsl = comp[comp["produto"] == "GHS-BUILT-S R2023A"].set_index("ano")["area_ha"]
    linhas = []
    for ano in sorted(set(mun.index) & set(wsf.index)):
        linhas.append({"ano": ano, "mapbiomas_ha": mun[ano], "wsf_ha": wsf[ano],
                       "ghsl_ha": float(ghsl.get(ano, np.nan)),
                       "razao_mb_wsf": mun[ano] / wsf[ano] if wsf[ano] else np.nan})
    d = pd.DataFrame(linhas)
    print(f"\n— diagnóstico da série MapBiomas —")
    print(f"anos com |Δ| < 0,5%: {len(est)} de {len(sede) - 1}; "
          f"maior sequência contígua: {maior[0]}–{maior[-1]} ({len(maior)} anos)" if maior
          else "nenhum ano estagnado")
    print(f"razão MapBiomas ÷ WSF-Evolution (município): "
          f"mediana {d['razao_mb_wsf'].median():.2f}, "
          f"faixa {d['razao_mb_wsf'].min():.2f}–{d['razao_mb_wsf'].max():.2f}")
    return d


def serie_populacional() -> pd.DataFrame:
    """População anual do município, montada a partir das tabelas SIDRA de E1,
    com a fonte declarada por ano (o artigo e o dashboard precisam distinguir
    censo de estimativa):
      censo 2000/2010/2022 (t/200, t/9923) > contagem 2007 (t/793) >
      estimativa intercensitária (t/6579).
    A descontinuidade 2021 (estimativa 39.103) → 2022 (censo 77.079) é real e
    documentada em `docs/qa/E3a.md`: as estimativas subcontaram Canaã em ~50%.
    """
    IBGE = OUT_GEO.parent / "ibge"

    def _tidy(arquivo: str, fonte: str, filtro=None) -> pd.DataFrame:
        p = IBGE / f"{arquivo}.parquet"
        if not p.exists():
            return pd.DataFrame(columns=["ano", "pop_municipio", "fonte_pop"])
        d = pd.read_parquet(p)
        if filtro is not None:
            d = filtro(d)
        return (
            d.assign(ano=pd.to_numeric(d["Ano"], errors="coerce"),
                     pop_municipio=pd.to_numeric(d["valor"], errors="coerce"))
            .dropna(subset=["ano", "pop_municipio"])
            .astype({"ano": int})[["ano", "pop_municipio"]]
            .assign(fonte_pop=fonte)
        )

    def _total(d: pd.DataFrame) -> pd.DataFrame:
        for col in ("Sexo", "Situação do domicílio", "Grupo de idade"):
            if col in d.columns:
                d = d[d[col] == "Total"]
        return d

    partes = [
        _tidy("t200_pop_historica_municipio", "censo", _total),
        _tidy("t9923_situacao_2022", "censo", _total),
        _tidy("t793_contagem_2007", "contagem"),
        _tidy("t6579_estimativas_2001_2026", "estimativa"),
    ]
    pop = pd.concat([p for p in partes if len(p)], ignore_index=True)
    # censo > contagem > estimativa quando o mesmo ano aparece em mais de uma
    ordem = {"censo": 0, "contagem": 1, "estimativa": 2}
    pop = (
        pop.assign(_o=pop["fonte_pop"].map(ordem))
        .sort_values(["ano", "_o"])
        .drop_duplicates("ano", keep="first")
        .drop(columns="_o")
        .reset_index(drop=True)
    )
    pop.to_parquet(OUT_GEO.parent / "ibge" / "populacao_anual_municipio.parquet")
    return pop


def densidade(df: pd.DataFrame) -> pd.DataFrame:
    """hab/ha nos anos com população conhecida.

    Atenção à mistura de denominadores: o numerador é a população **do
    município** (o SIDRA não estima população da sede ano a ano) e o
    denominador, a mancha urbana da janela da sede. Como ~90% da população é
    urbana e concentrada na sede (censo 2022: 69.332 de 77.079), a razão é uma
    aproximação útil, mas o nome da coluna carrega o aviso.
    """
    pop = serie_populacional()
    if pop.empty:
        print("  ! sem tabelas de população (E1) — densidade não calculada")
        return df
    df = df.merge(pop, on="ano", how="left")
    df["densidade_popmun_hab_ha"] = df["pop_municipio"] / df["area_urbanizada_ha"]
    n = int(df.loc[df["recorte"] == "sede", "pop_municipio"].notna().sum())
    print(f"  população anual: {len(pop)} anos ("
          f"{', '.join(f'{k}={v}' for k, v in pop['fonte_pop'].value_counts().items())}); "
          f"densidade calculada em {n} anos")
    return df


def main_mapbiomas() -> None:
    print("Conferindo legenda …")
    _conferir_legenda()
    print("Série anual MapBiomas 1985-2025 …")
    df = serie_mapbiomas()
    df = densidade(df)
    df.to_parquet(OUT_GEO / "mancha_mapbiomas_anual.parquet")
    df.to_csv(OUT_GEO / "mancha_mapbiomas_anual.csv", index=False)

    tx = taxa_geometrica(df)
    tx.to_parquet(OUT_GEO / "mancha_taxa_geometrica.parquet")

    comp = comparacao_produtos(df)
    comp.to_parquet(OUT_GEO / "comparacao_produtos.parquet")
    comp.to_csv(OUT_GEO / "comparacao_produtos.csv", index=False)

    diag = diagnostico(df, comp)
    diag.to_parquet(OUT_GEO / "diagnostico_serie_mapbiomas.parquet")

    sede = df[df["recorte"] == "sede"]
    OUT_WEB.mkdir(parents=True, exist_ok=True)
    (OUT_WEB / "mancha_anual.json").write_text(
        json.dumps(
            {
                "fonte": "MapBiomas Brasil, Coleção 11 (classes 24 e 30), recorte da janela "
                         "da sede de Canaã dos Carajás; áreas em EPSG:31982",
                "aviso": "série de produto de terceiros, só para comparação: a classe 24 fica "
                         "estagnada em 1996-2014 e supera a classificação própria ~4x (docs/qa/E3a.md, "
                         "E3b.md). A série principal está em estatisticas_mancha.json (E3c).",
                "serie": json.loads(
                    sede[["ano", "area_urbanizada_ha", "mineracao_ha",
                          "area_urbanizada_delta_ha", "area_urbanizada_var_pct",
                          "pop_municipio", "fonte_pop", "densidade_popmun_hab_ha"]]
                    .round(2).to_json(orient="records")
                ),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\n— janela da sede, classe 24 —")
    marcos = [1985, 1990, 1994, 2000, 2004, 2010, 2016, 2022, 2025]
    print(sede[sede["ano"].isin(marcos)][
        ["ano", "area_urbanizada_ha", "area_urbanizada_var_pct", "mineracao_ha"]
    ].round(1).to_string(index=False))
    print("\n— taxa geométrica anual —")
    print(tx.round(2).to_string(index=False))
    print("\n— comparação entre produtos (município) —")
    print(comp[comp["ano"].isin([2000, 2010, 2015, 2019, 2020, 2022])].round(1).to_string(index=False))




# ----------------------------------------------------------------------------
# E3c — estatísticas da classificação própria (Fase 3 passo 6)
# ----------------------------------------------------------------------------

MANCHA_P = OUT_GEO / "mancha_propria"
VALID = OUT_GEO / "validacao" / "validacao_acuracia.json"
COMP_REG = BASE / "data" / "interim" / "composicoes" / "composicoes.parquet"
SETORES = OUT_GEO.parent / "setores"
PX30_HA = 0.09

# Marcos: 1º ano da série (TM), emancipação (Lei 5.860/1994), início da operação
# do Sossego (2004) e do S11D (dez/2016), último ano da série. Anos censitários.
PERIODOS = [
    (1984, 1994, "assentamento → emancipação"),
    (1994, 2004, "emancipação → Sossego"),
    (2004, 2016, "Sossego → S11D"),
    (2016, 2026, "S11D → 2026"),
    (2000, 2010, "intercensitário 2000–2010"),
    (2010, 2022, "intercensitário 2010–2022"),
    (1984, 2026, "série inteira"),
]
ANOS_CENSO = (2000, 2010, 2022)
OCTANTES = ["N", "NE", "L", "SE", "S", "SO", "O", "NO"]  # L = leste, O = oeste

# Estimativas SIDRA com subcontagem conhecida (docs/qa/E3a.md): 2001–2006 ficam
# ~40 % abaixo da Contagem 2007 e 2011–2021 ~50 % abaixo do Censo 2022.
AVISO_POP = {
    "censo": "",
    "contagem": "",
    "estimativa_pre": "estimativa intercensitária do IBGE com subcontagem conhecida",
    "estimativa_pos": "estimativa do IBGE posterior ao Censo 2022",
}


def _ler_raster(p: Path) -> tuple[np.ndarray, rasterio.Affine]:
    with rasterio.open(p) as s:
        return s.read(1), s.transform


def _centros(transform: rasterio.Affine, shape_: tuple[int, int]) -> tuple[np.ndarray, np.ndarray]:
    h, w = shape_
    xs = transform.c + (np.arange(w) + 0.5) * transform.a
    ys = transform.f + (np.arange(h) + 0.5) * transform.e
    return np.meshgrid(xs, ys)


def fator_ajuste(anos: list[int]) -> pd.DataFrame:
    """Fator área ajustada / área mapeada (Olofsson) e IC relativo por ano.

    Validado em 2009, 2017 e 2022; interpolado linearmente entre eles e mantido
    constante antes de 2009 e depois de 2022 (extrapolado — declarar)."""
    v = json.loads(VALID.read_text("utf-8"))
    ep = sorted(
        (int(k), r["area_ajustada_urbano_ha"] / r["area_mapa_urbano_ha"],
         r["area_ajustada_ic95_ha"] / r["area_ajustada_urbano_ha"])
        for k, r in v.items()
    )
    xa = np.array([e[0] for e in ep])
    fa = np.array([e[1] for e in ep])
    ia = np.array([e[2] for e in ep])
    linhas = []
    for a in anos:
        origem = "validado" if a in xa else ("interpolado" if xa.min() < a < xa.max() else "extrapolado")
        linhas.append({"ano": a, "fator_ajuste": float(np.interp(a, xa, fa)),
                       "ic95_rel": float(np.interp(a, xa, ia)), "ajuste_origem": origem})
    return pd.DataFrame(linhas)


def populacao() -> pd.DataFrame:
    """População do município (série de E1/E3a) e urbana nos censos, com
    interpolação geométrica da população urbana entre censos (2000–2022) e
    extrapolação 2023–2026 pela taxa das estimativas municipais pós-2022 com a
    taxa de urbanização de 2022 constante — estimativa própria, rotulada."""
    pop = serie_populacional().copy()
    pop["tipo_pop"] = pop["fonte_pop"]
    pre = (pop["fonte_pop"] == "estimativa") & (pop["ano"] < 2022)
    pop.loc[pre, "tipo_pop"] = "estimativa_pre"
    pop.loc[(pop["fonte_pop"] == "estimativa") & (pop["ano"] > 2022), "tipo_pop"] = "estimativa_pos"
    pop["aviso_pop"] = pop["tipo_pop"].map(AVISO_POP).fillna("")

    urb = {}
    for arq, filtro in (("t200_pop_historica_municipio", None), ("t9923_situacao_2022", None)):
        d = pd.read_parquet(OUT_GEO.parent / "ibge" / f"{arq}.parquet")
        for col in ("Sexo", "Grupo de idade"):
            if col in d.columns:
                d = d[d[col] == "Total"]
        d = d[d["Situação do domicílio"] == "Urbana"]
        for _, r in d.iterrows():
            if pd.notna(r["valor"]):
                urb[int(r["Ano"])] = float(r["valor"])
    urb = {a: v for a, v in urb.items() if a in ANOS_CENSO}
    linhas = []
    anos_c = sorted(urb)
    for a in range(2000, 2027):
        if a in urb:
            v, f = urb[a], "censo"
        elif a < anos_c[-1]:
            a0 = max(x for x in anos_c if x < a)
            a1 = min(x for x in anos_c if x > a)
            v = urb[a0] * (urb[a1] / urb[a0]) ** ((a - a0) / (a1 - a0))
            f = "interpolacao_geometrica"
        else:
            pm = pop.set_index("ano")["pop_municipio"]
            if a in pm.index:
                v = urb[2022] * pm[a] / pop.set_index("ano").loc[2022, "pop_municipio"]
                f = "extrapolacao_estimativa_ibge"
            else:
                v, f = np.nan, ""
        linhas.append({"ano": a, "pop_urbana": v, "fonte_pop_urbana": f})
    return pop.merge(pd.DataFrame(linhas), on="ano", how="outer").sort_values("ano")


def forma_anual(anos: list[int], origem: tuple[float, float]) -> pd.DataFrame:
    """Métricas de forma da sede (classe 1) por ano."""
    linhas = []
    for a in anos:
        cls, tr = _ler_raster(MANCHA_P / f"mancha30_{a}.tif")
        sede = cls == 1
        n = int(sede.sum())
        if n == 0:
            continue
        X, Y = _centros(tr, cls.shape)
        x, y = X[sede], Y[sede]
        cx, cy = float(x.mean()), float(y.mean())
        area_m2 = n * 900.0
        r_eq = np.sqrt(area_m2 / np.pi)
        d_centroide = np.hypot(x - cx, y - cy)
        d_origem = np.hypot(x - origem[0], y - origem[1])
        dx, dy = cx - origem[0], cy - origem[1]
        linhas.append({
            "ano": a,
            "raio_equivalente_km": r_eq / 1000,
            "dist_media_nucleo_km": float(d_origem.mean()) / 1000,
            "dist_p95_nucleo_km": float(np.percentile(d_origem, 95)) / 1000,
            # Angel et al. 2010: distância média de um círculo de mesma área ao seu
            # centro (2/3 do raio) ÷ distância média da mancha ao seu centroide (1 = disco)
            "indice_proximidade": float((2 / 3) * r_eq / d_centroide.mean()),
            "centroide_desloc_km": float(np.hypot(dx, dy)) / 1000,
            "centroide_azimute_graus": float((np.degrees(np.arctan2(dx, dy)) + 360) % 360),
        })
    return pd.DataFrame(linhas)


def _octante(dx: np.ndarray, dy: np.ndarray) -> np.ndarray:
    az = (np.degrees(np.arctan2(dx, dy)) + 360) % 360  # 0 = norte, horário
    return ((az + 22.5) // 45).astype(int) % 8


def expansao_direcao(origem: tuple[float, float]) -> pd.DataFrame:
    """Área da sede final acrescida por período mineral e octante, com o 1º ano
    urbano de cada pixel (`ano_urbanizacao30.tif`) restrito à sede de 2026."""
    ano_urb, tr = _ler_raster(MANCHA_P / "ano_urbanizacao30.tif")
    ult = max(int(p.stem.split("_")[1]) for p in MANCHA_P.glob("mancha30_*.tif"))
    sede_final = _ler_raster(MANCHA_P / f"mancha30_{ult}.tif")[0] == 1
    X, Y = _centros(tr, ano_urb.shape)
    oc = _octante(X - origem[0], Y - origem[1])
    dist = np.hypot(X - origem[0], Y - origem[1]) / 1000
    linhas = []
    for a0, a1, rot in PERIODOS[:4]:
        # a0 exclusive (o que já existia no início do período não conta), exceto o 1º período
        ini = a0 if a0 > 1984 else a0 - 1
        m = sede_final & (ano_urb > ini) & (ano_urb <= a1)
        tot = m.sum() * PX30_HA
        for k, nome in enumerate(OCTANTES):
            mk = m & (oc == k)
            linhas.append({"periodo": f"{a0}-{a1}", "rotulo": rot, "octante": nome,
                           "area_ha": float(mk.sum() * PX30_HA),
                           "participacao_pct": float(mk.sum() * PX30_HA / tot * 100) if tot else np.nan,
                           "dist_media_km": float(dist[mk].mean()) if mk.any() else np.nan})
    return pd.DataFrame(linhas)


def setores_mancha() -> pd.DataFrame:
    """Setores 2010/2022 × mancha própria do mesmo ano: área construída mapeada
    (sede e outros núcleos), fração construída do setor e densidade líquida.
    Um setor urbano pertence à sede se a maior parte da sua área construída
    mapeada é classe 1; setor urbano sem construído mapeado fica 'sem_construido'."""
    cfg = {
        2010: ("setores_2010", "Situacao_setor", {1, 2, 3}, "domicilios_particulares_permanentes"),
        2022: ("setores_2022", "CD_SIT", {1, 2, 3}, "domicilios_particulares"),
    }
    partes = []
    for ano, (arq, col_sit, urbanos, col_dom) in cfg.items():
        geo = gpd.read_parquet(SETORES / f"{arq}.parquet")[["cod_setor", "geometry"]].to_crs(EPSG_METRICO)
        ind = pd.read_parquet(SETORES / f"{arq}_indicadores.parquet")
        ind = ind.drop(columns=[c for c in ("geometry",) if c in ind.columns])
        g = geo.merge(ind[["cod_setor", col_sit, "populacao_residente", col_dom]], on="cod_setor", how="left")
        g["situacao"] = pd.to_numeric(g[col_sit], errors="coerce")
        g["urbano"] = g["situacao"].isin(urbanos)
        mancha = gpd.read_parquet(MANCHA_P / f"mancha30_{ano}.parquet")
        mancha = mancha[mancha["classe"].isin([1, 2])]
        inter = gpd.overlay(g[["cod_setor", "geometry"]], mancha[["classe", "geometry"]], how="intersection",
                            keep_geom_type=True)
        inter["ha"] = inter.geometry.area / 1e4
        piv = inter.pivot_table(index="cod_setor", columns="classe", values="ha", aggfunc="sum").fillna(0)
        piv = piv.rename(columns={1: "construido_sede_ha", 2: "construido_outros_ha"})
        for c in ("construido_sede_ha", "construido_outros_ha"):
            if c not in piv.columns:
                piv[c] = 0.0
        g = g.merge(piv[["construido_sede_ha", "construido_outros_ha"]], left_on="cod_setor", right_index=True,
                    how="left").fillna({"construido_sede_ha": 0.0, "construido_outros_ha": 0.0})
        g["area_setor_ha"] = g.geometry.area / 1e4
        g["construido_ha"] = g["construido_sede_ha"] + g["construido_outros_ha"]
        g["frac_construida"] = g["construido_ha"] / g["area_setor_ha"]
        g["pertence"] = np.select(
            [~g["urbano"], g["construido_ha"] == 0, g["construido_sede_ha"] >= g["construido_outros_ha"]],
            ["rural", "sem_construido", "sede"], "outros_nucleos")
        g["densidade_liquida_hab_ha"] = np.where(g["construido_ha"] > 0,
                                                g["populacao_residente"] / g["construido_ha"], np.nan)
        g = g.rename(columns={col_dom: "domicilios"})
        g["ano"] = ano
        partes.append(pd.DataFrame(g.drop(columns=["geometry", col_sit])))
    out = pd.concat(partes, ignore_index=True)
    out.to_parquet(SETORES / "setores_mancha.parquet", index=False)
    return out


def densidade_censos(anual: pd.DataFrame, setm: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    urb = anual.set_index("ano")
    for a in ANOS_CENSO:
        r = urb.loc[a]
        if a in setm["ano"].unique():
            s = setm[setm["ano"] == a]
            sede = s[s["pertence"] == "sede"]
            pop_sede, dom_sede = float(sede["populacao_residente"].sum()), float(sede["domicilios"].sum())
            fonte = f"soma dos {len(sede)} setores urbanos do Universo {a} com construído majoritário na sede"
            pop_sem = float(s.loc[s["pertence"] == "sem_construido", "populacao_residente"].sum())
            pop_outros = float(s.loc[s["pertence"] == "outros_nucleos", "populacao_residente"].sum())
        else:
            pop_sede, dom_sede = float(r["pop_urbana"]), np.nan
            fonte = "população urbana do município (SIDRA t/200); sem malha digital de setores em 2000"
            pop_sem = pop_outros = np.nan
        linhas.append({
            "ano": a, "pop_sede": pop_sede, "dom_sede": dom_sede, "fonte_pop_sede": fonte,
            "pop_urbana_sidra": float(r["pop_urbana"]), "pop_setores_urbanos_sem_construido": pop_sem,
            "pop_outros_nucleos": pop_outros,
            "area_sede_ha": float(r["area_sede_ha"]), "area_sede_ajustada_ha": float(r["area_sede_ajustada_ha"]),
            "area_sede_ajustada_ic95_ha": float(r["area_sede_ajustada_ic95_ha"]),
            "ajuste_origem": r["ajuste_origem"],
            "densidade_bruta_hab_ha": pop_sede / float(r["area_sede_ha"]),
            "densidade_ajustada_hab_ha": pop_sede / float(r["area_sede_ajustada_ha"]),
            "densidade_ajustada_min_hab_ha": pop_sede / (float(r["area_sede_ajustada_ha"]) + float(r["area_sede_ajustada_ic95_ha"])),
            "densidade_ajustada_max_hab_ha": pop_sede / (float(r["area_sede_ajustada_ha"]) - float(r["area_sede_ajustada_ic95_ha"])),
            "dom_por_ha": dom_sede / float(r["area_sede_ha"]) if pd.notna(dom_sede) else np.nan,
            "dom_por_ha_ajustado": dom_sede / float(r["area_sede_ajustada_ha"]) if pd.notna(dom_sede) else np.nan,
            "moradores_por_domicilio": pop_sede / dom_sede if pd.notna(dom_sede) and dom_sede else np.nan,
        })
    return pd.DataFrame(linhas)


def periodos(anual: pd.DataFrame, censos: pd.DataFrame) -> pd.DataFrame:
    s = anual.set_index("ano")
    popc = censos.set_index("ano")["pop_sede"]
    linhas = []
    area_final = float(s["area_sede_ha"].iloc[-1])
    for a0, a1, rot in PERIODOS:
        v0, v1, n = float(s.loc[a0, "area_sede_ha"]), float(s.loc[a1, "area_sede_ha"]), a1 - a0
        l = {"periodo": f"{a0}-{a1}", "rotulo": rot, "anos": n,
             "sede_ha_inicio": v0, "sede_ha_fim": v1, "acrescimo_ha": v1 - v0,
             "ha_por_ano": (v1 - v0) / n,
             "taxa_geometrica_aa_pct": ((v1 / v0) ** (1 / n) - 1) * 100 if v0 > 0 else np.nan,
             "participacao_na_area_final_pct": (v1 - v0) / area_final * 100 if a1 == 2026 or rot != "série inteira" else np.nan,
             "urbano_total_ha_inicio": float(s.loc[a0, "area_urbana_total_ha"]),
             "urbano_total_ha_fim": float(s.loc[a1, "area_urbana_total_ha"]),
             "mineracao_ha_inicio": float(s.loc[a0, "area_construido_mineracao_ha"]),
             "mineracao_ha_fim": float(s.loc[a1, "area_construido_mineracao_ha"])}
        # ODS 11.3.1 (UN-Habitat): LCR = ln(Urb_t2/Urb_t1)/y ; PGR = ln(Pop_t2/Pop_t1)/y
        if a0 in popc.index and a1 in popc.index:
            lcr = np.log(v1 / v0) / n
            pgr = np.log(popc[a1] / popc[a0]) / n
            l.update({"pop_sede_inicio": float(popc[a0]), "pop_sede_fim": float(popc[a1]),
                      "taxa_pop_aa_pct": ((popc[a1] / popc[a0]) ** (1 / n) - 1) * 100,
                      "ods_11_3_1_lcr": lcr, "ods_11_3_1_pgr": pgr, "ods_11_3_1_razao": lcr / pgr})
        linhas.append(l)
    return pd.DataFrame(linhas)


def serie_anual() -> tuple[pd.DataFrame, tuple[float, float]]:
    t = pd.read_parquet(OUT_GEO / "mancha_propria_anual.parquet")
    t30 = t[t["serie"] == "landsat_30m"].drop(columns="serie").sort_values("ano").reset_index(drop=True)
    t10 = t[t["serie"] == "sentinel2_10m"][["ano", "area_sede_ha", "area_outros_nucleos_ha"]].rename(
        columns={"area_sede_ha": "area_sede_10m_ha", "area_outros_nucleos_ha": "area_outros_nucleos_10m_ha"})
    df = t30.copy()
    df["area_urbana_total_ha"] = df["area_sede_ha"] + df["area_outros_nucleos_ha"]
    for c in ("area_sede_ha", "area_urbana_total_ha", "area_construido_mineracao_ha"):
        df[c.replace("_ha", "_km2")] = df[c] / 100
        df[c.replace("_ha", "_delta_ha")] = df[c].diff()
        df[c.replace("_ha", "_var_pct")] = df[c].pct_change() * 100
    fa = fator_ajuste(df["ano"].tolist())
    df = df.merge(fa, on="ano")
    df["area_sede_ajustada_ha"] = df["area_sede_ha"] * df["fator_ajuste"]
    df["area_sede_ajustada_ic95_ha"] = df["area_sede_ajustada_ha"] * df["ic95_rel"]
    df = df.merge(t10, on="ano", how="left")
    mb = pd.read_parquet(OUT_GEO / "mancha_mapbiomas_anual.parquet")
    mb = mb[mb["recorte"] == "sede"][["ano", "area_urbanizada_ha"]].rename(
        columns={"area_urbanizada_ha": "mapbiomas24_janela_ha"})
    df = df.merge(mb, on="ano", how="left")
    # qualidade do ano
    comp = pd.read_parquet(COMP_REG)
    c30 = comp[comp["produto"] == "comp30"][["ano", "n_cenas", "sensores", "n_obs_mediana", "frac_preenchida"]]
    df = df.merge(c30, on="ano", how="left")
    df["era_modelo"] = np.where(df["ano"] <= 2012, "tm_etm", "oli")
    df["validacao"] = np.select(
        [df["ano"].isin([2009, 2017, 2022]), df["ano"] < 1999],
        ["validado (fotointerpretação independente)", "sem referência independente"],
        "não validado diretamente")
    # população e densidade anual (aproximações rotuladas)
    pop = populacao()
    df = df.merge(pop[["ano", "pop_municipio", "fonte_pop", "tipo_pop", "aviso_pop", "pop_urbana",
                       "fonte_pop_urbana"]], on="ano", how="left")
    df["densidade_popurb_hab_ha"] = df["pop_urbana"] / df["area_urbana_total_ha"]
    df["densidade_popurb_ajustada_hab_ha"] = df["pop_urbana"] / (df["area_urbana_total_ha"] * df["fator_ajuste"])
    # forma: origem = centroide da sede de 1990 (núcleo histórico)
    cls90, tr = _ler_raster(MANCHA_P / "mancha30_1990.tif")
    X, Y = _centros(tr, cls90.shape)
    origem = (float(X[cls90 == 1].mean()), float(Y[cls90 == 1].mean()))
    df = df.merge(forma_anual(df["ano"].tolist(), origem), on="ano", how="left")
    return df, origem


def main_propria() -> None:
    print("Série própria 1984–2026 …")
    anual, origem = serie_anual()
    print("Setores × mancha …")
    setm = setores_mancha()
    censos = densidade_censos(anual, setm)
    per = periodos(anual, censos)
    dire = expansao_direcao(origem)

    for nome, d in (("estatisticas_mancha", anual), ("estatisticas_mancha_censos", censos),
                    ("estatisticas_mancha_periodos", per), ("expansao_direcao", dire)):
        d.to_parquet(OUT_GEO / f"{nome}.parquet", index=False)
        d.to_csv(OUT_GEO / f"{nome}.csv", index=False)

    import pyproj

    lon, lat = pyproj.Transformer.from_crs(EPSG_METRICO, 4326, always_xy=True).transform(*origem)
    cols_web = ["ano", "area_sede_ha", "area_outros_nucleos_ha", "area_urbana_total_ha",
                "area_construido_mineracao_ha", "area_loteamento_vazio_ha", "area_sede_delta_ha",
                "area_sede_var_pct", "area_sede_ajustada_ha", "area_sede_ajustada_ic95_ha", "ajuste_origem",
                "area_sede_10m_ha", "mapbiomas24_janela_ha", "pop_municipio", "fonte_pop", "aviso_pop",
                "pop_urbana", "fonte_pop_urbana", "densidade_popurb_hab_ha", "densidade_popurb_ajustada_hab_ha",
                "raio_equivalente_km", "dist_media_nucleo_km", "indice_proximidade", "centroide_desloc_km",
                "n_cenas", "sensores", "frac_preenchida", "validacao"]
    v = json.loads(VALID.read_text("utf-8"))
    web = {
        "fonte": "Classificação própria (Random Forest sobre composições Landsat TM/ETM+/OLI da estação "
                 "seca), janela da sede de Canaã dos Carajás; áreas em EPSG:31982. Ver docs/qa/E3b.md.",
        "notas": [
            "Sede = mancha contígua ao núcleo (encadeamento de 1 km); outros núcleos = vilas e "
            "manchas isoladas na janela; construído em mineração é curva separada.",
            "Área ajustada = área mapeada × (área ajustada / área mapeada) das épocas validadas "
            "(2009, 2017, 2022; Olofsson et al. 2014), interpolado entre elas e constante fora.",
            "Antes de 1999 não há referência independente para validar a mancha.",
            "População urbana entre censos é interpolação geométrica (estimativa própria); "
            "estimativas municipais do IBGE de 2001–2006 e 2011–2021 subcontaram Canaã.",
        ],
        "nucleo_historico": {"lon": round(lon, 6), "lat": round(lat, 6),
                             "definicao": "centroide da sede mapeada em 1990"},
        "serie": json.loads(anual[cols_web].round(3).to_json(orient="records")),
        "periodos": json.loads(per.round(4).to_json(orient="records")),
        "censos": json.loads(censos.round(3).to_json(orient="records")),
        "expansao_direcao": json.loads(dire.round(3).to_json(orient="records")),
        "validacao": {k: {c: r[c] for c in ("referencia", "n_pontos", "n_incertos", "acuracia_global",
                                             "acuracia_global_ic95", "usuario_urbano", "produtor_urbano",
                                             "area_mapa_urbano_ha", "area_ajustada_urbano_ha",
                                             "area_ajustada_ic95_ha")} for k, r in v.items()},
    }
    OUT_WEB.mkdir(parents=True, exist_ok=True)
    (OUT_WEB / "estatisticas_mancha.json").write_text(json.dumps(web, ensure_ascii=False, indent=1), "utf-8")
    cols_set = ["ano", "cod_setor", "situacao", "pertence", "populacao_residente", "domicilios", "area_setor_ha",
                "construido_sede_ha", "construido_outros_ha", "frac_construida", "densidade_liquida_hab_ha"]
    (OUT_WEB / "setores_mancha.json").write_text(
        json.dumps({"fonte": "IBGE, Censo 2010 e 2022 (agregados por setor, Universo) × classificação própria",
                    "setores": json.loads(setm[cols_set].round(4).to_json(orient="records"))},
                   ensure_ascii=False), "utf-8")

    print(anual[anual["ano"].isin([1984, 1990, 1994, 2000, 2004, 2010, 2016, 2022, 2026])][
        ["ano", "area_sede_ha", "area_sede_ajustada_ha", "area_sede_ajustada_ic95_ha", "ajuste_origem",
         "pop_urbana", "densidade_popurb_hab_ha", "raio_equivalente_km", "indice_proximidade",
         "centroide_desloc_km"]].round(2).to_string(index=False))
    print(censos.drop(columns=["fonte_pop_sede"]).round(2).T.to_string())
    print(per[["periodo", "rotulo", "acrescimo_ha", "ha_por_ano", "taxa_geometrica_aa_pct",
               "participacao_na_area_final_pct", "taxa_pop_aa_pct", "ods_11_3_1_razao"]].round(2).to_string(index=False))
    print(dire.pivot_table(index="periodo", columns="octante", values="participacao_pct")[OCTANTES].round(1).to_string())
    print(setm.groupby(["ano", "pertence"]).agg(n=("cod_setor", "count"), pop=("populacao_residente", "sum"),
                                               construido_ha=("construido_ha", "sum")).round(0).to_string())


if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "tudo"
    if cmd in ("mapbiomas", "tudo"):
        main_mapbiomas()
    if cmd in ("propria", "tudo"):
        main_propria()
