"""
E1 / Fase 1 passo 1 (PLANO.md) — baixa e versiona em `data/processed/ibge/`
as tabelas públicas do IBGE (SIDRA + Cidades + CFEM/ANM) para Canaã dos
Carajás (1502152) e seu único distrito (150215205, = a sede). Dados públicos
agregados — não passam pelo gate de revelação (`disclosure_check.py`), que é
só para os microdados (Fase 2).

Cada tabela SIDRA é buscada por `lib.sidra.fetch_tabela()` (genérico: consulta
os metadados da tabela e pede todas as variáveis/classificações — nenhum
código de variável ou categoria foi digitado à mão). Grava bruto (JSON) +
tidy (parquet) por tabela e um índice (`_index.parquet`) com fonte/URL/data.

Uso:
    .venv/bin/python pipeline/10_ibge_api.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import sidra  # noqa: E402

MUNICIPIO = "1502152"
DISTRITO = "150215205"
OUT = sidra.OUT

# --- 1. Tabelas SIDRA (Fase 1 passo 1 do PLANO.md) --------------------------
# (tabela, nivel, codigo, nome_saida, descrição)
TABELAS = [
    (200, "n6", MUNICIPIO, "t200_pop_historica_municipio",
     "População residente 1970-2010 por sexo/situação/grupo de idade (série longa)"),
    (202, "n10", DISTRITO, "t202_pop_distrito",
     "População residente 1970-2010 por sexo/situação — nível distrito (sede)"),
    (1378, "n6", MUNICIPIO, "t1378_pop_2010_condicao",
     "População residente 2010 por situação/sexo/idade, condição no domicílio"),
    (9923, "n6", MUNICIPIO, "t9923_situacao_2022",
     "População residente 2022 por situação do domicílio"),
    (4714, "n6", MUNICIPIO, "t4714_area_densidade_2022",
     "População, área territorial e densidade demográfica 2022"),
    (4709, "n6", MUNICIPIO, "t4709_variacao_2022",
     "População, variação absoluta e taxa de crescimento geométrico 2022"),
    (9605, "n6", MUNICIPIO, "t9605_cor_raca_censos",
     "População residente por cor ou raça, Censos Demográficos"),
    (6579, "n6", MUNICIPIO, "t6579_estimativas_2001_2026",
     "População residente estimada 2001-2026 (com lacunas)"),
    (305, "n6", MUNICIPIO, "t305_contagem_1996",
     "Contagem da População 1996 — população em domicílios particulares por sexo do chefe/situação"),
    (793, "n6", MUNICIPIO, "t793_contagem_2007",
     "Contagem da População 2007 — população residente"),
    (5938, "n6", MUNICIPIO, "t5938_pib_municipal",
     "PIB municipal a preços correntes 2002-2023"),
    (1552, "n6", MUNICIPIO, "t1552_idade_2000_2010",
     "População residente por situação/sexo/idade (ano a ano) 2000 e 2010"),
    (9514, "n6", MUNICIPIO, "t9514_idade_2022",
     "População residente por sexo/idade (ano a ano) 2022"),
    (3175, "n6", MUNICIPIO, "t3175_cor_raca_situacao_idade",
     "População residente por cor/raça, situação, sexo e idade"),
    (1383, "n6", MUNICIPIO, "t1383_alfabetizacao",
     "Taxa de alfabetização das pessoas de 10+ anos por sexo"),
    (3596, "n6", MUNICIPIO, "t3596_frequencia_escolar",
     "Pessoas que frequentavam escola/creche"),
    (2098, "n6", MUNICIPIO, "t2098_condicao_atividade",
     "Pessoas de 10+ anos por cor/raça, condição de atividade"),
    (9542, "n6", MUNICIPIO, "t9542_alfabetizacao_grupo",
     "Pessoas de 15+ anos, alfabetizadas, por sexo/cor/grupo de idade"),
    # t/9556 (segurança alimentar) só existe em N1 (Brasil) — sem uso para
    # Canaã, não buscada. t/10063 (nível superior por área) só desce a N3
    # (UF) — buscada para o Pará como contexto regional, não município.
    (10063, "n3", "15", "t10063_ensino_superior_pa",
     "Pessoas com nível superior completo, por área de formação (Pará, UF — tabela não desce a município)"),
]

# CEMPRE (t/6449): 1.067 categorias de CNAE excede o limite de 50.000 células
# da API com todas as variáveis/anos — restrita às categorias de nível 0-1
# (Total + 21 seções da CNAE) em vez da desagregação completa.
TABELA_CEMPRE = (6449, "n6", MUNICIPIO, "t6449_cempre",
                  "CEMPRE — empresas, pessoal ocupado, salários (Total + seções CNAE)")


def _categorias_cnae_secao(meta: dict) -> str:
    cats = meta["classificacoes"][0]["categorias"]
    ids = [str(c["id"]) for c in cats if c.get("nivel", 0) <= 1]
    return ",".join(ids)

# --- 2. Indicadores Cidades (API v1/pesquisas/indicadores) ------------------
INDICADORES_CIDADES = {
    96385: "populacao_2010_2022",
    96386: "densidade_demografica_2022",
    60045: "escolarizacao_6_14_2010_2022",
    60036: "receitas_externas_pct_2014_2022",
}
URL_INDICADOR = "https://servicodados.ibge.gov.br/api/v1/pesquisas/indicadores/{ind}/resultados/{municipio}"


def fetch_indicadores_cidades() -> pd.DataFrame:
    linhas = []
    for ind, nome in INDICADORES_CIDADES.items():
        r = requests.get(URL_INDICADOR.format(ind=ind, municipio=MUNICIPIO), timeout=30)
        r.raise_for_status()
        dados = r.json()
        for bloco in dados:
            for res in bloco.get("res", []):
                for ano, valor in res.get("res", {}).items():
                    linhas.append({"indicador": ind, "nome": nome, "ano": ano, "valor": valor})
    df = pd.DataFrame(linhas)
    df.to_parquet(OUT / "cidades_indicadores.parquet", index=False)
    print(f"  Indicadores Cidades: {len(df)} linhas, {df['indicador'].nunique()} indicadores")
    return df


# --- 3. CFEM (ANM) — só Pará, filtrado para Canaã dos Carajás ---------------
URL_CFEM = (
    "https://sistemas.anm.gov.br/arrecadacao/extra/relatorios/"
    "distribuicao_cfem_muni.aspx?ano={ano}&uf=PA"
)
ANOS_CFEM = list(range(2004, 2027))  # antes de 2004 o relatório vem vazio (achado do projeto irmão)


def _parse_valor_br(txt: str):
    s = txt.replace("\xa0", "").strip()
    if not s:
        return None
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def fetch_cfem_canaa() -> pd.DataFrame:
    from bs4 import BeautifulSoup

    cache_dir = OUT.parent.parent / "externo" / "cfem_pa"
    cache_dir.mkdir(parents=True, exist_ok=True)
    linhas = []
    for ano in ANOS_CFEM:
        p_html = cache_dir / f"distribuicao_PA_{ano}.html"
        if not p_html.exists():
            r = requests.get(URL_CFEM.format(ano=ano), headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
            r.raise_for_status()
            p_html.write_bytes(r.content)
        soup = BeautifulSoup(p_html.read_bytes(), "lxml")
        tabela = soup.find("table", class_="tabelaRelatorio")
        if tabela is None:
            continue
        for tr in tabela.find_all("tr", recursive=False)[1:]:
            tds = tr.find_all("td")
            if not tds or "CARAJ" not in tds[0].get_text(strip=True).upper():
                continue
            nome = tds[0].get_text(strip=True)
            if "CANA" not in nome.upper():
                continue
            total = _parse_valor_br(tds[-1].get_text())
            linhas.append({"ano": ano, "municipio_nome_raw": nome, "cfem_distribuido_r": total})
    df = pd.DataFrame(linhas)
    df.to_parquet(OUT / "cfem_canaa_2004_2026.parquet", index=False)
    n_com_valor = df["cfem_distribuido_r"].notna().sum() if len(df) else 0
    print(f"  CFEM Canaã dos Carajás: {len(df)} anos, {n_com_valor} com valor > 0")
    return df


def main() -> None:
    resumo = []
    print(f"Baixando {len(TABELAS)} tabelas SIDRA para Canaã dos Carajás…\n")
    for i, (tabela, nivel, codigo, nome_saida, desc) in enumerate(TABELAS, 1):
        print(f"[{i}/{len(TABELAS)}] t/{tabela} ({nivel}/{codigo}) — {desc}")
        try:
            df = sidra.fetch_tabela(tabela, nivel=nivel, codigo=codigo, nome_saida=nome_saida)
            print(f"    OK — {len(df)} linhas")
            resumo.append({"tabela": tabela, "nome_saida": nome_saida, "status": "ok", "linhas": len(df)})
        except Exception as e:  # noqa: BLE001
            print(f"    FALHOU — {e}")
            resumo.append({"tabela": tabela, "nome_saida": nome_saida, "status": f"erro: {e}", "linhas": 0})

    tabela, nivel, codigo, nome_saida, desc = TABELA_CEMPRE
    print(f"\n[CEMPRE] t/{tabela} ({nivel}/{codigo}) — {desc}")
    try:
        meta = sidra.metadados(tabela)
        cats_secao = _categorias_cnae_secao(meta)
        df = sidra.fetch_tabela(tabela, nivel=nivel, codigo=codigo, nome_saida=nome_saida,
                                 classificacoes={12762: cats_secao})
        print(f"    OK — {len(df)} linhas")
        resumo.append({"tabela": tabela, "nome_saida": nome_saida, "status": "ok", "linhas": len(df)})
    except Exception as e:  # noqa: BLE001
        print(f"    FALHOU — {e}")
        resumo.append({"tabela": tabela, "nome_saida": nome_saida, "status": f"erro: {e}", "linhas": 0})

    print("\nIndicadores Cidades…")
    try:
        fetch_indicadores_cidades()
    except Exception as e:  # noqa: BLE001
        print(f"  FALHOU — {e}")

    print("\nCFEM (ANM) — Pará, 2004-2026, filtrado para Canaã dos Carajás…")
    try:
        fetch_cfem_canaa()
    except Exception as e:  # noqa: BLE001
        print(f"  FALHOU — {e}")

    resumo_df = pd.DataFrame(resumo)
    resumo_df.to_csv(OUT / "_resumo_fetch.csv", index=False)
    n_ok = (resumo_df["status"] == "ok").sum()
    print(f"\nResumo: {n_ok}/{len(resumo_df)} tabelas OK. Ver {OUT / '_resumo_fetch.csv'}")


if __name__ == "__main__":
    main()
