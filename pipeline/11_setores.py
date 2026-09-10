"""
E1 / Fase 1 passos 2-3 (PLANO.md) — malhas de setores censitários 2010 e 2022
recortadas para Canaã dos Carajás, com indicadores agregados por setor
(população, domicílios, densidade, moradores/domicílio, rendimento médio do
responsável, sexo, cor/raça, água/esgoto/lixo/energia). Dados 100% públicos
(agregados por setor, nunca microdados) — não passam pelo gate de revelação.

Fontes e formato dos códigos de variável (nunca digitados de memória):
  - 2010: `PA_20260615.zip` (Resultados do Universo por setor, planilhas
    Básico e Domicilio01, ambas em CSV ";"/latin-1) — os nomes V001..V0NN
    são conferidos em `Documentacao_Agregado_dos_Setores_2010_20231030.zip`
    (`Descrição_PA.xls`... na verdade a tabela de variáveis está no PDF
    "BASE DE INFORMAÇÕES POR SETOR CENSITÁRIO Censo 2010 - Universo novo.pdf",
    seções 6.1 e 6.2) — dicionário transcrito em `DIC_2010_BASICO` e
    `DIC_2010_DOMICILIO01` abaixo, cada chave com o texto exato da página.
  - 2022: arquivos nacionais (`Agregados_por_Setor_csv/*_BR*.zip`), filtrados
    para o distrito único de Canaã (código 150215205, prefixo de todo CD_SETOR
    do município) via `grep` no CSV descomprimido — evita carregar ~500 mil
    setores do Brasil em memória. Nomes de variável (V0NNNN) resolvidos
    dinamicamente pelo dicionário oficial `dicionario_de_dados_agregados_
    por_setores_censitarios_20260520.xlsx` (aba "Dicionário não PCT" +
    "Dicionário Básico"), nunca hard-coded a partir de memória.

Uso:
    .venv/bin/python pipeline/11_setores.py
"""
from __future__ import annotations

import subprocess
import sys
import zipfile
from io import StringIO
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))

BASE = Path(__file__).resolve().parent.parent
DL = BASE / "data" / "interim" / "_setor_dl"
DL.mkdir(parents=True, exist_ok=True)
OUT_PROC = BASE / "data" / "processed" / "setores"
OUT_PROC.mkdir(parents=True, exist_ok=True)
OUT_WEB = BASE / "web" / "public" / "data" / "geo"
OUT_WEB.mkdir(parents=True, exist_ok=True)

MUNICIPIO = "1502152"
DISTRITO_PREFIXO = "150215205"  # todo CD_SETOR do município começa assim
EPSG_METRICO = 31982  # SIRGAS 2000 / UTM 22S — convenção do projeto (CLAUDE.md)

GEOFTP = (
    "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/"
    "malhas_de_setores_censitarios__divisoes_intramunicipais"
)
URL_MALHA_2010 = f"{GEOFTP}/censo_2010/setores_censitarios_shp/pa/pa_setores_censitarios.zip"
URL_MALHA_2022 = f"{GEOFTP}/censo_2022/setores/shp/UF/PA_setores_CD2022.zip"
URL_UNIVERSO_2010 = (
    "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2010/Resultados_do_Universo/"
    "Agregados_por_Setores_Censitarios/PA_20260615.zip"
)
FTP_2022 = "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios"
URL_DIC_2022 = f"{FTP_2022}/dicionario_de_dados_agregados_por_setores_censitarios_20260520.xlsx"
URL_HISTORICO_SETORES = f"{GEOFTP}/censo_2022/Historico_formacao_Setores_Censitarios_2010_2022.xlsx"

ARQUIVOS_2022 = {
    "basico": f"{FTP_2022}/Agregados_por_Setor_csv/Agregados_por_setores_basico_BR_20260520.zip",
    "demografia": f"{FTP_2022}/Agregados_por_Setor_csv/Agregados_por_setores_demografia_BR.zip",
    "cor_raca": f"{FTP_2022}/Agregados_por_Setor_csv/Agregados_por_setores_cor_ou_raca_BR.zip",
    "domicilio2": f"{FTP_2022}/Agregados_por_Setor_csv/Agregados_por_setores_caracteristicas_domicilio2_BR_20250417.zip",
}

# --- Dicionário 2010 (transcrito das seções 6.1/6.2 do PDF de documentação
# oficial do Censo 2010 — "BASE DE INFORMAÇÕES POR SETOR CENSITÁRIO", ver
# docstring do módulo) — só as variáveis usadas neste script. -----------------
DIC_2010_BASICO = {
    "V001": "domicilios_particulares_permanentes",
    "V002": "populacao_residente",
    "V003": "media_moradores_domicilio",
    "V005": "rendimento_medio_responsavel_com_sem_r",
    "V007": "rendimento_medio_responsavel_com_r",
}
DIC_2010_DOMICILIO01 = {
    "V002": "domicilios_particulares_permanentes",  # denominador
    "V012": "agua_rede_geral",
    "V017": "esgoto_rede_geral_ou_pluvial",
    "V035": "lixo_coletado",
    "V043": "com_energia_eletrica",
}


def log(msg: str) -> None:
    print(f"[11_setores] {msg}")


def baixar(url: str, destino: Path) -> Path:
    if destino.exists():
        return destino
    log(f"baixando {url}")
    with requests.get(url, stream=True, timeout=300, headers={"User-Agent": "Mozilla/5.0"}) as r:
        r.raise_for_status()
        tmp = destino.with_suffix(destino.suffix + ".part")
        with open(tmp, "wb") as fh:
            for chunk in r.iter_content(chunk_size=1 << 20):
                fh.write(chunk)
        tmp.rename(destino)
    return destino


# --- 1. Malhas ----------------------------------------------------------------
def carregar_malha(url: str, campo_mun: str, campo_setor: str, nome_cache: str) -> gpd.GeoDataFrame:
    local = baixar(url, DL / nome_cache)
    gdf = gpd.read_file(f"/vsizip/{local}")
    gdf = gdf[gdf[campo_mun].astype(str).str.zfill(7) == MUNICIPIO].copy()
    gdf = gdf.rename(columns={campo_setor: "cod_setor"})
    gdf["cod_setor"] = gdf["cod_setor"].astype(str)
    gdf = gdf.to_crs(EPSG_METRICO)
    gdf["area_km2_geom"] = gdf.geometry.area / 1e6
    log(f"  {nome_cache}: {len(gdf)} setores de Canaã dos Carajás")
    return gdf


# --- 2. Universo 2010 (Básico + Domicilio01, filtrados p/ Canaã) -------------
def _ler_csv_zip_membro(zip_path: Path, membro_sufixo: str) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path) as zf:
        alvo = next(n for n in zf.namelist() if n.endswith(membro_sufixo))
        with zf.open(alvo) as fh:
            return pd.read_csv(fh, sep=";", encoding="latin-1", decimal=",")


def carregar_universo_2010() -> pd.DataFrame:
    local = baixar(URL_UNIVERSO_2010, DL / "PA_2010_universo.zip")
    basico = _ler_csv_zip_membro(local, "CSV/Basico_PA.csv")
    basico = basico[basico["Cod_municipio"] == int(MUNICIPIO)].copy()
    for n in (1, 2, 3, 5, 7):
        basico[f"V{n:03d}"] = pd.to_numeric(basico[f"V{n:03d}"], errors="coerce")
    basico = basico.rename(columns={f"V{n:03d}": DIC_2010_BASICO[f"V{n:03d}"]
                                     for n in (1, 2, 3, 5, 7)})
    basico["cod_setor"] = basico["Cod_setor"].astype(str)

    dom = _ler_csv_zip_membro(local, "CSV/Domicilio01_PA.csv")
    dom = dom[dom["Cod_setor"].astype(str).str.startswith(DISTRITO_PREFIXO)
              | dom["Cod_setor"].astype(str).isin(basico["cod_setor"])].copy()
    for col in DIC_2010_DOMICILIO01:
        dom[col] = pd.to_numeric(dom[col], errors="coerce")
    dom = dom.rename(columns={k: v for k, v in DIC_2010_DOMICILIO01.items()})
    dom["cod_setor"] = dom["Cod_setor"].astype(str)
    dom = dom[["cod_setor", "domicilios_particulares_permanentes",
               "agua_rede_geral", "esgoto_rede_geral_ou_pluvial",
               "lixo_coletado", "com_energia_eletrica"]]

    df = basico.merge(dom, on="cod_setor", suffixes=("", "_dom"))
    denom = df["domicilios_particulares_permanentes_dom"].astype("float64").replace(0, float("nan"))
    for col in ["agua_rede_geral", "esgoto_rede_geral_ou_pluvial", "lixo_coletado", "com_energia_eletrica"]:
        nome_pct = col.replace("_rede_geral_ou_pluvial", "").replace("_rede_geral", "") + "_pct"
        df[nome_pct] = (df[col].astype("float64") / denom * 100).round(1)
    log(f"  Universo 2010: {len(df)} setores com Básico + Domicílio01 casados")
    return df


# --- 3. Setor 2022 — arquivos nacionais filtrados por grep -------------------
def _baixar_e_filtrar_2022(nome: str, url: str) -> pd.DataFrame:
    local = baixar(url, DL / f"{nome}_BR.zip")
    with zipfile.ZipFile(local) as zf:
        membro = zf.namelist()[0]
        with zf.open(membro) as fh:
            cabecalho = fh.readline().decode("latin-1")
    # grep no membro descomprimido via pipe — evita materializar o CSV nacional
    # (texto vem em latin-1, não utf-8 — subprocess com text=True forçaria utf-8)
    proc = subprocess.run(
        f'unzip -p "{local}" "{membro}" | grep \'"{DISTRITO_PREFIXO}\'',
        shell=True, capture_output=True,
    )
    texto = cabecalho + proc.stdout.decode("latin-1")
    df = pd.read_csv(StringIO(texto), sep=";", encoding="latin-1", decimal=",")
    log(f"  {nome} 2022: {len(df)} setores filtrados de {membro}")
    return df


def carregar_dicionario_2022() -> dict[str, str]:
    local = baixar(URL_DIC_2022, DL / "dic2022.xlsx")
    partes = []
    d1 = pd.read_excel(local, sheet_name="Dicionário Básico")
    d1.columns = ["tema", "variavel", "descricao"]
    partes.append(d1[["variavel", "descricao"]])
    d2 = pd.read_excel(local, sheet_name="Dicionário não PCT")
    d2.columns = ["tipo", "tema", "variavel", "descricao"]
    partes.append(d2[["variavel", "descricao"]])
    dic = pd.concat(partes, ignore_index=True).drop_duplicates("variavel")
    return dict(zip(dic["variavel"], dic["descricao"]))


# Variáveis 2022 usadas (código -> nome curto), resolvidas contra o dicionário
# oficial em `main()` só para *validar* que a descrição bate com o esperado
# (nunca aceitas às cegas).
VARS_2022 = {
    "basico": {"V0001": "populacao_residente", "V0002": "total_domicilios",
               "V0003": "domicilios_particulares", "V0005": "media_moradores_domicilio",
               "V0007": "domicilios_particulares_ocupados"},
    "demografia": {"V01007": "sexo_masculino", "V01008": "sexo_feminino"},
    "cor_raca": {"V01317": "cor_branca", "V01318": "cor_preta", "V01319": "cor_amarela",
                 "V01320": "cor_parda", "V01321": "cor_indigena"},
    "domicilio2": {"V00111": "agua_rede_geral", "V00309": "esgoto_rede_geral",
                   "V00397": "lixo_coletado_servico"},
}


def carregar_setor_2022() -> pd.DataFrame:
    dic = carregar_dicionario_2022()
    esperado = {
        "V0001": "Total de pessoas", "V01007": "Sexo masculino", "V01317": "branca",
        "V00111": "rede geral de distribuição",
    }
    for cod, trecho in esperado.items():
        desc = dic.get(cod, "")
        assert trecho.lower() in desc.lower(), f"dicionário 2022 mudou: {cod} = {desc!r}"
    log("  Dicionário 2022 validado contra os códigos usados.")

    tabelas = {}
    for nome, url in ARQUIVOS_2022.items():
        df = _baixar_e_filtrar_2022(nome, url)
        col_setor = next(c for c in df.columns if c.lower() in ("cd_setor", "setor"))
        # nomes de coluna vêm em maiúsculo ou minúsculo conforme o arquivo
        # ("v0001" no básico, "V01006" na demografia) — casamento por upper().
        mapa_upper = {c.upper(): c for c in df.columns}
        renomeio = {mapa_upper[cod]: nome_curto for cod, nome_curto in VARS_2022[nome].items()
                    if cod in mapa_upper}
        df = df.rename(columns={col_setor: "cod_setor", **renomeio})
        df["cod_setor"] = df["cod_setor"].astype(str)
        cols = ["cod_setor"] + list(VARS_2022[nome].values())
        tabelas[nome] = df[[c for c in cols if c in df.columns]]

    df = tabelas["basico"]
    for nome in ("demografia", "cor_raca", "domicilio2"):
        df = df.merge(tabelas[nome], on="cod_setor", how="left")
    for cols in VARS_2022.values():
        for col in cols.values():
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

    denom = df["domicilios_particulares"].astype("float64").replace(0, float("nan"))
    df["agua_pct"] = (df["agua_rede_geral"].astype("float64") / denom * 100).round(1)
    df["esgoto_pct"] = (df["esgoto_rede_geral"].astype("float64") / denom * 100).round(1)
    df["lixo_pct"] = (df["lixo_coletado_servico"].astype("float64") / denom * 100).round(1)
    return df


# --- 4. Correspondência 2010<->2022 (tabela do IBGE, filtrada p/ Canaã) ------
def salvar_correspondencia() -> None:
    """Tabela oficial IBGE de correspondência de código de setor 2010-2022
    (`GEOCODIGO_{ano}`, um código por ano intermediário em que o setor
    mudou) — filtrada pelo prefixo do distrito único de Canaã, testado em
    QUALQUER coluna GEOCODIGO_* (o setor pode ter mudado de código em anos
    intermediários e nem todo registro tem o prefixo em todas as colunas)."""
    local = baixar(URL_HISTORICO_SETORES, DL / "historico_setores_2010_2022.xlsx")
    xl = pd.ExcelFile(local)
    aba = xl.sheet_names[0]
    df = pd.read_excel(xl, sheet_name=aba, dtype=str)
    cols_geocodigo = [c for c in df.columns if c.upper().startswith("GEOCODIGO")]
    mascara = pd.Series(False, index=df.index)
    for c in cols_geocodigo:
        mascara |= df[c].astype(str).str.startswith(DISTRITO_PREFIXO, na=False)
    sub = df[mascara]
    sub.to_parquet(OUT_PROC / "correspondencia_setores_2010_2022.parquet", index=False)
    log(f"  Correspondência 2010<->2022: {len(sub)} linhas para Canaã "
        f"(aba '{aba}', {len(cols_geocodigo)} colunas GEOCODIGO_*)")


# --- 5. Saída GeoJSON para o dashboard ----------------------------------------
def gravar_geojson(gdf: gpd.GeoDataFrame, ano: int) -> None:
    gdf_saida = gdf.to_crs(4326).copy()
    gdf_saida["geometry"] = gdf_saida.geometry.simplify(0.00003, preserve_topology=True)
    caminho = OUT_WEB / f"setores_{ano}.json"
    gdf_saida.to_file(caminho, driver="GeoJSON")
    gdf.drop(columns="geometry").to_parquet(OUT_PROC / f"setores_{ano}_indicadores.parquet", index=False)
    gdf.to_parquet(OUT_PROC / f"setores_{ano}.parquet", index=False)
    log(f"  {caminho.relative_to(BASE)}: {len(gdf_saida)} setores, "
        f"{caminho.stat().st_size / 1024:.0f} KB")


def main() -> None:
    log("=== 2010 ===")
    malha_2010 = carregar_malha(URL_MALHA_2010, "CD_GEOCODM", "CD_GEOCODI", "pa_2010.zip")
    universo_2010 = carregar_universo_2010()
    setores_2010 = malha_2010.merge(universo_2010, on="cod_setor", how="left")
    setores_2010["densidade_hab_km2"] = (
        setores_2010["populacao_residente"] / setores_2010["area_km2_geom"]
    ).round(1)
    pop_2010 = setores_2010["populacao_residente"].sum()
    log(f"  soma população setores 2010 (todos os situação): {pop_2010:,.0f}")
    gravar_geojson(setores_2010, 2010)

    log("\n=== 2022 ===")
    malha_2022 = carregar_malha(URL_MALHA_2022, "CD_MUN", "CD_SETOR", "pa_2022.zip")
    setor_2022 = carregar_setor_2022()
    setores_2022 = malha_2022.merge(setor_2022, on="cod_setor", how="left")
    area_col = "AREA_KM2" if "AREA_KM2" in setores_2022.columns else "area_km2_geom"
    area_num = pd.to_numeric(setores_2022[area_col], errors="coerce")
    setores_2022["densidade_hab_km2"] = (setores_2022["populacao_residente"] / area_num).round(1)
    pop_2022 = setores_2022["populacao_residente"].sum()
    log(f"  soma população setores 2022 (todos os situação): {pop_2022:,.0f}")
    gravar_geojson(setores_2022, 2022)

    log("\n=== Correspondência 2010<->2022 ===")
    try:
        salvar_correspondencia()
    except Exception as e:  # noqa: BLE001
        log(f"  FALHOU (não bloqueante) — {e}")

    log("\n=== Conferência × SIDRA (t/9923, t/1378) ===")
    sidra_2022 = pd.read_parquet(BASE / "data" / "processed" / "ibge" / "t9923_situacao_2022.parquet")
    total_sidra_2022 = sidra_2022.loc[sidra_2022["Situação do domicílio"] == "Total", "valor"].iloc[0]
    desvio_2022 = (pop_2022 - total_sidra_2022) / total_sidra_2022 * 100
    log(f"  2022: soma setores = {pop_2022:,.0f} | SIDRA t/9923 total = {total_sidra_2022:,.0f} | "
        f"desvio = {desvio_2022:+.2f}%")

    sidra_2010 = pd.read_parquet(BASE / "data" / "processed" / "ibge" / "t202_pop_distrito.parquet")
    total_sidra_2010 = sidra_2010.query("Ano == '2010' and Sexo == 'Total' and `Situação do domicílio` == 'Total'")["valor"].iloc[0]
    desvio_2010 = (pop_2010 - total_sidra_2010) / total_sidra_2010 * 100
    log(f"  2010: soma setores = {pop_2010:,.0f} | SIDRA t/202 (distrito) total = {total_sidra_2010:,.0f} | "
        f"desvio = {desvio_2010:+.2f}%")


if __name__ == "__main__":
    main()
