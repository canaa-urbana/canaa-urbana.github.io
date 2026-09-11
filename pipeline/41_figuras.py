#!/usr/bin/env python
"""41_figuras.py — figuras do artigo com a identidade Ardósia (PLANO.md, Fase 5 passo 2; etapa E5).

Lê SOMENTE `data/processed` (tabelas de `40_analise_artigo.py`, estatísticas da mancha da E3c,
polígonos/rasters da E3b, agregados públicos do IBGE da E1). Grava PNG 300 dpi + SVG em
`artigo/figuras/` e um índice `artigo/figuras/figuras.json` (arquivo, título, legenda, fonte,
resumo textual de uma frase para alt/aria-label — reaproveitado pelo dashboard em E7).

Regras de visualização seguidas (skills `ardosia-brand-guidelines` e `dataviz`): forma pelo trabalho
do dado; cor por papel (categórica em ordem fixa, sequencial de uma matiz, ênfase terracota + cinza);
uma escala por eixo (nunca eixo duplo); segundo sinal além da cor (traço/marcador); incerteza visível
(bandas de IC, barras de erro); rotulagem direta; marcos como linhas tracejadas discretas; fonte em cada
figura. Exceção à paleta (decisão do usuário, 10/09/2026): toda classe de uso do solo usa a cor
oficial MapBiomas/IBGE (`lib/legendas.py`) — mancha urbana = classe 24, construído em mineração =
classe 30, loteamento vazio = estilo .qml das Áreas Urbanizadas 2022. O "ano de urbanização"
(Figura 4) usa a rampa de vermelhos derivada da classe 24 (`rampa_urbana`), do escuro (antigo) ao claro.

Uso: .venv/bin/python pipeline/41_figuras.py [--so fig_01,fig_02]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import ListedColormap, BoundaryNorm  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "pipeline"))
from lib.ardosia_palette import (ARDOSIA, ARDOSIA_CL, ARDOSIA_MED, ARDOSIA_NEV, BORDO, FILETE, FILETE_CL, OCRE,  # noqa: E402
                                 PAPEL, PAPEL_CL, PAPEL_FIG, PEDRA, PETROLEO, SANS, SERIF, TERRACOTA, TERRACOTA_NEV, TINTA,
                                 VIZ_MUTED, VIZ_SEQUENTIAL, apply_ardosia)
from lib.viz import _titulo, salvar as _salvar  # noqa: E402
from lib.rotulos import CICLOS, JANELAS_OBRAS, SETORES_ORDEM, rotulo  # noqa: E402
from lib.legendas import MINERACAO, URBANO, ibge_qml, mapbiomas_hex, rampa_urbana  # noqa: E402

COR_URBANO = mapbiomas_hex(URBANO)          # MapBiomas Col. 11, classe 24
COR_MINERACAO = mapbiomas_hex(MINERACAO)    # MapBiomas Col. 11, classe 30
COR_LOTEAMENTO = ibge_qml("Loteamento vazio")["contorno"]  # IBGE AU 2022 (.qml oficial)

apply_ardosia(base_size=10)
plt.rcParams["axes.grid"] = False   # gridlines só onde a leitura pede; sem grade vertical em eixo de tempo

PROC = BASE / "data" / "processed"
AN = PROC / "analise"
GEO = PROC / "geo"
FIG = BASE / "artigo" / "figuras"
FIG.mkdir(parents=True, exist_ok=True)
INDICE: list[dict] = []

F_MICRO = "Elaboração própria a partir dos microdados da amostra dos Censos Demográficos (IBGE); estimativas aprovadas pelo controle de revelação."
F_MANCHA = "Elaboração própria: série própria Landsat/Sentinel-2 (30 m), validada com CBERS; população IBGE."
F_IBGE = "Elaboração própria a partir de IBGE (SIDRA)."


def registrar(nome: str, titulo: str, legenda: str, fonte: str, resumo: str) -> None:
    INDICE.append(dict(arquivo=f"{nome}.png", svg=f"{nome}.svg", titulo=titulo, legenda=legenda, fonte=fonte, resumo=resumo))


def salvar(fig, nome, titulo, legenda, fonte, resumo, kicker=None, topo=0.90, base=0.03):
    fig.tight_layout(rect=[0, base, 1, topo])
    _titulo(fig, titulo, kicker)
    _salvar(fig, FIG / nome, fonte=f"Fonte: {fonte}")
    registrar(nome, titulo, legenda, fonte, resumo)
    print(f"  {nome}")


def sombrear_obras(ax, y_rotulo=None):
    """Janelas de construção das minas (Sossego 2002–04, S11D 2013–16) em terracota névoa."""
    for a0, a1, rot in JANELAS_OBRAS:
        ax.axvspan(a0, a1, color=TERRACOTA_NEV, zorder=0, lw=0)
        if y_rotulo is not None:
            ax.text((a0 + a1) / 2, y_rotulo, f"obras\n{rot}", ha="center", va="top", fontsize=7.5, color=TERRACOTA, fontfamily=SANS)


def marcos_verticais(ax, anos=(1994, 2004, 2016), rotulos=("emancipação", "Sossego", "S11D"), y=None):
    for a, r in zip(anos, rotulos):
        ax.axvline(a, color=PEDRA, lw=0.8, ls=(0, (3, 3)), zorder=1)
        if y is not None:
            ax.text(a, y, f" {r} {a}", rotation=90, va="top", ha="right", fontsize=7.5, color=PEDRA, fontfamily=SANS)


def eixo_limpo(ax, grade_y=True):
    ax.spines[["top", "right"]].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(FILETE)
    if grade_y:
        ax.grid(axis="y", color=FILETE_CL, lw=0.7)
        ax.set_axisbelow(True)
    for lab in ax.get_xticklabels() + ax.get_yticklabels():
        lab.set_fontfamily(SANS)


def br(v, casas=0):
    s = f"{v:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


# ============================================================================
def fig_01():
    s = pd.read_parquet(AN / "serie_populacao.parquet")
    fig, ax = plt.subplots(figsize=(10, 5.6))
    sombrear_obras(ax, y_rotulo=98000)
    mun = s[s.recorte == "município"]
    ofi = mun[mun.tipo_fonte.isin(["oficial_censo", "oficial_contagem"])].sort_values("ano")
    estim = mun[mun.tipo_fonte == "estimativa_ibge"].sort_values("ano")
    cit = mun[mun.tipo_fonte == "citacao_terceiro"]
    urb = s[s.recorte == "urbana"].sort_values("ano")
    ax.plot(ofi.ano, ofi.valor, color=ARDOSIA, lw=2, zorder=3)
    ax.scatter(ofi.ano, ofi.valor, s=64, color=ARDOSIA, edgecolor=PAPEL_FIG, lw=1.5, zorder=4, label="Censo / Contagem (IBGE)")
    ax.scatter(estim.ano, estim.valor, s=22, facecolor=PAPEL_FIG, edgecolor=ARDOSIA_MED, lw=1.2, zorder=3, label="Estimativa anual (IBGE)")
    ax.scatter(cit.ano, cit.valor, s=60, marker="D", color=TERRACOTA, edgecolor=PAPEL_FIG, lw=1.2, zorder=4, label="Citação de terceiro (CETEM 1996; PDP 2005)")
    ax.plot(urb.ano, urb.valor, color=PETROLEO, lw=1.6, ls=(0, (4, 2)), marker="s", ms=5, zorder=3, label="População urbana (Censos)")
    # cenários de 1985 (faixas)
    cen = s[(s.ano == 1985) & (s.tipo_fonte == "estimativa_propria")]
    for i, (_, r) in enumerate(cen.iterrows()):
        x = 1985 + (i - 1) * 0.6
        ax.plot([x, x], [r.valor_min, r.valor_max], color=OCRE, lw=3, solid_capstyle="butt", zorder=3, label="Assentamento 1982–85: famílias × mor./dom. (cenários)" if i == 0 else None)
    ax.text(1986.6, 9200, "1.551 fam. (CEDERE II+III)\n~1.000 fam. (só CEDERE II)\n816 títulos", fontsize=7.2, color=PEDRA, fontfamily=SANS, va="center")
    for _, r in ofi.iterrows():
        ax.annotate(br(r.valor), (r.ano, r.valor), xytext=(0, 9), textcoords="offset points", ha="center", fontsize=8, color=TINTA, fontfamily=SANS)
    for _, r in cit.iterrows():
        ax.annotate(br(r.valor), (r.ano, r.valor), xytext=(0, -13), textcoords="offset points", ha="center", fontsize=7.5, color=TERRACOTA, fontfamily=SANS)
    marcos_verticais(ax, y=57000)
    ax.set_xlim(1983, 2027); ax.set_ylim(0, 100000)
    ax.set_yticks(range(0, 100001, 20000)); ax.set_yticklabels([br(v) for v in range(0, 100001, 20000)])
    ax.set_ylabel("Habitantes"); eixo_limpo(ax)
    ax.legend(loc="upper left", fontsize=8, frameon=False)
    salvar(fig, "fig_01_populacao", "Da colônia agrícola à cidade mineradora: população de Canaã dos Carajás, 1985–2026",
           "Figura 1 — População residente de Canaã dos Carajás, 1985–2026, por tipo de fonte. Faixas ocre em 1985: conversão de famílias assentadas em pessoas (4,76–5,5 moradores por domicílio), em três cenários de escopo; losangos: citações secundárias; círculos vazados: estimativas anuais do IBGE, ancoradas no censo anterior e sistematicamente subestimadas; janelas sombreadas: construção das minas.",
           "IBGE (Censos 1991–2022, Contagem 2007, Estimativas); CETEM (2011); PDP (2007); PLANO.md Fase 1b.",
           "A população municipal passa de cerca de 11 mil (1996–2000) para 26,7 mil (2010) e 77,1 mil (2022); as estimativas anuais do IBGE ficaram muito abaixo do que a Contagem 2007 e o Censo 2022 revelaram.",
           kicker="Série populacional")


def fig_02():
    m = pd.read_parquet(AN / "mancha_populacao_anual.parquet")
    mb = pd.read_parquet(GEO / "estatisticas_mancha.parquet")[["ano", "mapbiomas24_janela_ha"]]
    m = m.merge(mb, on="ano")
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 7.2), sharex=True, gridspec_kw=dict(height_ratios=[3, 2], hspace=0.12))
    for ax in (a1, a2):
        sombrear_obras(ax)
    a1.fill_between(m.ano, m.area_sede_ajustada_ha - m.area_sede_ajustada_ic95_ha, m.area_sede_ajustada_ha + m.area_sede_ajustada_ic95_ha,
                    color=ARDOSIA, alpha=0.12, lw=0, label="IC 95 % da área ajustada")
    a1.plot(m.ano, m.area_sede_ha, color=ARDOSIA_CL, lw=1.6, ls=(0, (4, 2)), label="Área mapeada (30 m)")
    a1.plot(m.ano, m.area_sede_ajustada_ha, color=ARDOSIA, lw=2.2, label="Área ajustada pela acurácia")
    a1.plot(m.ano, m.mapbiomas24_janela_ha, color=VIZ_MUTED, lw=1.4, ls=(0, (1, 2)), label="MapBiomas Col. 11 (classe 24, janela)")
    val = m[m.ajuste_origem == "validado"]
    a1.scatter(val.ano, val.area_sede_ajustada_ha, s=46, color=ARDOSIA, edgecolor=PAPEL_FIG, lw=1.2, zorder=5, label="Épocas validadas (2009, 2017, 2022)")
    for _, r in m[m.ano.isin([1990, 2000, 2010, 2022, 2026])].iterrows():
        a1.annotate(f"{br(r.area_sede_ajustada_ha)} ha", (r.ano, r.area_sede_ajustada_ha), xytext=(-4, 8), textcoords="offset points", ha="right" if r.ano == 2026 else "left",
                    fontsize=8, color=TINTA, fontfamily=SANS)
    a1.text(2026, m.loc[m.ano == 2026, "area_sede_ha"].iloc[0] + 120, "2026:\nprovisório", ha="right", fontsize=7.5, color=PEDRA, fontfamily=SANS)
    a1.set_ylabel("Área construída contígua da sede (ha)"); a1.set_ylim(0, 4500); eixo_limpo(a1)
    a1.legend(loc="upper left", fontsize=8, frameon=False, ncol=2)
    marcos_verticais(a1, y=4400)
    cores = [TERRACOTA if 2002 <= a <= 2004 or 2013 <= a <= 2016 else ARDOSIA_MED for a in m.ano]
    a2.bar(m.ano, m.area_sede_delta_ha, color=cores, width=0.8, lw=0)
    a2.set_ylabel("Acréscimo anual (ha/ano)"); eixo_limpo(a2)
    a2.set_xlim(1983.5, 2026.5); a2.set_xticks(range(1985, 2027, 5))
    a2.legend(handles=[Patch(color=ARDOSIA_MED, label="acréscimo anual"), Patch(color=TERRACOTA, label="anos de obras das minas")], loc="upper left", fontsize=8, frameon=False)
    salvar(fig, "fig_02_mancha_serie", "A sede cresceu 48 vezes em área entre 1984 e 2026, com o maior ritmo entre o Sossego e o S11D",
           "Figura 2 — Área construída contígua da sede de Canaã dos Carajás, 1984–2026 (acima: área mapeada, área ajustada pela acurácia com IC 95 % e MapBiomas como comparação; abaixo: acréscimo anual em hectares). Janelas sombreadas: construção do Sossego (2002–04) e do S11D (2013–16). O valor de 2026 é provisório (último ano da série, sem confirmação temporal).",
           F_MANCHA + " MapBiomas Col. 11 (CC-BY).",
           "A área construída da sede passa de menos de 10 ha (1984) para cerca de 140 ha (2000), 1.100 ha (2010), 2.600 ha (2022) e 3.700 ha (2026); os saltos anuais concentram-se nas obras das minas e no pós-2022.",
           kicker="Mancha urbana")


def fig_03():
    import geopandas as gpd
    anos = [1990, 2000, 2010, 2022, 2026]
    fig, axes = plt.subplots(1, 5, figsize=(13, 4.0))
    mun = gpd.read_parquet(GEO / "mancha_propria" / "mancha30_2026.parquet")
    b = mun[mun.classe == 1].total_bounds
    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    meio = max(b[2] - b[0], b[3] - b[1]) / 2 + 1200
    prev = None
    for ax, ano in zip(axes, anos):
        g = gpd.read_parquet(GEO / "mancha_propria" / f"mancha30_{ano}.parquet")
        if prev is not None:
            prev[prev.classe.isin([1, 2])].plot(ax=ax, facecolor=FILETE, edgecolor="none")
        g[g.classe == 3].plot(ax=ax, facecolor=COR_MINERACAO, edgecolor="none")
        g[g.classe == 2].plot(ax=ax, facecolor=COR_URBANO, alpha=0.45, edgecolor="none")
        g[g.classe == 1].plot(ax=ax, facecolor=COR_URBANO, edgecolor="none")
        g[g.classe == 4].plot(ax=ax, facecolor="none", edgecolor=COR_LOTEAMENTO, lw=0.5, hatch="////")
        ax.set_xlim(cx - meio, cx + meio); ax.set_ylim(cy - meio, cy + meio); ax.set_aspect("equal"); ax.axis("off")
        sede = g[g.classe == 1].area_ha.sum()
        ax.set_title(f"{ano}\n{br(sede)} ha", loc="center", fontsize=11, fontfamily=SERIF, color=TINTA, pad=6)
        prev = g
    # escala 5 km
    ax = axes[-1]
    x0, y0 = cx - meio + 800, cy - meio + 700
    ax.plot([x0, x0 + 5000], [y0, y0], color=TINTA, lw=1.5); ax.text(x0 + 2500, y0 + 250, "5 km", ha="center", fontsize=8, fontfamily=SANS, color=TINTA)
    fig.legend(handles=[Patch(color=COR_URBANO, label="sede contígua (MapBiomas 24)"), Patch(color=COR_URBANO, alpha=0.45, label="outros núcleos"),
                        Patch(color=COR_MINERACAO, label="construído em mineração (MapBiomas 30)"), Patch(color=FILETE, label="mancha do painel anterior"),
                        Patch(facecolor="none", edgecolor=COR_LOTEAMENTO, hatch="////", label="loteamento sem construção (IBGE AU 2022)")],
               loc="lower center", ncol=5, fontsize=8, frameon=False, bbox_to_anchor=(0.5, 0.045))
    fig.subplots_adjust(top=0.80, bottom=0.13, wspace=0.05)
    _titulo(fig, "A sede de Canaã dos Carajás em cinco cortes: 1990, 2000, 2010, 2022 e 2026", "Mancha urbana")
    _salvar(fig, FIG / "fig_03_mapas_censos", fonte="Fonte: " + F_MANCHA + " Janela de 26,6 × 22,2 km, EPSG:31982. Cores das classes: legenda MapBiomas Col. 11 e estilo oficial IBGE (Áreas Urbanizadas 2022).")
    registrar("fig_03_mapas_censos", "A sede em cinco cortes", "Figura 3 — Área construída classificada (30 m) nos anos de 1990, 2000, 2010, 2022 e 2026; em cinza, a mancha do painel anterior. Hachura: loteamentos aprovados sem construção (Áreas Urbanizadas 2022).",
              F_MANCHA, "Cinco mapas na mesma escala mostram a sede passando de um núcleo de 46 ha em 1990 para uma mancha de 3,7 mil ha em 2026, com expansão para oeste e noroeste.")
    print("  fig_03_mapas_censos")


def fig_04():
    import geopandas as gpd
    import rasterio
    with rasterio.open(GEO / "mancha_propria" / "ano_urbanizacao30.tif") as r:
        arr = r.read(1).astype(float); ext = [r.bounds.left, r.bounds.right, r.bounds.bottom, r.bounds.top]
    arr[arr <= 0] = np.nan
    limites = [1983, 1994.5, 2004.5, 2016.5, 2022.5, 2026.5]
    rot = ["1984–1994\nassentamento a município", "1995–2004\naté o Sossego", "2005–2016\nSossego a S11D", "2017–2022\npós-S11D", "2023–2026\nprovisório"]
    # mais antigo = escuro, mais recente = claro; vermelhos derivados da classe 24 do MapBiomas
    # (decisão do usuário, 10/09/2026: classe urbana sempre no padrão IBGE/MapBiomas)
    cmap = ListedColormap(rampa_urbana(5))
    norm = BoundaryNorm(limites, cmap.N)
    fig, ax = plt.subplots(figsize=(9.2, 8))
    ax.set_facecolor(PAPEL_CL)
    im = ax.imshow(arr, extent=ext, cmap=cmap, norm=norm, interpolation="nearest", origin="upper")
    vias = gpd.read_parquet(GEO / "osm_vias.parquet")
    vias.plot(ax=ax, color=PEDRA, lw=0.35, alpha=0.7)
    nuc = gpd.read_parquet(GEO / "mancha_propria" / "mancha30_1990.parquet")
    nuc = nuc[nuc.classe == 1].dissolve().geometry.centroid.iloc[0]
    # cruz em tinta com halo papel: a terracota sumia sobre os vermelhos da rampa urbana
    ax.scatter([nuc.x], [nuc.y], marker="x", s=70, color=PAPEL_CL, lw=3.2, zorder=5)
    ax.scatter([nuc.x], [nuc.y], marker="x", s=60, color=TINTA, lw=1.6, zorder=6)
    ax.annotate("núcleo de 1990", (nuc.x, nuc.y), xytext=(8, -12), textcoords="offset points", fontsize=8, color=TINTA, fontfamily=SANS,
                bbox=dict(boxstyle="square,pad=0.15", fc=PAPEL_CL, ec="none", alpha=0.85))
    g26 = gpd.read_parquet(GEO / "mancha_propria" / "mancha30_2026.parquet")
    b = g26[g26.classe == 1].total_bounds
    pad = 1500
    ax.set_xlim(b[0] - pad, b[2] + pad); ax.set_ylim(b[1] - pad, b[3] + pad); ax.set_aspect("equal"); ax.axis("off")
    x0, y0 = b[0] - pad + 400, b[1] - pad + 400
    ax.plot([x0, x0 + 2000], [y0, y0], color=TINTA, lw=1.5); ax.text(x0 + 1000, y0 + 150, "2 km", ha="center", fontsize=8, fontfamily=SANS, color=TINTA)
    ax.annotate("N", xy=(b[2] + pad - 500, b[3] + pad - 400), xytext=(b[2] + pad - 500, b[3] + pad - 1400), ha="center", fontsize=9, fontfamily=SANS, color=TINTA,
                arrowprops=dict(arrowstyle="-|>", color=TINTA, lw=1))
    handles = [Patch(color=cmap(i), label=rot[i]) for i in range(5)] + [Line2D([0], [0], color=PEDRA, lw=0.8, label="vias (OSM)")]
    ax.legend(handles=handles, loc="lower right", fontsize=8, frameon=True, facecolor=PAPEL_CL, edgecolor=FILETE, title="primeiro ano urbano", title_fontsize=8.5)
    fig.subplots_adjust(top=0.90, bottom=0.04, left=0.02, right=0.98)
    _titulo(fig, "Metade da cidade de 2026 foi construída entre o Sossego e o S11D", "Ano de urbanização")
    _salvar(fig, FIG / "fig_04_ano_urbanizacao", fonte="Fonte: " + F_MANCHA + " Vias: OpenStreetMap (ODbL). Cores: vermelhos derivados da classe 24 (Área urbanizada) da legenda MapBiomas.")
    registrar("fig_04_ano_urbanizacao", "Ano de urbanização", "Figura 4 — Primeiro ano em que cada pixel de 30 m da sede foi classificado como construído (série própria, 1984–2026), agrupado pelos ciclos minerais; cruz: centroide do núcleo de 1990.",
              F_MANCHA, "Os anéis de expansão mostram o núcleo de assentamento ao centro, o espraiamento para oeste e noroeste entre 2005 e 2016 e os loteamentos periféricos recentes ao sul e ao norte.")
    print("  fig_04_ano_urbanizacao")


def fig_05():
    c = pd.read_parquet(GEO / "estatisticas_mancha_censos.parquet")
    per = pd.read_parquet(GEO / "estatisticas_mancha_periodos.parquet")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.4), gridspec_kw=dict(width_ratios=[3, 2]))
    x = np.arange(len(c))
    a1.errorbar(x, c.densidade_ajustada_hab_ha, yerr=[c.densidade_ajustada_hab_ha - c.densidade_ajustada_min_hab_ha, c.densidade_ajustada_max_hab_ha - c.densidade_ajustada_hab_ha],
                fmt="o", color=ARDOSIA, ms=8, capsize=4, lw=1.4, label="densidade ajustada (IC 95 % da área)")
    a1.plot(x, c.densidade_bruta_hab_ha, marker="s", ms=6, color=ARDOSIA_CL, ls=(0, (4, 2)), lw=1.4, label="densidade sobre a área mapeada")
    for xi, v in zip(x, c.densidade_ajustada_hab_ha):
        a1.annotate(br(v, 1), (xi, v), xytext=(10, 0), textcoords="offset points", fontsize=8.5, color=TINTA, fontfamily=SANS, va="center")
    a1.set_xticks(x); a1.set_xticklabels(c.ano.astype(int)); a1.set_ylim(0, 50); a1.set_ylabel("Habitantes por hectare construído"); eixo_limpo(a1)
    a1.legend(loc="lower left", fontsize=8, frameon=False)
    p = per[per.periodo.isin(["2000-2010", "2010-2022"])]
    a2.bar(np.arange(2), p.ods_11_3_1_razao, color=[TERRACOTA, ARDOSIA], width=0.55, lw=0)
    a2.axhline(1, color=PEDRA, lw=0.8, ls=(0, (3, 3)))
    for i, v in enumerate(p.ods_11_3_1_razao):
        a2.text(i, v + 0.03, br(v, 2), ha="center", fontsize=9, color=TINTA, fontfamily=SANS)
    a2.set_xticks([0, 1]); a2.set_xticklabels(["2000–2010", "2010–2022"]); a2.set_ylim(0, 1.5); a2.set_ylabel("Razão ODS 11.3.1 (solo / população)"); eixo_limpo(a2)
    a2.text(0.5, 1.06, "> 1: espraiamento   < 1: adensamento", ha="center", fontsize=8, color=PEDRA, fontfamily=SANS)
    salvar(fig, "fig_05_densidade", "A cidade se espraiou nos anos 2000 e adensou nos anos 2010",
           "Figura 5 — Densidade populacional da sede sobre a área construída (esquerda; barras = IC 95 % da área ajustada) e razão entre a taxa de consumo de solo e a taxa de crescimento populacional (ODS 11.3.1, direita).",
           F_MANCHA, "A densidade ajustada cai de 36 para 24 hab./ha entre 2000 e 2010 (razão ODS 1,23, espraiamento) e sobe para 29 hab./ha em 2022 (razão 0,76, adensamento).",
           kicker="Densidade e forma")


def fig_06():
    an = pd.read_parquet(AN / "coortes_chegada_anual.parquet")
    co = pd.read_parquet(AN / "coortes_chegada.parquet")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.5, 4.8), gridspec_kw=dict(width_ratios=[3, 2]))
    a = an[(an.censo == 2022) & an.ano_num.notna() & (an.ano_num >= 1985)].sort_values("ano_num")
    sombrear_obras(a1)
    a1.bar(a.ano_num, a.valor, color=ARDOSIA, width=0.8, lw=0)
    a1.errorbar(a.ano_num, a.valor, yerr=1.96 * a.ep, fmt="none", ecolor=PEDRA, elinewidth=0.7, capsize=0)
    marcos_verticais(a1, y=a.valor.max() * 1.02)
    a1.set_xlim(1984, 2023); a1.set_ylabel("Residentes em 2022 por ano de chegada"); eixo_limpo(a1)
    a1.set_yticks(a1.get_yticks()); a1.set_yticklabels([br(v) for v in a1.get_yticks()])
    a1.text(1996, a.valor.max() * 0.62, "anos com n insuficiente\nforam fundidos e omitidos", fontsize=7.5, color=PEDRA, fontfamily=SANS)
    # painel 2: % dos chegados por período, 2000/2010/2022 (município)
    per = list(CICLOS)
    c = co[(co.geografia == "canaa_municipio") & (co.estatistica == "proporcao") & co.periodo.isin(per)]
    piv = c.pivot(index="periodo", columns="censo", values="valor").reindex(per)
    y = np.arange(len(per))
    cores = {2000: ARDOSIA_CL, 2010: ARDOSIA_MED, 2022: ARDOSIA}
    h = 0.26
    for i, censo in enumerate([2000, 2010, 2022]):
        if censo in piv:
            a2.barh(y + (i - 1) * h, piv[censo].fillna(0), height=h, color=cores[censo], lw=0, label=f"Censo {censo}")
    a2.set_yticks(y); a2.set_yticklabels([CICLOS[p].split(" (")[0] + "\n" + CICLOS[p].split(" (")[1].rstrip(")") for p in per], fontsize=8)
    a2.invert_yaxis(); a2.set_xlabel("% dos residentes não naturais, por período de chegada"); eixo_limpo(a2, grade_y=False); a2.grid(axis="x", color=FILETE_CL, lw=0.7); a2.set_axisbelow(True)
    a2.legend(loc="lower right", fontsize=8, frameon=False)
    salvar(fig, "fig_06_coortes_chegada", "Seis em cada dez moradores não naturais chegaram depois do início das obras do S11D",
           "Figura 6 — Esquerda: residentes de Canaã dos Carajás em 2022 não naturais do município, por ano de chegada (barras de erro: IC 95 %; anos com n insuficiente fundidos pelo controle de revelação e omitidos). Direita: distribuição por período de chegada nos Censos 2000, 2010 e 2022.",
           F_MICRO, "As chegadas sobreviventes em 2022 sobem em degraus com as obras do Sossego (2002–04) e do S11D (2013–16) e disparam de 2017 em diante; 60 % dos não naturais chegaram a partir de 2013.",
           kicker="Coortes de chegada")


def fig_07():
    faixas = [f"{a:02d}_{a+4:02d}" for a in range(0, 80, 5)] + ["80_mais"]
    rot = [rotulo(f, "faixa_etaria") for f in faixas]

    def universo(ano):
        if ano == 2022:
            t = pd.read_parquet(PROC / "ibge" / "t9514_idade_2022.parquet"); hm, ml = "Homens", "Mulheres"
        else:
            t = pd.read_parquet(PROC / "ibge" / "t1552_idade_2000_2010.parquet"); t = t[(t.Ano == str(ano)) & (t["Situação do domicílio"] == "Total")]; hm, ml = "Homem", "Mulher"
        t = t[t["Forma de declaração da idade"] == "Total"]
        out = {}
        for sexo, key in ((hm, "M"), (ml, "F")):
            s = t[t.Sexo == sexo].set_index("Idade").valor
            v = []
            for f in faixas:
                if f == "80_mais":
                    v.append(np.nansum([s.get(k, 0) for k in s.index if k.split(" ")[0].isdigit() and int(k.split(" ")[0]) >= 80 and " a " in k] + [s.get("100 anos ou mais", 0)]))
                else:
                    a, b = f.split("_"); v.append(s.get(f"{int(a)} a {int(b)} anos", np.nan))
            v = np.array(v, dtype=float)
            if np.isnan(v).any():
                print(f"  [aviso] pirâmide {ano} {key}: faixas ausentes {[f for f, x in zip(faixas, v) if x != x]} → 0")
            out[key] = np.nan_to_num(v)
        tot = out["M"].sum() + out["F"].sum()
        return {k: v / tot * 100 for k, v in out.items()}, tot

    def amostra_1991():
        e = pd.read_parquet(PROC / "microdados" / "estimativas.parquet")
        e = e[(e.geografia == "parauapebas_municipio") & (e.censo == 1991) & (e.universo == "pessoas") & (e.dim1 == "sexo") & (e.dim2 == "faixa_etaria") & (e.estatistica == "contagem")]
        out = {}
        for key in ("M", "F"):
            s = e[e.cat1 == key].set_index("cat2").valor
            v = np.zeros(len(faixas))
            for cat, val in s.items():
                partes = cat.split(":", 1)[1].split("+") if cat.startswith("outros:") else [cat]
                idx = faixas.index("80_mais") if any(int(p.split("_")[0]) >= 65 for p in partes) and len(partes) > 1 else faixas.index(partes[0])
                v[idx] += val
            out[key] = v
        tot = out["M"].sum() + out["F"].sum()
        return {k: v / tot * 100 for k, v in out.items()}, tot

    paineis = [("Parauapebas 1991\n(inclui o atual Canaã; amostra)", amostra_1991()), ("Canaã 2000", universo(2000)), ("Canaã 2010", universo(2010)), ("Canaã 2022", universo(2022))]
    fig, axes = plt.subplots(1, 4, figsize=(13, 5), sharey=True)
    y = np.arange(len(faixas))
    for ax, (tit, (d, tot)) in zip(axes, paineis):
        ax.barh(y, -d["M"], color=ARDOSIA, height=0.82, lw=0)
        ax.barh(y, d["F"], color=TERRACOTA, height=0.82, lw=0)
        ax.set_xlim(-9, 9); ax.set_xticks([-8, -4, 0, 4, 8]); ax.set_xticklabels(["8", "4", "0", "4", "8"])
        ax.set_title(f"{tit}\n{br(tot)} hab.", fontsize=10, fontfamily=SERIF, color=TINTA, loc="center", pad=8)
        ax.axvline(0, color=PAPEL_FIG, lw=1.5); eixo_limpo(ax, grade_y=False); ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
        ax.set_xlabel("% da população", fontsize=8.5)
    axes[0].set_yticks(y); axes[0].set_yticklabels(rot, fontsize=8)
    axes[0].text(-8.6, len(faixas) - 1.2, "homens", color=ARDOSIA, fontsize=8.5, fontfamily=SANS, fontweight="semibold")
    axes[0].text(8.6, len(faixas) - 1.2, "mulheres", color=TERRACOTA, fontsize=8.5, fontfamily=SANS, fontweight="semibold", ha="right")
    for f in ("80_mais",):
        pass
    fig.text(0.99, 0.012, "Nota: em 2022 a faixa 80+ agrega 80–84 a 100+; em 1991 as faixas ≥ 65 fundidas pelo sigilo estão em 80+.", ha="right", fontsize=7.5, color=PEDRA, fontfamily=SANS)
    salvar(fig, "fig_07_piramides", "De base larga a adulta jovem: pirâmides etárias, 1991–2022",
           "Figura 7 — Pirâmides etárias (% da população total): Parauapebas 1991 (amostra; inclui o atual Canaã), e Canaã dos Carajás 2000, 2010 e 2022 (Universo, SIDRA t/1552 e t/9514).",
           "IBGE — Censos 1991 (amostra, estimativa própria), 2000, 2010 e 2022 (Universo).",
           "A pirâmide passa de base larga (44 % com menos de 15 anos em 1991) a um perfil concentrado nos adultos jovens de 20 a 39 anos em 2010 e 2022, típico de cidade receptora de migrantes em idade ativa.",
           kicker="Estrutura etária", topo=0.86)


def fig_08():
    pf = pd.read_parquet(AN / "perfil_migrantes.parquet")
    s = pf[(pf.geografia == "canaa_municipio") & (pf.censo == 2022)]
    itens = [("nivel_instrucao", "superior_completo"), ("nivel_instrucao", "sem_instrucao_fund_incompleto"), ("posicao", "empregado_com_carteira"), ("posicao", "conta_propria"),
             ("formal", "sim"), ("setor", "extrativa_mineral"), ("setor", "construcao"), ("setor", "comercio"), ("setor", "servicos"), ("setor", "adm_publica_educacao_saude"),
             ("grupo_etario", "25_39"), ("grupo_etario", "60_mais"), ("sexo", "M"), ("cor_raca", "branca"), ("cor_raca", "parda"), ("naturalidade", "outra_uf")]
    rows = []
    for dim, cat in itens:
        r = s[(s.dimensao == dim) & (s.categoria == cat)]
        if len(r) and r.p_migrante.notna().all() and r.p_nao_migrante.notna().all():
            r = r.iloc[0]
            rot_ = {("formal", "sim"): "Vínculo formal", ("ocupado", "sim"): "Ocupado"}.get((dim, cat), f"{r.rotulo}  ({dim.replace('_', ' ')})" if dim in ("sexo", "cor_raca", "naturalidade") else r.rotulo)
            rows.append(dict(rot=rot_, m=r.p_migrante, n=r.p_nao_migrante,
                             em=r.ep_migrante, en=r.ep_nao_migrante, sig=r.significativo_95, dim=dim))
    d = pd.DataFrame(rows)
    d["dif"] = d.m - d.n
    d = d.sort_values("dif")
    fig, ax = plt.subplots(figsize=(9.5, 6.4))
    y = np.arange(len(d))
    for yi, (_, r) in zip(y, d.iterrows()):
        ax.plot([r.n, r.m], [yi, yi], color=FILETE if not r.sig else PEDRA, lw=2.2, zorder=1)
    ax.errorbar(d.n, y, xerr=1.96 * d.en, fmt="o", color=ARDOSIA, ms=8, ecolor=ARDOSIA, elinewidth=0.8, capsize=0, zorder=3, label="não migrantes")
    ax.errorbar(d.m, y, xerr=1.96 * d.em, fmt="o", color=TERRACOTA, ms=8, ecolor=TERRACOTA, elinewidth=0.8, capsize=0, zorder=3, label="migrantes (chegados 2017–2022)")
    for yi, (_, r) in zip(y, d.iterrows()):
        ax.text(max(r.m, r.n) + 1.8, yi, f"{'+' if r.dif > 0 else '−'}{br(abs(r.dif), 1)} p.p.{'' if r.sig else ' (n.s.)'}", va="center", fontsize=8, color=TINTA if r.sig else PEDRA, fontfamily=SANS)
    ax.set_yticks(y); ax.set_yticklabels(d.rot, fontsize=9); ax.set_xlim(0, 75); ax.set_xlabel("% do grupo (barras: IC 95 %)")
    eixo_limpo(ax, grade_y=False); ax.grid(axis="x", color=FILETE_CL, lw=0.7); ax.set_axisbelow(True)
    ax.legend(loc="lower right", fontsize=8.5, frameon=False)
    salvar(fig, "fig_08_seletividade", "Migrantes recentes são mais escolarizados, mais formalizados e mais presentes na mineração e na construção",
           "Figura 8 — Perfil dos migrantes de data fixa (residiam em outro município em 2017) e dos não migrantes, Canaã dos Carajás, 2022: proporção em cada categoria com IC 95 %; diferença em pontos percentuais (n.s. = não significativa a 95 %). Universos: pessoas de 5+ (sexo, idade, cor, naturalidade), 25+ (instrução), ocupados (setor, posição, formalidade).",
           F_MICRO, "Em 2022 os migrantes recentes têm mais superior completo, mais carteira assinada e mais inserção na extrativa e na construção, e menos presença na administração pública e no trabalho por conta própria, com renda média do trabalho igual à dos não migrantes.",
           kicker="Seletividade migratória")


def fig_09():
    oc = pd.read_parquet(AN / "insercao_ocupacional.parquet")
    grupos = [("Agropecuária", ["agropecuaria"], PETROLEO), ("Extrativa mineral", ["extrativa_mineral"], TERRACOTA), ("Construção", ["construcao"], OCRE),
              ("Ind. de transformação", ["transformacao"], BORDO), ("Comércio e serviços", ["comercio", "servicos", "domestico", "outras_atividades"], ARDOSIA),
              ("Adm. pública, educação e saúde", ["adm_publica_educacao_saude"], ARDOSIA_CL), ("Categorias fundidas (sigilo)", ["__outros__"], VIZ_MUTED)]
    geos = [("canaa_municipio", "Canaã dos Carajás"), ("parauapebas_municipio", "Parauapebas"), ("pa", "Pará")]
    censos = [2000, 2010, 2022]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.6), sharey=True)
    for ax, (geo, gr) in zip(axes, geos):
        s = oc[(oc.geografia == geo) & (oc.dimensao == "setor")]
        y = np.arange(len(censos))
        left = np.zeros(len(censos))
        for nome, cats, cor in grupos:
            vals = []
            for c in censos:
                sc = s[s.censo == c]
                if cats == ["__outros__"]:
                    vals.append(sc[sc.categoria.str.startswith("outros:")].valor.sum())
                else:
                    vals.append(sc[sc.categoria.isin(cats)].valor.sum())
            vals = np.array(vals)
            ax.barh(y, vals, left=left, height=0.62, color=cor, lw=0, label=nome, edgecolor=PAPEL_FIG)
            for yi, (l, v) in enumerate(zip(left, vals)):
                if v >= 7:
                    ax.text(l + v / 2, yi, br(v, 0), ha="center", va="center", fontsize=8, color=PAPEL if cor not in (ARDOSIA_CL, VIZ_MUTED, OCRE) else TINTA, fontfamily=SANS)
            left += vals
        ax.set_yticks(y); ax.set_yticklabels([str(c) for c in censos]); ax.set_xlim(0, 100); ax.set_xlabel("% dos ocupados")
        ax.set_title(gr, loc="left", fontsize=11, fontfamily=SERIF, color=TINTA, pad=6); eixo_limpo(ax, grade_y=False); ax.invert_yaxis()
        ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=4, fontsize=8, frameon=False, bbox_to_anchor=(0.5, 0.04))
    salvar(fig, "fig_09_setores", "Da agropecuária à mineração, à construção e aos serviços: ocupados por setor, 2000–2022",
           "Figura 9 — Ocupados por setor de atividade (CNAE harmonizada), Canaã dos Carajás, Parauapebas e Pará, Censos 2000, 2010 e 2022. Comércio e serviços agrega comércio, serviços, serviços domésticos e outras atividades; cinza: categorias fundidas pelo controle de revelação (Canaã 2000: extrativa + construção).",
           F_MICRO, "Em Canaã a agropecuária cai de 55 % dos ocupados em 2000 para 3 % em 2022, enquanto a extrativa mineral chega a 10 % e a construção a 14 %, proporções acima das do Pará e próximas às de Parauapebas.",
           kicker="Inserção ocupacional", topo=0.88, base=0.14)


def fig_10():
    dom = pd.read_parquet(AN / "condicoes_domiciliares.parquet")
    itens = [("agua_rede", "sim", "Água da rede geral"), ("esgoto_adequado", "sim", "Esgoto por rede ou fossa séptica"), ("lixo_coletado", "sim", "Lixo coletado"),
             ("adequacao", "adequada", "Adequado (água+esgoto+lixo)"), ("condicao_ocupacao", "alugado", "Domicílio alugado"), ("densidade_faixa", "mais_de_3", "> 3 moradores por dormitório")]
    fig, axes = plt.subplots(2, 3, figsize=(11.5, 6.2), sharex=True)
    d = dom[dom.geografia == "canaa_municipio"]
    for ax, (dim, cat, tit) in zip(axes.flat, itens):
        for grupo, cor, ls, lab in (("sem_migrante_recente", ARDOSIA, "-", "sem migrante recente"), ("com_migrante_recente", TERRACOTA, (0, (4, 2)), "com migrante recente")):
            s = d[(d.grupo == grupo) & (d.dimensao == dim) & (d.categoria == cat)].sort_values("censo")
            ax.errorbar(s.censo, s.valor, yerr=1.96 * s.ep, color=cor, ls=ls, marker="o", ms=6, lw=1.8, capsize=3, elinewidth=0.8, label=lab)
            if len(s):
                r = s.iloc[-1]
                ax.text(r.censo + 0.5, r.valor, br(r.valor, 0), fontsize=8.5, color=cor, fontfamily=SANS, va="center")
        ax.set_title(tit, loc="left", fontsize=10.5, fontfamily=SERIF, color=TINTA, pad=5)
        ax.set_xlim(1998, 2026); ax.set_xticks([2000, 2010, 2022]); ax.set_ylim(0, 100); eixo_limpo(ax)
    axes[0, 0].set_ylabel("% dos domicílios"); axes[1, 0].set_ylabel("% dos domicílios")
    axes[0, 0].legend(loc="upper left", fontsize=8, frameon=False)
    salvar(fig, "fig_10_domicilios", "Infraestrutura converge; a moradia alugada e o adensamento marcam os domicílios com migrantes",
           "Figura 10 — Condições dos domicílios particulares permanentes de Canaã dos Carajás, 2000–2022, segundo a presença de morador que residia em outro município cinco anos antes (barras: IC 95 %; células suprimidas omitidas).",
           F_MICRO, "Água, esgoto e lixo melhoram para todos entre 2000 e 2022, mas o aluguel passa de 10 % para 51 % nos domicílios com migrante recente, contra 20 % nos demais, e o adensamento por dormitório é o dobro.",
           kicker="Condições domiciliares")


def fig_11():
    import geopandas as gpd
    st = pd.read_parquet(AN / "setores_sede_indicadores.parquet")
    s10 = gpd.read_parquet(PROC / "setores" / "setores_2010.parquet"); s22 = gpd.read_parquet(PROC / "setores" / "setores_2022.parquet")
    s10 = s10[["cod_setor", "geometry"]].assign(cod_setor=s10.cod_setor.astype(str)); s22 = s22[["cod_setor", "geometry"]].assign(cod_setor=s22.cod_setor.astype(str))
    g10 = s10.merge(st[st.ano == 2010], on="cod_setor"); g22 = s22.merge(st[st.ano == 2022], on="cod_setor")
    g26 = gpd.read_parquet(GEO / "mancha_propria" / "mancha30_2026.parquet"); g26 = g26[g26.classe == 1]
    vias = gpd.read_parquet(GEO / "osm_vias.parquet")
    b = g22.total_bounds; pad = 500
    paineis = [(g10, "agua_pct", "Água da rede geral, 2010"), (g22, "agua_pct", "Água da rede geral, 2022"),
               (g10, "esgoto_pct", "Esgoto (rede geral/pluvial), 2010"), (g22, "esgoto_pct", "Esgoto (rede geral), 2022")]
    fig, axes = plt.subplots(2, 2, figsize=(10, 9.6))
    cmap = ListedColormap(VIZ_SEQUENTIAL); norm = BoundaryNorm([0, 20, 40, 60, 80, 100], cmap.N)
    for ax, (g, col, tit) in zip(axes.flat, paineis):
        ax.set_facecolor(PAPEL_CL)
        g26.plot(ax=ax, facecolor=COR_URBANO, alpha=0.25, edgecolor="none", zorder=0)
        g.plot(ax=ax, column=col, cmap=cmap, norm=norm, edgecolor=PAPEL, lw=0.5, zorder=1, missing_kwds=dict(facecolor="none", edgecolor=PEDRA, hatch="///", lw=0.3))
        vias.plot(ax=ax, color=PEDRA, lw=0.3, alpha=0.5, zorder=2)
        ax.set_xlim(b[0] - pad, b[2] + pad); ax.set_ylim(b[1] - pad, b[3] + pad); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(tit, loc="left", fontsize=11, fontfamily=SERIF, color=TINTA, pad=4)
    handles = [Patch(color=cmap(i), label=l) for i, l in enumerate(["0–20 %", "20–40 %", "40–60 %", "60–80 %", "80–100 %"])] + [Patch(facecolor=COR_URBANO, alpha=0.25, label="mancha construída 2026 (MapBiomas 24)")]
    fig.legend(handles=handles, loc="lower center", ncol=6, fontsize=8.5, frameon=False, bbox_to_anchor=(0.5, 0.035))
    x0, y0 = b[0] - pad + 300, b[1] - pad + 300
    axes[1, 1].plot([x0, x0 + 2000], [y0, y0], color=TINTA, lw=1.5); axes[1, 1].text(x0 + 1000, y0 + 120, "2 km", ha="center", fontsize=8, fontfamily=SANS, color=TINTA)
    fig.subplots_adjust(top=0.86, bottom=0.08, left=0.02, right=0.98, hspace=0.08, wspace=0.03)
    _titulo(fig, "Água e esgoto por setor censitário da sede: o centro atendido primeiro, a periferia depois", "Desigualdade intraurbana")
    _salvar(fig, FIG / "fig_11_setores_mapa", fonte="Fonte: IBGE, agregados por setor censitário do Universo (2010: 24 setores da sede; 2022: 88). Malhas IBGE; vias OSM (ODbL). Escala sequencial Ardósia em cinco classes fixas.")
    registrar("fig_11_setores_mapa", "Água e esgoto por setor", "Figura 11 — Percentual de domicílios com água da rede geral e com esgoto por rede nos setores censitários da sede, 2010 e 2022 (classes fixas de 20 p.p.; ao fundo, a mancha construída de 2026). O esgoto de 2010 inclui rede pluvial.",
              "IBGE — agregados por setor censitário (2010, 2022).", "Em 2010 a rede de esgoto se restringia aos setores centrais; em 2022 a cobertura de água e esgoto se generaliza, mas os setores periféricos mais novos permanecem abaixo de 40 %.")
    print("  fig_11_setores_mapa")


def fig_12():
    pg = pd.read_parquet(AN / "painel_amc_grupos.parquet")
    itens = [("pct_imigrante_5anos", "Imigrantes de data fixa (% da população)"), ("pct_ocupado_extrativo", "Ocupados na extrativa (%)"),
             ("pct_alugado", "População em domicílio alugado (%)"), ("renda_trabalho_media_r2022", "Renda média do trabalho (R$ jul/2022)")]
    estilo = {"Canaã dos Carajás": (TERRACOTA, "-", 2.4, "o"), "Parauapebas": (ARDOSIA, "-", 1.8, "s"), "Sudeste Paraense — outros mineradores": (VIZ_MUTED, "-", 1.4, "^"),
              "Sudeste Paraense — não mineradores": (VIZ_MUTED, (0, (4, 2)), 1.4, "v"), "Pará — mineradores (demais)": (PEDRA, (0, (1, 2)), 1.2, "D"), "Pará — não mineradores (demais)": (PEDRA, (0, (4, 2)), 1.2, "x")}
    fig, axes = plt.subplots(1, 4, figsize=(13, 4.2))
    for ax, (col, tit) in zip(axes, itens):
        for grupo, (cor, ls, lw, mk) in estilo.items():
            s = pg[pg.grupo == grupo].sort_values("censo")
            ax.plot(s.censo, s[col], color=cor, ls=ls, lw=lw, marker=mk, ms=5, label=grupo)
        r = pg[(pg.grupo == "Canaã dos Carajás") & (pg.censo == 2022)].iloc[0]
        ax.text(2022.6, r[col], br(r[col], 0 if "renda" in col else 1), color=TERRACOTA, fontsize=8.5, fontfamily=SANS, va="center")
        ax.set_title(tit, loc="left", fontsize=9, fontfamily=SERIF, color=TINTA, pad=5); ax.set_xticks([2000, 2010, 2022]); ax.set_xlim(1998, 2027); ax.set_ylim(0, None); eixo_limpo(ax)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, fontsize=8, frameon=False, bbox_to_anchor=(0.5, 0.04))
    salvar(fig, "fig_12_comparacao_regional", "Canaã se descola dos municípios comparáveis do Sudeste Paraense a partir de 2010",
           "Figura 12 — Canaã dos Carajás, Parauapebas e grupos de municípios do Pará (Áreas Mínimas Comparáveis 2000–2022, médias ponderadas pela população; grupos por porte de CFEM per capita), Censos 2000, 2010 e 2022.",
           "Painel municipal 2000–2022 do projeto irmão migracoes-mineracao (microdados da amostra dos Censos; ANM).",
           "Enquanto a imigração recente cai em todos os grupos de comparação entre 2000 e 2022, em Canaã ela dobra; a inserção na extrativa, o aluguel e a renda do trabalho também se afastam dos municípios não mineradores do Sudeste Paraense.",
           kicker="Comparação regional", topo=0.84, base=0.16)


def fig_13():
    e = pd.read_parquet(AN / "economia_anual.parquet")
    e = e[(e.ano >= 2002) & (e.ano <= 2026)]
    fig, (a1, a2, a3) = plt.subplots(3, 1, figsize=(10, 8), sharex=True, gridspec_kw=dict(hspace=0.15))
    for ax in (a1, a2, a3):
        sombrear_obras(ax)
    a1.bar(e.ano, e.area_sede_delta_ha, color=ARDOSIA_MED, width=0.8, lw=0)
    a1.set_ylabel("Área acrescida\n(ha/ano)"); eixo_limpo(a1)
    a1.text(2003, a1.get_ylim()[1] * 0.9, "obras do Sossego", color=TERRACOTA, fontsize=8, fontfamily=SANS, ha="center")
    a1.text(2014.5, a1.get_ylim()[1] * 0.9, "obras do S11D", color=TERRACOTA, fontsize=8, fontfamily=SANS, ha="center")
    cf = e.cfem_r2022 / 1e6
    cores = [VIZ_MUTED if a == 2026 else TERRACOTA for a in e.ano]
    a2.bar(e.ano, cf, color=cores, width=0.8, lw=0)
    a2.set_ylabel("CFEM distribuída\n(R$ mi de jul/2022)"); eixo_limpo(a2)
    a2.text(2026, cf.max() * 0.15, "2026\nparcial", ha="center", fontsize=7.5, color=PEDRA, fontfamily=SANS)
    a3.plot(e.ano, e.pib_per_capita_r / 1000, color=ARDOSIA, lw=2, marker="o", ms=4)
    a3.set_ylabel("PIB per capita\n(R$ mil correntes)"); eixo_limpo(a3); a3.set_xticks(range(2002, 2027, 2))
    a3.text(2021, e.loc[e.ano == 2021, "pib_per_capita_r"].iloc[0] / 1000 - 90, "2021: pico do minério\ne população estimada\nsubestimada", fontsize=7.5, color=PEDRA, fontfamily=SANS, ha="right")
    salvar(fig, "fig_13_economia", "A cidade cresce nas obras; os royalties chegam depois",
           "Figura 13 — Área acrescida anualmente à sede (alto), CFEM distribuída ao município em R$ de julho de 2022 (meio) e PIB per capita a preços correntes (baixo), 2002–2026. Janelas sombreadas: construção das minas.",
           F_MANCHA + " ANM (CFEM); IBGE (PIB dos Municípios, estimativas de população); IPCA para o deflacionamento.",
           "O acréscimo de área concentra-se nas fases de obra (2002–04, 2013–16) e no pós-2022, enquanto a CFEM só se torna relevante a partir de 2018 com o S11D; a correlação contemporânea entre CFEM e área acrescida é nula ou negativa.",
           kicker="Mineração e economia")


def fig_14():
    b = pd.read_parquet(AN / "baseline_1991.parquet")
    itens = ["Migrantes de data fixa (%)", "Ocupados na agropecuária (%)", "Ocupados na extrativa mineral (%)", "Ocupados na construção (%)", "Ocupados nos serviços (%)",
             "Ocupados formais (%)", "Sem instrução / fund. incompleto, 25+ (%)", "Superior completo, 25+ (%)", "Domicílios com água da rede (%)", "Esgoto adequado (%)",
             "Lixo coletado (%)", "Domicílios alugados (%)", "Mais de 3 moradores/dormitório (%)", "População de 0–14 anos (%)"]
    d = b[b.indicador.isin(itens)].set_index("indicador").reindex(itens).reset_index()
    fig, ax = plt.subplots(figsize=(9.5, 6.4))
    y = np.arange(len(d))
    for yi, (_, r) in zip(y, d.iterrows()):
        if r.parauapebas_1991 == r.parauapebas_1991 and r.canaa_2022 == r.canaa_2022:
            ax.plot([r.parauapebas_1991, r.canaa_2022], [yi, yi], color=FILETE, lw=2.2, zorder=1)
    ax.errorbar(d.parauapebas_1991, y, xerr=1.96 * d.parauapebas_1991_ep, fmt="o", color=ARDOSIA_CL, ms=8, ecolor=ARDOSIA_CL, elinewidth=0.8, capsize=0, zorder=3, label="Parauapebas 1991 (inclui Canaã)")
    ax.errorbar(d.canaa_2000, y, xerr=1.96 * d.canaa_2000_ep, fmt="s", color=ARDOSIA_MED, ms=6, ecolor=ARDOSIA_MED, elinewidth=0.8, capsize=0, zorder=3, label="Canaã 2000")
    ax.errorbar(d.canaa_2022, y, xerr=1.96 * d.canaa_2022_ep, fmt="o", color=ARDOSIA, ms=8, ecolor=ARDOSIA, elinewidth=0.8, capsize=0, zorder=4, label="Canaã 2022")
    ax.set_yticks(y); ax.set_yticklabels(d.indicador, fontsize=9); ax.invert_yaxis(); ax.set_xlim(0, 100); ax.set_xlabel("% (barras: IC 95 %)")
    eixo_limpo(ax, grade_y=False); ax.grid(axis="x", color=FILETE_CL, lw=0.7); ax.set_axisbelow(True)
    ax.legend(loc="lower right", fontsize=8.5, frameon=False)
    salvar(fig, "fig_14_baseline_1991", "Trinta anos entre a fronteira agrícola e a cidade mineradora: 1991, 2000 e 2022",
           "Figura 14 — Indicadores selecionados para Parauapebas em 1991 (município que então incluía o atual Canaã dos Carajás), Canaã em 2000 e Canaã em 2022 (IC 95 %). Células suprimidas pelo controle de revelação omitidas.",
           F_MICRO, "Entre a linha de base de 1991 e 2022, a agropecuária deixa de ser o principal setor, a formalidade quase dobra, o superior completo passa de 2 % para 13 % e água, esgoto e lixo coletado saltam de patamares de 20–50 % para 67–93 %.",
           kicker="Linha de base pré-mineral")


def fig_15():
    cad = pd.read_parquet(AN / "cadeia_mineral_migrantes.parquet")
    oc = pd.read_parquet(AN / "cadeia_mineral_por_origem_coorte.parquet")
    elos = ["extrativa_mineral", "construcao", "transformacao", "cadeia_ampliada"]
    rot_elo = {"extrativa_mineral": "Extrativa mineral (B)", "construcao": "Construção (F)", "transformacao": "Ind. de transformação (C)", "cadeia_ampliada": "Cadeia ampliada (B+F+C)"}
    cor_elo = {"extrativa_mineral": TERRACOTA, "construcao": OCRE, "transformacao": BORDO}
    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(13.5, 5.2), gridspec_kw=dict(width_ratios=[3, 2, 2.4]))
    # (a) dumbbell: migrantes × não migrantes por elo, 2010 e 2022
    c = cad[cad.geografia == "canaa_municipio"]
    linhas = [(censo, elo) for censo in (2010, 2022) for elo in elos]
    y = np.arange(len(linhas))
    for yi, (censo, elo) in zip(y, linhas):
        r = c[(c.censo == censo) & (c.elo == elo)]
        if len(r) == 0:
            continue
        r = r.iloc[0]
        a1.plot([r.p_nao_migrante, r.p_migrante], [yi, yi], color=PEDRA if r.significativo_95 else FILETE, lw=2.2, zorder=1)
        a1.errorbar([r.p_nao_migrante], [yi], xerr=[1.96 * r.ep_nao_migrante], fmt="o", color=ARDOSIA, ms=8, elinewidth=0.8, zorder=3)
        a1.errorbar([r.p_migrante], [yi], xerr=[1.96 * r.ep_migrante], fmt="o", color=TERRACOTA, ms=8, elinewidth=0.8, zorder=3)
        a1.text(max(r.p_migrante, r.p_nao_migrante) + 1.96 * max(r.ep_migrante, r.ep_nao_migrante) + 0.8, yi, f"×{br(r.razao_seletividade, 2)}{'' if r.significativo_95 else ' (n.s.)'}",
                va="center", fontsize=8, color=TINTA if r.significativo_95 else PEDRA, fontfamily=SANS)
    a1.set_yticks(y); a1.set_yticklabels([f"{rot_elo[e]}\n{censo}" for censo, e in linhas], fontsize=8.5); a1.invert_yaxis(); a1.set_xlim(0, 48)
    a1.axhline(3.5, color=FILETE, lw=0.8); a1.set_xlabel("% dos ocupados do grupo (barras: IC 95 %; ×: razão de seletividade)")
    eixo_limpo(a1, grade_y=False); a1.grid(axis="x", color=FILETE_CL, lw=0.7); a1.set_axisbelow(True)
    a1.legend(handles=[Line2D([0], [0], marker="o", color=ARDOSIA, lw=0, ms=8, label="não migrantes"), Line2D([0], [0], marker="o", color=TERRACOTA, lw=0, ms=8, label="migrantes (data fixa)")],
              loc="upper right", fontsize=8.5, frameon=False)
    a1.set_title("Inserção por elo, 2010 e 2022", loc="left", fontsize=10.5, fontfamily=SERIF, color=TINTA, pad=6)
    # (b) 2022: por tipo de migrante, empilhado por elo
    def empilhar(ax, sub, ordem, rotulos, titulo, xlabel):
        yy = np.arange(len(ordem)); left = np.zeros(len(ordem))
        for elo in ("extrativa_mineral", "construcao", "transformacao"):
            vals = np.array([sub[(sub.categoria == cat) & (sub.elo == elo)].proporcao.sum() for cat in ordem])
            ax.barh(yy, vals, left=left, height=0.6, color=cor_elo[elo], lw=0, label=rot_elo[elo])
            for yi, (l, v) in enumerate(zip(left, vals)):
                if v >= 4:
                    ax.text(l + v / 2, yi, br(v, 1), ha="center", va="center", fontsize=7.5, color=PAPEL if elo != "construcao" else TINTA, fontfamily=SANS)
            left += vals
        for yi, tot in enumerate(left):
            ax.text(tot + 0.6, yi, br(tot, 1), va="center", fontsize=8.5, color=TINTA, fontfamily=SANS)
        ax.set_yticks(yy); ax.set_yticklabels(rotulos, fontsize=8.5); ax.invert_yaxis(); ax.set_xlabel(xlabel)
        ax.set_title(titulo, loc="left", fontsize=10.5, fontfamily=SERIF, color=TINTA, pad=6)
        eixo_limpo(ax, grade_y=False); ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
    s22 = oc[(oc.censo == 2022) & (oc.dimensao == "tipo_mig_5anos")]
    ordem = ["nao_migrante", "intraestadual", "outros:interestadual+internacional"]
    empilhar(a2, s22, ordem, ["Não migrantes", "Migrantes\nintraestaduais", "Migrantes de outra UF\nou do exterior"], "Por origem do migrante, 2022", "% dos ocupados do grupo")
    a2.set_xlim(0, 46)
    t22 = oc[(oc.censo == 2022) & (oc.dimensao == "tempo_moradia_faixa")]
    ordem = ["menos_1", "1_a_4", "5_a_9", "10_a_19", "20_mais"]
    empilhar(a3, t22, ordem, [rotulo(o, "tempo_moradia_faixa") for o in ordem], "Por tempo de moradia no município, 2022", "% dos ocupados da faixa")
    a3.set_xlim(0, 46)
    h, l = a2.get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, fontsize=8.5, frameon=False, bbox_to_anchor=(0.5, 0.045))
    salvar(fig, "fig_15_cadeia_mineral", "Migrantes recentes entram mais na cadeia da mineração, sobretudo pela construção e pela extrativa", 
           "Figura 15 — Ocupados na cadeia produtiva da mineração (extrativa mineral, construção e indústria de transformação), Canaã dos Carajás. Esquerda: migrantes de data fixa e não migrantes por elo, 2010 e 2022 (IC 95 %; × = razão de seletividade; n.s. = não significativa). Centro: por origem do migrante, 2022. Direita: por tempo de moradia, 2022 (com menos de 1 ano, só a construção é publicável). Fornecedores de serviços e transporte à mina não são identificáveis no CNAE-Dom.",
           F_MICRO, "Em 2022, 36 % dos migrantes recentes ocupados estão na cadeia da mineração contra 29 % dos não migrantes (razão 1,23); a diferença vem da construção e da extrativa, é maior entre migrantes de outras UFs e era ainda mais acentuada em 2010, quando os migrantes tinham o dobro da chance de estar na extrativa.",
           kicker="Cadeia da mineração", topo=0.88, base=0.12)


# ============================================================================
FIGURAS = {f.__name__: f for f in (fig_01, fig_02, fig_03, fig_04, fig_05, fig_06, fig_07, fig_08, fig_09, fig_10, fig_11, fig_12, fig_13, fig_14, fig_15)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--so", default=None, help="lista de figuras separadas por vírgula (ex.: fig_01,fig_03)")
    a = ap.parse_args()
    sel = a.so.split(",") if a.so else list(FIGURAS)
    idx_path = FIG / "figuras.json"
    antigo = {d["arquivo"]: d for d in json.loads(idx_path.read_text())} if idx_path.exists() else {}
    for nome in sel:
        FIGURAS[nome]()
    novo = {d["arquivo"]: d for d in INDICE}
    antigo.update(novo)
    idx_path.write_text(json.dumps(sorted(antigo.values(), key=lambda d: d["arquivo"]), ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"índice: {idx_path} ({len(antigo)} figuras)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
