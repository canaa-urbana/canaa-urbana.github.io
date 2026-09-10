"""
E2 / Fase 2 passos 1-2 — parsers dos microdados da amostra (Pará) dos censos
1991, 2000, 2010 e 2022, com harmonização para o esquema único do projeto.

Fontes (lidas in loco, nunca copiadas para o repositório):
  - 1991: `data/raw/microdados_local/Microdados_Censo_Demografico_1991_Amostra_ftp/
    Microdados_Censo_Demografico_1991_Amostra.zip` (baixado do FTP público do
    IBGE em 2026-09-10, SHA-256 idêntico à cópia de `data/raw/zeitmaschine`).
    O zip usa Deflate64 (zipfile não lê): o DBF do Pará (`CD91AMOUP15.DBF`) é
    extraído com `unzip -p` para `data/interim/censo1991/` e lido com dbfread.
    Um registro por pessoa, com as variáveis do domicílio repetidas; não há
    chave de domicílio — ela é reconstruída pela sequência de `PESSOAN == 1`
    (número de ordem do morador), conferida nesta sessão contra o total de
    domicílios de Parauapebas (contagens amostrais omitidas — só faixas, regra R3).
  - 2000: `data/raw/zeitmaschine/.../PA/{Pes15.txt,Dom15.txt}` (FWF, layouts
    JSON em `data/interim/layouts/`; município só no registro de domicílio,
    juntado via V0300).
  - 2010: `data/raw/microdados_local/microdados_censo_amostra_2010_txt/PA/`
    (FWF, layouts JSON).
  - 2022: `data/raw/microdados_local/microdados_censo_amostra_2022_csv_.../15/`
    (CSV ';', ACESSO CONTROLADO — peso `P0111`/`D0111`).

Saída (`data/interim/microdados/`, fora do git): `pessoas_{censo}.parquet` e
`domicilios_{censo}.parquet` com o Pará inteiro no esquema harmonizado de
`lib/censos.py` — Canaã, Parauapebas e o estado são filtrados em
`13_migracao_perfil.py`. Só agregados aprovados pelo gate saem daqui.

Uso:
    .venv/bin/python pipeline/12_microdados.py [1991 2000 2010 2022]
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "pipeline"))
from lib import censos as C  # noqa: E402
from lib.deflator import SALARIO_MINIMO, para_reais_jul2022  # noqa: E402
from lib.fwf import ler_fwf, to_num  # noqa: E402
from lib.geo import UF_CODIGO_MIGRACAO_2000  # noqa: E402
from lib.migracao import classificar_5anos, eh_retorno  # noqa: E402

RAW_LOCAL = BASE / "data/raw/microdados_local"
RAW_ZEIT = BASE / "data/raw/zeitmaschine"
INTERIM = BASE / "data/interim"
OUT = INTERIM / "microdados"
OUT.mkdir(parents=True, exist_ok=True)

ZIP_1991 = [
    RAW_LOCAL / "Microdados_Censo_Demografico_1991_Amostra_ftp/Microdados_Censo_Demografico_1991_Amostra.zip",
    RAW_ZEIT / "Microdados_Censo_Demografico_1991_Amostra/Microdados_Censo_Demografico_1991_Amostra.zip",
]
DIR_2000 = RAW_ZEIT / "Microdados_Censo_Demografico_2000_Amostra/PA"
DIR_2010 = RAW_LOCAL / "microdados_censo_amostra_2010_txt/PA"
# pasta da entrega controlada (o nome traz data/hora da entrega: localizada por padrão, não escrita no código)
DIR_2022 = next(iter(sorted(RAW_LOCAL.glob("microdados_censo_amostra_2022_csv_*"))), RAW_LOCAL / "microdados_censo_amostra_2022_csv") / "15"

COLS_PESSOAS = [
    "censo", "uf", "mun", "controle", "situacao", "ap", "peso", "sexo", "idade", "cor_raca",
    "responsavel", "nivel_instrucao", "ocupado", "posicao", "formal", "setor", "extrativa_mineral",
    "renda_trabalho", "renda_total", "renda_trabalho_r2022", "renda_total_r2022", "renda_total_sm",
    "renda_sm_faixa", "tipo_mig_5anos", "origem_uf", "origem_mun", "naturalidade", "uf_nascimento",
    "tempo_moradia", "ano_chegada", "retorno", "trabalha_outro_mun",
]
COLS_DOMICILIOS = [
    "censo", "uf", "mun", "controle", "situacao", "ap", "peso", "tipo", "condicao_ocupacao",
    "agua_rede", "esgoto_adequado", "lixo_coletado", "energia", "internet", "densidade_dormitorio",
    "moradores", "renda_dom_pc", "renda_dom_pc_r2022", "renda_dom_pc_sm", "adequacao",
]


def _log(msg: str) -> None:
    print(f"  {msg}", flush=True)


def _bool(s: pd.Series, verdadeiro: set[str], validos: set[str] | None = None) -> pd.Series:
    """Booleano com NA quando o código não está entre `validos` (branco = NA)."""
    s = s.astype("string").str.strip()
    out = s.isin(verdadeiro).astype("boolean")
    validos = validos or verdadeiro
    out[~s.isin(validos | verdadeiro)] = pd.NA
    return out


def _finalizar(df: pd.DataFrame, cols: list[str], censo: int, nome: str) -> pd.DataFrame:
    df = df.reindex(columns=cols)
    df["censo"] = censo
    for c in ("uf", "mun", "controle", "ap", "origem_uf", "origem_mun", "uf_nascimento"):
        if c in df:
            df[c] = df[c].astype("string")
    df.to_parquet(OUT / f"{nome}_{censo}.parquet", index=False)
    n_canaa = int((df["mun"] == C.CANAA).sum()) if censo != 1991 else int((df["mun"] == C.PARAUAPEBAS).sum())
    _log(f"{nome}_{censo}: {len(df):,} registros amostrais no PA; {n_canaa:,} em "
         f"{'Parauapebas (proxy)' if censo == 1991 else 'Canaã'}; peso total {df['peso'].sum():,.0f}")
    return df


# =====================================================================================
# 2022 — CSV acesso controlado
# =====================================================================================
def parse_2022() -> None:
    import duckdb

    p_pes = DIR_2022 / "Pessoas_15_controlado.csv"
    p_dom = DIR_2022 / "Domicilios_15_controlado.csv"
    con = duckdb.connect()
    campos_p = ["P0020", "P0080", "P0090", "P0100", "P0111", "P0130", "P0140", "P0150", "P0170",
                "P0181", "P0210", "P0480", "P0490", "P0500", "P0530", "P0540", "P0550", "P0600",
                "P0610", "P0620", "P0770", "P0960", "P1020", "P1030", "P1080", "P1110", "P1120", "P1140"]
    num = {"P0111": "DOUBLE", "P0181": "INTEGER", "P0540": "INTEGER", "P0550": "DOUBLE",
           "P1080": "DOUBLE", "P1110": "DOUBLE"}
    sel = ", ".join(f"TRY_CAST(NULLIF({c}, '') AS {num[c]}) AS {c}" if c in num else c for c in campos_p)
    df = con.execute(f"SELECT {sel} FROM read_csv('{p_pes.as_posix()}', delim=';', header=true, "
                     f"all_varchar=true)").df()
    _log(f"2022 pessoas PA lidas: {len(df):,}")
    df = df[df["P0130"].str.strip() == "01"].copy()  # domicílios particulares permanentes ocupados

    out = pd.DataFrame(index=df.index)
    out["uf"], out["mun"], out["ap"], out["controle"] = df["P0020"], df["P0080"], df["P0090"], df["P0100"]
    out["situacao"] = np.where(df["P0140"] == "1", "urbana", "rural")
    out["peso"] = df["P0111"]
    out["sexo"] = df["P0150"].map(C.SEXO)
    out["idade"] = df["P0181"]
    out["cor_raca"] = df["P0210"].map(C.COR_RACA)
    out["responsavel"] = df["P0170"].str.strip() == "01"
    out["nivel_instrucao"] = df["P0770"].map(C.NIVEL_INSTRUCAO)
    out["ocupado"] = _bool(df["P0960"], {"1"}, {"0"})
    out["posicao"] = df["P1020"].str.strip().map(C.POSICAO_2022)
    out["formal"] = out["posicao"].isin(C.FORMAL).astype("boolean").where(out["posicao"].notna(), pd.NA)
    out["setor"] = df["P1030"].str.strip().map(C.SETOR_2022)
    out["extrativa_mineral"] = (out["setor"] == "extrativa_mineral").astype("boolean").where(out["setor"].notna(), pd.NA)
    out["renda_trabalho"], out["renda_total"] = df["P1080"], df["P1110"]
    out["renda_trabalho_r2022"] = para_reais_jul2022(df["P1080"], 2022)
    out["renda_total_r2022"] = para_reais_jul2022(df["P1110"], 2022)
    out["renda_total_sm"] = df["P1110"] / SALARIO_MINIMO[2022]
    out["renda_sm_faixa"] = C.faixa_renda_sm(out["renda_total_sm"])
    out["tipo_mig_5anos"] = classificar_5anos(df, censo=2022).astype("object")
    out.loc[df["P0181"] < 5, "tipo_mig_5anos"] = pd.NA
    out["origem_uf"] = df["P0610"].where(out["tipo_mig_5anos"].isin(["intraestadual", "interestadual"]))
    out["origem_mun"] = df["P0620"].where(out["tipo_mig_5anos"].isin(["intraestadual", "interestadual"]))
    nat = pd.Series(pd.NA, index=df.index, dtype="object")
    nat[df["P0480"] == "1"] = "municipio"
    nat[(df["P0480"] == "2") & (df["P0490"] == df["P0020"])] = "mesma_uf"
    nat[(df["P0480"] == "2") & (df["P0490"] != df["P0020"]) & df["P0490"].notna() & (df["P0490"] != "")] = "outra_uf"
    nat[df["P0480"] == "3"] = "exterior"
    out["naturalidade"] = nat
    out["uf_nascimento"] = df["P0490"].where(df["P0480"].isin(["1", "2"]))
    out.loc[df["P0480"] == "1", "uf_nascimento"] = df["P0020"]
    # P0530 ("já morou em outro município?") só é perguntada a quem NASCEU neste município
    # (P0480 = 1); quem nasceu fora (P0480 = 2/3) tem P0530 em branco e P0550 preenchido
    # (conferido nesta sessão: 0 brancos de P0550 em Canaã). P0540 é "ano de fixação de
    # residência" só de quem nasceu no exterior — a coorte de chegada vem de P0550.
    mudou = (df["P0480"] != "1") | (df["P0530"] == "1")
    out["tempo_moradia"] = df["P0550"].where(mudou)
    out.loc[df["P0530"] == "2", "tempo_moradia"] = df["P0181"]  # nunca morou em outro município
    out["ano_chegada"] = (2022 - df["P0550"]).where(mudou)
    out["retorno"] = eh_retorno(df, censo=2022)
    out["trabalha_outro_mun"] = _bool(df["P1120"], {"3"}, {"1", "2", "4", "5"})
    _finalizar(out, COLS_PESSOAS, 2022, "pessoas")

    campos_d = ["D0020", "D0080", "D0090", "D0100", "D0111", "D0130", "D0140", "D0150", "D0190", "D0200",
                "D0240", "D0250", "D0260", "D0310", "D0330", "D0360"]
    numd = {"D0111": "DOUBLE", "D0150": "INTEGER", "D0240": "DOUBLE", "D0360": "DOUBLE"}
    sel = ", ".join(f"TRY_CAST(NULLIF({c}, '') AS {numd[c]}) AS {c}" if c in numd else c for c in campos_d)
    dd = con.execute(f"SELECT {sel} FROM read_csv('{p_dom.as_posix()}', delim=';', header=true, "
                     f"all_varchar=true)").df()
    dd = dd[dd["D0130"].str.strip() == "01"].copy()
    od = pd.DataFrame(index=dd.index)
    od["uf"], od["mun"], od["ap"], od["controle"] = dd["D0020"], dd["D0080"], dd["D0090"], dd["D0100"]
    od["situacao"] = np.where(dd["D0140"] == "1", "urbana", "rural")
    od["peso"] = dd["D0111"]
    od["tipo"] = dd["D0200"].str.strip().map(C.TIPO_DOMICILIO_2022)
    od["condicao_ocupacao"] = dd["D0190"].str.strip().map(C.CONDICAO_OCUPACAO_2022)
    od["agua_rede"] = _bool(dd["D0260"], {"1"}, set("2345678"))
    od["esgoto_adequado"] = _bool(dd["D0250"], {"1", "2", "3"}, set("45679"))
    od["lixo_coletado"] = _bool(dd["D0310"], {"1", "2"}, set("3456"))
    od["energia"] = pd.Series(pd.NA, index=dd.index, dtype="boolean")  # variável não existe em 2022
    od["internet"] = _bool(dd["D0330"], {"1"}, {"2"})
    od["densidade_dormitorio"] = dd["D0240"]
    od["moradores"] = dd["D0150"]
    od["renda_dom_pc"] = dd["D0360"]
    od["renda_dom_pc_r2022"] = para_reais_jul2022(dd["D0360"], 2022)
    od["renda_dom_pc_sm"] = dd["D0360"] / SALARIO_MINIMO[2022]
    od["adequacao"] = C.adequacao(od["agua_rede"], od["esgoto_adequado"], od["lixo_coletado"])
    _finalizar(od, COLS_DOMICILIOS, 2022, "domicilios")


# =====================================================================================
# 2010 — FWF
# =====================================================================================
_UFS_VALIDAS = set(C.REGIAO_UF)


def _uf_de_codigo7(serie: pd.Series) -> pd.Series:
    s = serie.str.strip()
    uf2 = s.str[:2]
    valido = (s != "") & s.str[2:].str.fullmatch(r"0{5}").fillna(False) & uf2.isin(_UFS_VALIDAS)
    return uf2.where(valido, pd.NA)


def parse_2010() -> None:
    campos = ["V0001", "V0002", "V0011", "V0300", "V0010", "V1006", "V0502", "V0601", "V6036", "V0606",
              "V0618", "V0619", "V6222", "V0624", "V0626", "V6262", "V6264", "V6400", "V6900", "V6910",
              "V6930", "V6471", "V6511", "V6527", "V0660"]
    df = ler_fwf(DIR_2010 / "Amostra_Pessoas_15.txt", 2010, "pessoas", campos)
    _log(f"2010 pessoas PA lidas: {len(df):,}")
    df["uf_atual"] = df["V0001"].str.strip()
    df["mun_atual"] = df["uf_atual"] + df["V0002"].str.strip().str.zfill(5)
    df["uf_resid_5anos"] = _uf_de_codigo7(df["V6262"])
    df["mun_resid_5anos"] = df["V6264"].str.strip().replace("", pd.NA)
    idade = to_num(df["V6036"])

    out = pd.DataFrame(index=df.index)
    out["uf"], out["mun"], out["ap"], out["controle"] = df["uf_atual"], df["mun_atual"], df["V0011"].str.strip(), df["V0300"].str.strip()
    out["situacao"] = np.where(df["V1006"].str.strip() == "1", "urbana", "rural")
    out["peso"] = to_num(df["V0010"]) / 1e13
    out["sexo"] = df["V0601"].str.strip().map(C.SEXO)
    out["idade"] = idade
    out["cor_raca"] = df["V0606"].str.strip().map(C.COR_RACA)
    out["responsavel"] = df["V0502"].str.strip() == "01"
    out["nivel_instrucao"] = df["V6400"].str.strip().map(C.NIVEL_INSTRUCAO)
    # V6910 (ocupada/desocupada) fica em branco para quem NÃO é economicamente ativo
    # (V6900 = 2): essas pessoas são "não ocupadas", não faltantes.
    out["ocupado"] = _bool(df["V6910"], {"1"}, {"2"})
    out.loc[df["V6900"].str.strip() == "2", "ocupado"] = False
    out.loc[idade < 10, "ocupado"] = pd.NA
    out["posicao"] = df["V6930"].str.strip().map(C.POSICAO_2010)
    out["formal"] = out["posicao"].isin(C.FORMAL).astype("boolean").where(out["posicao"].notna(), pd.NA)
    out["setor"] = C.setor_por_cnae(df["V6471"], 2010)
    out["extrativa_mineral"] = (out["setor"] == "extrativa_mineral").astype("boolean").where(out["setor"].notna(), pd.NA)
    out["renda_trabalho"], out["renda_total"] = to_num(df["V6511"]), to_num(df["V6527"])
    out["renda_trabalho_r2022"] = para_reais_jul2022(out["renda_trabalho"], 2010)
    out["renda_total_r2022"] = para_reais_jul2022(out["renda_total"], 2010)
    out["renda_total_sm"] = out["renda_total"] / SALARIO_MINIMO[2010]
    out["renda_sm_faixa"] = C.faixa_renda_sm(out["renda_total_sm"])
    out["tipo_mig_5anos"] = classificar_5anos(df, censo=2010).astype("object")
    out.loc[idade < 5, "tipo_mig_5anos"] = pd.NA
    mig = out["tipo_mig_5anos"].isin(["intraestadual", "interestadual"])
    out["origem_uf"] = df["uf_resid_5anos"].where(mig)
    out["origem_mun"] = df["mun_resid_5anos"].where(mig)
    uf_nasc = _uf_de_codigo7(df["V6222"])
    v618 = df["V0618"].str.strip()
    nat = pd.Series(pd.NA, index=df.index, dtype="object")
    nat[v618.isin(["1", "2"])] = "municipio"
    # V6222 (UF de nascimento) só é preenchida para quem nasceu em OUTRA UF (V0619 = 3);
    # quem nasceu nesta UF (V0619 = 1 ou 2) mas em outro município é "mesma_uf".
    v619 = df["V0619"].str.strip()
    nat[(v618 == "3") & (v619.isin(["1", "2"]) | (uf_nasc == df["uf_atual"]))] = "mesma_uf"
    nat[(v618 == "3") & uf_nasc.notna() & (uf_nasc != df["uf_atual"])] = "outra_uf"
    nat[(v618 == "3") & uf_nasc.isna() & (df["V6222"].str.strip() != "")] = "exterior"
    out["naturalidade"] = nat
    out["uf_nascimento"] = uf_nasc
    out.loc[v618.isin(["1", "2"]) | v619.isin(["1", "2"]), "uf_nascimento"] = df["uf_atual"]
    tempo = to_num(df["V0624"])
    out["tempo_moradia"] = tempo
    out.loc[v618 == "1", "tempo_moradia"] = idade
    out["ano_chegada"] = (2010 - tempo).where(v618 != "1")
    out["retorno"] = eh_retorno(df, censo=2010)
    out["trabalha_outro_mun"] = _bool(df["V0660"], {"3"}, {"1", "2", "4", "5"})
    _finalizar(out, COLS_PESSOAS, 2010, "pessoas")

    campos_d = ["V0001", "V0002", "V0011", "V0300", "V0010", "V1006", "V4001", "V4002", "V0201", "V0207",
                "V0208", "V0210", "V0211", "V0219", "V0220", "V6204", "V0401", "V6531"]
    dd = ler_fwf(DIR_2010 / "Amostra_Domicilios_15.txt", 2010, "domicilios", campos_d)
    dd = dd[dd["V4001"].str.strip() == "01"].copy()
    od = pd.DataFrame(index=dd.index)
    od["uf"] = dd["V0001"].str.strip()
    od["mun"] = od["uf"] + dd["V0002"].str.strip().str.zfill(5)
    od["ap"], od["controle"] = dd["V0011"].str.strip(), dd["V0300"].str.strip()
    od["situacao"] = np.where(dd["V1006"].str.strip() == "1", "urbana", "rural")
    od["peso"] = to_num(dd["V0010"]) / 1e13
    od["tipo"] = dd["V4002"].str.strip().map(C.TIPO_DOMICILIO_2010)
    od["condicao_ocupacao"] = dd["V0201"].str.strip().map(C.CONDICAO_OCUPACAO_2010)
    od["agua_rede"] = _bool(dd["V0208"], {"01"}, {"02", "03", "04", "05", "06", "07", "08", "09", "10"})
    od["esgoto_adequado"] = _bool(dd["V0207"], {"1", "2"}, {"3", "4", "5", "6"})
    od["lixo_coletado"] = _bool(dd["V0210"], {"1", "2"}, set("34567"))
    od["energia"] = _bool(dd["V0211"], {"1", "2"}, {"3"})
    od["internet"] = _bool(dd["V0220"], {"1"}, {"2"})
    od.loc[dd["V0219"].str.strip() == "2", "internet"] = False   # sem microcomputador -> V0220 em branco
    od["densidade_dormitorio"] = to_num(dd["V6204"]) / 10   # DEC=1 no layout oficial
    od["moradores"] = to_num(dd["V0401"])
    od["renda_dom_pc"] = to_num(dd["V6531"]) / 100          # DEC=2 no layout oficial
    od["renda_dom_pc_r2022"] = para_reais_jul2022(od["renda_dom_pc"], 2010)
    od["renda_dom_pc_sm"] = od["renda_dom_pc"] / SALARIO_MINIMO[2010]
    # esgoto só é perguntado a quem tem sanitário (V0206); sem sanitário = inadequado
    od.loc[dd["V0207"].str.strip() == "", "esgoto_adequado"] = False
    od["adequacao"] = C.adequacao(od["agua_rede"], od["esgoto_adequado"], od["lixo_coletado"])
    _finalizar(od, COLS_DOMICILIOS, 2010, "domicilios")


# =====================================================================================
# 2000 — FWF
# =====================================================================================
def parse_2000() -> None:
    campos_d = ["V0102", "V0103", "V0300", "AREAP", "V1006", "P001", "V0201", "V0202", "V0205", "V0207",
                "V0210", "V0211", "V0212", "V0213", "V7100", "V7204", "V7616"]
    dd = ler_fwf(DIR_2000 / "Dom15.txt", 2000, "domicilios", campos_d)
    dd = dd[dd["V0102"].str.strip() == C.UF_PA].copy()
    mun_map = dict(zip(dd["V0300"].str.strip(), dd["V0103"].str.strip()))
    dd = dd[dd["V0201"].str.strip() == "1"].copy()  # particular permanente
    od = pd.DataFrame(index=dd.index)
    od["uf"], od["mun"] = dd["V0102"].str.strip(), dd["V0103"].str.strip()
    od["ap"], od["controle"] = dd["AREAP"].str.strip(), dd["V0300"].str.strip()
    od["situacao"] = np.where(dd["V1006"].str.strip() == "1", "urbana", "rural")
    od["peso"] = to_num(dd["P001"]) / 1e8
    od["tipo"] = dd["V0202"].str.strip().map(C.TIPO_DOMICILIO_2000)
    od["condicao_ocupacao"] = dd["V0205"].str.strip().map(C.CONDICAO_OCUPACAO_2000)
    od["agua_rede"] = _bool(dd["V0207"], {"1"}, {"2", "3"})
    od["esgoto_adequado"] = _bool(dd["V0211"], {"1", "2"}, {"3", "4", "5", "6"})
    od.loc[dd["V0210"].str.strip() == "2", "esgoto_adequado"] = False   # sem sanitário
    od["lixo_coletado"] = _bool(dd["V0212"], {"1", "2"}, set("34567"))
    od["energia"] = _bool(dd["V0213"], {"1"}, {"2"})
    od["internet"] = pd.Series(pd.NA, index=dd.index, dtype="boolean")
    od["densidade_dormitorio"] = to_num(dd["V7204"]) / 10   # formato SAS 3.1
    od["moradores"] = to_num(dd["V7100"])
    od["renda_dom_pc"] = to_num(dd["V7616"]) / od["moradores"]
    od["renda_dom_pc_r2022"] = para_reais_jul2022(od["renda_dom_pc"], 2000)
    od["renda_dom_pc_sm"] = od["renda_dom_pc"] / SALARIO_MINIMO[2000]
    od["adequacao"] = C.adequacao(od["agua_rede"], od["esgoto_adequado"], od["lixo_coletado"])
    _finalizar(od, COLS_DOMICILIOS, 2000, "domicilios")

    campos = ["V0102", "V0300", "AREAP", "V1006", "P001", "V0401", "V0402", "V4572", "V0408", "V0415",
              "V0416", "V0417", "V4210", "V0424", "V4250", "V4260", "V4276", "V4300", "V4462", "V0447",
              "V4512", "V4614"]
    df = ler_fwf(DIR_2000 / "Pes15.txt", 2000, "pessoas", campos)
    _log(f"2000 pessoas PA lidas: {len(df):,}")
    df["uf_atual"] = df["V0102"].str.strip()
    df = df[df["uf_atual"] == C.UF_PA].copy()
    df["mun_atual"] = df["V0300"].str.strip().map(mun_map)
    sem = df["mun_atual"].isna()
    if sem.any():
        _log(f"aviso 2000: {sem.sum()} pessoas sem domicílio correspondente descartadas")
        df = df[~sem].copy()
    idade = to_num(df["V4572"])

    out = pd.DataFrame(index=df.index)
    out["uf"], out["mun"], out["ap"], out["controle"] = df["uf_atual"], df["mun_atual"], df["AREAP"].str.strip(), df["V0300"].str.strip()
    out["situacao"] = np.where(df["V1006"].str.strip() == "1", "urbana", "rural")
    out["peso"] = to_num(df["P001"]) / 1e8
    out["sexo"] = df["V0401"].str.strip().map(C.SEXO)
    out["idade"] = idade
    out["cor_raca"] = df["V0408"].str.strip().map(C.COR_RACA)
    out["responsavel"] = df["V0402"].str.strip() == "1"
    out["nivel_instrucao"] = C.nivel_por_anos_estudo(df["V4300"].str.strip().replace("", pd.NA))
    out["ocupado"] = (df["V4462"].str.strip() != "").astype("boolean")
    out.loc[idade < 10, "ocupado"] = pd.NA
    out["posicao"] = df["V0447"].str.strip().map(C.POSICAO_2000)
    out["formal"] = out["posicao"].isin(C.FORMAL).astype("boolean").where(out["posicao"].notna(), pd.NA)
    out["setor"] = C.setor_por_cnae(df["V4462"], 2000)
    out["extrativa_mineral"] = (out["setor"] == "extrativa_mineral").astype("boolean").where(out["setor"].notna(), pd.NA)
    out["renda_trabalho"], out["renda_total"] = to_num(df["V4512"]), to_num(df["V4614"])
    out["renda_trabalho_r2022"] = para_reais_jul2022(out["renda_trabalho"], 2000)
    out["renda_total_r2022"] = para_reais_jul2022(out["renda_total"], 2000)
    out["renda_total_sm"] = out["renda_total"] / SALARIO_MINIMO[2000]
    out["renda_sm_faixa"] = C.faixa_renda_sm(out["renda_total_sm"])
    out["tipo_mig_5anos"] = classificar_5anos(df, censo=2000).astype("object")
    out.loc[idade < 5, "tipo_mig_5anos"] = pd.NA
    mig = out["tipo_mig_5anos"].isin(["intraestadual", "interestadual"])
    out["origem_uf"] = df["V4260"].str.strip().map(UF_CODIGO_MIGRACAO_2000).where(mig)
    out["origem_mun"] = df["V4250"].str.strip().replace("", pd.NA).where(mig)
    v415, v417 = df["V0415"].str.strip(), df["V0417"].str.strip()
    uf_nasc = df["V4210"].str.strip().map(UF_CODIGO_MIGRACAO_2000)   # branco = natural do PA
    nat = pd.Series(pd.NA, index=df.index, dtype="object")
    nat[(v415 == "1") | (v417 == "1")] = "municipio"
    nat[(v417 == "2") & (df["V4210"].str.strip() == "")] = "mesma_uf"
    nat[(v417 == "2") & uf_nasc.notna() & (uf_nasc != C.UF_PA)] = "outra_uf"
    nat[(v417 == "2") & (df["V4210"].str.strip() != "") & uf_nasc.isna()] = "exterior"
    out["naturalidade"] = nat
    out["uf_nascimento"] = uf_nasc
    out.loc[nat.isin(["municipio", "mesma_uf"]), "uf_nascimento"] = C.UF_PA
    tempo = to_num(df["V0416"])
    out["tempo_moradia"] = tempo
    out.loc[v415 == "1", "tempo_moradia"] = idade
    out["ano_chegada"] = (2000 - tempo).where(v415 == "2")
    out["retorno"] = eh_retorno(df, censo=2000)
    v4276 = df["V4276"].str.strip()
    outro = (v4276 != "") & ~v4276.isin(["0100008", "0200006"]) & (v4276 != df["mun_atual"])
    out["trabalha_outro_mun"] = outro.astype("boolean")
    out.loc[v4276 == "", "trabalha_outro_mun"] = pd.NA   # 2000 mistura trabalho E estudo (ver lib.migracao)
    _finalizar(out, COLS_PESSOAS, 2000, "pessoas")


# =====================================================================================
# 1991 — DBF (Deflate64 no zip -> unzip -p)
# =====================================================================================
def _dbf_1991() -> Path:
    dest = INTERIM / "censo1991" / "CD91AMOUP15.DBF"
    if dest.exists() and dest.stat().st_size == 260751753:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    zips = [z for z in ZIP_1991 if z.exists()]
    if not zips:
        raise FileNotFoundError("zip do Censo 1991 não encontrado (FTP local nem Zeitmaschine)")
    with dest.open("wb") as fh:
        subprocess.run(["unzip", "-p", str(zips[0]), "Dados/*/CD91AMOUP15.DBF"], stdout=fh, check=True)
    return dest


def parse_1991() -> None:
    from dbfread import DBF

    campos = ["MUNICNUM", "SITSET", "PESO", "PESSOAN", "SEXO", "IDADEANO", "RACACOR", "PARENDOM", "EDANOEST",
              "ATIVISET", "ATIVIDAD", "POSOCUP", "CARTASS", "RPRINCIV", "RTOTALPV", "RTONOMIF",
              "MINASCMU", "MIUFPAIS", "MIANMOMU", "MIMO86UF", "MIMO86MU", "MIULTMUD",
              "ESPECIE", "LOCALIZA", "CONDOCUP", "AGUA", "SANESCOA", "SANUSO", "LIXO", "ILUMINA",
              "DEMODORM", "RDOMICIV", "RFAPCAPF", "RDONOMIF"]
    tabela = DBF(_dbf_1991(), load=False, encoding="cp850")
    df = pd.DataFrame(iter(tabela), columns=tabela.field_names)[campos]
    _log(f"1991 registros PA lidos: {len(df):,}")
    df = df.reset_index(drop=True)
    # chave de domicílio: sequência de PESSOAN == 1 (número de ordem do morador)
    df["controle"] = "91" + (df["PESSOAN"] == 1).cumsum().astype(str)
    df["mun"] = ("15" + df["MUNICNUM"].astype(str).str.zfill(4)).map(
        lambda x: C.MUNICIPIOS_1991.get(x[2:], "15" + x[2:] + "X"))
    df = df[df["ESPECIE"] == 1].copy()

    out = pd.DataFrame(index=df.index)
    out["uf"], out["mun"], out["ap"], out["controle"] = C.UF_PA, df["mun"], pd.NA, df["controle"]
    out["situacao"] = np.where(df["SITSET"].isin([1, 2, 3]), "urbana", "rural")
    out["peso"] = pd.to_numeric(df["PESO"], errors="coerce")
    out["sexo"] = df["SEXO"].astype(str).map(C.SEXO)
    out["idade"] = pd.to_numeric(df["IDADEANO"], errors="coerce")
    out["cor_raca"] = df["RACACOR"].astype(str).map(C.COR_RACA)
    out["responsavel"] = df["PARENDOM"] == 1
    anos = pd.to_numeric(df["EDANOEST"], errors="coerce").replace(31, pd.NA)
    out["nivel_instrucao"] = C.nivel_por_anos_estudo(anos)
    ocup = df["ATIVISET"].between(1, 11)
    out["ocupado"] = ocup.astype("boolean")
    out.loc[out["idade"] < 10, "ocupado"] = pd.NA
    pos = df["POSOCUP"].map(C.POSICAO_1991)
    emp = df["POSOCUP"].isin(C.POSICAO_1991_EMPREGADO)
    pos[emp & (df["CARTASS"] == 1)] = "empregado_com_carteira"
    pos[emp & (df["CARTASS"] != 1)] = "empregado_sem_carteira"
    out["posicao"] = pos.where(ocup, pd.NA)
    out["formal"] = out["posicao"].isin(C.FORMAL).astype("boolean").where(out["posicao"].notna(), pd.NA)
    out["setor"] = C.setor_1991(df["ATIVISET"], df["ATIVIDAD"], df["POSOCUP"]).where(ocup, pd.NA)
    out["extrativa_mineral"] = (out["setor"] == "extrativa_mineral").astype("boolean").where(out["setor"].notna(), pd.NA)
    # renda em Cr$ de 1991 — sem deflator IPCA para 1991 no projeto; publica-se só em faixas de SM
    out["renda_trabalho"] = pd.to_numeric(df["RPRINCIV"], errors="coerce").where(df["RPRINCIV"] < 9999998)
    out["renda_total"] = pd.to_numeric(df["RTOTALPV"], errors="coerce").where(df["RTOTALPV"] < 99999998)
    out["renda_trabalho_r2022"] = np.nan
    out["renda_total_r2022"] = np.nan
    out["renda_total_sm"] = np.nan
    out["renda_sm_faixa"] = df["RTONOMIF"].map(C.RENDA_SM_1991)
    # migração de data fixa (residência em 01/09/1986)
    uf86 = pd.to_numeric(df["MIMO86UF"], errors="coerce")
    mu86 = df["MIMO86MU"].astype(str).str.zfill(4)
    tempo = pd.to_numeric(df["MIANMOMU"], errors="coerce").replace(99, pd.NA)
    tipo = pd.Series(pd.NA, index=df.index, dtype="object")
    tipo[uf86 == 70] = "nao_migrante"
    tipo[(uf86 == 15) & (mu86 == df["MUNICNUM"].astype(str).str.zfill(4))] = "nao_migrante"
    tipo[(uf86 == 15) & (mu86 != df["MUNICNUM"].astype(str).str.zfill(4)) & (mu86 != "9999")] = "intraestadual"
    tipo[uf86.between(11, 54) & (uf86 != 15)] = "interestadual"
    tipo[uf86 == 80] = "internacional"
    implicito = (df["MINASCMU"] == 1) | (df["MIULTMUD"] == 98) | (tempo >= 5)
    tipo[implicito & tipo.isna()] = "nao_migrante"
    tipo[out["idade"] < 5] = pd.NA
    out["tipo_mig_5anos"] = tipo
    mig = tipo.isin(["intraestadual", "interestadual"])
    out["origem_uf"] = uf86.map(lambda x: f"{int(x):02d}" if pd.notna(x) and 11 <= x <= 53 else pd.NA).where(mig)
    out["origem_mun"] = pd.NA   # código municipal de 1991 (4 dígitos) sem tabela de conversão publicada
    nasc = df["MINASCMU"]
    ufp = pd.to_numeric(df["MIUFPAIS"], errors="coerce")
    uf_nasc = ufp.map(lambda x: UF_CODIGO_MIGRACAO_2000.get(f"{int(x):02d}") if pd.notna(x) and 1 <= x <= 27 else pd.NA)
    nat = pd.Series(pd.NA, index=df.index, dtype="object")
    nat[nasc.isin([1, 2])] = "municipio"
    nat[(nasc == 3) & (uf_nasc == C.UF_PA)] = "mesma_uf"
    nat[(nasc == 3) & uf_nasc.notna() & (uf_nasc != C.UF_PA)] = "outra_uf"
    nat[(nasc == 3) & (ufp >= 30)] = "exterior"
    out["naturalidade"] = nat
    out["uf_nascimento"] = uf_nasc
    out.loc[nasc.isin([1, 2]), "uf_nascimento"] = C.UF_PA
    out["tempo_moradia"] = tempo
    out.loc[nasc == 1, "tempo_moradia"] = out["idade"]
    out["ano_chegada"] = (1991 - tempo).where(nasc != 1)
    out["retorno"] = (nasc == 2) & mig
    out["trabalha_outro_mun"] = pd.Series(pd.NA, index=df.index, dtype="boolean")
    _finalizar(out, COLS_PESSOAS, 1991, "pessoas")

    dom = df[df["PESSOAN"] == 1].copy()
    od = pd.DataFrame(index=dom.index)
    od["uf"], od["mun"], od["ap"], od["controle"] = C.UF_PA, dom["mun"], pd.NA, dom["controle"]
    od["situacao"] = np.where(dom["SITSET"].isin([1, 2, 3]), "urbana", "rural")
    od["peso"] = pd.to_numeric(dom["PESO"], errors="coerce")
    od["tipo"] = dom["LOCALIZA"].map(C.TIPO_DOMICILIO_1991)
    od["condicao_ocupacao"] = dom["CONDOCUP"].map(C.CONDICAO_OCUPACAO_1991)
    od["agua_rede"] = dom["AGUA"].isin([1, 4]).astype("boolean").where(dom["AGUA"].between(1, 6), pd.NA)
    od["esgoto_adequado"] = dom["SANESCOA"].isin([1, 2, 3]).astype("boolean").where(dom["SANESCOA"].between(0, 7), pd.NA)
    od["lixo_coletado"] = dom["LIXO"].isin([1, 2]).astype("boolean").where(dom["LIXO"].between(1, 7), pd.NA)
    od["energia"] = dom["ILUMINA"].isin([1, 2]).astype("boolean").where(dom["ILUMINA"].between(1, 4), pd.NA)
    od["internet"] = pd.Series(pd.NA, index=dom.index, dtype="boolean")
    od["densidade_dormitorio"] = pd.to_numeric(dom["DEMODORM"], errors="coerce").where(dom["DEMODORM"] < 9999)
    od["moradores"] = df.groupby("controle").size().reindex(dom["controle"]).values
    od["renda_dom_pc"] = np.nan
    od["renda_dom_pc_r2022"] = np.nan
    od["renda_dom_pc_sm"] = np.nan
    od["adequacao"] = C.adequacao(od["agua_rede"], od["esgoto_adequado"], od["lixo_coletado"])
    _finalizar(od, COLS_DOMICILIOS, 1991, "domicilios")


PARSERS = {1991: parse_1991, 2000: parse_2000, 2010: parse_2010, 2022: parse_2022}

if __name__ == "__main__":
    alvo = [int(a) for a in sys.argv[1:]] or [1991, 2000, 2010, 2022]
    for censo in alvo:
        t0 = time.time()
        print(f"Censo {censo}")
        PARSERS[censo]()
        print(f"  concluído em {time.time() - t0:,.0f}s")
