"""
Deflator de renda — regra obrigatória do projeto (ver CLAUDE.md, regra 1; plano §3.1).

Nenhum valor monetário é comparado entre os censos em termos nominais. Todo valor é
convertido para R$ de **julho de 2022** (data de referência do Censo 2022) pelo
IPCA (IBGE/SIDRA, tabela 1737, variável 2266 — número-índice, base dez/1993=100),
usando o índice do mês de julho de cada ano censitário — os três censos captam
rendimento com referência a julho.

Uso:
    from lib.deflator import para_reais_jul2022, SALARIO_MINIMO, fator_ipca

    df["renda_r2022"] = para_reais_jul2022(df["renda_nom"], censo=2010)
    df["renda_sm"] = df["renda_nom"] / SALARIO_MINIMO[2010]
"""
import json
from pathlib import Path

import requests

CACHE = Path(__file__).resolve().parent.parent.parent / "data" / "externo" / "ipca_fatores.json"

SIDRA_URL = "https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/2266/p/200007,201007,202207"

# Salário mínimo vigente na semana de referência de cada censo (fonte: decretos/leis
# federais de salário mínimo; mesma convenção usada nos parsers 2022 já existentes
# no projeto irmão, ver atualizacao_2022/scripts/parser_2022_publico.py).
SALARIO_MINIMO = {2000: 151.00, 2010: 510.00, 2022: 1212.00}

# Valores de segurança (índices IPCA de julho de cada ano, base dez/1993=100),
# usados apenas se a API do SIDRA estiver indisponível no momento da execução.
# Conferidos em 2026-08-31 na própria API (ver docstring acima).
_FALLBACK_INDICES = {2000: 1640.62, 2010: 3111.05, 2022: 6411.95}


def _buscar_indices_sidra() -> dict[int, float]:
    r = requests.get(SIDRA_URL, timeout=30)
    r.raise_for_status()
    dados = r.json()[1:]  # primeira linha é o cabeçalho de metadados
    indices = {}
    for row in dados:
        ano = int(row["D3C"][:4])
        indices[ano] = float(row["V"])
    faltando = set(_FALLBACK_INDICES) - set(indices)
    if faltando:
        raise ValueError(f"SIDRA não retornou índice IPCA para {faltando}")
    return indices


def _carregar_indices() -> dict[int, float]:
    if CACHE.exists():
        cached = json.loads(CACHE.read_text())
        return {int(k): v for k, v in cached.items() if k.lstrip("-").isdigit()}
    try:
        indices = _buscar_indices_sidra()
        origem = "sidra"
    except Exception as e:  # rede indisponível, API fora do ar etc.
        print(f"[deflator] aviso: falha ao buscar IPCA no SIDRA ({e}); usando fallback fixo.")
        indices = dict(_FALLBACK_INDICES)
        origem = "fallback"
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps({**indices, "_origem": origem}, indent=1))
    return indices


_INDICES = _carregar_indices()
_BASE_ANO = 2022  # todos os valores monetários do projeto são expressos em R$ de jul/2022


def fator_ipca(censo: int) -> float:
    """Fator multiplicativo para converter R$ nominais de `censo` em R$ de julho/2022."""
    if censo not in _INDICES:
        raise ValueError(f"sem índice IPCA para o censo {censo}")
    return _INDICES[_BASE_ANO] / _INDICES[censo]


def para_reais_jul2022(valor, censo: int):
    """Converte uma série/valor nominal do `censo` para R$ de julho de 2022 (IPCA)."""
    return valor * fator_ipca(censo)


def para_salarios_minimos(valor_nominal, censo: int):
    """Converte um valor nominal do `censo` para múltiplos do salário mínimo da época."""
    return valor_nominal / SALARIO_MINIMO[censo]


if __name__ == "__main__":
    for c in (2000, 2010, 2022):
        f = fator_ipca(c)
        print(f"jul/{c} -> jul/2022: fator = {f:.4f}  (R$100 em {c} = R${100*f:.2f} em 2022)")
