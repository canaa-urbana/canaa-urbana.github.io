"""Cores oficiais das classes de uso e cobertura do solo (decisão do usuário, 10/09/2026):
toda classificação de uso do solo — mapas do painel E7 e figuras do artigo — usa a legenda
MapBiomas (Col. 11) e o estilo `.qml` oficial das Áreas Urbanizadas do IBGE, em exceção à
paleta Ardósia (que segue valendo para interface, gráficos e escalas não classificatórias).

As cores são lidas das fontes versionadas em `web/src/legend/` (baixadas na E3a/E3c), nunca
digitadas. Usado por `27_tiles_camadas.py` (manifesto do painel) e `41_figuras.py` (artigo).
"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path

LEGENDAS = Path(__file__).resolve().parents[2] / "web" / "src" / "legend"

# classes MapBiomas usadas pelo projeto
URBANO = 24       # Área urbanizada
MINERACAO = 30    # Mineração


@lru_cache(maxsize=None)
def _mapbiomas() -> dict[int, str]:
    leg = json.loads((LEGENDAS / "mapbiomas.json").read_text("utf-8"))
    return {int(c["class_id"]): c["hex"] for c in leg["classes"]}


def mapbiomas_hex(classe: int) -> str:
    """Hex oficial de uma classe da legenda MapBiomas Col. 11."""
    return _mapbiomas()[classe]


def ibge_qml(rotulo: str, arquivo: str = "ibge_au_2022_densidade_tipo.qml") -> dict:
    """Preenchimento e contorno do símbolo da regra `rotulo` no .qml oficial da AU 2022
    (None quando o símbolo não tem preenchimento/contorno)."""
    r = ET.parse(LEGENDAS / arquivo).getroot()
    regra = next(x for x in r.iter("rule") if x.get("label") == rotulo)
    sim = next(s for s in r.iter("symbol") if s.get("name") == regra.get("symbol"))

    def cor(chave):
        for o in sim.iter("Option"):
            if o.get("name") == chave and o.get("value"):
                return o.get("value")
        for p in sim.iter("prop"):
            if p.get("k") == chave:
                return p.get("v")
        return None

    def hexa(v):
        if not v:
            return None
        rgba = [int(x) for x in v.split(",")[:4]]
        return None if rgba[3] == 0 else "#{:02x}{:02x}{:02x}".format(*rgba[:3])

    return {"preenchimento": hexa(cor("color")), "contorno": hexa(cor("outline_color"))}


def rampa_urbana(n: int = 5) -> list[str]:
    """Rampa sequencial de vermelhos para escalas da classe urbana no tempo ou em intensidade
    (ano de urbanização, WSF-Evolution, fração construída do GHSL), derivada da cor oficial da
    classe 24 do MapBiomas misturada com preto (tons escuros) e com branco (tons claros). Ordem:
    do mais escuro (mais antigo / mais construído) ao mais claro. A cor do meio é a própria classe 24."""
    base = [int(mapbiomas_hex(URBANO)[i:i + 2], 16) for i in (1, 3, 5)]
    # fração de preto (<0) ou de branco (>0) em cada passo; 0 = a cor oficial
    passos = {5: [-0.5, -0.25, 0.0, 0.4, 0.7], 4: [-0.4, 0.0, 0.35, 0.65], 3: [-0.35, 0.0, 0.5]}[n]
    cores = []
    for f in passos:
        alvo = 0 if f < 0 else 255
        rgb = [round(c + (alvo - c) * abs(f)) for c in base]
        cores.append("#{:02x}{:02x}{:02x}".format(*rgb))
    return cores


def cores_oficiais() -> set[str]:
    """Todos os hex das legendas oficiais (para as checagens de paleta do validate.py)."""
    import re

    s = {h.lower() for h in _mapbiomas().values()}
    for n in (3, 4, 5):
        s |= set(rampa_urbana(n))
    for f in LEGENDAS.glob("*.qml"):
        for r_, g_, b_ in re.findall(r'"(\d+),(\d+),(\d+),\d+', f.read_text("utf-8", errors="ignore")):
            s.add("#{:02x}{:02x}{:02x}".format(int(r_), int(g_), int(b_)))
    return s
