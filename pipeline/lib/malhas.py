"""
Malha geográfica de UF e de município (IBGE Malhas API v3) para os mapas
coropléticos e de fluxos deste e dos outros artigos da pasta (plano §7/§9).

`data/externo/malhas/malha_{uf,municipio}.json` são baixados uma vez; as
funções `carregar*()` usam o cache e só rebaixam se o arquivo não existir.

Todas as geometrias chegam da API em EPSG:4326 (graus) — projeção inadequada
para qualquer cálculo de área, distância ou posição de centroide (distorce
mais no Norte/Nordeste do que no Sul, exatamente onde ficam os municípios
minerários deste artigo). `carregar()`/`carregar_municipios()` reprojetam
para **EPSG:5880** (SIRGAS 2000 / Brasil Polar Estereográfica) antes de
devolver — nunca calcular centroide ou fazer `representative_point()` em
4326.
"""
from pathlib import Path

import geopandas as gpd
import requests

BASE = Path(__file__).resolve().parent.parent.parent
CACHE = BASE / "data" / "externo" / "malhas" / "malha_uf.json"
CACHE_MUN = BASE / "data" / "externo" / "malhas" / "malha_municipio.json"

URL = (
    "https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR"
    "?formato=application/vnd.geo+json&intrarregiao=UF&qualidade=intermediaria"
)
URL_MUN = (
    "https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR"
    "?formato=application/vnd.geo+json&intrarregiao=municipio&qualidade=minima"
)
EPSG_BRASIL = 5880


def carregar() -> gpd.GeoDataFrame:
    """GeoDataFrame das 27 UFs, indexado pelo código IBGE de 2 dígitos
    (mesma chave usada em todo o painel harmonizado — `uf_res` etc.), já em
    EPSG:5880."""
    if not CACHE.exists():
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(URL, timeout=90)
        r.raise_for_status()
        CACHE.write_bytes(r.content)
    gdf = gpd.read_file(CACHE)
    gdf = gdf.rename(columns={"codarea": "uf"}).set_index("uf")
    return gdf.to_crs(EPSG_BRASIL)


def com_coluna(serie, nome_coluna: str = "valor") -> gpd.GeoDataFrame:
    """Malha das UFs mesclada a uma série indexada por código de UF — pronta
    para `lib.viz.fig_choropleth`."""
    gdf = carregar().copy()
    gdf[nome_coluna] = serie.reindex(gdf.index)
    return gdf


def centroides() -> gpd.GeoDataFrame:
    """Centróides das 27 UFs — usados em `lib.viz.fig_fluxos_mapa`."""
    gdf = carregar()
    out = gdf.copy()
    out["geometry"] = out.geometry.representative_point()
    return out


def carregar_municipios() -> gpd.GeoDataFrame:
    """GeoDataFrame dos 5.570 municípios (qualidade 'minima' -- suficiente
    para mapa temático nacional, ~3,6MB; não usar para análise de precisão
    geométrica), indexado pelo código IBGE de 7 dígitos (= `P0080`/
    `cod_municipio`), já em EPSG:5880."""
    if not CACHE_MUN.exists():
        CACHE_MUN.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(URL_MUN, timeout=180)
        r.raise_for_status()
        CACHE_MUN.write_bytes(r.content)
    gdf = gpd.read_file(CACHE_MUN)
    gdf = gdf.rename(columns={"codarea": "municipio"}).set_index("municipio")
    return gdf.to_crs(EPSG_BRASIL)


def com_coluna_municipios(serie, nome_coluna: str = "valor") -> gpd.GeoDataFrame:
    """Malha municipal mesclada a uma série indexada por código de município
    (7 dígitos) — pronta para `lib.viz.fig_choropleth`."""
    gdf = carregar_municipios().copy()
    gdf[nome_coluna] = serie.reindex(gdf.index)
    return gdf


def centroides_municipios() -> gpd.GeoDataFrame:
    """Centróides internos (`representative_point`, sempre dentro do
    polígono -- ao contrário do centroide geométrico, que pode cair fora em
    municípios de litoral recortado) dos 5.570 municípios, em EPSG:5880.
    Usados em `lib.viz.fig_fluxos_mapa` para os corredores migratórios."""
    gdf = carregar_municipios()
    out = gdf.copy()
    out["geometry"] = out.geometry.representative_point()
    return out
