"""
Tipologias migratórias, taxas por unidade geográfica e matriz origem-destino —
nível municipal, habilitado pelo acesso controlado do Censo 2022 (ver PLANO.md)
e generalizado para 2000 e 2010 (PLANO_TEMPORAL.md §2/§4 — harmonização
temporal). Toda função de classificação aceita `censo` (2000, 2010 ou 2022,
default 2022 para não quebrar `02_construir_painel.py`).

PADRÃO DE SALTO DE PERGUNTA -- confirmado nos TRÊS censos nesta sessão, não só
em 2022 (que já estava documentado): a bateria inteira de migração fica em
branco quando a pessoa nunca morou em outro município, e a imputação correta
é sempre "não migrante quando nunca mudou OU tempo de moradia >= 5 anos":
  - 2022: `P0530`='2' (nunca mudou) | `P0550`>=5 (tempo no município atual)
  - 2010: `V0618`='1' ("sim e sempre morou") -- sozinho já garante tempo>=idade;
    `V0624` (tempo no município) ficaTOTALMENTE em branco quando `V0618`='1'
    (conferido em RO: 0/71.025 preenchidos)
  - 2000: `V0415`='1' ("sempre morou neste município", quesito 4.15 do
    questionário da amostra) | `V0416`>=5 (tempo no município, quesito 4.16).
    ACHADO DESTA SESSÃO: `V0415`/`V0416` não estão entre as variáveis "código
    novo" mais óbvias do Censo 2000 -- sem elas, a bateria de migração de 2000
    (`V0417` nasceu aqui, `V4210` UF nascimento, `V0422` tempo na UF, `V4230`
    UF anterior, `V0424` residência em 1995) fica em branco para ~34% da
    amostra (conferido em RO) e pareceria "faltante" sem explicação -- é
    exatamente o mesmo tipo de armadilha do `P0600` de 2022 documentada no
    CLAUDE.md, só que a montante: aqui falta a PRÓPRIA variável de gate, não
    só a lógica de imputação.

Convenções deste projeto (diferentes do `migracoes-br`, que trabalha em UF/AMC):
    - Geografia atual: `P0080` (município, 7 dígitos) / `P0020` (UF, 2 dígitos).
    - Migração data-fixa (5 anos): `P0600` (indicador) / `P0610` (UF) / `P0620`
      (município), residência em 2017.
    - Última etapa: `P0560` (indicador) / `P0570` (UF) / `P0580` (município).
    - Naturalidade: `P0480` (indicador) / `P0490` (UF) / `P0500` (município).
    - Tempo de moradia no município atual: `P0550`; nunca morou em outro
      município: `P0530`='2'.
    - Peso amostral: `P0111`.
Município "sem especificação" vem codificado `9999999` pelo IBGE — tratado como
origem desconhecida, nunca como um município real (ver `_origem_valida`).

PEGADINHA CONFERIDA EMPIRICAMENTE NESTA SESSÃO (RO e MG, mesmo padrão nas duas —
documentar no CLAUDE.md, não repetir): as duas baterias migratórias têm SALTO DE
PERGUNTA (skip pattern) do questionário, não faltante aleatório:
  - `P0600` (residência há 5 anos) fica EM BRANCO sempre que a resposta é óbvia
    pelo tempo de moradia: `P0530`='2' (nunca morou em outro município) ou
    `P0550`>=5 (mudou-se para o município atual há 5 anos ou mais) — nos dois
    casos a pessoa obviamente já morava aqui há 5 anos, e o questionário não
    pergunta de novo. Tratar esse branco como resposta implícita "neste
    município" é ERRADO ignorar; classificar como missing sem tratamento faz o
    universo de referência da taxa de imigração encolher em ~45% da população
    (RO, `P0181`>=5) e enviesar a taxa para cima. `classificar_5anos()` já faz
    essa imputação.
  - `P0560`/`P0570`/`P0580` (moradia anterior) só é preenchida quando
    `P0550` < 10 — confirmado em RO e MG com o MESMO corte exato (preenchido:
    P0550 em [0,9]; em branco: P0550 em [10,98]). Não é dado faltante: é que o
    IBGE não pergunta "onde morava antes" de quem mora no município atual há
    10 anos ou mais. `classificar_ultima_etapa()` por isso só é válida — e só
    deve ser usada — para o subconjunto de residentes com `P0550` < 10; não
    tentar inferir "não migrante" para o restante, porque a pergunta nunca foi
    feita a essas pessoas (ao contrário de `P0600`, aqui não há como inferir a
    partir de outra variável).

Uso:
    from lib.migracao import classificar_5anos, taxas_por_unidade, matriz_od

    df["tipo_mig_5anos"] = classificar_5anos(df)
    taxas = taxas_por_unidade(df, nivel="municipio")
    od = matriz_od(df, nivel="municipio")
"""
import pandas as pd

MUNICIPIO_SEM_ESPECIFICACAO = "9999999"


def _origem_valida(cod: pd.Series) -> pd.Series:
    return cod.notna() & (cod != "") & (cod != MUNICIPIO_SEM_ESPECIFICACAO)


def _classificar_5anos_2022(
    df: pd.DataFrame,
    col_ind: str = "P0600", col_uf_origem: str = "P0610", col_mun_origem: str = "P0620",
    col_uf_atual: str = "P0020", col_mun_atual: str = "P0080",
    col_tempo_moradia: str = "P0550", col_nunca_mudou: str = "P0530",
) -> pd.Series:
    """Tipologia de migração data-fixa (residência em relação a 5 anos atrás):
    'nao_migrante' | 'intraestadual' | 'interestadual' | 'internacional' | NA.

    Prioriza a resposta direta de `P0600`; onde ela está em branco por SALTO DE
    PERGUNTA (ver docstring do módulo — `P0530`='2' ou `P0550`>=5), imputa
    'nao_migrante'. Fica NA apenas para `P0600`='9' (ignorado) e para pessoas
    com menos de 5 anos de idade (pergunta não se aplica)."""
    ind = df[col_ind]
    out = pd.Series(pd.NA, index=df.index, dtype="object")

    out[ind == "1"] = "nao_migrante"
    out[ind == "3"] = "internacional"
    mudou_brasil = ind == "2"
    mesma_uf = mudou_brasil & (df[col_uf_origem] == df[col_uf_atual])
    outra_uf = mudou_brasil & (df[col_uf_origem] != df[col_uf_atual]) & df[col_uf_origem].notna()
    out[mesma_uf] = "intraestadual"
    out[outra_uf] = "interestadual"
    # ind == '9' (ignorado) permanece NA -- não é o mesmo caso do salto de pergunta.

    tempo = pd.to_numeric(df[col_tempo_moradia], errors="coerce")
    implicito_nao_migrante = (df[col_nunca_mudou] == "2") | (tempo >= 5)
    preencher = implicito_nao_migrante & out.isna()
    out[preencher] = "nao_migrante"

    return out.astype("category")


def _classificar_5anos_2010(
    df: pd.DataFrame,
    col_ind: str = "V0626", col_uf_origem: str = "uf_resid_5anos", col_mun_origem: str = "mun_resid_5anos",
    col_uf_atual: str = "uf_atual", col_mun_atual: str = "mun_atual",
    col_tempo_moradia: str = "V0624", col_nunca_mudou: str = "V0618",
) -> pd.Series:
    """Equivalente de `_classificar_5anos_2022` para o Censo 2010. `V0626`
    ("residência em 31/07/2005") tem só duas categorias não-brancas -- 1
    UF/Município, 2 país estrangeiro -- e, diferente de 2022 (`P0600`, que
    tem categoria explícita '1 neste município'), **'1' não significa
    necessariamente "outro município"**: é só o formato da resposta (uma
    localização doméstica), que pode coincidir com o município atual.

    ARMADILHA CONFERIDA NESTA SESSÃO (grande, ~29% dos que eu chamava de
    'intraestadual' antes da correção -- uniforme entre UFs, não um
    problema de uma UF isolada): `V0624` ("tempo de moradia no município")
    é definida pelo IBGE como "anos desde o ÚLTIMO RETORNO, para quem
    migrou e depois retornou" (Descrição das variáveis, p.35) -- não
    "anos desde que mora aqui pela primeira vez". Uma pessoa que morava no
    município em 2005, saiu depois, e voltou antes de 2010 tem `V6264`
    (residência em 2005) == município atual (correto -- ela estava lá) MAS
    `V0624` baixo (conta só desde o retorno mais recente) e `V0626`='1'
    (a resposta é uma localização doméstica -- que aqui coincide com a
    atual). Sem checar `mun_resid_5anos` contra o município atual, essas
    pessoas eram contadas como migrantes intra/interestaduais quando na
    verdade NÃO mudaram de município entre os dois pontos no tempo do
    indicador quinquenal -- são `nao_migrante` para esse fim, mesmo tendo
    uma história residencial interrompida no meio do caminho."""
    ind = df[col_ind]
    out = pd.Series(pd.NA, index=df.index, dtype="object")

    out[ind == "2"] = "internacional"
    mudou_brasil = ind == "1"
    mun_origem = df[col_mun_origem]
    mesmo_municipio = mudou_brasil & (mun_origem == df[col_mun_atual]) & mun_origem.notna()
    mesma_uf = mudou_brasil & ~mesmo_municipio & (df[col_uf_origem] == df[col_uf_atual])
    outra_uf = mudou_brasil & ~mesmo_municipio & (df[col_uf_origem] != df[col_uf_atual]) & df[col_uf_origem].notna()
    out[mesma_uf] = "intraestadual"
    out[outra_uf] = "interestadual"
    out[mesmo_municipio] = "nao_migrante"

    tempo = pd.to_numeric(df[col_tempo_moradia], errors="coerce")
    implicito_nao_migrante = (df[col_nunca_mudou] == "1") | (tempo >= 5)
    preencher = implicito_nao_migrante & out.isna()
    out[preencher] = "nao_migrante"

    return out.astype("category")


def _classificar_5anos_2000(
    df: pd.DataFrame,
    col_ind: str = "V0424", col_uf_origem: str = "V4260", col_mun_origem: str = "V4250",
    col_uf_atual: str = "uf_atual", col_mun_atual: str = "mun_atual",
    col_tempo_moradia: str = "V0416", col_nunca_mudou: str = "V0415",
) -> pd.Series:
    """Equivalente de `_classificar_5anos_2022` para o Censo 2000. `V0424`
    ("onde residia em 31/07/1995") tem 6 categorias: 1,2 neste município
    (urbano/rural) -> não migrante; 3,4 outro município (urbano/rural) ->
    intra/interestadual por `V4260` x UF atual; 5 outro país -> internacional;
    6 "não era nascido" -> NA (pergunta não se aplica, equivalente a
    idade<5 nos outros censos). `V0415`/`V0416` (ver docstring do módulo)
    fazem o papel de `P0530`/`P0550` -- sem eles ~34% da amostra (RO, conferido
    nesta sessão) ficaria sem classificação por causa do salto de pergunta do
    quesito 4.15 do questionário da amostra.

    ARMADILHA CONFERIDA NESTA SESSÃO: `V4260` (e `V4210`/`V4230`) usam um
    esquema de código de UF SEQUENCIAL (01-27, `lib.geo.UF_CODIGO_MIGRACAO_2000`),
    DIFERENTE do código padrão IBGE (11-53) usado em `col_uf_atual`/`uf_atual`
    (de `V0102`). Comparar os dois brutos faz `V4260 == uf_atual` quase nunca
    bater (os intervalos nem se sobrepõem: 01-27 vs 11-53), inflando
    'interestadual' e esvaziando 'intraestadual' quase a zero -- bug já visto
    e corrigido nesta sessão (pct_intraestadual saía < 0,2% em vez de ~65%,
    nível parecido a 2010/2022). Traduzir SEMPRE via
    `lib.geo.UF_CODIGO_MIGRACAO_2000` antes de comparar."""
    from lib.geo import UF_CODIGO_MIGRACAO_2000

    ind = df[col_ind]
    out = pd.Series(pd.NA, index=df.index, dtype="object")

    out[ind.isin(["1", "2"])] = "nao_migrante"
    out[ind == "5"] = "internacional"
    # ind == '6' ("não era nascido") permanece NA -- pergunta não se aplica.
    uf_origem_padrao = df[col_uf_origem].map(UF_CODIGO_MIGRACAO_2000)  # sequencial -> IBGE padrão
    mudou_municipio = ind.isin(["3", "4"])
    mesma_uf = mudou_municipio & (uf_origem_padrao == df[col_uf_atual])
    outra_uf = mudou_municipio & (uf_origem_padrao != df[col_uf_atual]) & uf_origem_padrao.notna()
    out[mesma_uf] = "intraestadual"
    out[outra_uf] = "interestadual"

    tempo = pd.to_numeric(df[col_tempo_moradia], errors="coerce")
    implicito_nao_migrante = (df[col_nunca_mudou] == "1") | (tempo >= 5)
    preencher = implicito_nao_migrante & out.isna()
    out[preencher] = "nao_migrante"

    return out.astype("category")


_IMPL_5ANOS = {2000: _classificar_5anos_2000, 2010: _classificar_5anos_2010, 2022: _classificar_5anos_2022}


def classificar_5anos(df: pd.DataFrame, censo: int = 2022, **kwargs) -> pd.Series:
    """Tipologia de migração data-fixa (residência em relação a 5 anos atrás):
    'nao_migrante' | 'intraestadual' | 'interestadual' | 'internacional' | NA,
    para qualquer um dos três censos (default 2022, mesmo comportamento de
    antes desta generalização -- `02_construir_painel.py` continua chamando
    sem argumentos). Passe `censo=2000` ou `censo=2010` para o painel
    temporal; `**kwargs` sobrescreve nomes de coluna quando necessário (ver
    as três implementações `_classificar_5anos_{2000,2010,2022}` para os
    defaults de cada censo e a docstring do módulo para o padrão de salto de
    pergunta comum aos três)."""
    return _IMPL_5ANOS[censo](df, **kwargs)


def classificar_ultima_etapa(
    df: pd.DataFrame, censo: int = 2022,
    col_ind: str | None = None, col_uf_origem: str | None = None, col_mun_origem: str | None = None,
    col_uf_atual: str | None = None, col_mun_atual: str | None = None,
    col_tempo_moradia: str | None = None,
) -> pd.Series:
    """Tipologia da última mudança de residência -- APENAS para quem mora no
    município atual há menos de 10 anos (tempo de moradia < 10): é o universo
    a que essa bateria é de fato perguntada (ver docstring do módulo). Fora
    desse universo retorna NA -- não interpretar como 'não migrante', a
    pergunta não foi feita. Usar para caracterizar migrantes recentes
    (duração, timing), não para medir taxa de imigração -- essa é
    `classificar_5anos`.

    SÓ EXISTE PARA 2010 E 2022 -- o Censo 2000 não tem município de residência
    anterior (`V4230` é só UF, ver `lib/esquema.py`); chamar com `censo=2000`
    levanta `NotImplementedError`, não retorna uma coluna toda NA em silêncio."""
    if censo == 2000:
        raise NotImplementedError(
            "classificar_ultima_etapa não existe para o Censo 2000 -- município de "
            "residência anterior não está nos microdados (só UF, V4230). Ver lib/esquema.py."
        )
    defaults = {
        2022: dict(col_ind="P0560", col_uf_origem="P0570", col_mun_origem="P0580",
                    col_uf_atual="P0020", col_mun_atual="P0080", col_tempo_moradia="P0550"),
        2010: dict(col_ind="V0625", col_uf_origem="uf_resid_ant", col_mun_origem="mun_resid_ant",
                    col_uf_atual="uf_atual", col_mun_atual="mun_atual", col_tempo_moradia="V0624"),
    }[censo]
    col_ind = col_ind or defaults["col_ind"]
    col_uf_origem = col_uf_origem or defaults["col_uf_origem"]
    col_mun_origem = col_mun_origem or defaults["col_mun_origem"]
    col_uf_atual = col_uf_atual or defaults["col_uf_atual"]
    col_mun_atual = col_mun_atual or defaults["col_mun_atual"]
    col_tempo_moradia = col_tempo_moradia or defaults["col_tempo_moradia"]

    tempo = pd.to_numeric(df[col_tempo_moradia], errors="coerce")
    elegivel = tempo < 10

    ind = df[col_ind]
    out = pd.Series(pd.NA, index=df.index, dtype="object")
    veio_brasil = ind == "1"
    mesma_uf = veio_brasil & (df[col_uf_origem] == df[col_uf_atual])
    outra_uf = veio_brasil & (df[col_uf_origem] != df[col_uf_atual]) & df[col_uf_origem].notna()
    out[mesma_uf] = "intraestadual"
    out[outra_uf] = "interestadual"
    out[ind == "2"] = "internacional"

    out[~elegivel] = pd.NA
    return out.astype("category")


def eh_retorno(df: pd.DataFrame, censo: int = 2022) -> pd.Series:
    """True para quem nasceu no município onde reside hoje mas morava em outro
    município do Brasil há 5 anos -- migração de retorno na janela quinquenal.

    2022: usa a resposta DIRETA de `P0500`==`P0080` e `P0600`='2' (não a
    versão imputada de `classificar_5anos`), porque o retorno precisa da
    confirmação explícita de mudança na janela -- a imputação por `P0550`>=5
    cobriria quem nunca saiu.

    2000/2010 não têm município de nascimento (só o indicador "nasceu neste
    município" -- `V0417`/`V0618`, ver `lib/esquema.py`), mas o teste é
    semanticamente o mesmo: nasceu aqui E a resposta direta de data-fixa
    indica mudança na janela de 5 anos."""
    if censo == 2022:
        nasceu_aqui = _origem_valida(df["P0500"]) & (df["P0500"] == df["P0080"])
        migrou_5anos = df["P0600"] == "2"
    elif censo == 2010:
        nasceu_aqui = df["V0618"].isin(["1", "2"])  # "sim e sempre morou" ou "sim mas morou fora"
        # V0626='1' sozinho NÃO garante "outro município" (ver bug documentado
        # em _classificar_5anos_2010 -- ~29% dos '1' têm mun_resid_5anos ==
        # mun_atual, por causa da definição de V0624 "desde o último retorno").
        migrou_5anos = (df["V0626"] == "1") & (df["mun_resid_5anos"] != df["mun_atual"]) & df["mun_resid_5anos"].notna()
    elif censo == 2000:
        nasceu_aqui = (df["V0415"] == "1") | (df["V0417"] == "1")
        migrou_5anos = df["V0424"].isin(["3", "4"])  # residia em outro município do Brasil em 31/07/1995
    else:
        raise ValueError(f"censo inválido: {censo}")
    return nasceu_aqui & migrou_5anos


def commuting_longa_distancia(df: pd.DataFrame, censo: int = 2022) -> pd.Series:
    """Proxy de deslocamento pendular de longa distância / FIFO-DIDO: pessoa
    ocupada cujo local de trabalho é outro município, diferente do de
    residência. Não é migração -- é o substituto que a discute (ver
    PLANO.md §3.1, Q2).

    ATENÇÃO -- 2000 (`V4276`) mistura trabalho E ESTUDO num único quesito
    ("em que município trabalha OU estuda"); 2010 (`V0660`/`V6604`) e 2022
    (`P1120`/`P1140`) isolam só trabalho. Reportar 2000 com essa ressalva
    explícita, nunca como série estritamente comparável (ver lib/esquema.py)."""
    if censo == 2022:
        outro_municipio = df["P1120"] == "3"
        mun_trab, mun_atual = df["P1140"], df["P0080"]
    elif censo == 2010:
        outro_municipio = df["V0660"] == "3"
        mun_trab, mun_atual = df["mun_trabalho"], df["mun_atual"]
    elif censo == 2000:
        # V4276: sentinelas "0100008" (neste município) e "0200006" (não
        # trabalha nem estuda) -- qualquer outro código de 7 dígitos é
        # município/país onde trabalha OU estuda (ver docstring acima).
        v = df["V4276"].str.strip()
        outro_municipio = _origem_valida(v) & ~v.isin(["0100008", "0200006"])
        mun_trab, mun_atual = v, df["mun_atual"]
    else:
        raise ValueError(f"censo inválido: {censo}")
    mun_dif = _origem_valida(mun_trab) & (mun_trab != mun_atual)
    return outro_municipio & mun_dif


_NIVEL_COLS = {
    2022: {"municipio": "P0080", "uf": "P0020", "rgi": "P0060"},
    2010: {"municipio": "mun_atual", "uf": "uf_atual"},
    2000: {"municipio": "mun_atual", "uf": "uf_atual"},
}


def taxas_por_unidade(
    df: pd.DataFrame, nivel: str = "municipio", censo: int = 2022,
    col_tipo: str = "tipo_mig_5anos", col_peso: str | None = None,
    col_unidade: str | None = None,
) -> pd.DataFrame:
    """Taxa de imigração quinquenal por unidade geográfica (`nivel` em
    {'municipio','uf','rgi'} -- 'rgi' só existe depois do crosswalk município
    -> RGI ser aplicado ao dataframe, ver `02_construir_painel.py`/
    `02b_construir_painel_harmonizado.py`), ponderada por `col_peso` (default
    `P0111` em 2022, `peso` em 2000/2010), com `n_amostral` ao lado de
    `n_expandido` (regra 6 do CLAUDE.md -- nunca uma sem a outra). Linhas com
    `col_tipo` NA (idade<5 ou indicador ignorado) são excluídas do
    denominador, não tratadas como não migrantes. `col_unidade` sobrescreve a
    coluna de agregação quando ela não é nenhuma das de `_NIVEL_COLS` (ex.:
    `amc` no painel temporal harmonizado)."""
    col_peso = col_peso or ("P0111" if censo == 2022 else "peso")
    col_unidade = col_unidade or _NIVEL_COLS[censo][nivel]
    base = df[[col_unidade, col_tipo, col_peso]].dropna(subset=[col_tipo]).copy()
    base["imigrante"] = base[col_tipo].isin(["intraestadual", "interestadual", "internacional"])
    base["pop_expandida_imigrante"] = base["imigrante"] * base[col_peso]

    g = base.groupby(col_unidade, observed=True)
    out = g.agg(
        n_amostral=(col_tipo, "size"),
        n_amostral_imigrante=("imigrante", "sum"),
        pop_expandida=(col_peso, "sum"),
        pop_expandida_imigrante=("pop_expandida_imigrante", "sum"),
    ).reset_index().rename(columns={col_unidade: nivel})
    out["taxa_imigracao_5anos"] = 100 * out["pop_expandida_imigrante"] / out["pop_expandida"]
    return out


_ORIGEM_DESTINO_MAP = {
    2022: {"municipio": ("P0620", "P0080"), "uf": ("P0610", "P0020")},
    2010: {"municipio": ("mun_resid_5anos", "mun_atual"), "uf": ("uf_resid_5anos", "uf_atual")},
    2000: {"municipio": ("V4250", "mun_atual"), "uf": ("V4260", "uf_atual")},
}


def matriz_od(
    df: pd.DataFrame, nivel: str = "municipio", censo: int = 2022,
    col_tipo: str = "tipo_mig_5anos", col_peso: str | None = None,
    col_origem_map: dict | None = None,
) -> pd.DataFrame:
    """Matriz origem-destino em formato longo (`origem`, `destino`, `n_amostral`,
    `fluxo_expandido`) para migração data-fixa (5 anos), no `nivel` pedido.
    `col_origem_map` sobrescreve as colunas de origem/destino padrão -- default
    é a migração quinquenal municipal por censo (`_ORIGEM_DESTINO_MAP`).
    ATENÇÃO: linhas imputadas como 'nao_migrante' por `classificar_5anos`
    (salto de pergunta) não têm origem preenchida e são automaticamente
    excluídas por `_origem_valida`; isso é o esperado -- só entram na matriz
    migrantes com origem informada.

    ARMADILHA (ver `_classificar_5anos_2000`): `nivel='uf'` com `censo=2000`
    usa `V4260`, no esquema de código SEQUENCIAL (01-27), não o padrão IBGE
    (11-53) de `uf_atual` -- traduzido automaticamente aqui via
    `lib.geo.UF_CODIGO_MIGRACAO_2000`, senão a origem nunca bateria com o
    destino."""
    col_peso = col_peso or ("P0111" if censo == 2022 else "peso")
    col_origem, col_destino = (col_origem_map or _ORIGEM_DESTINO_MAP[censo])[nivel]

    fluiu = df[col_tipo].isin(["intraestadual", "interestadual"])
    base = df.loc[fluiu, [col_origem, col_destino, col_peso]].copy()
    if censo == 2000 and nivel == "uf" and col_origem == "V4260":
        from lib.geo import UF_CODIGO_MIGRACAO_2000
        base[col_origem] = base[col_origem].map(UF_CODIGO_MIGRACAO_2000)
    base = base[_origem_valida(base[col_origem])]
    base = base.rename(columns={col_origem: "origem", col_destino: "destino"})

    out = base.groupby(["origem", "destino"]).agg(
        n_amostral=(col_peso, "size"),
        fluxo_expandido=(col_peso, "sum"),
    ).reset_index()
    return out.sort_values("fluxo_expandido", ascending=False)


def matriz_od_top(od: pd.DataFrame, k: int = 50) -> pd.DataFrame:
    """Os `k` maiores corredores origem-destino de uma matriz já construída por
    `matriz_od` -- formato pronto para `lib.viz.fig_fluxos_od`."""
    return od.nlargest(k, "fluxo_expandido").reset_index(drop=True)
