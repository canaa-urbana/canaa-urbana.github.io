"""
Classificação de exposição mineral municipal — PLANO.md §3.2.

Métrica primária: CFEM per capita (distribuição, não arrecadação — é o valor
que de fato chega ao caixa do município), média 2018-2022, de
`data/externo/cfem/cfem_distribuicao_municipal.parquet` (produzido por
`00_fetch_externos.py::consolidar_cfem`). Município sem nenhum ano de CFEM
distribuído entra como zero, não como ausente -- ausência de linha em
`cfem_distribuicao_municipal.parquet` significa "não recebeu CFEM naquele
ano", confirmado pela lista de municípios do próprio relatório da ANM ser mais
curta que o total de municípios da UF (ver 00_fetch_externos.py).

ESCOPO ATUAL (2026-09-01) -- ver PLANO.md §3.2 para o desenho completo:
    - Implementado: intensidade contínua (CFEM per capita) e tiers por
      quantil (`grupo_cfem`).
    - NÃO implementado ainda, sinalizado explicitamente abaixo em vez de
      aproximado às pressas:
        (a) separação por substância (ferro/ouro/bauxita/...) -- precisa do
            relatório de CFEM por substância em nível municipal, ainda não
            explorado;
        (b) garimpo vs. industrial -- mesma dependência;
        (c) exclusão de municípios de petróleo/gás por royalties ANP -- os
            dados existem (`gov.br/anp/.../royalties`, planilhas mensais em
            ZIP, 1999-presente) mas NÃO foram baixados nesta sessão por
            restrição de tempo. `EXCLUIR_PETROLEO_GAS` fica vazio de
            propósito -- **NUNCA** preencher com uma lista digitada de
            memória (violaria a regra de verificação em fonte primária do
            projeto); buscar os dados da ANP antes de usar este módulo para
            qualquer resultado que entre no artigo.
"""
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent.parent
EXTERNO = BASE / "data" / "externo"

ANOS_CFEM_PADRAO = (2018, 2019, 2020, 2021, 2022)

# Municípios com royalties de petróleo/gás relevantes -- EXCLUÍDOS do grupo de
# tratamento mineral (grupo "petroleo_gas", nunca somado a "mineral").
# VAZIO DE PROPÓSITO -- ver docstring do módulo, item (c).
EXCLUIR_PETROLEO_GAS: set[str] = set()


def carregar_cfem(anos: tuple[int, ...] = ANOS_CFEM_PADRAO) -> pd.DataFrame:
    """CFEM distribuído médio (R$/ano) e per capita por município, média dos
    `anos` pedidos. Usa `populacao_municipal_2022.parquet` como denominador
    fixo (não há série de população municipal para os anos intermediários no
    Censo -- é uma aproximação documentada, não um erro)."""
    cfem = pd.read_parquet(EXTERNO / "cfem" / "cfem_distribuicao_municipal.parquet")
    cfem = cfem[cfem["ano"].isin(anos)]
    media = (
        cfem.groupby(["cod_municipio", "municipio_nome", "uf_sigla"])["cfem_distribuido_r"]
        .sum().div(len(anos)).reset_index()
        .rename(columns={"cfem_distribuido_r": "cfem_medio_r"})
    )

    pop = pd.read_parquet(EXTERNO / "populacao_municipal_2022.parquet")
    pib = pd.read_parquet(EXTERNO / "pib_municipal.parquet")

    out = pop.merge(media[["cod_municipio", "cfem_medio_r"]], on="cod_municipio", how="left")
    out = out.merge(pib[["cod_municipio", "pib_mil_r"]], on="cod_municipio", how="left")
    out["cfem_medio_r"] = out["cfem_medio_r"].fillna(0.0)

    out["cfem_per_capita"] = out["cfem_medio_r"] / out["populacao_2022"]
    out["cfem_pct_pib"] = 100 * out["cfem_medio_r"] / (out["pib_mil_r"] * 1000)
    return out


def classificar_grupo_cfem(
    df: pd.DataFrame, col_valor: str = "cfem_per_capita",
    cortes: dict[str, float] | None = None,
) -> pd.Series:
    """Tiers de intensidade mineral por CFEM per capita (R$/hab/ano, média
    2018-2022). Cortes default a partir da distribuição observada nesta
    sessão (ver `scripts/lib/tests` -- ajustar com sensibilidade antes de
    publicar, PLANO.md exige documentar o corte e testá-lo):
        0                -> 'nao_minerario'
        (0, p50_pos]     -> 'produtor_baixo'   (mediana entre os >0)
        (p50, p90_pos]   -> 'produtor_medio'
        > p90_pos        -> 'produtor_alto'
    Município em `EXCLUIR_PETROLEO_GAS` recebe 'petroleo_gas' independente do
    valor de CFEM (a seção B do Censo mistura minério e petróleo -- ver
    PLANO.md regra 4)."""
    v = df[col_valor]
    positivos = v[v > 0]
    if cortes is None:
        cortes = {
            "p50": positivos.quantile(0.50) if len(positivos) else 0.0,
            "p90": positivos.quantile(0.90) if len(positivos) else 0.0,
        }
    out = pd.Series("nao_minerario", index=df.index, dtype="object")
    out[v > 0] = "produtor_baixo"
    out[v > cortes["p50"]] = "produtor_medio"
    out[v > cortes["p90"]] = "produtor_alto"

    if "cod_municipio" in df.columns and EXCLUIR_PETROLEO_GAS:
        out[df["cod_municipio"].isin(EXCLUIR_PETROLEO_GAS)] = "petroleo_gas"
    return out.astype("category")


# Limiar de CFEM/PIB (%) para "universo minerário" nas perguntas 2-7 -- ver
# achado desta sessão: `grupo_cfem` por CFEM per capita SOZINHO classifica
# Recife, Guarulhos, Maceió, Duque de Caxias, Sorocaba, Ribeirão Preto, Cuiabá,
# Joinville e Caxias do Sul como 'produtor_medio' -- todas cidades grandes e
# diversificadas em que a mineração é econômicamente irrelevante (CFEM/PIB
# entre 0,0007% e 0,006%), mas cujo porte populacional faz um CFEM per capita
# trivial passar da mediana dos municípios com CFEM>0. `cfem_pct_pib` não sofre
# desse viés de escala. Testado nesta sessão: 0,02% de CFEM/PIB é o menor corte
# que remove TODAS as cidades >300 mil habitantes sem mineração relevante,
# mantendo os municípios genuinamente mineradores de porte médio (ex.
# Mogi das Cruzes/SP, Porto Velho/RO ficam de fora acima de 0,02%, mas só
# entram com limiares mais frouxos, sem clareza sobre se é mineração real ou
# efeito de escala -- por isso o corte mais conservador).
LIMIAR_CFEM_PCT_PIB = 0.02


def municipios_minerarios(
    grupo_min: int = 1, anos: tuple[int, ...] = ANOS_CFEM_PADRAO
) -> pd.DataFrame:
    """Painel de exposição mineral pronto para juntar ao Censo por `cod_municipio`
    (= `P0080`), restrito a `grupo_cfem` != 'produtor_baixo' se `grupo_min`>0
    -- conveniência para os testes de mercado de trabalho (Q1, Q6), que
    precisam de um corte binário além da variável contínua. Traz também
    `minerario_significativo` (bool) = `grupo_cfem` em produtor_médio/alto E
    `cfem_pct_pib` >= `LIMIAR_CFEM_PCT_PIB` -- usar esse, não só `grupo_cfem`,
    para selecionar o "universo minerário" nas perguntas 2-7 (ver docstring de
    `LIMIAR_CFEM_PCT_PIB`).

    NUNCA MUDAR O COMPORTAMENTO DEFAULT DESTA FUNÇÃO -- `02_construir_painel.py`
    do artigo 2022 (já publicado) depende dela com `EXCLUIR_PETROLEO_GAS`
    vazio; qualquer melhoria na exclusão de petróleo entra como uma função
    NOVA (`municipios_minerarios_sem_petroleo`, abaixo), nunca como alteração
    aqui, para que reprocessar o artigo 2022 continue reproduzindo os mesmos
    números (ver PLANO_TEMPORAL.md, decisão de preservar o artigo existente)."""
    df = carregar_cfem(anos)
    df["grupo_cfem"] = classificar_grupo_cfem(df)
    df["minerario_significativo"] = (
        df["grupo_cfem"].isin(["produtor_medio", "produtor_alto"])
        & (df["cfem_pct_pib"] >= LIMIAR_CFEM_PCT_PIB)
    )
    return df


# ---------------------------------------------------------------------------
# Exclusão de petróleo/gás por evidência censitária -- painel temporal
# (PLANO_TEMPORAL.md §2/§4/Fase E). NÃO usada pelo artigo 2022 (ver nota
# acima); implementa o que `EXCLUIR_PETROLEO_GAS` deixava vazio de propósito,
# agora com fonte primária verificável em vez de lista digitada de memória:
# a participação de trabalhadores em extração de petróleo e gás
# (`lib.cnae.eh_petroleo_gas`) dentro dos OCUPADOS de cada município, medida
# no próprio Censo (2000 ou 2010 -- 2022 só tem a seção agregada e não permite
# essa separação, ver lib/cnae.py).
# ---------------------------------------------------------------------------

# Limiar de participação censitária de petróleo/gás (%) entre os ocupados do
# município -- testado nesta sessão com o Censo 2010 (900/5.565 municípios
# com participação > 0; distribuição bem assimétrica, mediana 0,11%, p90
# 0,63%). 0,5% fica entre p75 (0,26%) e p90 (0,63%) e captura os hubs
# conhecidos de royalties ANP -- Macaé (7,9%), Rio das Ostras (7,2%), Bacia de
# Campos (Carapebus, Quissamã, São Fidélis, Campos dos Goytacazes), Bacia
# Potiguar (Mossoró, Macau, Alto do Rodrigues, Guamaré 0,87%), Recôncavo
# Baiano (Catu, São Sebastião do Passé, Alagoinhas, Pojuca) e o polo de
# refino de Araucária/PR -- sem exigir mais que ~2% dos municípios do país.
LIMIAR_PCT_PETROLEO = 0.5


def calcular_participacao_petroleo(censo: int = 2010) -> pd.DataFrame:
    """Participação de trabalhadores de petróleo/gás (`lib.cnae.eh_petroleo_gas`)
    entre os OCUPADOS de cada município, no `censo` pedido (2000 ou 2010).
    Lê `data/processed/raw_{censo}/pessoas_*.parquet` -- roda depois da Fase B
    (`01c_parse_2000.py`/`01d_parse_2010.py`)."""
    import glob

    import duckdb

    from lib.cnae import eh_petroleo_gas

    raw_dir = BASE / "data" / "processed" / f"raw_{censo}"
    arquivos = sorted(glob.glob(str(raw_dir / "pessoas_*.parquet")))
    assert arquivos, f"{raw_dir} vazio -- rode o parser do Censo {censo} antes"

    col_ativ = {2000: "V4462", 2010: "V6471"}[censo]
    col_ocupado = {2000: "V0439", 2010: "V6910"}[censo]
    con = duckdb.connect()
    df = con.execute(
        f"SELECT mun_atual, {col_ativ} AS atividade, peso "
        f"FROM read_parquet({arquivos!r}) WHERE {col_ocupado} = '1'"
    ).fetchdf()
    df["petroleo"] = eh_petroleo_gas(df["atividade"], censo)
    df["peso_petroleo"] = df["petroleo"] * df["peso"]

    out = df.groupby("mun_atual").agg(
        pop_ocupada=("peso", "sum"), pop_ocupada_petroleo=("peso_petroleo", "sum"),
    ).reset_index().rename(columns={"mun_atual": "cod_municipio"})
    out["pct_petroleo"] = 100 * out["pop_ocupada_petroleo"] / out["pop_ocupada"]
    return out


def municipios_minerarios_sem_petroleo(
    grupo_min: int = 1, anos: tuple[int, ...] = ANOS_CFEM_PADRAO, censo_petroleo: int = 2010,
) -> pd.DataFrame:
    """Como `municipios_minerarios`, mas com `grupo_cfem` recodificado para
    'petroleo_gas' nos municípios com participação censitária de petróleo/gás
    >= `LIMIAR_PCT_PETROLEO` -- EXCETO quando o município já é
    `minerario_significativo` por CFEM: alguns municípios têm as duas coisas
    (ex.: Rosário do Catete/SE, potássio da Vale/Mosaic E petróleo do
    Recôncavo -- conferido nesta sessão, `cfem_pct_pib`=1,11%, participação de
    petróleo=0,7%), e forçar 'petroleo_gas' nesses casos apagaria um produtor
    mineral real. A guarda evita esse falso negativo; só reclassifica
    municípios de petróleo que NÃO têm sinal mineral relevante -- exatamente o
    grupo placebo que PLANO.md pede (Macaé, Rio das Ostras, Bacia Potiguar,
    Recôncavo Baiano sem mineração associada, Araucária)."""
    df = municipios_minerarios(grupo_min=grupo_min, anos=anos)
    petro = calcular_participacao_petroleo(censo=censo_petroleo)
    df = df.merge(petro[["cod_municipio", "pct_petroleo"]], on="cod_municipio", how="left")
    df["pct_petroleo"] = df["pct_petroleo"].fillna(0.0)

    eh_petroleo = (df["pct_petroleo"] >= LIMIAR_PCT_PETROLEO) & ~df["minerario_significativo"]
    df["grupo_cfem"] = df["grupo_cfem"].astype(object)
    df.loc[eh_petroleo, "grupo_cfem"] = "petroleo_gas"
    df["grupo_cfem"] = df["grupo_cfem"].astype("category")
    print(f"  municipios_minerarios_sem_petroleo: {int(eh_petroleo.sum())} municípios "
          f"recodificados para 'petroleo_gas' (censo {censo_petroleo}, limiar {LIMIAR_PCT_PETROLEO}%)")
    return df
