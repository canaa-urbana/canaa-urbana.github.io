"""Rótulos em português, ordem das categorias e marcos históricos/minerais
compartilhados por `40_analise_artigo.py`, `41_figuras.py` e, depois, pelo
dashboard (E7). Nada aqui lê dados: são só constantes de apresentação.

As chaves seguem os códigos harmonizados de `lib/censos.py` e `lib/dimensoes.py`.
Categorias fundidas pelo gate (`outros:a+b`) recebem rótulo composto via
`rotulo()` — nunca são renomeadas para esconder a fusão.
"""
from __future__ import annotations

# --- marcos (ano de início, ano de fim, rótulo curto, tipo) ----------------
# Fontes: PLANO.md (Fase 1b, levantamento de 09/09/2026, todas verificadas);
# docs/revisao_bibliografica.md. Anos são civis; fases de construção seguem
# o licenciamento/obra declarados pela Vale e recolhidos na bibliografia.
MARCOS = [
    dict(inicio=1982, fim=1985, rotulo="Assentamento GETAT (CEDERE II)", tipo="fundiario"),
    dict(inicio=1988, fim=1988, rotulo="Parauapebas emancipada de Marabá", tipo="administrativo"),
    dict(inicio=1994, fim=1994, rotulo="Criação do município (Lei 5.860)", tipo="administrativo"),
    dict(inicio=1997, fim=1997, rotulo="Instalação do município", tipo="administrativo"),
    dict(inicio=2002, fim=2004, rotulo="Sossego — construção", tipo="mineral"),
    dict(inicio=2004, fim=2004, rotulo="Sossego — operação (cobre)", tipo="mineral"),
    dict(inicio=2013, fim=2016, rotulo="S11D — construção", tipo="mineral"),
    dict(inicio=2016, fim=2016, rotulo="S11D — operação (ferro, dez/2016)", tipo="mineral"),
]
CENSOS = [1991, 2000, 2010, 2022]
CONTAGENS = [1996, 2007]

# Ciclos usados para alinhar coortes de chegada (mesmos cortes de
# `lib.dimensoes.PERIODOS_CHEGADA`).
CICLOS = {
    "ate_1984": "até 1984 (assentamento)",
    "1985_1994": "1985–1994 (pré-município)",
    "1995_2001": "1995–2001 (instalação)",
    "2002_2004": "2002–2004 (obras do Sossego)",
    "2005_2012": "2005–2012 (operação Sossego)",
    "2013_2016": "2013–2016 (obras do S11D)",
    "2017_2022": "2017–2022 (operação S11D)",
}
# Janelas sombreadas nas figuras de série temporal (construção das minas)
JANELAS_OBRAS = [(2002, 2004, "Sossego"), (2013, 2016, "S11D")]

# --- geografias --------------------------------------------------------------
GEOGRAFIAS = {
    "canaa_sede": "Canaã dos Carajás — sede",
    "canaa_municipio": "Canaã dos Carajás — município",
    "parauapebas_sede": "Parauapebas — sede",
    "parauapebas_municipio": "Parauapebas — município",
    "pa": "Pará",
}
GEOGRAFIAS_CURTAS = {
    "canaa_sede": "Canaã (sede)", "canaa_municipio": "Canaã", "parauapebas_sede": "Parauapebas (sede)",
    "parauapebas_municipio": "Parauapebas", "pa": "Pará",
}

# --- dimensões e categorias --------------------------------------------------
DIMENSOES = {
    "sexo": "Sexo", "faixa_etaria": "Faixa etária", "grupo_etario": "Grupo etário", "cor_raca": "Cor ou raça",
    "nivel_instrucao": "Nível de instrução (25 anos ou mais)", "ocupado": "Ocupação (10 anos ou mais)",
    "posicao": "Posição na ocupação", "formal": "Vínculo formal", "setor": "Setor de atividade",
    "extrativa_mineral": "Extrativa mineral", "renda_sm_faixa": "Renda em salários mínimos",
    "tipo_mig_5anos": "Status migratório de data fixa", "migrante": "Migrante de data fixa (5 anos)",
    "origem_regiao": "Região de origem", "origem_uf": "UF de origem", "origem_mun": "Município de origem",
    "naturalidade": "Naturalidade", "tempo_moradia_faixa": "Tempo de moradia no município",
    "periodo_chegada": "Período de chegada", "ano_chegada": "Ano de chegada", "retorno": "Migrante de retorno",
    "trabalha_outro_mun": "Trabalha em outro município", "tem_migrante_recente": "Domicílio com migrante recente",
    "tipo_domicilio": "Tipo de domicílio", "condicao_ocupacao": "Condição de ocupação", "agua_rede": "Água da rede geral",
    "esgoto_adequado": "Esgoto adequado (rede ou fossa séptica)", "lixo_coletado": "Lixo coletado",
    "energia": "Energia elétrica", "internet": "Acesso à internet", "adequacao": "Adequação do domicílio",
    "densidade_faixa": "Moradores por dormitório", "renda_dom_pc_faixa": "Renda domiciliar per capita (SM)",
}

CATEGORIAS = {
    "M": "Homens", "F": "Mulheres", "sim": "Sim", "nao": "Não",
    "migrante": "Migrantes", "nao_migrante": "Não migrantes",
    "intraestadual": "Intraestadual", "interestadual": "Interestadual", "internacional": "Internacional",
    "branca": "Branca", "preta": "Preta", "parda": "Parda", "amarela": "Amarela", "indigena": "Indígena",
    "ignorado": "Ignorada",
    "sem_instrucao_fund_incompleto": "Sem instrução / fund. incompleto",
    "fund_completo_medio_incompleto": "Fundamental completo / médio incompleto",
    "medio_completo_sup_incompleto": "Médio completo / superior incompleto",
    "superior_completo": "Superior completo", "nao_determinado": "Não determinado",
    "empregado_com_carteira": "Empregado com carteira", "empregado_sem_carteira": "Empregado sem carteira",
    "militar_estatutario": "Militar / estatutário", "conta_propria": "Conta própria", "empregador": "Empregador",
    "nao_remunerado": "Não remunerado",
    "agropecuaria": "Agropecuária", "extrativa_mineral": "Extrativa mineral", "transformacao": "Ind. de transformação",
    "construcao": "Construção", "comercio": "Comércio", "servicos": "Serviços",
    "adm_publica_educacao_saude": "Adm. pública, educação e saúde", "domestico": "Serviços domésticos",
    "outras_atividades": "Outras atividades",
    "sem_rendimento": "Sem rendimento", "ate_1_2": "Até ½ SM", "1_2_a_1": "½ a 1 SM", "1_a_2": "1 a 2 SM",
    "2_a_3": "2 a 3 SM", "3_a_5": "3 a 5 SM", "5_a_10": "5 a 10 SM", "mais_de_10": "Mais de 10 SM",
    "mesma_uf": "Mesma UF (Pará)", "Norte": "Norte (outras UFs)", "Nordeste": "Nordeste", "Sudeste": "Sudeste",
    "Sul": "Sul", "Centro-Oeste": "Centro-Oeste", "exterior": "Exterior",
    "municipio": "No município", "outra_uf": "Outra UF",
    "menos_1": "Menos de 1 ano", "1_a_4": "1 a 4 anos", "5_a_9": "5 a 9 anos", "10_a_19": "10 a 19 anos",
    "20_mais": "20 anos ou mais",
    "casa": "Casa", "apartamento": "Apartamento", "comodo": "Cômodo", "outro": "Outro",
    "proprio": "Próprio", "alugado": "Alugado", "cedido_empregador": "Cedido pelo empregador",
    "cedido_outro": "Cedido (outro)", "outra": "Outra condição",
    "adequada": "Adequada", "semi_adequada": "Semiadequada", "inadequada": "Inadequada",
    "ate_1": "Até 1", "mais_de_3": "Mais de 3",
    "00_14": "0–14", "15_24": "15–24", "25_39": "25–39", "40_59": "40–59", "60_mais": "60+",
    "80_mais": "80+",
}
CATEGORIAS.update({k: v for k, v in CICLOS.items()})

UFS = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO", "21": "MA", "22": "PI",
    "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE", "29": "BA", "31": "MG", "32": "ES",
    "33": "RJ", "35": "SP", "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}

SETORES_ORDEM = ["agropecuaria", "extrativa_mineral", "transformacao", "construcao", "comercio", "servicos",
                 "adm_publica_educacao_saude", "domestico", "outras_atividades"]


def rotulo(cat: str, dim: str | None = None) -> str:
    """Rótulo em português de uma categoria; fusões `outros:a+b` viram
    'Outros (a, b)' com os constituintes visíveis; faixas etárias `00_04` viram '0–4'."""
    if cat is None:
        return ""
    cat = str(cat)
    if cat.startswith("outros:"):
        partes = cat.split(":", 1)[1].split("+")
        return "Outros (" + ", ".join(rotulo(p, dim) for p in partes) + ")"
    if dim == "origem_uf" and cat in UFS:
        return UFS[cat]
    if dim == "faixa_etaria" and "_" in cat and cat[0].isdigit():
        a, b = cat.split("_")
        return f"{int(a)}–{int(b)}" if b.isdigit() else f"{int(a)}+"
    if dim == "densidade_faixa":
        return {"ate_1": "Até 1", "1_a_2": "1 a 2", "2_a_3": "2 a 3", "mais_de_3": "Mais de 3"}.get(cat, cat)
    return CATEGORIAS.get(cat, cat)


def fmt_num(v, casas: int = 0) -> str:
    """Formato brasileiro: milhar com ponto, decimal com vírgula."""
    if v is None or (isinstance(v, float) and v != v):
        return "—"
    s = f"{v:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(v, casas: int = 1) -> str:
    return "—" if v is None or v != v else fmt_num(v, casas) + " %"


def classe_marca(classe: str) -> str:
    """Marca de precisão para tabelas: boa = '', cautela = '*', baixa = '**'."""
    return {"boa": "", "cautela": "*", "baixa": "**"}.get(classe, "")
