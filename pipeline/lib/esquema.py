"""
Registro declarativo de harmonização entre os três censos (2000, 2010, 2022) —
PLANO_TEMPORAL.md §2. Este módulo é a fonte única do mapeamento CONCEITO ->
coluna por censo; antes dele, `01_parse_2022.py` e os parsers de 2000/2010
cada um definia sua própria seleção de colunas sem registro compartilhado.

Os nomes de coluna aqui referenciados são os que SAEM dos parsers brutos
(`01c_parse_2000.py`, `01d_parse_2010.py`, `01_parse_2022.py` /
`01b_parse_domicilios.py`) -- ainda códigos nativos do IBGE (ou as poucas
colunas já derivadas nos parsers de 2000/2010, como `peso`/`idade`/`mun_atual`
-- ver docstring de cada parser), nunca posições de arquivo. A decodificação
de categorias (que código numérico significa "migrante", "extração mineral"
etc.) continua em `lib/migracao.py` e `lib/cnae.py`, generalizados por censo.

ASSIMETRIAS que não fecham entre os três censos (não escondidas, documentadas
aqui para quem for usar o registro):
  - Última etapa municipal (`mun_resid_ant`) NÃO existe em 2000 -- só UF
    (`V4230`). `PESSOAS["mun_resid_ant"][2000]` é `None`.
  - Tempo de moradia no MUNICÍPIO em 2000 é `V0416` (quesito 4.16 do
    questionário da amostra) -- só aparece depois de `V0415` ("sempre morou
    neste município"), que faz o mesmo papel de `P0530` em 2022: gate da
    bateria inteira de migração. Achado desta sessão (não estava nas
    variáveis "código novo" mais óbvias de `Estrutura Migração V4210,
    V4260.xls`); sem ele, a imputação do salto de pergunta de 2000 replicaria
    o mesmo viés que a inflação de ~45% já documentada em CLAUDE.md para o
    Censo 2022 (P0600 sem a correção de P0530/P0550).
  - Município de nascimento só existe em 2022 (`P0500`). Em 2000/2010 há
    apenas o indicador "nasceu neste município" (`V0417`/`V0618`).
  - Commuting (`mun_trabalho`) de 2000 (`V4276`) mistura trabalho E ESTUDO --
    diferente de 2010/2022, que isolam trabalho. Ver `lib/migracao.py`.
  - `mun_trabalho` codifica só a UF quando o trabalho é no exterior; a
    validação de origem (`_origem_valida`) trata isso à parte.

Uso:
    from lib.esquema import PESSOAS, DOMICILIOS, coluna

    col_peso = coluna(PESSOAS, "peso", 2010)   # "peso"
    col_mun  = coluna(PESSOAS, "municipio", 2022)  # "P0080"
"""

# ---------------------------------------------------------------------------
# Registro de Pessoas
# ---------------------------------------------------------------------------
PESSOAS: dict[str, dict[int, str | None]] = {
    # controle / geografia / peso
    "controle_domicilio": {2000: "V0300", 2010: "V0300", 2022: "P0100"},
    "uf": {2000: "uf_atual", 2010: "uf_atual", 2022: "P0020"},
    "municipio": {2000: "mun_atual", 2010: "mun_atual", 2022: "P0080"},
    "peso": {2000: "peso", 2010: "peso", 2022: "P0111"},
    # demografia
    "sexo": {2000: "V0401", 2010: "V0601", 2022: "P0150"},
    "idade": {2000: "idade", 2010: "idade", 2022: "P0181"},
    "cor_raca": {2000: "V0408", 2010: "V0606", 2022: "P0210"},
    # nascimento
    "nasceu_no_municipio": {2000: "V0417", 2010: "V0618", 2022: "P0480"},
    "uf_nascimento": {2000: "V4210", 2010: "uf_nasc", 2022: "P0490"},
    "municipio_nascimento": {2000: None, 2010: None, 2022: "P0500"},  # só 2022
    # data-fixa (5 anos) -- ver lib/migracao.py p/ decodificação por censo
    "indicador_5anos": {2000: "V0424", 2010: "V0626", 2022: "P0600"},
    "uf_5anos": {2000: "V4260", 2010: "uf_resid_5anos", 2022: "P0610"},
    "municipio_5anos": {2000: "V4250", 2010: "mun_resid_5anos", 2022: "P0620"},
    # última etapa -- SÓ 2010 e 2022 (município); 2000 só tem UF
    "indicador_ultima_etapa": {2000: None, 2010: "V0625", 2022: "P0560"},
    "uf_anterior": {2000: "V4230", 2010: "uf_resid_ant", 2022: "P0570"},
    "municipio_anterior": {2000: None, 2010: "mun_resid_ant", 2022: "P0580"},
    # tempo de moradia
    "tempo_moradia_uf": {2000: "V0422", 2010: None, 2022: None},
    "tempo_moradia_municipio": {2000: "V0416", 2010: "V0624", 2022: "P0550"},
    "sempre_morou_no_municipio": {2000: "V0415", 2010: None, 2022: "P0530"},  # gate do salto de pergunta
    # educação
    "anos_estudo": {2000: "anos_estudo", 2010: None, 2022: "P0790"},
    "nivel_instrucao": {2000: None, 2010: "V6400", 2022: "P0770"},
    # trabalho
    "ocupado": {2000: "V0439", 2010: "V6910", 2022: "P0950"},
    "atividade_cnae": {2000: "V4462", 2010: "V6471", 2022: "P1030"},
    "ocupacao": {2000: "V4452", 2010: "V6461", 2022: "P1040"},
    "posicao_ocupacao": {2000: "V0447", 2010: "V6930", 2022: "P1020"},
    "renda_trabalho_principal": {2000: "V4512", 2010: "V6511", 2022: "P1080"},
    "renda_total": {2000: "V4614", 2010: "V6527", 2022: "P1110"},
    # local de trabalho / commuting -- 2000 mistura trabalho e estudo (V4276)
    "indicador_local_trabalho": {2000: None, 2010: "V0660", 2022: "P1120"},
    "municipio_trabalho": {2000: "V4276", 2010: "mun_trabalho", 2022: "P1140"},
}

# ---------------------------------------------------------------------------
# Registro de Domicílios
# ---------------------------------------------------------------------------
DOMICILIOS: dict[str, dict[int, str | None]] = {
    "controle_domicilio": {2000: "V0300", 2010: "V0300", 2022: "D0100"},
    "uf": {2000: "uf", 2010: "uf", 2022: "D0020"},
    "municipio": {2000: "mun_res", 2010: "mun_res", 2022: "D0080"},
    "peso": {2000: "peso", 2010: "peso", 2022: "D0111"},
    "condicao_ocupacao": {2000: "V0205", 2010: "V0201", 2022: "D0190"},  # 3 alugado, 4 cedido por empregador (os 3 censos)
    "esgotamento_sanitario": {2000: "V0211", 2010: "V0207", 2022: "D0250"},
    "abastecimento_agua": {2000: "V0207", 2010: "V0208", 2022: "D0260"},
    "canalizacao_agua": {2000: "V0208", 2010: "V0209", 2022: "D0290"},
    "destino_lixo": {2000: "V0212", 2010: "V0210", 2022: "D0310"},
    "moradores": {2000: "moradores", 2010: "moradores", 2022: None},  # 2022: contar por D0100
    "densidade_dormitorio": {2000: "densidade_dormitorio", 2010: None, 2022: "D0240"},
    "renda_domiciliar_pc": {2000: None, 2010: "renda_domiciliar_pc", 2022: "D0360"},  # 2000: via familias (V4616_7400)
}


def coluna(mapa: dict[str, dict[int, str | None]], conceito: str, censo: int) -> str:
    """Nome da coluna que representa `conceito` no `censo` pedido. Levanta
    `KeyError` se o conceito não existe no registro e `ValueError` se ele
    existe mas NÃO TEM análogo naquele censo (assimetria documentada na
    docstring do módulo) -- nunca retorna `None` silenciosamente."""
    if conceito not in mapa:
        raise KeyError(f"conceito desconhecido: {conceito!r}")
    col = mapa[conceito][censo]
    if col is None:
        raise ValueError(
            f"'{conceito}' não tem coluna equivalente no Censo {censo} "
            f"(assimetria documentada em lib/esquema.py) — não usar para esse censo."
        )
    return col


def existe(mapa: dict[str, dict[int, str | None]], conceito: str, censo: int) -> bool:
    """True se `conceito` tem coluna equivalente no `censo` pedido."""
    return mapa.get(conceito, {}).get(censo) is not None
