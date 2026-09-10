"""
E7 / Fase 6 (PLANO.md) — dados do dashboard em `web/public/data/painel/`.

Converte para JSON leve o que o dashboard lê além das camadas da E3c:

  estimativas.json        tabela longa da E2 (`microdados/estimativas.parquet`), em colunas com
                          dicionário de categorias; só agregados aprovados pelo gate (R1–R8)
  analise/<nome>.json     as 24 tabelas analíticas da E5 (`data/processed/analise/*.parquet`)
  resumo_analise.json     números-síntese da E5
  geo/<nome>.json         comparação com produtos (MapBiomas, GHSL, WSF, IBGE AU), períodos e
                          direção da expansão (E3a/E3c)
  rotulos.json            rótulos, ordens, marcos e ciclos de `pipeline/lib/rotulos.py`
  setores_{2010,2022}.json  setores do Universo (IBGE) com indicadores escolhidos e a pertença
                          sede/outros/rural da E3c — GeoJSON 4326 enxuto para o coroplético
  indicadores_setores.json  metadados dos indicadores (rótulo, unidade, escala, anos)
  referencias.json        bibliografia verificada da E4 (campos de exibição) + metodológicas
  figuras.json            títulos, legendas e resumos das figuras do artigo (E5)
  artigo.json             título, resumo/abstract, sumário, limitações e declaração de IA (E6)
  _manifesto.json         arquivo → SHA-256 e a versão do gate que aprovou a origem

e copia `artigo/artigo.pdf` para `web/public/artigo/artigo.pdf`.

Regra de sigilo (CLAUDE.md, item 3): só `data/processed` aprovado pelo gate vai para
`web/public/data`. O script roda `verify_gate.py` antes de escrever qualquer arquivo e
recusa se o carimbo não conferir. Nenhum microdado é lido aqui.

Uso:
    .venv/bin/python pipeline/60_dados_web.py
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import rotulos as R  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
PROC = BASE / "data" / "processed"
WEB = BASE / "web" / "public"
DEST = WEB / "data" / "painel"
DEST_AN = DEST / "analise"
ARTIGO = BASE / "artigo"


# ----------------------------------------------------------------------------
# utilidades
# ----------------------------------------------------------------------------

def _limpo(v):
    """Valor serializável: NaN/NA → None, numpy → nativo, floats com 4 casas significativas úteis."""
    if v is None or v is pd.NA or v is pd.NaT:
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        if math.isnan(v) or math.isinf(v):
            return None
        f = float(v)
        return int(f) if f.is_integer() and abs(f) < 1e15 else round(f, 4)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    if isinstance(v, (list, tuple, np.ndarray)):
        return [_limpo(x) for x in v]
    return v


def _registros(df: pd.DataFrame) -> list[dict]:
    return [{k: _limpo(v) for k, v in r.items()} for r in df.to_dict(orient="records")]


def _gravar(obj, destino: Path) -> int:
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), "utf-8")
    return destino.stat().st_size


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def verificar_gate() -> str:
    r = subprocess.run([sys.executable, str(BASE / "pipeline" / "verify_gate.py")],
                       capture_output=True, text=True)
    if r.returncode != 0 or "VERIFICAÇÃO APROVADA" not in r.stdout:
        print(r.stdout[-2000:], r.stderr[-2000:])
        raise SystemExit("verify_gate.py reprovou: rode disclosure_check.py antes de exportar para a web")
    carimbo = json.loads((PROC / ".gate_ok").read_text("utf-8"))
    return carimbo["versao_dados"]


# ----------------------------------------------------------------------------
# estimativas (E2) em colunas
# ----------------------------------------------------------------------------

def estimativas() -> int:
    e = pd.read_parquet(PROC / "microdados" / "estimativas.parquet")
    colunas_cat = ["censo", "geografia", "universo", "estatistica", "variavel", "dim1", "cat1", "dim2", "cat2",
                   "classe_precisao", "n_faixa", "n_dom_faixa"]
    saida = {"fonte": "IBGE, microdados da amostra 1991/2000/2010/2022 — estimativas agregadas aprovadas "
                      "pelo gate de revelação (R1–R8); EP por bootstrap de domicílios (200 réplicas)",
             "n": len(e), "dic": {}, "col": {}}
    for c in colunas_cat:
        s = e[c].astype("string").fillna("")
        cats = sorted(s.unique().tolist(), key=lambda x: (x == "", x))
        idx = {k: i for i, k in enumerate(cats)}
        saida["dic"][c] = cats
        saida["col"][c] = [idx[x] for x in s.tolist()]
    for c in ("valor", "ep", "cv"):
        saida["col"][c] = [_limpo(v) for v in e[c].tolist()]
    return _gravar(saida, DEST / "estimativas.json")


# ----------------------------------------------------------------------------
# análise (E5)
# ----------------------------------------------------------------------------

def analise() -> dict[str, int]:
    tam = {}
    for p in sorted((PROC / "analise").glob("*.parquet")):
        df = pd.read_parquet(p)
        tam[p.stem] = _gravar(_registros(df), DEST_AN / f"{p.stem}.json")
    for extra in ("resumo_analise.json",):
        shutil.copyfile(PROC / "analise" / extra, DEST / extra)
        tam[extra] = (DEST / extra).stat().st_size
    return tam


def geo_tabelas() -> dict[str, int]:
    """Tabelas de sensoriamento remoto (E3a/E3c) que os gráficos da aba Mancha usam."""
    tam = {}
    for nome in ("comparacao_produtos", "estatisticas_mancha_periodos", "expansao_direcao"):
        df = pd.read_parquet(PROC / "geo" / f"{nome}.parquet")
        tam[nome] = _gravar(_registros(df), DEST / "geo" / f"{nome}.json")
    return tam


def rotulos() -> int:
    return _gravar({
        "marcos": R.MARCOS, "censos": R.CENSOS, "contagens": R.CONTAGENS, "ciclos": R.CICLOS,
        "janelas_obras": [list(j) for j in R.JANELAS_OBRAS], "geografias": R.GEOGRAFIAS,
        "geografias_curtas": R.GEOGRAFIAS_CURTAS, "dimensoes": R.DIMENSOES, "categorias": R.CATEGORIAS,
        "ufs": R.UFS, "setores_ordem": R.SETORES_ORDEM,
    }, DEST / "rotulos.json")


# ----------------------------------------------------------------------------
# setores do Universo (E1) × pertença da mancha (E3c)
# ----------------------------------------------------------------------------

INDICADORES = [
    # id, rótulo, unidade, escala, casas, anos
    ("pop", "População residente", "hab.", "seq", 0, [2010, 2022]),
    ("dom", "Domicílios particulares ocupados", "dom.", "seq", 0, [2010, 2022]),
    ("densidade_liquida", "Densidade líquida (sobre a área construída)", "hab./ha", "seq", 1, [2010, 2022]),
    ("moradores_dom", "Moradores por domicílio", "mor./dom.", "seq", 2, [2010, 2022]),
    ("agua_pct", "Água da rede geral", "% dos domicílios", "seq", 1, [2010, 2022]),
    ("esgoto_pct", "Esgoto por rede geral ou pluvial", "% dos domicílios", "seq", 1, [2010, 2022]),
    ("lixo_pct", "Lixo coletado", "% dos domicílios", "seq", 1, [2010, 2022]),
    ("energia_pct", "Energia elétrica", "% dos domicílios", "seq", 1, [2010]),
    ("renda_resp", "Rendimento médio do responsável (nominal)", "R$", "seq", 0, [2010]),
    ("pretos_pardos_pct", "Pretos e pardos", "% da população", "seq", 1, [2022]),
    ("razao_sexo", "Razão de sexo", "homens por 100 mulheres", "seq", 1, [2022]),
    ("frac_construida", "Fração construída do setor", "%", "seq", 1, [2010, 2022]),
    ("ano_urbanizacao", "Ano mediano de urbanização", "ano", "seq", 0, [2010, 2022]),
    ("dist_nucleo_km", "Distância ao núcleo histórico", "km", "seq", 2, [2010, 2022]),
]


def _ind_setor(ano: int) -> pd.DataFrame:
    d = pd.read_parquet(PROC / "setores" / f"setores_{ano}_indicadores.parquet")
    o = pd.DataFrame({"cod_setor": d["cod_setor"].astype(str)})
    o["pop"] = d["populacao_residente"]
    if ano == 2010:
        o["dom"] = d["domicilios_particulares_permanentes"]
        o["lixo_pct"] = d["lixo_coletado_pct"]
        o["energia_pct"] = d["com_energia_eletrica_pct"]
        o["renda_resp"] = d["rendimento_medio_responsavel_com_sem_r"]
        o["situacao"] = np.where(d["Situacao_setor"].isin([1, 2, 3]), "urbana", "rural")
    else:
        o["dom"] = d["domicilios_particulares_ocupados"]
        o["lixo_pct"] = d["lixo_pct"]
        cor = d[["cor_branca", "cor_preta", "cor_amarela", "cor_parda", "cor_indigena"]].fillna(0).sum(axis=1)
        o["pretos_pardos_pct"] = np.where(cor > 0, 100 * (d["cor_preta"].fillna(0) + d["cor_parda"].fillna(0)) / cor,
                                          np.nan)
        o["razao_sexo"] = np.where(d["sexo_feminino"] > 0, 100 * d["sexo_masculino"] / d["sexo_feminino"], np.nan)
        o["situacao"] = np.where(d["CD_SIT"].astype(str).isin(["1", "2", "3"]), "urbana", "rural")
    o["moradores_dom"] = d["media_moradores_domicilio"]
    o["agua_pct"] = d["agua_pct"]
    o["esgoto_pct"] = d["esgoto_pct"]
    # setores sem domicílio ocupado não têm indicador de domicílio
    for c in ("agua_pct", "esgoto_pct", "lixo_pct", "energia_pct", "moradores_dom", "renda_resp"):
        if c in o:
            o.loc[o["dom"].fillna(0) <= 0, c] = np.nan

    m = pd.read_parquet(PROC / "setores" / "setores_mancha.parquet")
    m = m[m["ano"] == ano].assign(cod_setor=lambda x: x["cod_setor"].astype(str))
    o = o.merge(m[["cod_setor", "pertence", "frac_construida", "densidade_liquida_hab_ha"]], on="cod_setor",
                how="left").rename(columns={"densidade_liquida_hab_ha": "densidade_liquida"})
    o["frac_construida"] = 100 * o["frac_construida"]
    s = pd.read_parquet(PROC / "analise" / "setores_sede_indicadores.parquet")
    s = s[s["ano"] == ano].assign(cod_setor=lambda x: x["cod_setor"].astype(str))
    o = o.merge(s[["cod_setor", "dist_nucleo_km", "ano_urbanizacao_mediano"]], on="cod_setor", how="left") \
         .rename(columns={"ano_urbanizacao_mediano": "ano_urbanizacao"})
    return o


def setores() -> dict[str, int]:
    tam = {}
    for ano in (2010, 2022):
        geo = json.loads((WEB / "data" / "geo" / f"setores_{ano}.json").read_text("utf-8"))
        ind = _ind_setor(ano).set_index("cod_setor")
        feats = []
        for f in geo["features"]:
            cod = str(f["properties"]["cod_setor"])
            props = {"cod_setor": cod, "ano": ano}
            if cod in ind.index:
                props.update({k: _limpo(v) for k, v in ind.loc[cod].items()})
            feats.append({"type": "Feature", "properties": props, "geometry": f["geometry"]})
        tam[f"setores_{ano}"] = _gravar({"type": "FeatureCollection", "features": feats},
                                        DEST / f"setores_{ano}.json")
    meta = [{"id": i, "rotulo": r, "unidade": u, "escala": e, "casas": c, "anos": a} for i, r, u, e, c, a in INDICADORES]
    tam["indicadores_setores"] = _gravar({
        "fonte": "IBGE, Censos 2010 e 2022, agregados por setor censitário (Universo); pertença sede/outros/rural, "
                 "fração construída e densidade líquida da classificação própria (E3c); distância e ano de "
                 "urbanização da E5",
        "notas": ["Setores 2010 e 2022 têm malhas diferentes: compare padrões, não setor a setor.",
                  "Densidade líquida = população / área construída mapeada dentro do setor.",
                  "Rendimento do responsável só existe no Universo de 2010; cor/raça e sexo por setor só em 2022 "
                  "neste recorte."],
        "indicadores": meta}, DEST / "indicadores_setores.json")
    return tam


# ----------------------------------------------------------------------------
# bibliografia e figuras
# ----------------------------------------------------------------------------

def referencias() -> int:
    campos = ("slug", "tipo", "autores", "ano", "titulo", "veiculo", "doi", "url", "camada", "eixos", "periodo",
              "metodo", "achados", "abnt", "verificado_em")
    refs = json.loads((ARTIGO / "bibliografia" / "referencias.json").read_text("utf-8"))["referencias"]
    met = ARTIGO / "bibliografia" / "referencias_metodologicas.json"
    if met.exists():
        m = json.loads(met.read_text("utf-8"))
        refs += (m["referencias"] if isinstance(m, dict) else m)
    citadas = set()
    cp = ARTIGO / "citadas.json"
    if cp.exists():
        c = json.loads(cp.read_text("utf-8"))
        citadas = set(c if isinstance(c, list) else c.get("citadas", c.keys()))
    saida = []
    for r in refs:
        e = {k: r.get(k) for k in campos if r.get(k) not in (None, "", [])}
        e["citada_no_artigo"] = r.get("slug") in citadas
        saida.append(e)
    saida.sort(key=lambda r: (str(r.get("autores", [""])[0]).lower() if r.get("autores") else "", r.get("ano") or 0))
    return _gravar({"fonte": "artigo/bibliografia/referencias*.json (E4/E6), todas verificadas", "referencias": saida},
                   DEST / "referencias.json")


def figuras() -> int:
    figs = json.loads((ARTIGO / "figuras" / "figuras.json").read_text("utf-8"))
    return _gravar(figs, DEST / "figuras.json")


def artigo_meta() -> int:
    """Título, resumo/abstract, palavras-chave, sumário, limitações e declaração de IA do artigo
    (lidos de `texto_resolvido.md`, com as citações já resolvidas pela E6)."""
    import re

    txt = (ARTIGO / "texto_resolvido.md").read_text("utf-8")
    linhas = txt.splitlines()
    titulo = linhas[0].lstrip("# ").strip()
    secoes, atual, corpo = [], None, {}
    for ln in linhas[1:]:
        m = re.match(r"^(#{2,3})\s+(.*)$", ln)
        if m:
            atual = m.group(2).strip()
            secoes.append({"nivel": len(m.group(1)), "titulo": atual})
            corpo[atual] = []
        elif atual:
            corpo[atual].append(ln)

    def paragrafos(nome: str) -> list[str]:
        bloco = "\n".join(corpo.get(nome, [])).strip()
        ps = [re.sub(r"\s+", " ", p).strip() for p in bloco.split("\n\n")]
        return [p for p in ps if p and not p.startswith("<!--")]

    def chaves(pars: list[str], rotulo: str) -> tuple[list[str], list[str]]:
        kw, resto = [], []
        for p in pars:
            if p.startswith(f"**{rotulo}"):
                kw = [k.strip(" .") for k in p.split(":**", 1)[-1].split(";")]
            else:
                resto.append(p)
        return resto, kw

    resumo, pc = chaves(paragrafos("Resumo"), "Palavras-chave")
    abstract, kw = chaves(paragrafos("Abstract"), "Keywords")
    versao = next((ln.strip() for ln in linhas[:8] if ln.startswith("Versão")), "")
    return _gravar({
        "titulo": titulo, "autor": "Daniel Pessini Sobreira", "versao": versao,
        "resumo": resumo, "palavras_chave": pc, "abstract": abstract, "keywords": kw,
        "secoes": [s for s in secoes if s["titulo"] not in ("Resumo", "Abstract")],
        "limitacoes": paragrafos("4.6 Limitações"),
        "declaracao_ia": paragrafos("Declaração de uso de inteligência artificial"),
        "pdf": "artigo/artigo.pdf", "paginas": None,
    }, DEST / "artigo.json")


def artigo_pdf() -> int:
    dest = WEB / "artigo" / "artigo.pdf"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ARTIGO / "artigo.pdf", dest)
    return dest.stat().st_size


# ----------------------------------------------------------------------------

def main() -> None:
    versao = verificar_gate()
    print(f"gate aprovado (versão {versao})")
    tam = {"estimativas": estimativas()}
    tam.update(analise())
    tam.update(geo_tabelas())
    tam["rotulos"] = rotulos()
    tam.update(setores())
    tam["referencias"] = referencias()
    tam["figuras"] = figuras()
    tam["artigo_pdf"] = artigo_pdf()
    tam["artigo_meta"] = artigo_meta()
    arquivos = {p.relative_to(WEB).as_posix(): _sha(p) for p in sorted(DEST.rglob("*.json"))
                if p.name != "_manifesto.json"}
    arquivos["artigo/artigo.pdf"] = _sha(WEB / "artigo" / "artigo.pdf")
    _gravar({"versao_gate": versao, "gerado_por": "pipeline/60_dados_web.py", "arquivos": arquivos},
            DEST / "_manifesto.json")
    total = sum(tam.values())
    print(f"{len(tam)} saídas, {total / 1e6:.2f} MB; maiores: " +
          ", ".join(f"{k} {v / 1e3:.0f} KB" for k, v in sorted(tam.items(), key=lambda x: -x[1])[:5]))


if __name__ == "__main__":
    main()
