"""
Crosswalk de Áreas Mínimas Comparáveis (AMC) 2000 <-> 2010 <-> 2022 —
PLANO_TEMPORAL.md §2/Fase C. Uma AMC é o município de 2000 (a malha mais
"grossa" dos três censos): todo município criado depois de 2000 é reagregado
ao seu município de origem, para que a mesma unidade geográfica exista nos
três recortes temporais.

MÉTODO: só 64 dos 5.570 municípios de 2022 foram criados depois de 2000
(conferido nesta sessão: `Municipios-V4250.xls`, a lista oficial de
municípios de 2000 do próprio Censo, tem 5.529 códigos válidos + sentinelas
"sem especificação" = 5.507 municípios reais, contra 5.570 em 2022). Como a
IBGE Malhas API v3 não serve malha municipal de períodos anteriores a 2022
(`periodo=2000`/`2010` retornam HTTP 500, conferido nesta sessão), a origem de
cada um dos 64 é aproximada por PROXIMIDADE GEOMÉTRICA: o município de 2000
mais próximo (centroide a centroide, `representative_point` em EPSG:5880,
`lib.malhas.centroides_municipios`) dentro da MESMA UF. Desmembramentos
municipais brasileiros quase sempre recortam território contíguo do
município-mãe, então o vizinho mais próximo é uma aproximação forte — mas é
uma aproximação, não a fronteira histórica exata, e fica documentada como tal
(`origem_aproximada=True` na coluna de saída).

Dos 463 municípios `minerario_significativo` (`lib.mineracao`), só 6 foram
criados depois de 2000 -- Nazária/PI, Barrocas/BA, Governador Lindenberg/ES,
Forquetinha/RS, Colniza/MT, Nova Santa Helena/MT -- nenhum entre os grandes
produtores que sustentam o artigo (Carajás, Quadrilátero Ferrífero já
existiam em 2000). O crosswalk cobre os 5.570 de qualquer forma, mas o risco
de erro de aproximação geométrica nesses 6 casos específicos é baixo para os
resultados centrais.

Uso:
    from lib.amc import carregar_crosswalk, para_amc

    cw = carregar_crosswalk()              # município(2022) -> amc
    df["amc"] = para_amc(df["mun_atual"])  # qualquer código de município nos 3 censos
"""
import io
import sys
import zipfile
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent.parent
EXTERNO = BASE / "data" / "externo"
CROSSWALK = EXTERNO / "amc" / "amc_crosswalk.parquet"

sys.path.insert(0, str(Path(__file__).resolve().parent))


def _municipios_2000() -> set[str]:
    """Códigos IBGE (7 díg.) dos municípios que existiam em 2000, a partir do
    anexo oficial do próprio Censo (`Municipios-V4250.xls`, a lista de
    categorias da variável de residência em 1995) -- baixado por
    `00c_layouts.py` para `data/raw/2000/_docs/documentacao_2000.zip`."""
    zpath = BASE / "data" / "raw" / "2000" / "_docs" / "documentacao_2000.zip"
    assert zpath.exists(), f"{zpath} não existe -- rode scripts/00c_layouts.py antes"
    z = zipfile.ZipFile(zpath)
    d = pd.read_excel(io.BytesIO(z.read("Arquivos Auxiliares/Municipios-V4250.xls")), header=None, dtype=str)
    cod = d.iloc[:, 0].astype(str).str.strip()
    # sentinelas "<UF>00001" = "<UF> - SEM ESPECIFICAÇÃO" (não são município real)
    return set(cod[cod.str.fullmatch(r"\d{7}") & ~cod.str.endswith("00001")])


def construir_crosswalk() -> pd.DataFrame:
    """Constrói o crosswalk município(2022) -> amc, grava em
    `data/externo/amc/amc_crosswalk.parquet` e retorna. Colunas:
    `municipio` (código 2022), `amc` (código do município de 2000 mais
    próximo, ou o próprio código se o município já existia em 2000),
    `origem_aproximada` (bool -- True para os 64 criados depois de 2000)."""
    from lib.malhas import centroides_municipios  # import tardio -- depende de geopandas

    mun2000 = _municipios_2000()
    cent = centroides_municipios().reset_index()  # colunas: municipio, geometry
    cent["uf"] = cent["municipio"].str[:2]
    cent["existia_2000"] = cent["municipio"].isin(mun2000)

    linhas = []
    for uf, grupo in cent.groupby("uf"):
        antigos = grupo[grupo["existia_2000"]]
        novos = grupo[~grupo["existia_2000"]]
        for _, row in grupo.iterrows():
            if row["existia_2000"]:
                linhas.append({"municipio": row["municipio"], "amc": row["municipio"], "origem_aproximada": False})
                continue
            dist = antigos.geometry.distance(row.geometry)
            amc = antigos.loc[dist.idxmin(), "municipio"]
            linhas.append({"municipio": row["municipio"], "amc": amc, "origem_aproximada": True})

    out = pd.DataFrame(linhas)
    assert len(out) == len(cent), "crosswalk não cobriu todos os municípios"
    n_existentes = int((~out["origem_aproximada"]).sum())
    print(f"  crosswalk AMC: {n_existentes} municípios já existiam em 2000, "
          f"{len(out) - n_existentes} reagregados por proximidade geométrica "
          f"(esperado ~64, ver docstring do módulo)")
    CROSSWALK.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(CROSSWALK, index=False)
    return out


def carregar_crosswalk() -> pd.DataFrame:
    if not CROSSWALK.exists():
        return construir_crosswalk()
    return pd.read_parquet(CROSSWALK)


def para_amc(serie: pd.Series) -> pd.Series:
    """Mapeia uma coluna de código de município (qualquer um dos 3 censos --
    os códigos IBGE de município são estáveis entre censos exceto para os 64
    criados depois de 2000) para a AMC correspondente. Códigos fora do
    crosswalk (ex.: `9999999` sem especificação) viram NA."""
    cw = carregar_crosswalk().set_index("municipio")["amc"]
    return serie.map(cw)


def amc_de_uf(serie_amc: pd.Series) -> pd.Series:
    """UF (2 díg.) de uma coluna de código de AMC."""
    return serie_amc.astype(str).str[:2]


def municipios_por_amc(amc: str) -> list[str]:
    """Lista de códigos de município (2022) que uma AMC agrega."""
    cw = carregar_crosswalk()
    return sorted(cw.loc[cw["amc"] == amc, "municipio"])
