#!/usr/bin/env python
"""40_analise_artigo.py — desenho analítico do artigo (PLANO.md, Fase 5 passo 1; etapa E5).

Lê SOMENTE `data/processed` (agregados aprovados pelo gate) e as tabelas públicas do
IBGE/ANM já baixadas em E1. Nunca toca em `data/raw`/`data/interim`. Grava:

  data/processed/analise/*.parquet|csv   tabelas analíticas (entrada de 41_figuras.py, E6 e E7)
  artigo/tabelas/tab_XX_*.md|csv          tabelas prontas para o texto (markdown ABNT-ish)

Blocos (letras do PLANO.md, Fase 5 passo 1):
  (a) série populacional oficial + estimativas + citações de terceiros vs. marcos minerais
  (b) mancha urbana anual × população / CFEM: elasticidade área-população, densidade, ritmo
  (c) coortes de chegada dos migrantes alinhadas aos ciclos de investimento
  (d) perfil migrantes × não migrantes (razões de seletividade com erro-padrão)
  (e) inserção ocupacional (setor, posição, formalidade, extrativa)
  (f) condições domiciliares e desigualdade intraurbana por setor censitário (2010 → 2022)
  (g) comparação com Parauapebas, Pará e municípios do Sudeste Paraense (painel AMC 2000–2022)
  (h) 1991 como baseline pré-mineral (Parauapebas inclui o atual Canaã; mancha 1990/1991)
  (i) economia: PIB, VA setorial, CFEM (nominal e R$ 2022), CEMPRE

Regras de sigilo: as estimativas amostrais já saem do gate com CV/classe e faixas de n;
este script só as recombina (razões, diferenças) e propaga o erro-padrão pelo método
delta supondo independência entre células — aproximação conservadora declarada no texto.
Nenhuma contagem amostral exata é escrita.

Uso: .venv/bin/python pipeline/40_analise_artigo.py [--sem-rede]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "pipeline"))
from lib.rotulos import (CATEGORIAS, CICLOS, DIMENSOES, GEOGRAFIAS, MARCOS, SETORES_ORDEM,  # noqa: E402
                         classe_marca, fmt_num, fmt_pct, rotulo)

PROC = BASE / "data" / "processed"
OUT = PROC / "analise"
TAB = BASE / "artigo" / "tabelas"
OUT.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)

EST = pd.read_parquet(PROC / "microdados" / "estimativas.parquet")
MANCHA = pd.read_parquet(PROC / "geo" / "estatisticas_mancha.parquet").sort_values("ano")
MANCHA_CENSOS = pd.read_parquet(PROC / "geo" / "estatisticas_mancha_censos.parquet")
MANCHA_PER = pd.read_parquet(PROC / "geo" / "estatisticas_mancha_periodos.parquet")
CFEM = pd.read_parquet(PROC / "ibge" / "cfem_canaa_2004_2026.parquet")
POP_ANUAL = pd.read_parquet(PROC / "ibge" / "populacao_anual_municipio.parquet")

RESUMO: dict[str, object] = {}   # números-chave para o QA e para o texto (E6)


# ----------------------------------------------------------------------------
# utilitários
# ----------------------------------------------------------------------------
def gravar(df: pd.DataFrame, nome: str) -> None:
    df = df.reset_index(drop=True)
    df.to_parquet(OUT / f"{nome}.parquet", index=False)
    df.to_csv(OUT / f"{nome}.csv", index=False)
    print(f"  {nome}: {len(df)} linhas")


def tabela_md(df: pd.DataFrame, nome: str, titulo: str, fonte: str, nota: str | None = None) -> None:
    """Tabela em markdown (pipe) + CSV com os mesmos valores já formatados."""
    linhas = [f"**{titulo}**", ""]
    cols = list(df.columns)
    linhas.append("| " + " | ".join(cols) + " |")
    linhas.append("|" + "|".join(["---"] * len(cols)) + "|")
    for _, r in df.iterrows():
        linhas.append("| " + " | ".join("" if pd.isna(v) else str(v) for v in r.values) + " |")
    linhas.append("")
    linhas.append(f"Fonte: {fonte}")
    if nota:
        linhas.append("")
        linhas.append(f"Nota: {nota}")
    (TAB / f"{nome}.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    df.to_csv(TAB / f"{nome}.csv", index=False)


def est(geo: str, censo: int, universo: str, dim1: str | None = None, cat1: str | None = None,
        dim2: str | None = None, cat2: str | None = None, estat: str = "proporcao",
        variavel: str | None = None) -> pd.DataFrame:
    """Recorte da tabela longa de estimativas. `None` em dim/cat = filtro 'ausente'."""
    m = (EST.geografia == geo) & (EST.censo == censo) & (EST.universo == universo) & (EST.estatistica == estat)
    m &= EST.dim1.isna() if dim1 is None else (EST.dim1 == dim1)
    if cat1 is not None:
        m &= EST.cat1 == cat1
    m &= EST.dim2.isna() if dim2 is None else (EST.dim2 == dim2)
    if cat2 is not None:
        m &= EST.cat2 == cat2
    if variavel is not None:
        m &= EST.variavel == variavel
    # os totais marginais dos cruzamentos repetem as linhas simples (mesmo valor): deduplicar
    return EST[m].drop_duplicates(subset=["cat1", "cat2", "estatistica", "variavel"]).copy()


def valor(geo, censo, universo, dim1=None, cat1=None, dim2=None, cat2=None, estat="proporcao", variavel=None):
    r = est(geo, censo, universo, dim1, cat1, dim2, cat2, estat, variavel)
    if len(r) == 0:
        return np.nan, np.nan, None
    r = r.iloc[0]
    return float(r.valor), float(r.ep), r.classe_precisao


def razao(v1, ep1, v2, ep2):
    """Razão v1/v2 com erro-padrão pelo método delta (independência entre células)."""
    if not (v1 > 0 and v2 > 0):
        return np.nan, np.nan
    r = v1 / v2
    ep = r * np.sqrt((ep1 / v1) ** 2 + (ep2 / v2) ** 2)
    return r, ep


def taxa_geometrica(p0, p1, anos):
    return ((p1 / p0) ** (1.0 / anos) - 1) * 100


def ipca_anual(sem_rede: bool) -> dict[int, float]:
    """Índice IPCA de julho de cada ano 2004–2026 (t/1737, v/2266), cache em data/externo.
    Base = jul/2022 (mesma convenção de lib.deflator). Sem rede e sem cache → só nominal."""
    cache = BASE / "data" / "externo" / "ipca_anual_julho.json"
    if cache.exists():
        d = json.loads(cache.read_text())
        return {int(k): v for k, v in d.items() if k.isdigit()}
    if sem_rede:
        return {}
    import requests
    periodos = ",".join(f"{a}07" for a in range(2004, 2027))
    url = f"https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/2266/p/{periodos}"
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        out = {}
        for reg in r.json()[1:]:
            per = reg["D3C"]
            if reg["V"] not in ("...", "-", "", None):
                out[int(per[:4])] = float(reg["V"])
        cache.write_text(json.dumps({**{str(k): v for k, v in out.items()}, "_origem": url, "_variavel": "IPCA número-índice jul, base dez/1993=100"}, indent=1))
        return out
    except Exception as e:  # noqa: BLE001
        print(f"  [aviso] IPCA anual indisponível ({e}); CFEM só nominal")
        return {}


# ----------------------------------------------------------------------------
# (a) série populacional
# ----------------------------------------------------------------------------
def bloco_a() -> pd.DataFrame:
    print("(a) série populacional")
    reg = []

    def add(ano, valor, tipo, recorte, fonte, vmin=None, vmax=None, nota=None):
        reg.append(dict(ano=ano, valor=valor, valor_min=vmin, valor_max=vmax, tipo_fonte=tipo,
                        recorte=recorte, fonte=fonte, nota=nota))

    # oficiais (SIDRA, E1) — município
    for _, r in POP_ANUAL.iterrows():
        tipo = {"censo": "oficial_censo", "contagem": "oficial_contagem", "estimativa": "estimativa_ibge"}[r.fonte_pop]
        fonte = {"censo": "IBGE, Censo Demográfico (SIDRA t/202, t/9923)",
                 "contagem": "IBGE, Contagem da População 2007 (SIDRA t/793)",
                 "estimativa": "IBGE, Estimativas da população (SIDRA t/6579)"}[r.fonte_pop]
        nota = None
        if r.fonte_pop == "estimativa" and (2001 <= r.ano <= 2006 or 2011 <= r.ano <= 2021):
            nota = "estimativa ancorada no censo anterior; subestimou o crescimento real (ver 2007 e 2022)"
        add(int(r.ano), float(r.pop_municipio), tipo, "município", fonte, nota=nota)
    # urbana/rural oficiais
    t202 = pd.read_parquet(PROC / "ibge" / "t202_pop_distrito.parquet")
    for ano in (2000, 2010):
        for sit, rec in (("Urbana", "urbana"), ("Rural", "rural")):
            v = t202[(t202.Ano == str(ano)) & (t202.Sexo == "Total") & (t202["Situação do domicílio"] == sit)].valor.iloc[0]
            add(ano, float(v), "oficial_censo", rec, "IBGE, Censo Demográfico (SIDRA t/202)")
    t9923 = pd.read_parquet(PROC / "ibge" / "t9923_situacao_2022.parquet")
    for sit, rec in (("Urbana", "urbana"), ("Rural", "rural")):
        v = t9923[t9923["Situação do domicílio"] == sit].valor.iloc[0]
        add(2022, float(v), "oficial_censo", rec, "IBGE, Censo Demográfico 2022 (SIDRA t/9923)")
    # população da sede (E3c: soma dos setores urbanos da sede)
    for _, r in MANCHA_CENSOS.iterrows():
        add(int(r.ano), float(r.pop_sede), "oficial_censo" if r.ano == 2000 else "derivado_setores", "sede",
            r.fonte_pop_sede)
    # Parauapebas 1991 (inclui o atual Canaã)
    add(1991, 53335, "oficial_censo", "Parauapebas (inclui o atual Canaã)", "IBGE, Censo 1991 (SIDRA t/200)",
        nota="Canaã só é município em 1994; em 1991 era localidade de Parauapebas")
    # citações de terceiros (PLANO.md, Fase 1b; verificadas em 09/09/2026)
    add(1996, 11139, "citacao_terceiro", "município", "CETEM (2011, Tab. 3) e Prefeitura; SIDRA t/305 vazio para Canaã",
        nota="aritmeticamente coerente com Parauapebas 1996 (74.702), mas não recuperável no SIDRA")
    add(2005, 20474, "citacao_terceiro", "município", "Censo municipal 2005 (Diagonal Urbana) apud PDP 2007, Tab. 1",
        nota="14.305 urbanos / 6.169 rurais")
    add(2005, 14305, "citacao_terceiro", "urbana", "PDP 2007, Tab. 1–2 (censo municipal 2005)")
    # estimativa própria 1984/85: famílias assentadas × moradores por domicílio (dois cenários de escopo)
    mor_min, mor_max = 4.76, 5.5   # Parauapebas 1991 (t/156) como piso; 5,0–5,5 como teto (PLANO.md)
    add(1985, None, "estimativa_propria", "assentamento (CEDERE II+III)", "1.551 famílias (PDP 2007 p. 55; IBGE; CETEM) × 4,76–5,5 mor./dom.",
        vmin=round(1551 * mor_min), vmax=round(1551 * mor_max),
        nota="cenário amplo: as 1.551 famílias correspondem aos núcleos que hoje são Canaã")
    add(1985, None, "estimativa_propria", "assentamento (só CEDERE II)", "1.551 − ~550 famílias do CEDERE I (Carmo 2023, Tab. 1) × 4,76–5,5 mor./dom.",
        vmin=round(1001 * mor_min), vmax=round(1001 * mor_max),
        nota="cenário restrito: exclui o CEDERE I (hoje vila de Parauapebas)")
    add(1985, None, "estimativa_propria", "assentamento (títulos definitivos)", "816 famílias tituladas até 1985 (IBGE Histórico; PDP 2007) × 4,76–5,5 mor./dom.",
        vmin=round(816 * mor_min), vmax=round(816 * mor_max))
    serie = pd.DataFrame(reg).sort_values(["ano", "recorte"])
    gravar(serie, "serie_populacao")

    # taxas geométricas entre âncoras oficiais
    anc = serie[(serie.recorte == "município") & serie.tipo_fonte.isin(["oficial_censo", "oficial_contagem"])].sort_values("ano")
    taxas = []
    for (a0, p0), (a1, p1) in zip(anc[["ano", "valor"]].values[:-1], anc[["ano", "valor"]].values[1:]):
        taxas.append(dict(periodo=f"{int(a0)}–{int(a1)}", pop_inicio=p0, pop_fim=p1, anos=int(a1 - a0),
                          taxa_geometrica_aa_pct=taxa_geometrica(p0, p1, a1 - a0),
                          acrescimo=p1 - p0, acrescimo_por_ano=(p1 - p0) / (a1 - a0)))
    # intervalos censitários (sem a Contagem 2007 no meio)
    cen = anc[anc.tipo_fonte == "oficial_censo"].sort_values("ano")
    for (a0, p0), (a1, p1) in zip(cen[["ano", "valor"]].values[:-1], cen[["ano", "valor"]].values[1:]):
        if not any(t["periodo"] == f"{int(a0)}–{int(a1)}" for t in taxas):
            taxas.append(dict(periodo=f"{int(a0)}–{int(a1)}", pop_inicio=p0, pop_fim=p1, anos=int(a1 - a0),
                              taxa_geometrica_aa_pct=taxa_geometrica(p0, p1, a1 - a0),
                              acrescimo=p1 - p0, acrescimo_por_ano=(p1 - p0) / (a1 - a0)))
    # 1996 (citação) → 2000 e 2022 → 2026 (estimativa)
    taxas.append(dict(periodo="1996–2000 (1996 = citação CETEM)", pop_inicio=11139, pop_fim=10922, anos=4,
                      taxa_geometrica_aa_pct=taxa_geometrica(11139, 10922, 4), acrescimo=-217, acrescimo_por_ano=-217 / 4))
    taxas.append(dict(periodo="2022–2026 (2026 = estimativa IBGE)", pop_inicio=77079, pop_fim=92311, anos=4,
                      taxa_geometrica_aa_pct=taxa_geometrica(77079, 92311, 4), acrescimo=92311 - 77079,
                      acrescimo_por_ano=(92311 - 77079) / 4))
    taxas = pd.DataFrame(taxas)
    gravar(taxas, "populacao_taxas")
    RESUMO["taxa_2010_2022_aa"] = float(taxas.loc[taxas.periodo == "2010–2022", "taxa_geometrica_aa_pct"].iloc[0])
    RESUMO["taxa_2000_2010_aa"] = float(taxas.loc[taxas.periodo == "2000–2010", "taxa_geometrica_aa_pct"].iloc[0])

    tab = taxas.copy()
    tab["pop_inicio"] = tab.pop_inicio.map(fmt_num)
    tab["pop_fim"] = tab.pop_fim.map(fmt_num)
    tab["taxa_geometrica_aa_pct"] = tab.taxa_geometrica_aa_pct.map(lambda v: fmt_num(v, 1))
    tab["acrescimo_por_ano"] = tab.acrescimo_por_ano.map(fmt_num)
    tab = tab[["periodo", "pop_inicio", "pop_fim", "taxa_geometrica_aa_pct", "acrescimo_por_ano"]]
    tab.columns = ["Período", "População inicial", "População final", "Taxa geométrica (% a.a.)", "Acréscimo médio (hab./ano)"]
    tabela_md(tab, "tab_01_populacao_taxas", "Tabela 1 — População residente de Canaã dos Carajás e taxas geométricas de crescimento, 1996–2026",
              "IBGE (Censos 2000, 2010 e 2022; Contagem 2007; Estimativas 2026); CETEM (2011) para 1996.",
              "O SIDRA não publica a Contagem 1996 para Canaã (município instalado em 1997); o valor de 1996 é citação secundária.")
    return serie


# ----------------------------------------------------------------------------
# (b) mancha × população × CFEM
# ----------------------------------------------------------------------------
def bloco_b(sem_rede: bool) -> None:
    print("(b) mancha urbana × população × CFEM")
    m = MANCHA.copy()
    # CFEM em R$ de jul/2022
    ipca = ipca_anual(sem_rede)
    cf = CFEM.rename(columns={"cfem_distribuido_r": "cfem_nominal_r"})[["ano", "cfem_nominal_r"]].copy()
    if ipca and 2022 in ipca:
        cf["cfem_r2022"] = [v * ipca[2022] / ipca[a] if a in ipca else np.nan for a, v in zip(cf.ano, cf.cfem_nominal_r)]
    else:
        cf["cfem_r2022"] = np.nan
    cf["cfem_2026_parcial"] = cf.ano == 2026
    m = m.merge(cf, on="ano", how="left")
    m["cfem_per_capita_r2022"] = m.cfem_r2022 / m.pop_municipio
    # variação anual da população (estimativas/censos) — só para leitura, não para regressão
    m["pop_municipio_delta"] = m.pop_municipio.diff()
    anual = m[["ano", "area_sede_ha", "area_sede_ajustada_ha", "area_sede_ajustada_ic95_ha", "area_sede_delta_ha",
               "area_sede_var_pct", "area_urbana_total_ha", "area_construido_mineracao_ha", "pop_municipio",
               "fonte_pop", "tipo_pop", "pop_urbana", "fonte_pop_urbana", "densidade_popurb_ajustada_hab_ha",
               "cfem_nominal_r", "cfem_r2022", "cfem_per_capita_r2022", "indice_proximidade", "centroide_desloc_km",
               "ajuste_origem"]].copy()
    gravar(anual, "mancha_populacao_anual")

    # elasticidade área-população nos intervalos censitários (sede) e municipal
    el = []
    c = MANCHA_CENSOS.sort_values("ano")
    for (a0, r0), (a1, r1) in zip(c.iterrows(), list(c.iterrows())[1:]):
        for col, nome in (("area_sede_ha", "mapeada"), ("area_sede_ajustada_ha", "ajustada")):
            dA = np.log(r1[col] / r0[col]); dP = np.log(r1.pop_sede / r0.pop_sede)
            el.append(dict(periodo=f"{int(r0.ano)}–{int(r1.ano)}", area=nome, area_inicio_ha=r0[col], area_fim_ha=r1[col],
                           pop_inicio=r0.pop_sede, pop_fim=r1.pop_sede, elasticidade_area_pop=dA / dP,
                           taxa_area_aa_pct=taxa_geometrica(r0[col], r1[col], r1.ano - r0.ano),
                           taxa_pop_aa_pct=taxa_geometrica(r0.pop_sede, r1.pop_sede, r1.ano - r0.ano),
                           densidade_inicio_hab_ha=r0.pop_sede / r0[col], densidade_fim_hab_ha=r1.pop_sede / r1[col]))
    # série inteira 2000–2022
    r0, r1 = c.iloc[0], c.iloc[-1]
    for col, nome in (("area_sede_ha", "mapeada"), ("area_sede_ajustada_ha", "ajustada")):
        el.append(dict(periodo="2000–2022", area=nome, area_inicio_ha=r0[col], area_fim_ha=r1[col], pop_inicio=r0.pop_sede,
                       pop_fim=r1.pop_sede, elasticidade_area_pop=np.log(r1[col] / r0[col]) / np.log(r1.pop_sede / r0.pop_sede),
                       taxa_area_aa_pct=taxa_geometrica(r0[col], r1[col], 22), taxa_pop_aa_pct=taxa_geometrica(r0.pop_sede, r1.pop_sede, 22),
                       densidade_inicio_hab_ha=r0.pop_sede / r0[col], densidade_fim_hab_ha=r1.pop_sede / r1[col]))
    el = pd.DataFrame(el)
    gravar(el, "elasticidade_area_populacao")
    RESUMO["elasticidade_2000_2010_ajustada"] = float(el[(el.periodo == "2000–2010") & (el.area == "ajustada")].elasticidade_area_pop.iloc[0])
    RESUMO["elasticidade_2010_2022_ajustada"] = float(el[(el.periodo == "2010–2022") & (el.area == "ajustada")].elasticidade_area_pop.iloc[0])

    # ritmo anual da mancha × CFEM (defasagens) e × variação populacional estimada — descritivo
    s = m[(m.ano >= 2004) & (m.ano <= 2025)].copy()
    corr = []
    for lag in (0, 1, 2, 3):
        x = s.cfem_r2022.shift(lag) if s.cfem_r2022.notna().any() else s.cfem_nominal_r.shift(lag)
        y = s.area_sede_delta_ha
        ok = x.notna() & y.notna()
        corr.append(dict(variavel="CFEM (R$ 2022)" if s.cfem_r2022.notna().any() else "CFEM (nominal)", defasagem_anos=lag,
                         n=int(ok.sum()), pearson=float(np.corrcoef(x[ok], y[ok])[0, 1]),
                         spearman=float(pd.Series(x[ok]).rank().corr(pd.Series(y[ok]).rank()))))
    # área acrescida por período mineral × CFEM acumulada no período
    per = []
    for ini, fim, rot in ((2004, 2016, "Sossego → S11D"), (2016, 2026, "S11D → 2026"), (2004, 2010, "2004–2010"), (2010, 2016, "2010–2016"),
                          (2016, 2022, "2016–2022"), (2022, 2026, "2022–2026")):
        w = m[(m.ano > ini) & (m.ano <= fim)]
        per.append(dict(periodo=f"{ini}–{fim}", rotulo=rot, area_acrescida_ha=float(w.area_sede_delta_ha.sum()),
                        ha_por_ano=float(w.area_sede_delta_ha.sum() / (fim - ini)),
                        cfem_acumulada_r2022=float(w.cfem_r2022.sum()) if w.cfem_r2022.notna().any() else np.nan,
                        cfem_acumulada_nominal=float(w.cfem_nominal_r.sum()),
                        cfem_media_anual_r2022=float(w.cfem_r2022.mean()) if w.cfem_r2022.notna().any() else np.nan))
    per = pd.DataFrame(per)
    gravar(pd.DataFrame(corr), "mancha_cfem_correlacao")
    gravar(per, "mancha_cfem_periodos")
    pico = m.loc[m.area_sede_delta_ha.idxmax()]
    RESUMO["pico_area_delta"] = dict(ano=int(pico.ano), ha=float(pico.area_sede_delta_ha))
    RESUMO["cfem_pico"] = dict(ano=int(cf.loc[cf.cfem_nominal_r.idxmax(), "ano"]), nominal=float(cf.cfem_nominal_r.max()))
    RESUMO["corr_cfem_area"] = corr

    # tabela: densidade e forma nos anos censitários (E3c) + elasticidade
    d = MANCHA_CENSOS.copy()
    tab = pd.DataFrame({
        "Ano": d.ano.astype(int),
        "População da sede": d.pop_sede.map(fmt_num),
        "Área mapeada (ha)": d.area_sede_ha.map(fmt_num),
        "Área ajustada (ha) ± IC 95 %": [f"{fmt_num(a)} ± {fmt_num(i)}" for a, i in zip(d.area_sede_ajustada_ha, d.area_sede_ajustada_ic95_ha)],
        "Densidade ajustada (hab./ha)": d.densidade_ajustada_hab_ha.map(lambda v: fmt_num(v, 1)),
        "Domicílios/ha (ajust.)": d.dom_por_ha_ajustado.map(lambda v: fmt_num(v, 1)),
        "Moradores/domicílio": d.moradores_por_domicilio.map(lambda v: fmt_num(v, 2)),
    })
    tabela_md(tab, "tab_02_densidade_censos", "Tabela 2 — População, área construída e densidade da sede de Canaã dos Carajás nos anos censitários",
              "Elaboração própria: série própria Landsat 30 m (E3b), validada com CBERS (Olofsson et al., 2014); população dos setores urbanos do Universo (IBGE).",
              "Área ajustada = área mapeada corrigida pela acurácia (usuário/produtor) das épocas validadas (2009, 2017, 2022); em 2000 o fator é extrapolado.")
    tab2 = el[el.area == "ajustada"].copy()
    tab2 = pd.DataFrame({"Período": tab2.periodo, "Taxa da área (% a.a.)": tab2.taxa_area_aa_pct.map(lambda v: fmt_num(v, 1)),
                         "Taxa da população (% a.a.)": tab2.taxa_pop_aa_pct.map(lambda v: fmt_num(v, 1)),
                         "Elasticidade área-população": tab2.elasticidade_area_pop.map(lambda v: fmt_num(v, 2)),
                         "Densidade inicial → final (hab./ha)": [f"{fmt_num(a, 1)} → {fmt_num(b, 1)}" for a, b in zip(tab2.densidade_inicio_hab_ha, tab2.densidade_fim_hab_ha)]})
    tabela_md(tab2, "tab_03_elasticidade", "Tabela 3 — Elasticidade área construída–população da sede (área ajustada)",
              "Elaboração própria (E3c, E5).", "Elasticidade = Δln(área) / Δln(população); > 1 indica espraiamento (área cresce mais que a população), < 1 adensamento.")


# ----------------------------------------------------------------------------
# (c) coortes de chegada
# ----------------------------------------------------------------------------
def bloco_c() -> None:
    print("(c) coortes de chegada")
    regs = []
    for geo in ("canaa_municipio", "canaa_sede", "parauapebas_municipio"):
        for censo in (2000, 2010, 2022):
            for estat in ("contagem", "proporcao"):
                r = est(geo, censo, "chegados", "periodo_chegada", estat=estat)
                for _, x in r.iterrows():
                    regs.append(dict(geografia=geo, censo=censo, estatistica=estat, periodo=x.cat1, rotulo=rotulo(x.cat1),
                                     valor=x.valor, ep=x.ep, cv=x.cv, classe=x.classe_precisao, n_faixa=x.n_faixa))
    co = pd.DataFrame(regs)
    gravar(co, "coortes_chegada")
    # ano a ano (2022 e 2010, município) — para a figura de pulsos
    an = []
    for censo in (2010, 2022):
        r = est("canaa_municipio", censo, "chegados", "ano_chegada", estat="contagem")
        for _, x in r.iterrows():
            an.append(dict(censo=censo, ano_chegada=x.cat1, valor=x.valor, ep=x.ep, cv=x.cv, classe=x.classe_precisao, n_faixa=x.n_faixa))
    an = pd.DataFrame(an)
    an["ano_num"] = pd.to_numeric(an.ano_chegada, errors="coerce")
    gravar(an, "coortes_chegada_anual")
    # chegados por ano no período de chegada (intensidade), 2022
    c22 = co[(co.geografia == "canaa_municipio") & (co.censo == 2022) & (co.estatistica == "contagem")].copy()
    dur = {"ate_1984": np.nan, "1985_1994": 10, "1995_2001": 7, "2002_2004": 3, "2005_2012": 8, "2013_2016": 4, "2017_2022": 5.6}
    c22["anos"] = c22.periodo.map(dur)
    c22["chegados_por_ano"] = c22.valor / c22.anos
    tot = c22.valor.sum()
    RESUMO["chegados_2022_total"] = float(tot)
    RESUMO["chegados_2022_pos_2013_pct"] = float(c22[c22.periodo.isin(["2013_2016", "2017_2022"])].valor.sum() / tot * 100)
    tab = pd.DataFrame({"Período de chegada": c22.rotulo,
                        "Residentes em 2022 (arredondado)": c22.valor.map(fmt_num),
                        "% dos chegados": (c22.valor / tot * 100).map(lambda v: fmt_num(v, 1)),
                        "Chegados por ano": c22.chegados_por_ano.map(lambda v: fmt_num(v) if v == v else "—"),
                        "CV (%)": c22.cv.map(lambda v: fmt_num(v, 1)) + c22.classe.map(classe_marca)})
    tabela_md(tab, "tab_04_coortes_chegada", "Tabela 4 — Residentes de Canaã dos Carajás em 2022 não naturais do município, por período de chegada",
              "Elaboração própria a partir dos microdados da amostra do Censo 2022 (IBGE; acesso controlado); estimativas aprovadas pelo controle de revelação.",
              "Sobreviventes em 2022 de cada coorte (não o fluxo original); contagens arredondadas a 10. * CV 15–30 %; ** CV > 30 %.")


# ----------------------------------------------------------------------------
# (d) perfil migrantes × não migrantes
# ----------------------------------------------------------------------------
PERFIL_DIMS = [("pessoas_5mais", "sexo"), ("pessoas_5mais", "grupo_etario"), ("pessoas_5mais", "cor_raca"),
               ("pessoas_25mais", "nivel_instrucao"), ("pessoas_10mais", "ocupado"), ("ocupados", "posicao"),
               ("ocupados", "formal"), ("ocupados", "setor"), ("ocupados", "extrativa_mineral"),
               ("pessoas_10mais", "renda_sm_faixa"), ("ocupados", "trabalha_outro_mun"), ("pessoas_5mais", "naturalidade")]


def bloco_d() -> None:
    print("(d) perfil migrantes × não migrantes")
    regs = []
    for geo in ("canaa_municipio", "canaa_sede", "parauapebas_municipio", "pa"):
        for censo in (1991, 2000, 2010, 2022):
            for universo, dim in PERFIL_DIMS:
                r = est(geo, censo, universo, "migrante", dim2=dim)
                if len(r) == 0:
                    continue
                mig = r[r.cat1 == "migrante"].set_index("cat2")
                nao = r[r.cat1 == "nao_migrante"].set_index("cat2")
                for cat in sorted(set(mig.index) | set(nao.index)):
                    vm, em, cm = (mig.loc[cat, ["valor", "ep", "classe_precisao"]] if cat in mig.index else (np.nan, np.nan, None))
                    vn, en, cn = (nao.loc[cat, ["valor", "ep", "classe_precisao"]] if cat in nao.index else (np.nan, np.nan, None))
                    rz, erz = razao(vm, em, vn, en) if (vm == vm and vn == vn) else (np.nan, np.nan)
                    dif = vm - vn if (vm == vm and vn == vn) else np.nan
                    edif = np.sqrt(em ** 2 + en ** 2) if (vm == vm and vn == vn) else np.nan
                    regs.append(dict(geografia=geo, censo=censo, universo=universo, dimensao=dim, categoria=cat, rotulo=rotulo(cat, dim),
                                     p_migrante=vm, ep_migrante=em, classe_migrante=cm, p_nao_migrante=vn, ep_nao_migrante=en,
                                     classe_nao_migrante=cn, razao_seletividade=rz, ep_razao=erz, diferenca_pp=dif, ep_diferenca=edif,
                                     significativo_95=(abs(dif) > 1.96 * edif) if edif == edif else None))
    # médias (idade, renda)
    for geo in ("canaa_municipio", "canaa_sede", "parauapebas_municipio", "pa"):
        for censo in (1991, 2000, 2010, 2022):
            for var, uni in (("idade", "pessoas"), ("renda_total_r2022", "com_rendimento"), ("renda_trabalho_r2022", "ocupados")):
                r = est(geo, censo, uni, "migrante", estat="media", variavel=var)
                if len(r) < 2:
                    continue
                vm, em, cm = r[r.cat1 == "migrante"].iloc[0][["valor", "ep", "classe_precisao"]]
                vn, en, cn = r[r.cat1 == "nao_migrante"].iloc[0][["valor", "ep", "classe_precisao"]]
                rz, erz = razao(vm, em, vn, en)
                regs.append(dict(geografia=geo, censo=censo, universo=uni, dimensao=f"media_{var}", categoria="media", rotulo=f"Média de {var}",
                                 p_migrante=vm, ep_migrante=em, classe_migrante=cm, p_nao_migrante=vn, ep_nao_migrante=en, classe_nao_migrante=cn,
                                 razao_seletividade=rz, ep_razao=erz, diferenca_pp=vm - vn, ep_diferenca=np.sqrt(em ** 2 + en ** 2),
                                 significativo_95=abs(vm - vn) > 1.96 * np.sqrt(em ** 2 + en ** 2)))
    pf = pd.DataFrame(regs)
    gravar(pf, "perfil_migrantes")

    # perfil por período de chegada (2022): setor, naturalidade, origem
    regs = []
    for censo in (2010, 2022):
        for uni, dim2 in (("chegados", "setor"), ("chegados", "naturalidade"), ("migrantes_5anos", "origem_regiao")):
            r = est("canaa_municipio", censo, uni, "periodo_chegada", dim2=dim2)
            for _, x in r.iterrows():
                regs.append(dict(censo=censo, universo=uni, periodo=x.cat1, periodo_rotulo=rotulo(x.cat1), dimensao=dim2, categoria=x.cat2,
                                 rotulo=rotulo(x.cat2, dim2), valor=x.valor, ep=x.ep, cv=x.cv, classe=x.classe_precisao, n_faixa=x.n_faixa))
    gravar(pd.DataFrame(regs), "perfil_por_periodo_chegada")

    # tabela síntese 2022 (município) — seletividade nas dimensões-chave
    sel = pf[(pf.geografia == "canaa_municipio") & (pf.censo == 2022)]
    chave = [("nivel_instrucao", "superior_completo"), ("nivel_instrucao", "sem_instrucao_fund_incompleto"), ("ocupado", "sim"),
             ("formal", "sim"), ("setor", "extrativa_mineral"), ("setor", "construcao"), ("setor", "servicos"), ("setor", "adm_publica_educacao_saude"),
             ("posicao", "empregado_com_carteira"), ("posicao", "conta_propria"), ("renda_sm_faixa", "mais_de_10"), ("renda_sm_faixa", "sem_rendimento"),
             ("grupo_etario", "25_39"), ("grupo_etario", "00_14"), ("sexo", "M"), ("cor_raca", "branca"), ("trabalha_outro_mun", "sim")]
    linhas = []
    for dim, cat in chave:
        r = sel[(sel.dimensao == dim) & (sel.categoria == cat)]
        if len(r) == 0:
            continue
        r = r.iloc[0]
        rot_cat = "5–14 (universo de 5 anos ou mais)" if (dim == "grupo_etario" and cat == "00_14") else r.rotulo
        linhas.append({"Dimensão": DIMENSOES[dim], "Categoria": rot_cat,
                       "Migrantes (%)": fmt_num(r.p_migrante, 1) + classe_marca(r.classe_migrante),
                       "Não migrantes (%)": fmt_num(r.p_nao_migrante, 1) + classe_marca(r.classe_nao_migrante),
                       "Razão de seletividade": fmt_num(r.razao_seletividade, 2), "EP da razão": fmt_num(r.ep_razao, 2),
                       "Diferença signif. (95 %)": "sim" if r.significativo_95 else "não"})
    for var, rot in (("media_idade", "Idade média (anos)"), ("media_renda_trabalho_r2022", "Renda média do trabalho (R$ jul/2022)")):
        r = sel[sel.dimensao == var]
        if len(r):
            r = r.iloc[0]
            linhas.append({"Dimensão": rot, "Categoria": "—", "Migrantes (%)": fmt_num(r.p_migrante, 1 if "idade" in var else 0),
                           "Não migrantes (%)": fmt_num(r.p_nao_migrante, 1 if "idade" in var else 0),
                           "Razão de seletividade": fmt_num(r.razao_seletividade, 2), "EP da razão": fmt_num(r.ep_razao, 2),
                           "Diferença signif. (95 %)": "sim" if r.significativo_95 else "não"})
    tabela_md(pd.DataFrame(linhas), "tab_05_seletividade_2022",
              "Tabela 5 — Perfil de migrantes de data fixa (chegados em 2017–2022) e não migrantes, Canaã dos Carajás, 2022",
              "Elaboração própria a partir dos microdados da amostra do Censo 2022 (IBGE; acesso controlado).",
              "Razão de seletividade = proporção entre migrantes ÷ proporção entre não migrantes; erro-padrão pelo método delta (bootstrap de domicílios, 200 réplicas), supondo independência entre grupos. * CV 15–30 %; ** CV > 30 %.")


# ----------------------------------------------------------------------------
# (e) inserção ocupacional
# ----------------------------------------------------------------------------
def bloco_e() -> None:
    print("(e) inserção ocupacional")
    regs = []
    for geo in GEOGRAFIAS:
        for censo in (1991, 2000, 2010, 2022):
            for dim in ("setor", "posicao", "formal", "extrativa_mineral"):
                r = est(geo, censo, "ocupados", dim)
                for _, x in r.iterrows():
                    regs.append(dict(geografia=geo, censo=censo, dimensao=dim, categoria=x.cat1, rotulo=rotulo(x.cat1, dim), valor=x.valor,
                                     ep=x.ep, cv=x.cv, classe=x.classe_precisao, n_faixa=x.n_faixa))
            r = est(geo, censo, "pessoas_10mais", "ocupado")
            for _, x in r.iterrows():
                regs.append(dict(geografia=geo, censo=censo, dimensao="ocupado", categoria=x.cat1, rotulo=rotulo(x.cat1), valor=x.valor,
                                 ep=x.ep, cv=x.cv, classe=x.classe_precisao, n_faixa=x.n_faixa))
            for var, uni in (("renda_trabalho_r2022", "ocupados"),):
                for estat in ("media", "mediana"):
                    r = est(geo, censo, uni, estat=estat, variavel=var)
                    for _, x in r.iterrows():
                        regs.append(dict(geografia=geo, censo=censo, dimensao=f"{estat}_{var}", categoria="total", rotulo=f"{estat} {var}",
                                         valor=x.valor, ep=x.ep, cv=x.cv, classe=x.classe_precisao, n_faixa=x.n_faixa))
                r = est(geo, censo, uni, "setor", estat="media", variavel=var)
                for _, x in r.iterrows():
                    regs.append(dict(geografia=geo, censo=censo, dimensao=f"media_{var}_setor", categoria=x.cat1, rotulo=rotulo(x.cat1, "setor"),
                                     valor=x.valor, ep=x.ep, cv=x.cv, classe=x.classe_precisao, n_faixa=x.n_faixa))
    oc = pd.DataFrame(regs)
    gravar(oc, "insercao_ocupacional")
    # setor × posição (formalidade por setor), Canaã 2010/2022
    regs = []
    for censo in (2000, 2010, 2022):
        for dim2 in ("posicao", "sexo"):
            r = est("canaa_municipio", censo, "ocupados", "setor", dim2=dim2)
            for _, x in r.iterrows():
                regs.append(dict(censo=censo, setor=x.cat1, setor_rotulo=rotulo(x.cat1, "setor"), dimensao=dim2, categoria=x.cat2,
                                 rotulo=rotulo(x.cat2, dim2), valor=x.valor, ep=x.ep, cv=x.cv, classe=x.classe_precisao, n_faixa=x.n_faixa))
        r = est("canaa_municipio", censo, "ocupados", "extrativa_mineral", dim2="nivel_instrucao")
        for _, x in r.iterrows():
            regs.append(dict(censo=censo, setor="extrativa_mineral" if x.cat1 == "sim" else "demais_setores", setor_rotulo="Extrativa mineral" if x.cat1 == "sim" else "Demais setores",
                             dimensao="nivel_instrucao", categoria=x.cat2, rotulo=rotulo(x.cat2, "nivel_instrucao"), valor=x.valor, ep=x.ep, cv=x.cv,
                             classe=x.classe_precisao, n_faixa=x.n_faixa))
    gravar(pd.DataFrame(regs), "setor_cruzamentos")

    # tabela: setor de atividade por censo, Canaã município vs Parauapebas vs Pará
    linhas = []
    for cat in SETORES_ORDEM:
        row = {"Setor": rotulo(cat, "setor")}
        for geo, gr in (("canaa_municipio", "Canaã"), ("parauapebas_municipio", "Parauapebas"), ("pa", "Pará")):
            for censo in (2000, 2010, 2022):
                r = oc[(oc.geografia == geo) & (oc.censo == censo) & (oc.dimensao == "setor") & (oc.categoria == cat)]
                row[f"{gr} {censo}"] = (fmt_num(r.valor.iloc[0], 1) + classe_marca(r.classe.iloc[0])) if len(r) else "—"
        linhas.append(row)
    # linha 'outros' (fusões) por coluna
    row = {"Setor": "Outros (categorias fundidas pelo sigilo)"}
    for geo, gr in (("canaa_municipio", "Canaã"), ("parauapebas_municipio", "Parauapebas"), ("pa", "Pará")):
        for censo in (2000, 2010, 2022):
            r = oc[(oc.geografia == geo) & (oc.censo == censo) & (oc.dimensao == "setor") & oc.categoria.str.startswith("outros:")]
            row[f"{gr} {censo}"] = fmt_num(r.valor.sum(), 1) if len(r) else "—"
    linhas.append(row)
    for dim, cat, rot in (("formal", "sim", "Ocupados com vínculo formal (%)"), ("posicao", "empregado_com_carteira", "Empregados com carteira (%)"),
                          ("posicao", "conta_propria", "Conta própria (%)"), ("ocupado", "sim", "Taxa de ocupação, 10 anos ou mais (%)")):
        row = {"Setor": rot}
        for geo, gr in (("canaa_municipio", "Canaã"), ("parauapebas_municipio", "Parauapebas"), ("pa", "Pará")):
            for censo in (2000, 2010, 2022):
                r = oc[(oc.geografia == geo) & (oc.censo == censo) & (oc.dimensao == dim) & (oc.categoria == cat)]
                row[f"{gr} {censo}"] = (fmt_num(r.valor.iloc[0], 1) + classe_marca(r.classe.iloc[0])) if len(r) else "—"
        linhas.append(row)
    row = {"Setor": "Renda média do trabalho (R$ jul/2022)"}
    for geo, gr in (("canaa_municipio", "Canaã"), ("parauapebas_municipio", "Parauapebas"), ("pa", "Pará")):
        for censo in (2000, 2010, 2022):
            r = oc[(oc.geografia == geo) & (oc.censo == censo) & (oc.dimensao == "media_renda_trabalho_r2022")]
            row[f"{gr} {censo}"] = fmt_num(r.valor.iloc[0]) if len(r) else "—"
    linhas.append(row)
    tabela_md(pd.DataFrame(linhas), "tab_06_insercao_ocupacional",
              "Tabela 6 — Ocupados por setor de atividade e indicadores de inserção, Canaã dos Carajás, Parauapebas e Pará, 2000–2022 (%)",
              "Elaboração própria a partir dos microdados da amostra dos Censos 2000, 2010 e 2022 (IBGE).",
              "Setores harmonizados (CNAE-Dom 1.0/2.0 e seção CNAE 2022). Categorias com n insuficiente foram fundidas em 'Outros' pelo controle de revelação. * CV 15–30 %; ** CV > 30 %.")
    r22 = oc[(oc.geografia == "canaa_municipio") & (oc.dimensao == "setor")]
    RESUMO["setor_extrativa_canaa"] = {int(c): float(r22[(r22.censo == c) & (r22.categoria == "extrativa_mineral")].valor.iloc[0])
                                       for c in (2010, 2022) if len(r22[(r22.censo == c) & (r22.categoria == "extrativa_mineral")])}


# ----------------------------------------------------------------------------
# (f) condições domiciliares e desigualdade intraurbana
# ----------------------------------------------------------------------------
def bloco_f() -> None:
    print("(f) condições domiciliares e desigualdade intraurbana")
    regs = []
    dims = ["adequacao", "agua_rede", "esgoto_adequado", "lixo_coletado", "energia", "internet", "condicao_ocupacao", "tipo_domicilio",
            "densidade_faixa", "renda_dom_pc_faixa"]
    for geo in GEOGRAFIAS:
        for censo in (1991, 2000, 2010, 2022):
            for dim in dims:
                r = est(geo, censo, "domicilios", dim)
                for _, x in r.iterrows():
                    regs.append(dict(geografia=geo, censo=censo, grupo="todos", dimensao=dim, categoria=x.cat1, rotulo=rotulo(x.cat1, dim), valor=x.valor,
                                     ep=x.ep, cv=x.cv, classe=x.classe_precisao, n_faixa=x.n_dom_faixa))
                r = est(geo, censo, "domicilios", "tem_migrante_recente", dim2=dim)
                for _, x in r.iterrows():
                    regs.append(dict(geografia=geo, censo=censo, grupo="com_migrante_recente" if x.cat1 == "sim" else "sem_migrante_recente", dimensao=dim,
                                     categoria=x.cat2, rotulo=rotulo(x.cat2, dim), valor=x.valor, ep=x.ep, cv=x.cv, classe=x.classe_precisao, n_faixa=x.n_dom_faixa))
            for var in ("renda_dom_pc_r2022", "densidade_dormitorio", "moradores"):
                r = est(geo, censo, "domicilios", estat="media", variavel=var)
                for _, x in r.iterrows():
                    regs.append(dict(geografia=geo, censo=censo, grupo="todos", dimensao=f"media_{var}", categoria="media", rotulo=var, valor=x.valor, ep=x.ep,
                                     cv=x.cv, classe=x.classe_precisao, n_faixa=x.n_dom_faixa))
                r = est(geo, censo, "domicilios", "tem_migrante_recente", estat="media", variavel=var)
                for _, x in r.iterrows():
                    regs.append(dict(geografia=geo, censo=censo, grupo="com_migrante_recente" if x.cat1 == "sim" else "sem_migrante_recente",
                                     dimensao=f"media_{var}", categoria="media", rotulo=var, valor=x.valor, ep=x.ep, cv=x.cv, classe=x.classe_precisao, n_faixa=x.n_dom_faixa))
    dom = pd.DataFrame(regs)
    gravar(dom, "condicoes_domiciliares")

    # tabela 7: condições domiciliares por censo e por presença de migrante recente (Canaã município)
    itens = [("agua_rede", "sim", "Água da rede geral"), ("esgoto_adequado", "sim", "Esgoto por rede ou fossa séptica"), ("lixo_coletado", "sim", "Lixo coletado"),
             ("energia", "sim", "Energia elétrica"), ("internet", "sim", "Internet no domicílio"), ("adequacao", "adequada", "Adequado (água + esgoto + lixo)"),
             ("condicao_ocupacao", "alugado", "Alugado"), ("condicao_ocupacao", "cedido_empregador", "Cedido pelo empregador"),
             ("densidade_faixa", "mais_de_3", "Mais de 3 moradores por dormitório"), ("tipo_domicilio", "apartamento", "Apartamento")]
    linhas = []
    for dim, cat, rot in itens:
        row = {"Indicador": rot}
        for censo in (2000, 2010, 2022):
            for grupo, gr in (("com_migrante_recente", "c/ migr."), ("sem_migrante_recente", "s/ migr.")):
                r = dom[(dom.geografia == "canaa_municipio") & (dom.censo == censo) & (dom.grupo == grupo) & (dom.dimensao == dim) & (dom.categoria == cat)]
                row[f"{censo} {gr}"] = (fmt_num(r.valor.iloc[0], 1) + classe_marca(r.classe.iloc[0])) if len(r) else "—"
        linhas.append(row)
    for var, rot, casas in (("media_renda_dom_pc_r2022", "Renda domiciliar per capita média (R$ jul/2022)", 0), ("media_moradores", "Moradores por domicílio", 2),
                            ("media_densidade_dormitorio", "Moradores por dormitório", 2)):
        row = {"Indicador": rot}
        for censo in (2000, 2010, 2022):
            for grupo, gr in (("com_migrante_recente", "c/ migr."), ("sem_migrante_recente", "s/ migr.")):
                r = dom[(dom.geografia == "canaa_municipio") & (dom.censo == censo) & (dom.grupo == grupo) & (dom.dimensao == var)]
                row[f"{censo} {gr}"] = fmt_num(r.valor.iloc[0], casas) if len(r) else "—"
        linhas.append(row)
    tabela_md(pd.DataFrame(linhas), "tab_07_condicoes_domiciliares",
              "Tabela 7 — Condições dos domicílios particulares permanentes, por presença de migrante de data fixa, Canaã dos Carajás, 2000–2022",
              "Elaboração própria a partir dos microdados da amostra dos Censos 2000, 2010 e 2022 (IBGE).",
              "Valores em % dos domicílios, salvo indicação. 'c/ migr.' = domicílio com ao menos um morador que residia em outro município cinco anos antes; 's/ migr.' = demais domicílios (os totais estão em data/processed/analise/condicoes_domiciliares). Energia não é investigada em 2022; internet só a partir de 2010. * CV 15–30 %; ** CV > 30 %. '—' = célula suprimida.")

    # --- desigualdade intraurbana por setor censitário (sede), 2010 → 2022 -----------------
    import geopandas as gpd
    import rasterio
    from rasterio.features import geometry_mask
    sm = pd.read_parquet(PROC / "setores" / "setores_mancha.parquet")
    s10 = gpd.read_parquet(PROC / "setores" / "setores_2010.parquet")
    s22 = gpd.read_parquet(PROC / "setores" / "setores_2022.parquet")
    i10 = pd.read_parquet(PROC / "setores" / "setores_2010_indicadores.parquet")
    i22 = pd.read_parquet(PROC / "setores" / "setores_2022_indicadores.parquet")
    nucleo = gpd.read_parquet(PROC / "geo" / "mancha_propria" / "mancha30_1990.parquet")
    nucleo = nucleo[nucleo.classe == 1].dissolve().geometry.centroid.iloc[0]
    ano_urb = rasterio.open(PROC / "geo" / "mancha_propria" / "ano_urbanizacao30.tif")
    arr = ano_urb.read(1)

    def ano_medio_urbanizacao(geom):
        m = geometry_mask([geom], transform=ano_urb.transform, invert=True, out_shape=arr.shape)
        v = arr[m]
        v = v[v > 0]
        return (float(np.median(v)), float(np.mean(v)), int(v.size)) if v.size else (np.nan, np.nan, 0)

    regs = []
    for ano, geo, ind, cols in ((2010, s10, i10, dict(agua="agua_pct", esgoto="esgoto_pct", lixo="lixo_coletado_pct", energia="com_energia_eletrica_pct",
                                                   renda="rendimento_medio_responsavel_com_r", moradores="media_moradores_domicilio", pop="populacao_residente",
                                                   dom="domicilios_particulares_permanentes")),
                                (2022, s22, i22, dict(agua="agua_pct", esgoto="esgoto_pct", lixo="lixo_pct", energia=None, renda=None,
                                                   moradores="media_moradores_domicilio", pop="populacao_residente", dom="domicilios_particulares_ocupados"))):
        sede = sm[(sm.ano == ano) & (sm.pertence == "sede")]
        g = geo.merge(ind[[c for c in ind.columns if c not in geo.columns or c == "cod_setor"]], on="cod_setor", how="inner")
        g = g[g.cod_setor.astype(str).isin(sede.cod_setor.astype(str))].copy()
        g = g.merge(sede[["cod_setor", "densidade_liquida_hab_ha", "construido_ha", "frac_construida"]].assign(cod_setor=lambda d: d.cod_setor.astype(str)),
                    left_on=g.cod_setor.astype(str), right_on="cod_setor", how="left", suffixes=("", "_sm"))
        for _, r in g.iterrows():
            geom = r.geometry
            med, mean, n = ano_medio_urbanizacao(geom)
            d = dict(ano=ano, cod_setor=str(r.cod_setor), pop=r[cols["pop"]], dom=r[cols["dom"]],
                     dist_nucleo_km=geom.centroid.distance(nucleo) / 1000, ano_urbanizacao_mediano=med, ano_urbanizacao_medio=mean, n_pixels_urbanos=n,
                     densidade_liquida_hab_ha=r.densidade_liquida_hab_ha, frac_construida=r.frac_construida,
                     agua_pct=r[cols["agua"]], esgoto_pct=r[cols["esgoto"]], lixo_pct=r[cols["lixo"]],
                     energia_pct=r[cols["energia"]] if cols["energia"] else np.nan,
                     renda_media_responsavel=r[cols["renda"]] if cols["renda"] else np.nan, moradores_por_dom=r[cols["moradores"]])
            if ano == 2022:
                tot = r.populacao_residente
                d["pct_pretos_pardos"] = (r.cor_preta + r.cor_parda) / tot * 100 if tot else np.nan
                d["razao_sexo"] = r.sexo_masculino / r.sexo_feminino * 100 if r.sexo_feminino else np.nan
            regs.append(d)
    ano_urb.close()
    st = pd.DataFrame(regs)
    gravar(st, "setores_sede_indicadores")

    # resumo da desigualdade: dispersão entre setores + gradiente centro-periferia
    ind_cols = ["agua_pct", "esgoto_pct", "lixo_pct", "energia_pct", "renda_media_responsavel", "moradores_por_dom", "densidade_liquida_hab_ha", "pct_pretos_pardos"]
    regs = []
    for ano in (2010, 2022):
        s = st[st.ano == ano]
        for col in ind_cols:
            v = s[col].dropna()
            if len(v) < 5:
                continue
            w = s.loc[v.index, "dom"].fillna(0).astype(float)
            ok = w > 0
            v, w = v[ok], w[ok]
            wm = np.average(v, weights=w)
            q = np.percentile(v, [10, 50, 90])
            # gradiente: regressão simples do indicador na distância ao núcleo e no ano mediano de urbanização
            x1 = s.loc[v.index, "dist_nucleo_km"]; x2 = s.loc[v.index, "ano_urbanizacao_mediano"]
            b_dist = np.polyfit(x1, v, 1)[0]
            rho_dist = float(pd.Series(v.values).corr(pd.Series(x1.values), method="spearman"))
            okx2 = x2.notna()
            b_ano = np.polyfit(x2[okx2], v[okx2], 1)[0] if okx2.sum() > 4 else np.nan
            rho_ano = float(pd.Series(v[okx2].values).corr(pd.Series(x2[okx2].values), method="spearman")) if okx2.sum() > 4 else np.nan
            regs.append(dict(ano=ano, indicador=col, n_setores=int(len(v)), media_ponderada=wm, minimo=float(v.min()), p10=q[0], p50=q[1], p90=q[2],
                             maximo=float(v.max()), cv_entre_setores_pct=float(v.std(ddof=0) / v.mean() * 100) if v.mean() else np.nan,
                             razao_p90_p10=(q[2] / q[0]) if q[0] > 0 else np.nan, gradiente_por_km=b_dist, spearman_distancia=rho_dist,
                             gradiente_por_ano_urbanizacao=b_ano, spearman_ano_urbanizacao=rho_ano))
    des = pd.DataFrame(regs)
    gravar(des, "desigualdade_intraurbana")
    RESUMO["desigualdade"] = des[des.indicador.isin(["agua_pct", "esgoto_pct", "lixo_pct"])][["ano", "indicador", "media_ponderada", "p10", "p90", "spearman_distancia", "spearman_ano_urbanizacao"]].to_dict("records")

    nomes = {"agua_pct": "Água da rede geral (%)", "esgoto_pct": "Esgoto rede geral (%)", "lixo_pct": "Lixo coletado (%)", "energia_pct": "Energia elétrica (%)",
             "renda_media_responsavel": "Rend. do responsável (R$ de 2010)", "moradores_por_dom": "Moradores por domicílio",
             "densidade_liquida_hab_ha": "Densidade líquida (hab./ha construído)", "pct_pretos_pardos": "Pretos e pardos (%)"}
    tab = pd.DataFrame({"Indicador": des.indicador.map(nomes), "Ano": des.ano, "Setores": des.n_setores, "Média pond.": des.media_ponderada.map(lambda v: fmt_num(v, 1)),
                        "P10": des.p10.map(lambda v: fmt_num(v, 1)), "P90": des.p90.map(lambda v: fmt_num(v, 1)),
                        "CV (%)": des.cv_entre_setores_pct.map(lambda v: fmt_num(v, 0)),
                        "ρ distância": des.spearman_distancia.map(lambda v: fmt_num(v, 2)),
                        "ρ ano urb.": des.spearman_ano_urbanizacao.map(lambda v: fmt_num(v, 2))})
    tabela_md(tab, "tab_08_desigualdade_intraurbana", "Tabela 8 — Desigualdade intraurbana entre setores censitários da sede, 2010 e 2022",
              "Elaboração própria a partir dos agregados por setor censitário do Universo (IBGE, 2010 e 2022), da série própria de mancha (ano de urbanização) e do núcleo histórico de 1990.",
              "Setores 'da sede' = setores urbanos cujo construído mapeado pertence majoritariamente à mancha contígua (E3c). CV = coeficiente de variação entre setores; ρ = correlação de Spearman entre setores com a distância ao núcleo de 1990 e com o ano de urbanização; ano de urbanização = mediana do primeiro ano urbano dos pixels do setor. O esgoto de 2010 inclui rede pluvial; o de 2022 só rede geral.")


# ----------------------------------------------------------------------------
# (g) comparação regional
# ----------------------------------------------------------------------------
def bloco_g(sem_rede: bool) -> None:
    print("(g) comparação regional")
    # 1. Canaã × Parauapebas × Pará com as estimativas do projeto (mesmo esquema, mesmo gate)
    itens = [("pessoas_5mais", "migrante", "migrante", "Migrantes de data fixa (% da pop. 5+)"),
             ("pessoas", "naturalidade", "municipio", "Naturais do município (%)"),
             ("pessoas_25mais", "nivel_instrucao", "superior_completo", "Superior completo, 25+ (%)"),
             ("pessoas_25mais", "nivel_instrucao", "sem_instrucao_fund_incompleto", "Sem instrução / fund. incompleto, 25+ (%)"),
             ("pessoas_10mais", "ocupado", "sim", "Taxa de ocupação 10+ (%)"),
             ("ocupados", "formal", "sim", "Ocupados formais (%)"), ("ocupados", "extrativa_mineral", "sim", "Ocupados na extrativa mineral (%)"),
             ("ocupados", "setor", "construcao", "Ocupados na construção (%)"), ("ocupados", "setor", "agropecuaria", "Ocupados na agropecuária (%)"),
             ("domicilios", "condicao_ocupacao", "alugado", "Domicílios alugados (%)"), ("domicilios", "adequacao", "adequada", "Domicílios adequados (%)"),
             ("domicilios", "esgoto_adequado", "sim", "Esgoto adequado (%)"), ("domicilios", "densidade_faixa", "mais_de_3", "Mais de 3 moradores/dormitório (%)")]
    regs = []
    for geo in GEOGRAFIAS:
        for censo in (1991, 2000, 2010, 2022):
            for uni, dim, cat, rot in itens:
                v, ep, cl = valor(geo, censo, uni, dim, cat)
                regs.append(dict(geografia=geo, censo=censo, indicador=rot, dimensao=dim, categoria=cat, valor=v, ep=ep, classe=cl))
            for var, uni, rot in (("renda_trabalho_r2022", "ocupados", "Renda média do trabalho (R$ jul/2022)"), ("idade", "pessoas", "Idade média (anos)"),
                                  ("renda_dom_pc_r2022", "domicilios", "Renda domiciliar per capita média (R$ jul/2022)")):
                v, ep, cl = valor(geo, censo, uni, estat="media", variavel=var)
                regs.append(dict(geografia=geo, censo=censo, indicador=rot, dimensao=f"media_{var}", categoria="media", valor=v, ep=ep, classe=cl))
    cmpg = pd.DataFrame(regs)
    gravar(cmpg, "comparacao_geografias")

    # diferença-em-diferenças descritiva: Δ Canaã − Δ comparação (2000→2022 e 2010→2022)
    regs = []
    for ind in cmpg.indicador.unique():
        for a0, a1 in ((2000, 2010), (2010, 2022), (2000, 2022)):
            c = cmpg[(cmpg.indicador == ind) & (cmpg.geografia == "canaa_municipio")].set_index("censo")
            if a0 not in c.index or a1 not in c.index or c.loc[a0, "valor"] != c.loc[a0, "valor"] or c.loc[a1, "valor"] != c.loc[a1, "valor"]:
                continue
            dc = c.loc[a1, "valor"] - c.loc[a0, "valor"]; ec = np.sqrt(c.loc[a1, "ep"] ** 2 + c.loc[a0, "ep"] ** 2)
            for geo in ("parauapebas_municipio", "pa"):
                k = cmpg[(cmpg.indicador == ind) & (cmpg.geografia == geo)].set_index("censo")
                if k.loc[a0, "valor"] != k.loc[a0, "valor"] or k.loc[a1, "valor"] != k.loc[a1, "valor"]:
                    continue
                dk = k.loc[a1, "valor"] - k.loc[a0, "valor"]; ek = np.sqrt(k.loc[a1, "ep"] ** 2 + k.loc[a0, "ep"] ** 2)
                did = dc - dk; edid = np.sqrt(ec ** 2 + ek ** 2)
                regs.append(dict(indicador=ind, periodo=f"{a0}–{a1}", comparacao=geo, delta_canaa=dc, ep_delta_canaa=ec, delta_comparacao=dk,
                                 ep_delta_comparacao=ek, dif_em_dif=did, ep_dif_em_dif=edid, significativo_95=abs(did) > 1.96 * edid))
    did = pd.DataFrame(regs)
    gravar(did, "dif_em_dif_descritiva")

    # 2. painel AMC 2000–2022 do projeto irmão: Canaã × grupos de municípios do Pará / Sudeste Paraense
    painel = BASE.parent / "migracoes-mineracao" / "data" / "processed" / "painel_temporal" / "painel_amc_temporal.parquet"
    if not painel.exists():
        print("  [aviso] painel AMC do projeto irmão ausente; bloco (g.2) pulado")
        return
    p = pd.read_parquet(painel)
    p = p[p.amc.str.startswith("15")].drop(columns=["n_amostral"])  # Pará; sem contagens amostrais exatas
    sud = OUT / "municipios_sudeste_paraense.json"
    if sud.exists():
        sud_ids = set(json.loads(sud.read_text())["ids"])
    elif not sem_rede:
        import requests
        r = requests.get("https://servicodados.ibge.gov.br/api/v1/localidades/mesorregioes/1506/municipios", timeout=60)
        r.raise_for_status()
        sud_ids = {str(m["id"]) for m in r.json()}
        sud.write_text(json.dumps({"fonte": "IBGE localidades API v1, mesorregião 1506 Sudeste Paraense", "acesso": "2026-09-10",
                                   "ids": sorted(sud_ids), "nomes": sorted(m["nome"] for m in r.json())}, ensure_ascii=False, indent=1))
    else:
        sud_ids = set()
    p["sudeste_paraense"] = p.amc.isin(sud_ids)
    p["grupo"] = np.select([p.amc == "1502152", p.amc == "1505536", p.sudeste_paraense & (p.grupo_cfem != "nao_minerario"),
                            p.sudeste_paraense & (p.grupo_cfem == "nao_minerario"), p.grupo_cfem == "nao_minerario"],
                           ["Canaã dos Carajás", "Parauapebas", "Sudeste Paraense — outros mineradores", "Sudeste Paraense — não mineradores",
                            "Pará — não mineradores (demais)"], default="Pará — mineradores (demais)")
    p["pct_imigrante_5anos"] = p.pop_expandida_imigrante_5anos / p.pop_expandida * 100
    p["pct_ocupado_extrativo"] = p.pop_expandida_setor_extrativo / p.pop_expandida_ocupado * 100
    p["pct_sem_esgoto_adequado"] = p.pop_expandida_domic_sem_esgoto_adequado / p.pop_expandida * 100
    p["pct_alugado"] = p.pop_expandida_domic_alugado / p.pop_expandida * 100
    p["pct_crianca_0a5"] = p.pop_expandida_crianca_0a5 / p.pop_expandida * 100
    p["pct_idoso_65mais"] = p.pop_expandida_idoso_65mais / p.pop_expandida * 100
    ind = ["pct_imigrante_5anos", "pct_ocupado_extrativo", "pct_sem_esgoto_adequado", "pct_alugado", "pct_crianca_0a5", "pct_idoso_65mais",
           "renda_trabalho_media_r2022", "cfem_per_capita"]
    regs = []
    for (grupo, censo), g in p.groupby(["grupo", "censo"]):
        w = g.pop_expandida
        d = dict(grupo=grupo, censo=int(censo), n_municipios_amc=int(len(g)), pop_expandida=float(w.sum()))
        for c in ind:
            ok = g[c].notna()
            d[c] = float(np.average(g.loc[ok, c], weights=w[ok])) if ok.any() else np.nan
            d[c + "_mediana"] = float(g.loc[ok, c].median()) if ok.any() else np.nan
        # crescimento populacional do grupo (pop expandida)
        regs.append(d)
    pg = pd.DataFrame(regs).sort_values(["grupo", "censo"])
    pg["pop_var_pct_vs_2000"] = pg.groupby("grupo").pop_expandida.transform(lambda s: (s / s.iloc[0] - 1) * 100)
    gravar(pg, "painel_amc_grupos")
    # tabela 9: painel — Canaã × grupos, 2000/2010/2022
    nomes = {"pct_imigrante_5anos": "Imigrantes de data fixa (%)", "pct_ocupado_extrativo": "Ocupados na extrativa (%)", "pct_sem_esgoto_adequado": "Pop. em domicílio sem esgoto adequado (%)",
             "pct_alugado": "Pop. em domicílio alugado (%)", "renda_trabalho_media_r2022": "Renda média do trabalho (R$ 2022)", "pop_var_pct_vs_2000": "População (var. % vs 2000)"}
    linhas = []
    ordem = ["Canaã dos Carajás", "Parauapebas", "Sudeste Paraense — outros mineradores", "Sudeste Paraense — não mineradores", "Pará — mineradores (demais)", "Pará — não mineradores (demais)"]
    for c, rot in nomes.items():
        for grupo in ordem:
            row = {"Indicador": rot, "Grupo": grupo}
            for censo in (2000, 2010, 2022):
                r = pg[(pg.grupo == grupo) & (pg.censo == censo)]
                row[str(censo)] = fmt_num(r[c].iloc[0], 0 if "renda" in c or "var" in c else 1) if len(r) and r[c].notna().all() else "—"
            linhas.append(row)
    n = {g: int(pg[(pg.grupo == g) & (pg.censo == 2022)].n_municipios_amc.iloc[0]) for g in ordem if len(pg[pg.grupo == g])}
    tabela_md(pd.DataFrame(linhas), "tab_09_painel_regional", "Tabela 9 — Canaã dos Carajás e grupos de municípios comparáveis (Áreas Mínimas Comparáveis), 2000–2022",
              "Painel municipal 2000–2022 do projeto irmão migracoes-mineracao (microdados da amostra dos Censos; CFEM/ANM), médias ponderadas pela população.",
              "Grupos por porte de CFEM per capita (lib.mineracao do projeto irmão). Municípios por grupo em 2022: " + "; ".join(f"{g}: {v}" for g, v in n.items()) + ". Sudeste Paraense = mesorregião IBGE 1506 (39 municípios).")
    RESUMO["painel_grupos_n"] = n


# ----------------------------------------------------------------------------
# (h) baseline 1991 e (i) economia
# ----------------------------------------------------------------------------
def bloco_h() -> None:
    print("(h) baseline 1991")
    itens = [("pessoas_5mais", "migrante", "migrante", "Migrantes de data fixa (%)"), ("pessoas", "naturalidade", "municipio", "Naturais do município (%)"),
             ("pessoas", "naturalidade", "outra_uf", "Naturais de outra UF (%)"), ("pessoas_25mais", "nivel_instrucao", "sem_instrucao_fund_incompleto", "Sem instrução / fund. incompleto, 25+ (%)"),
             ("pessoas_25mais", "nivel_instrucao", "superior_completo", "Superior completo, 25+ (%)"), ("pessoas_10mais", "ocupado", "sim", "Taxa de ocupação 10+ (%)"),
             ("ocupados", "setor", "agropecuaria", "Ocupados na agropecuária (%)"), ("ocupados", "extrativa_mineral", "sim", "Ocupados na extrativa mineral (%)"),
             ("ocupados", "setor", "construcao", "Ocupados na construção (%)"), ("ocupados", "setor", "servicos", "Ocupados nos serviços (%)"),
             ("ocupados", "formal", "sim", "Ocupados formais (%)"), ("domicilios", "agua_rede", "sim", "Domicílios com água da rede (%)"),
             ("domicilios", "esgoto_adequado", "sim", "Esgoto adequado (%)"), ("domicilios", "lixo_coletado", "sim", "Lixo coletado (%)"),
             ("domicilios", "energia", "sim", "Energia elétrica (%)"), ("domicilios", "condicao_ocupacao", "alugado", "Domicílios alugados (%)"),
             ("domicilios", "densidade_faixa", "mais_de_3", "Mais de 3 moradores/dormitório (%)"), ("pessoas", "grupo_etario", "00_14", "População de 0–14 anos (%)"),
             ("pessoas", "sexo", "M", "Homens (%)")]
    regs = []
    for uni, dim, cat, rot in itens:
        row = dict(indicador=rot)
        for geo, censo, col in (("parauapebas_municipio", 1991, "parauapebas_1991"), ("parauapebas_sede", 1991, "parauapebas_sede_1991"),
                                ("canaa_municipio", 2000, "canaa_2000"), ("canaa_municipio", 2022, "canaa_2022"), ("canaa_sede", 2022, "canaa_sede_2022"),
                                ("pa", 1991, "pa_1991")):
            v, ep, cl = valor(geo, censo, uni, dim, cat)
            row[col] = v; row[col + "_ep"] = ep; row[col + "_classe"] = cl
        regs.append(row)
    for uni, var, rot in (("pessoas", "idade", "Idade média (anos)"), ("domicilios", "moradores", "Moradores por domicílio")):
        row = dict(indicador=rot)
        for geo, censo, col in (("parauapebas_municipio", 1991, "parauapebas_1991"), ("parauapebas_sede", 1991, "parauapebas_sede_1991"),
                                ("canaa_municipio", 2000, "canaa_2000"), ("canaa_municipio", 2022, "canaa_2022"), ("canaa_sede", 2022, "canaa_sede_2022"), ("pa", 1991, "pa_1991")):
            v, ep, cl = valor(geo, censo, uni, estat="media", variavel=var)
            row[col] = v; row[col + "_ep"] = ep; row[col + "_classe"] = cl
        regs.append(row)
    b = pd.DataFrame(regs)
    gravar(b, "baseline_1991")
    m90 = MANCHA[MANCHA.ano.isin([1990, 1991])]
    RESUMO["mancha_1990_1991"] = m90[["ano", "area_sede_ha", "area_outros_nucleos_ha", "area_construido_mineracao_ha"]].to_dict("records")
    tab = pd.DataFrame({"Indicador": b.indicador,
                        "Parauapebas 1991 (inclui Canaã)": [fmt_num(v, 1) + classe_marca(c) if v == v else "—" for v, c in zip(b.parauapebas_1991, b.parauapebas_1991_classe)],
                        "Pará 1991": [fmt_num(v, 1) + classe_marca(c) if v == v else "—" for v, c in zip(b.pa_1991, b.pa_1991_classe)],
                        "Canaã 2000": [fmt_num(v, 1) + classe_marca(c) if v == v else "—" for v, c in zip(b.canaa_2000, b.canaa_2000_classe)],
                        "Canaã 2022": [fmt_num(v, 1) + classe_marca(c) if v == v else "—" for v, c in zip(b.canaa_2022, b.canaa_2022_classe)],
                        "Canaã sede 2022": [fmt_num(v, 1) + classe_marca(c) if v == v else "—" for v, c in zip(b.canaa_sede_2022, b.canaa_sede_2022_classe)]})
    tabela_md(tab, "tab_10_baseline_1991", "Tabela 10 — Linha de base pré-mineral: Parauapebas em 1991 (inclui o atual Canaã dos Carajás) e Canaã em 2000 e 2022",
              "Elaboração própria a partir dos microdados da amostra dos Censos 1991, 2000 e 2022 (IBGE).",
              "Em 1991 Canaã era localidade de Parauapebas: o perfil é de um superconjunto, não de um proxy externo. Renda de 1991 não é comparável (moeda pré-Real). '—' = célula suprimida ou não investigada. * CV 15–30 %; ** CV > 30 %.")


def bloco_i(sem_rede: bool) -> None:
    print("(i) economia: PIB, VA, CFEM, CEMPRE")
    pib = pd.read_parquet(PROC / "ibge" / "t5938_pib_municipal.parquet")
    pib["Ano"] = pib.Ano.astype(int)
    vars_ = {"Produto Interno Bruto a preços correntes": "pib_mil_r",
             "Valor adicionado bruto a preços correntes total": "va_total_mil_r",
             "Valor adicionado bruto a preços correntes da agropecuária": "va_agro_mil_r",
             "Valor adicionado bruto a preços correntes da indústria": "va_industria_mil_r",
             "Valor adicionado bruto a preços correntes dos serviços, exclusive administração, defesa, educação e saúde públicas e seguridade social": "va_servicos_mil_r",
             "Valor adicionado bruto a preços correntes da administração, defesa, educação e saúde públicas e seguridade social": "va_adm_publica_mil_r",
             "Participação do produto interno bruto a preços correntes no produto interno bruto a preços correntes da unidade da federação": "pib_part_pa_pct"}
    w = pib[pib.Variável.isin(vars_)].pivot_table(index="Ano", columns="Variável", values="valor").rename(columns=vars_).reset_index().rename(columns={"Ano": "ano"})
    for c in ("va_agro", "va_industria", "va_servicos", "va_adm_publica"):
        w[c + "_pct"] = w[c + "_mil_r"] / w.va_total_mil_r * 100
    cem = pd.read_parquet(PROC / "ibge" / "t6449_cempre.parquet")
    cem["Ano"] = cem.Ano.astype(int)
    cn = "Classificação Nacional de Atividades Econômicas (CNAE 2.0)"
    tot = cem[cem[cn] == "Total"].pivot_table(index="Ano", columns="Variável", values="valor").rename(columns={
        "Número de empresas e outras organizações": "cempre_empresas", "Pessoal ocupado total": "cempre_pessoal_ocupado",
        "Pessoal ocupado assalariado": "cempre_assalariados", "Salários e outras remunerações": "cempre_salarios_mil_r"}).reset_index().rename(columns={"Ano": "ano"})
    ext = cem[cem[cn].str.startswith("B ") & (cem.Variável == "Pessoal ocupado assalariado")][["Ano", "valor"]].rename(columns={"Ano": "ano", "valor": "cempre_assalariados_extrativa"})
    cons = cem[cem[cn].str.startswith("F ") & (cem.Variável == "Pessoal ocupado assalariado")][["Ano", "valor"]].rename(columns={"Ano": "ano", "valor": "cempre_assalariados_construcao"})
    eco = pd.DataFrame({"ano": range(2002, 2027)}).merge(w, on="ano", how="left").merge(tot, on="ano", how="left").merge(ext, on="ano", how="left").merge(cons, on="ano", how="left")
    cf = pd.read_parquet(OUT / "mancha_populacao_anual.parquet")[["ano", "cfem_nominal_r", "cfem_r2022", "cfem_per_capita_r2022", "pop_municipio", "area_sede_ha", "area_sede_delta_ha"]]
    eco = eco.merge(cf, on="ano", how="left")
    eco["pib_per_capita_r"] = eco.pib_mil_r * 1000 / eco.pop_municipio
    eco["cfem_pct_pib"] = eco.cfem_nominal_r / (eco.pib_mil_r * 1000) * 100
    eco["assalariados_extrativa_pct"] = eco.cempre_assalariados_extrativa / eco.cempre_assalariados * 100
    gravar(eco, "economia_anual")
    RESUMO["pib_part_pa_2023"] = float(eco[eco.ano == 2023].pib_part_pa_pct.iloc[0]) if eco[eco.ano == 2023].pib_part_pa_pct.notna().any() else None
    sel = eco[eco.ano.isin([2002, 2004, 2007, 2010, 2013, 2016, 2019, 2021, 2022, 2023])].copy()
    tab = pd.DataFrame({"Ano": sel.ano, "População (IBGE)": sel.pop_municipio.map(fmt_num), "PIB (R$ mi correntes)": (sel.pib_mil_r / 1000).map(lambda v: fmt_num(v, 0)),
                        "PIB per capita (R$ correntes)": sel.pib_per_capita_r.map(lambda v: fmt_num(v, 0)), "VA indústria (%)": sel.va_industria_pct.map(lambda v: fmt_num(v, 1)),
                        "VA adm. pública (%)": sel.va_adm_publica_pct.map(lambda v: fmt_num(v, 1)), "Part. no PIB do Pará (%)": sel.pib_part_pa_pct.map(lambda v: fmt_num(v, 2)),
                        "CFEM (R$ mi correntes)": (sel.cfem_nominal_r / 1e6).map(lambda v: fmt_num(v, 1)), "CFEM per capita (R$ jul/2022)": sel.cfem_per_capita_r2022.map(lambda v: fmt_num(v, 0)),
                        "Assalariados CEMPRE": sel.cempre_assalariados.map(fmt_num),
                        "Área da sede (ha)": sel.area_sede_ha.map(fmt_num)})
    tabela_md(tab, "tab_11_economia", "Tabela 11 — Indicadores econômicos de Canaã dos Carajás e área construída da sede, 2002–2023",
              "IBGE (PIB dos Municípios, t/5938; CEMPRE, t/6449; Estimativas de população); ANM (CFEM distribuída); série própria de mancha (E3b/E3c).",
              "PIB e VA a preços correntes (VA setorial ainda não divulgado para 2022–2023); CFEM per capita deflacionada pelo IPCA de julho (jul/2022 = 100) e dividida pela população estimada do ano (subestimada em 2011–2021). CEMPRE disponível de 2006 a 2021; o pessoal da seção B (extrativa) é suprimido pelo IBGE por haver poucas unidades locais.")


# ----------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sem-rede", action="store_true", help="não consultar a API do IBGE (usa caches; CFEM só nominal se não houver IPCA)")
    a = ap.parse_args()
    bloco_a()
    bloco_b(a.sem_rede)
    bloco_c()
    bloco_d()
    bloco_e()
    bloco_f()
    bloco_g(a.sem_rede)
    bloco_h()
    bloco_i(a.sem_rede)
    bloco_j()
    (OUT / "resumo_analise.json").write_text(json.dumps(RESUMO, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print("resumo:", json.dumps(RESUMO, ensure_ascii=False, default=float)[:1500])
    return 0



# ----------------------------------------------------------------------------
# (j) inserção produtiva de migrantes e não migrantes na cadeia da mineração
#     (pedido do usuário em 10/09/2026, durante a E5)
# ----------------------------------------------------------------------------
CADEIA = {"extrativa_mineral": "extrativa mineral (B)", "construcao": "construção (F)", "transformacao": "transformação (C)"}


def bloco_j() -> None:
    """Cadeia produtiva da mineração = extrativa mineral (núcleo) + construção (obras das minas e da cidade)
    + indústria de transformação (beneficiamento). O CNAE-Dom do Censo não identifica fornecedores da mina
    dentro de serviços/transporte, então a 'cadeia ampliada' é um limite inferior declarado."""
    print("(j) cadeia da mineração: migrantes × não migrantes")
    regs = []
    for geo in ("canaa_municipio", "canaa_sede", "parauapebas_municipio", "pa"):
        for censo in (1991, 2000, 2010, 2022):
            r = est(geo, censo, "ocupados", "migrante", dim2="setor")
            c = est(geo, censo, "ocupados", "migrante", dim2="setor", estat="contagem")
            if len(r) == 0:
                continue
            tot_grp = {g: est(geo, censo, "ocupados", "migrante", cat1=g, estat="contagem") for g in ("migrante", "nao_migrante")}
            for grupo in ("migrante", "nao_migrante"):
                rg = r[r.cat1 == grupo].set_index("cat2"); cg = c[c.cat1 == grupo].set_index("cat2")
                soma_v = soma_var = 0.0; soma_n = 0.0; faltam = []
                for setor, rot in CADEIA.items():
                    if setor in rg.index:
                        regs.append(dict(geografia=geo, censo=censo, grupo=grupo, elo=setor, rotulo=rot, proporcao=rg.loc[setor, "valor"], ep=rg.loc[setor, "ep"],
                                         cv=rg.loc[setor, "cv"], classe=rg.loc[setor, "classe_precisao"], n_faixa=rg.loc[setor, "n_faixa"],
                                         contagem=cg.loc[setor, "valor"] if setor in cg.index else np.nan))
                        soma_v += rg.loc[setor, "valor"]; soma_var += rg.loc[setor, "ep"] ** 2
                        soma_n += cg.loc[setor, "valor"] if setor in cg.index else 0
                    else:
                        faltam.append(setor)
                # fusões 'outros:' que contenham só elos da cadeia entram na soma
                for cat in rg.index:
                    if str(cat).startswith("outros:"):
                        partes = set(cat.split(":", 1)[1].split("+"))
                        if partes <= set(CADEIA):
                            soma_v += rg.loc[cat, "valor"]; soma_var += rg.loc[cat, "ep"] ** 2
                            soma_n += cg.loc[cat, "valor"] if cat in cg.index else 0
                            faltam = [f for f in faltam if f not in partes]
                if soma_v <= 0:
                    continue
                regs.append(dict(geografia=geo, censo=censo, grupo=grupo, elo="cadeia_ampliada", rotulo="cadeia ampliada (B + F + C)", proporcao=soma_v,
                                 ep=np.sqrt(soma_var), cv=np.sqrt(soma_var) / soma_v * 100 if soma_v else np.nan,
                                 classe=("boa" if soma_var ** 0.5 / soma_v * 100 <= 15 else "cautela" if soma_var ** 0.5 / soma_v * 100 <= 30 else "baixa") if soma_v else None,
                                 n_faixa=None, contagem=soma_n, elos_ausentes="+".join(faltam) if faltam else None,
                                 ocupados_grupo=tot_grp[grupo].valor.iloc[0] if len(tot_grp[grupo]) else np.nan))
    cd = pd.DataFrame(regs)
    # razão de seletividade e composição (participação dos migrantes entre os ocupados de cada elo)
    out = []
    for (geo, censo, elo), g in cd.groupby(["geografia", "censo", "elo"]):
        m = g[g.grupo == "migrante"]; n = g[g.grupo == "nao_migrante"]
        if len(m) == 0 or len(n) == 0:
            continue
        m, n = m.iloc[0], n.iloc[0]
        rz, erz = razao(m.proporcao, m.ep, n.proporcao, n.ep)
        dif = m.proporcao - n.proporcao; edif = np.sqrt(m.ep ** 2 + n.ep ** 2)
        tot = m.contagem + n.contagem
        out.append(dict(geografia=geo, censo=censo, elo=elo, rotulo=m.rotulo, p_migrante=m.proporcao, ep_migrante=m.ep, classe_migrante=m.classe,
                        p_nao_migrante=n.proporcao, ep_nao_migrante=n.ep, classe_nao_migrante=n.classe, razao_seletividade=rz, ep_razao=erz,
                        diferenca_pp=dif, ep_diferenca=edif, significativo_95=abs(dif) > 1.96 * edif if edif == edif else None,
                        ocupados_elo_arred=tot, participacao_migrantes_no_elo_pct=m.contagem / tot * 100 if tot else np.nan,
                        elos_ausentes=m.get("elos_ausentes")))
    cad = pd.DataFrame(out)
    gravar(cad, "cadeia_mineral_migrantes")

    # participação dos migrantes entre todos os ocupados (para comparar com a participação no elo)
    regs = []
    for geo in ("canaa_municipio", "parauapebas_municipio", "pa"):
        for censo in (2000, 2010, 2022):
            cm = est(geo, censo, "ocupados", "migrante", estat="contagem").set_index("cat1")
            if {"migrante", "nao_migrante"} <= set(cm.index):
                m_, n_ = cm.loc["migrante"], cm.loc["nao_migrante"]
                v = m_.valor / (m_.valor + n_.valor) * 100
                regs.append(dict(geografia=geo, censo=censo, p_migrantes_entre_ocupados=v, ep=np.nan, classe=None))
    gravar(pd.DataFrame(regs), "cadeia_mineral_base_migrantes")

    # tipo de migrante (intra/interestadual) e coorte de chegada × elo
    regs = []
    for censo in (2000, 2010, 2022):
        for dim in ("tipo_mig_5anos", "periodo_chegada", "tempo_moradia_faixa"):
            uni = "chegados" if dim == "periodo_chegada" else "ocupados"
            r = est("canaa_municipio", censo, uni, dim, dim2="setor")
            for _, x in r.iterrows():
                if x.cat2 in CADEIA or (str(x.cat2).startswith("outros:") and set(str(x.cat2).split(":", 1)[1].split("+")) <= set(CADEIA)):
                    regs.append(dict(censo=censo, universo=uni, dimensao=dim, categoria=x.cat1, rotulo=rotulo(x.cat1, dim), elo=x.cat2, elo_rotulo=rotulo(x.cat2, "setor"),
                                     proporcao=x.valor, ep=x.ep, cv=x.cv, classe=x.classe_precisao, n_faixa=x.n_faixa))
    gravar(pd.DataFrame(regs), "cadeia_mineral_por_origem_coorte")

    # perfil dos ocupados na extrativa (sem recorte migratório, cruzamento indisponível): posição, instrução, renda
    regs = []
    for censo in (2000, 2010, 2022):
        for dim2 in ("posicao", "nivel_instrucao"):
            r = est("canaa_municipio", censo, "ocupados", "extrativa_mineral", dim2=dim2)
            for _, x in r.iterrows():
                regs.append(dict(censo=censo, grupo="extrativa" if x.cat1 == "sim" else "demais_setores", dimensao=dim2, categoria=x.cat2, rotulo=rotulo(x.cat2, dim2),
                                 valor=x.valor, ep=x.ep, cv=x.cv, classe=x.classe_precisao, n_faixa=x.n_faixa))
        r = est("canaa_municipio", censo, "ocupados", "extrativa_mineral", estat="media", variavel="renda_trabalho_r2022")
        for _, x in r.iterrows():
            regs.append(dict(censo=censo, grupo="extrativa" if x.cat1 == "sim" else "demais_setores", dimensao="media_renda_trabalho_r2022", categoria="media", rotulo="renda média do trabalho",
                             valor=x.valor, ep=x.ep, cv=x.cv, classe=x.classe_precisao, n_faixa=x.n_faixa))
        r = est("canaa_municipio", censo, "ocupados", "setor", estat="media", variavel="renda_trabalho_r2022")
        for _, x in r[r.cat1.isin(CADEIA)].iterrows():
            regs.append(dict(censo=censo, grupo=x.cat1, dimensao="media_renda_trabalho_r2022", categoria="media", rotulo="renda média do trabalho",
                             valor=x.valor, ep=x.ep, cv=x.cv, classe=x.classe_precisao, n_faixa=x.n_faixa))
    gravar(pd.DataFrame(regs), "cadeia_mineral_perfil_extrativa")

    # tabela 12
    linhas = []
    for censo in (2000, 2010, 2022):
        for elo in list(CADEIA) + ["cadeia_ampliada"]:
            r = cad[(cad.geografia == "canaa_municipio") & (cad.censo == censo) & (cad.elo == elo)]
            if len(r) == 0:
                linhas.append({"Censo": censo, "Elo da cadeia": CADEIA.get(elo, "cadeia ampliada (B + F + C)"), "Migrantes (%)": "—", "Não migrantes (%)": "—",
                               "Razão de seletividade": "—", "Diferença (p.p.)": "—", "Signif. 95 %": "—", "Migrantes no elo (%)": "—"})
                continue
            r = r.iloc[0]
            nota = f" (sem {r.elos_ausentes.replace('+', ', ')})" if isinstance(r.elos_ausentes, str) else ""
            linhas.append({"Censo": censo, "Elo da cadeia": r.rotulo + nota, "Migrantes (%)": fmt_num(r.p_migrante, 1) + classe_marca(r.classe_migrante),
                           "Não migrantes (%)": fmt_num(r.p_nao_migrante, 1) + classe_marca(r.classe_nao_migrante),
                           "Razão de seletividade": f"{fmt_num(r.razao_seletividade, 2)} ± {fmt_num(1.96 * r.ep_razao, 2)}",
                           "Diferença (p.p.)": f"{'+' if r.diferenca_pp > 0 else ''}{fmt_num(r.diferenca_pp, 1)}", "Signif. 95 %": "sim" if r.significativo_95 else "não",
                           "Migrantes no elo (%)": fmt_num(r.participacao_migrantes_no_elo_pct, 1)})
    base = pd.read_parquet(OUT / "cadeia_mineral_base_migrantes.parquet")
    base_txt = "; ".join(f"{int(r.censo)}: {fmt_num(r.p_migrantes_entre_ocupados, 1)} %" for _, r in base[base.geografia == "canaa_municipio"].iterrows())
    tabela_md(pd.DataFrame(linhas), "tab_12_cadeia_mineral_migrantes",
              "Tabela 12 — Inserção de migrantes de data fixa e não migrantes na cadeia produtiva da mineração, Canaã dos Carajás, 2000–2022 (% dos ocupados de cada grupo)",
              "Elaboração própria a partir dos microdados da amostra dos Censos 2000, 2010 e 2022 (IBGE).",
              "Cadeia = extrativa mineral (seção B, inclui atividades de apoio à extração) + construção (F) + indústria de transformação (C); fornecedores de serviços e transporte à mina não são identificáveis no CNAE-Dom, logo a cadeia ampliada é um limite inferior. "
              "Migrante = residia em outro município cinco anos antes. Razão = proporção entre migrantes ÷ proporção entre não migrantes (± IC 95 %, método delta). "
              f"Participação dos migrantes no total de ocupados: {base_txt}. * CV 15–30 %; ** CV > 30 %; '—' = célula suprimida pelo controle de revelação.")
    r22 = cad[(cad.geografia == "canaa_municipio") & (cad.censo == 2022)].set_index("elo")
    RESUMO["cadeia_2022"] = {e: dict(mig=float(r22.loc[e, "p_migrante"]), nao=float(r22.loc[e, "p_nao_migrante"]), razao=float(r22.loc[e, "razao_seletividade"]),
                                     part_mig=float(r22.loc[e, "participacao_migrantes_no_elo_pct"])) for e in r22.index}


if __name__ == "__main__":
    sys.exit(main())
