"""
Figuras com a identidade visual Ardósia — usadas pelos três artigos e pelo
site (plano §7: "as mesmas figuras alimentam o site em SVG e o dashboard").

Cada `fig_*` devolve a Figure já pronta; `salvar()` grava PNG 300dpi (para o
DOCX/PDF) e SVG (para o HTML) a partir do mesmo objeto, sempre com a fonte
padrão do projeto no rodapé.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .ardosia_palette import (
    ARDOSIA, TERRACOTA, PETROLEO, OCRE, BORDO, ARDOSIA_CL,
    VIZ_CATEGORICAL, VIZ_SEQUENTIAL, VIZ_DIVERGING, VIZ_MUTED,
    PEDRA, SERIF, SANS, apply_ardosia, emphasis,
)

FONTE_PADRAO = "Elaboração própria a partir dos microdados da amostra do Censo Demográfico — IBGE."

apply_ardosia()


def _titulo(fig: plt.Figure, titulo_txt: str, kicker: str = None):
    """Título+kicker de TODAS as figuras deste módulo — em coordenadas da
    FIGURA (0-1), não dos eixos. O `titulo()` de ardosia_palette posiciona o
    título como fração da ALTURA DO AXES, e chamar `fig.tight_layout()`
    depois dele mexe nos eixos sem re-ajustar essa fração — as duas linhas
    saem sobrepostas (bug visto em mapas E em gráficos de barra comuns).
    Sempre chamar `fig.tight_layout(rect=[0,0,1,0.88])` (ou
    `fig.subplots_adjust(top=...)` nos mapas) ANTES desta função, nunca
    depois — a margem de 12% do topo é reservada para o título."""
    if kicker:
        fig.text(0.02, 0.98, kicker.upper(), fontsize=8, color=TERRACOTA,
                  fontweight="semibold", fontfamily=SANS, ha="left", va="top")
        fig.text(0.02, 0.955, titulo_txt, fontsize=14, color="#1B1F23",
                  fontfamily=SERIF, ha="left", va="top")
    else:
        fig.text(0.02, 0.98, titulo_txt, fontsize=14, color="#1B1F23",
                  fontfamily=SERIF, ha="left", va="top")


def salvar(fig: plt.Figure, caminho_base: str | Path, fonte: str = FONTE_PADRAO):
    """Grava `{caminho_base}.png` (300dpi) e `.svg`, com a fonte no rodapé."""
    caminho_base = Path(caminho_base)
    if fonte:
        fig.text(0.01, 0.01, fonte, fontsize=7, color=PEDRA, ha="left", va="bottom")
    caminho_base.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(caminho_base.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(caminho_base.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)


def fig_barras_uf(
    serie: pd.Series, titulo_txt: str, kicker: str = None, cor=ARDOSIA,
    destaque: list[str] | None = None, fmt: str = "{:.1f}", figsize=(9, 6),
) -> plt.Figure:
    """Barras horizontais ordenadas — o padrão mais usado nos três artigos
    (taxas/índices por UF). `destaque` pinta em terracota as UFs listadas."""
    s = serie.sort_values()
    fig, ax = plt.subplots(figsize=figsize)
    if destaque:
        cores = [TERRACOTA if i in destaque else VIZ_MUTED for i in s.index]
    else:
        cores = [cor] * len(s)
    ax.barh(s.index, s.values, color=cores)
    for i, v in enumerate(s.values):
        ax.text(v, i, f" {fmt.format(v)}", va="center", fontsize=8, color=PEDRA)
    fig.tight_layout(rect=[0, 0, 1, 0.88])
    _titulo(fig, titulo_txt, kicker)
    return fig


def fig_linha_temporal(
    df: pd.DataFrame, titulo_txt: str, kicker: str = None, ylabel: str = "",
    figsize=(9, 5.5),
) -> plt.Figure:
    """Linha por série (colunas do df) ao longo do índice (censos/anos) —
    usada nas séries 2000/2010/2022 do dashboard e do Artigo 1."""
    fig, ax = plt.subplots(figsize=figsize)
    for i, col in enumerate(df.columns):
        cor = VIZ_CATEGORICAL[i % len(VIZ_CATEGORICAL)]
        ax.plot(df.index, df[col], marker="o", label=col, color=cor)
    ax.set_ylabel(ylabel)
    ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0))
    fig.tight_layout(rect=[0, 0, 1, 0.88])
    _titulo(fig, titulo_txt, kicker)
    return fig


def fig_heatmap_od(
    matriz: pd.DataFrame, titulo_txt: str, kicker: str = None,
    fmt: str = "{:.0f}", figsize=(11, 10), anotar: bool = False,
) -> plt.Figure:
    """Heatmap origem×destino (matriz OD) na escala sequencial Ardósia."""
    fig, ax = plt.subplots(figsize=figsize)
    m = matriz.values.astype(float)
    im = ax.imshow(m, cmap="ardosia_seq", aspect="auto")
    ax.set_xticks(range(len(matriz.columns)))
    ax.set_xticklabels(matriz.columns, rotation=90, fontsize=7)
    ax.set_yticks(range(len(matriz.index)))
    ax.set_yticklabels(matriz.index, fontsize=7)
    ax.set_xlabel("Destino")
    ax.set_ylabel("Origem")
    if anotar and m.size <= 900:
        vmax = np.nanmax(m) if np.isfinite(m).any() else 1
        for i in range(m.shape[0]):
            for j in range(m.shape[1]):
                if m[i, j] > 0:
                    cor_txt = "white" if m[i, j] > 0.6 * vmax else PEDRA
                    ax.text(j, i, fmt.format(m[i, j]), ha="center", va="center", fontsize=5, color=cor_txt)
    fig.colorbar(im, ax=ax, shrink=0.7, label="pessoas (população expandida)")
    fig.tight_layout(rect=[0, 0, 1, 0.88])
    _titulo(fig, titulo_txt, kicker)
    return fig


def fig_piramide(
    dados_m: pd.Series, dados_f: pd.Series, titulo_txt: str, kicker: str = None,
    figsize=(8, 7), cor_m=ARDOSIA, cor_f=TERRACOTA,
) -> plt.Figure:
    """Pirâmide etária — mesmo índice (faixas etárias) para homens e mulheres,
    homens à esquerda (negativo), mulheres à direita."""
    fig, ax = plt.subplots(figsize=figsize)
    faixas = dados_m.index
    ax.barh(faixas, -dados_m.values, color=cor_m, label="Homens")
    ax.barh(faixas, dados_f.values, color=cor_f, label="Mulheres")
    ax.set_xticks(ax.get_xticks())
    ax.set_xticklabels([f"{abs(x):,.0f}" for x in ax.get_xticks()])
    ax.legend(loc="lower right")
    fig.tight_layout(rect=[0, 0, 1, 0.88])
    _titulo(fig, titulo_txt, kicker)
    return fig


def fig_dispersao_convergencia(
    x: pd.Series, y: pd.Series, titulo_txt: str, kicker: str = None,
    xlabel: str = "", ylabel: str = "", rotular_ufs: bool = True, figsize=(8, 7),
) -> plt.Figure:
    """Dispersão renda inicial × crescimento (β-convergência), com UFs
    rotuladas e reta de tendência OLS simples desenhada por cima."""
    fig, ax = plt.subplots(figsize=figsize)
    ax.scatter(x, y, color=ARDOSIA, s=40, zorder=3)
    if rotular_ufs:
        for uf in x.index:
            ax.annotate(uf, (x[uf], y[uf]), fontsize=7, color=PEDRA,
                        xytext=(4, 3), textcoords="offset points")
    coef = np.polyfit(x, y, 1)
    xs = np.linspace(x.min(), x.max(), 50)
    ax.plot(xs, np.polyval(coef, xs), color=TERRACOTA, linewidth=1.5, linestyle="--", zorder=2)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    fig.tight_layout(rect=[0, 0, 1, 0.88])
    _titulo(fig, titulo_txt, kicker)
    return fig


def fig_choropleth(
    gdf, coluna: str, titulo_txt: str, kicker: str = None,
    cmap: str = "ardosia_seq", figsize=(8, 8), fmt_legenda: str = "{:.1f}",
    vmin: float = None, vmax: float = None,
) -> plt.Figure:
    """Mapa coroplético das 27 UFs — `gdf` é um GeoDataFrame com a malha do
    IBGE (ver scripts/lib/malhas.py) já mesclado à coluna `coluna`. Passe
    `vmin`/`vmax` (ex.: -m, m para escala divergente simétrica) quando o mapa
    fizer parte de uma série comparável entre censos — sem isso, cada mapa
    normaliza sozinho e a comparação visual entre eles fica enviesada."""
    fig, ax = plt.subplots(figsize=figsize)
    gdf.plot(column=coluna, cmap=cmap, linewidth=0.4, edgecolor="white", ax=ax, legend=True,
              vmin=vmin, vmax=vmax, legend_kwds={"shrink": 0.6, "label": coluna})
    ax.axis("off")
    fig.subplots_adjust(top=0.90)
    _titulo(fig, titulo_txt, kicker)
    return fig


def fig_fluxos_mapa(
    gdf_centroides, fluxos: pd.DataFrame, titulo_txt: str, kicker: str = None,
    n_top: int = 30, figsize=(8, 8), gdf_poligonos=None,
) -> plt.Figure:
    """Mapa de fluxos — linhas entre centróides de UF, espessura ∝ volume.
    `gdf_centroides`: GeoDataFrame indexado por UF com geometria de ponto.
    `fluxos`: DataFrame long com colunas [origem, destino, valor].
    `gdf_poligonos`: opcional — a malha das UFs (scripts/lib/malhas.carregar()),
    desenhada como contorno de fundo para dar contexto geográfico aos pontos e
    fluxos (sem ela, o mapa vira uma constelação de pontos soltos, ilegível).
    """
    fig, ax = plt.subplots(figsize=figsize)
    if gdf_poligonos is not None:
        gdf_poligonos.plot(ax=ax, facecolor="#EDEBE5", edgecolor="white", linewidth=0.6, zorder=1)
    gdf_centroides.plot(ax=ax, color=ARDOSIA_CL, markersize=8, zorder=3)
    top = fluxos.nlargest(n_top, "valor")
    vmax = top["valor"].max()
    for _, row in top.iterrows():
        if row["origem"] not in gdf_centroides.index or row["destino"] not in gdf_centroides.index:
            continue
        p1 = gdf_centroides.loc[row["origem"], "geometry"]
        p2 = gdf_centroides.loc[row["destino"], "geometry"]
        ax.plot([p1.x, p2.x], [p1.y, p2.y], color=TERRACOTA,
                linewidth=0.5 + 4 * row["valor"] / vmax, alpha=0.55, zorder=2)
    ax.axis("off")
    fig.subplots_adjust(top=0.90)
    _titulo(fig, titulo_txt, kicker)
    return fig
