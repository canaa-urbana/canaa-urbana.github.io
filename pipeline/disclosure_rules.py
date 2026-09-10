"""Regras de controle estatístico de revelação (R1-R8) do projeto urban-canaa.

Adaptado em E2 (2026-09-10) do gate herdado de `atlas-migração` (commit 1c05d27) para os
limiares do PLANO.md / CLAUDE.md (regra 4 de sigilo). Estas constantes são a única fonte
de verdade: `13_migracao_perfil.py` as aplica ao publicar e `disclosure_check.py` as
verifica de forma independente (recalcula as contagens amostrais a partir de
`data/interim/microdados/`); `verify_gate.py` confere o carimbo sem microdados.

Regras:
  R1  limiar mínimo por célula publicada — n amostral de pessoas E de domicílios distintos
      (Censo 2022, acesso controlado: 20 pessoas / 10 domicílios; 1991/2000/2010: 10 / 5).
  R2  estimativas ponderadas (contagens) arredondadas a múltiplos de 10 (50 se a célula
      fosse rural — a área rural nunca é publicada diretamente, ver R7).
  R3  contagem amostral só em faixas, nunca exata.
  R4  no máximo 2 dimensões temáticas cruzadas (geografia, censo e universo não contam).
  R5  nenhuma coluna que identifique domicílio ou área de ponderação; nada por área de
      ponderação (Canaã tem uma única área de ponderação em 2000, 2010 e 2022 — o município
      É a área de ponderação, então a regra é redundante mas fica explícita).
  R6  toda estimativa leva CV e classe de precisão (Guia IBGE 2021: boa ≤ 15 %, cautela
      15-30 %, baixa > 30 %).
  R7  diferenciação: município − sede ⇒ rural. Uma célula da sede só é publicada se a célula
      rural implícita também cumprir R1; caso contrário a versão "sede" é suprimida (a
      municipal permanece).
  R8  supressão complementar: categorias suprimidas de uma dimensão nominal são somadas em
      `outros` da mesma dimensão quando `outros` cumpre R1; senão só o total é publicado.
"""

# R1 -- limiar mínimo por célula, por censo
MIN_PESSOAS = {1991: 10, 2000: 10, 2010: 10, 2022: 20}
MIN_DOMICILIOS = {1991: 5, 2000: 5, 2010: 5, 2022: 10}

# R2 -- arredondamento das estimativas ponderadas (contagens)
ARREDONDAMENTO = 10
ARREDONDAMENTO_RURAL = 50

# R3 -- faixas de n divulgadas
FAIXAS_N = [(5, 9, "5-9"), (10, 19, "10-19"), (20, 49, "20-49"), (50, 99, "50-99"),
            (100, 499, "100-499"), (500, None, ">=500")]

# R4 -- cruzamentos
MAX_DIMENSOES_TEMATICAS = 2

# R5 -- colunas jamais publicadas
COLUNAS_PROIBIDAS = {"controle", "ap", "cd_apond", "apond", "areap", "v0011", "v0300",
                     "d0100", "p0100", "d0090", "p0090", "peso"}

# R6 -- classes de precisão (CV em %)
CV_BOA, CV_CAUTELA = 15.0, 30.0

# Geografias publicáveis (a rural nunca aparece: só é derivável por diferença, ver R7)
GEOGRAFIAS = {
    "canaa_sede": ("1502152", "urbana"),
    "canaa_municipio": ("1502152", None),
    "parauapebas_sede": ("1505536", "urbana"),
    "parauapebas_municipio": ("1505536", None),
    "pa": (None, None),
}
PARES_DIFERENCIACAO = [("canaa_sede", "canaa_municipio"), ("parauapebas_sede", "parauapebas_municipio")]

CENSOS = [1991, 2000, 2010, 2022]


def faixa_n(n: int) -> str:
    """R3: converte a contagem amostral na faixa divulgável."""
    for lo, hi, rot in FAIXAS_N:
        if n >= lo and (hi is None or n <= hi):
            return rot
    return "<5"


def arredondar(valor: float, rural: bool = False) -> float:
    base = ARREDONDAMENTO_RURAL if rural else ARREDONDAMENTO
    return round(valor / base) * base


def classe_precisao(cv: float | None) -> str:
    if cv is None or cv != cv:  # None ou NaN
        return "sem_estimativa"
    if cv <= CV_BOA:
        return "boa"
    if cv <= CV_CAUTELA:
        return "cautela"
    return "baixa"


def cumpre_r1(censo: int, n_pessoas: int, n_domicilios: int) -> bool:
    return n_pessoas >= MIN_PESSOAS[censo] and n_domicilios >= MIN_DOMICILIOS[censo]
