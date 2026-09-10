"""
E4 / Fase 4 passo 1 (PLANO.md) — levantamento bibliográfico em APIs abertas.

Consulta OpenAlex, Crossref, Semantic Scholar, BDTD/IBICT (VuFind) e o Catálogo
de Teses e Dissertações da CAPES com os termos do núcleo ("Canaã dos Carajás" e
variantes) e de contexto (S11D, Sossego, Parauapebas/Carajás + urbanização,
company towns amazônicos) em menor profundidade. SciELO fica de fora da busca
automática: `search.scielo.org` responde com desafio anti-bot (não contornar);
os artigos SciELO têm DOI e chegam por OpenAlex/Crossref.

Saídas (dados bibliográficos públicos — não passam pelo gate de microdados):
    data/interim/bibliografia/raw/<fonte>_<termo>.json   respostas brutas
    data/processed/bibliografia/candidatos.parquet       registros deduplicados
    data/processed/bibliografia/log_buscas.parquet       fonte × termo × n
    data/processed/bibliografia/triagem.txt              lista compacta p/ triagem

Cada candidato recebe `area_auto` (geociencias / outra) por palavras-chave e
tópico OpenAlex — a triagem temática fina e a verificação são feitas em
`31_verificar_refs.py` a partir de `artigo/bibliografia/triagem.json`.

Uso:
    .venv/bin/python pipeline/30_bibliografia.py            # busca (usa cache)
    .venv/bin/python pipeline/30_bibliografia.py --refresh  # ignora o cache
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
import unicodedata
from datetime import date
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/interim/bibliografia/raw"
OUT = ROOT / "data/processed/bibliografia"
MAILTO = "urban-canaa@example.org"  # polite pool OpenAlex/Crossref (sem dado pessoal)
UA = {"User-Agent": f"urban-canaa-bibliografia/0.1 (mailto:{MAILTO})"}
HOJE = date.today().isoformat()

# (termo, camada, limite de registros por fonte)
TERMOS_NUCLEO = [
    '"Canaã dos Carajás"',
    '"Canaa dos Carajas"',
    '"Canaã do Carajás"',
]
TERMOS_CONTEXTO = [
    'S11D',
    '"Sossego" mine Carajás',
    '"mina do Sossego"',
    'Parauapebas urbanização',
    'Parauapebas cidade mineração',
    'Carajás urbanização',
    '"Programa Grande Carajás" cidades',
    '"company town" Amazônia mineração',
    'Carajás mining urbanization',
    'GETAT colonização Carajás',
]

# Geociências: estudo da província mineral, não do município (excluídos da revisão,
# contados no relatório). Palavras-chave em título/assunto, sem acento, minúsculas.
GEO_PAT = re.compile(
    r"petrolog|petrogra|granit|granodior|tonalit|trondhjem|charnock|geoquim|geocronolog|"
    r"magmat|arquean|archean|neoarch|mesoarch|paleoprot|zircon|u-pb|sm-nd|lu-hf|"
    r"hidroterm|hydrotherm|iocg|iron oxide|oxido de ferro|cobre-ouro|copper-gold|cu-au|"
    r"mineraliz|mineralis|depositos? |deposit\b|deposits\b|jazida|metalogen|ore\b|"
    r"greenstone|craton|cratao|supracrust|gnaiss|gneiss|migmat|metamorf|metamorph|"
    r"estrutural|structural geology|geofis|geophys|gravimet|magnetometr|aerogeof|"
    r"litoestrat|lithostrat|sedimentolog|estratigraf|stratigraph|mafic|ultramaf|"
    r"komatiit|basalt|sulfet|sulfide|calcopirit|chalcopyrite|magnetit|isotop|"
    r"fluid inclus|inclusoes fluidas|alteracao hidrot|serra dourada|sequeirinho|"
    r"cristalino deposit|bacia carajas|carajas basin|terreno|terrane|faixa|belt\b"
)
GEO_TOPIC = {"Earth and Planetary Sciences"}


# --- utilitários -------------------------------------------------------------

RE_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def sem_dados_pessoais(df: pd.DataFrame) -> pd.DataFrame:
    """Remove e-mails de terceiros dos textos (resumos de repositórios trazem "Submitted by
    Fulano (email) on ..."): o repositório é público e não publica dados pessoais (E8)."""
    df = df.copy()
    for c in df.columns:
        if pd.api.types.is_string_dtype(df[c]) or df[c].dtype == object:
            df[c] = df[c].map(lambda v: RE_EMAIL.sub("[e-mail removido]", v) if isinstance(v, str) else v)
    return df


def norm(s: str | None) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]+", " ", s.lower()).strip()


def titulo_chave(t: str) -> str:
    return re.sub(r"\s+", " ", norm(t))[:120]


def cache_path(fonte: str, termo: str, pagina: int) -> Path:
    h = hashlib.sha1(termo.encode()).hexdigest()[:10]
    return RAW / f"{fonte}_{h}_p{pagina}.json"


def get_json(fonte, termo, pagina, fn, refresh, pausa=0.2, tentativas=6):
    p = cache_path(fonte, termo, pagina)
    if p.exists() and not refresh:
        return json.loads(p.read_text())
    for tentativa in range(tentativas):
        try:
            r = fn()
        except requests.RequestException as e:  # rede
            print(f"  {fonte} erro de rede ({e.__class__.__name__}); tentativa {tentativa + 1}")
            time.sleep(3 * (tentativa + 1))
            continue
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(min(60, 5 * 2 ** tentativa))
            continue
        r.raise_for_status()
        d = r.json()
        p.write_text(json.dumps(d, ensure_ascii=False))
        time.sleep(pausa)
        return d
    print(f"  {fonte}: desistiu de '{termo}' p{pagina} (limite de requisições)")
    return None


def abstract_openalex(inv: dict | None) -> str:
    if not inv:
        return ""
    pos = sorted((i, w) for w, idx in inv.items() for i in idx)
    return " ".join(w for _, w in pos)


# --- fontes ------------------------------------------------------------------

def openalex(termo, limite, refresh):
    recs, cursor, pagina = [], "*", 0
    campo = "title_and_abstract.search"
    while cursor and len(recs) < limite:
        pagina += 1
        d = get_json("openalex", termo, pagina, lambda: requests.get(
            "https://api.openalex.org/works", headers=UA, timeout=60, params={
                "filter": f"{campo}:{termo}", "per-page": 200, "cursor": cursor,
                "mailto": MAILTO}), refresh)
        if not d:
            break
        for w in d["results"]:
            loc = w.get("primary_location") or {}
            src = loc.get("source") or {}
            pt = w.get("primary_topic") or {}
            recs.append(dict(
                fonte="openalex", id_fonte=w["id"], titulo=w.get("display_name") or "",
                autores=[a["author"]["display_name"] for a in w.get("authorships", [])],
                ano=w.get("publication_year"), tipo_fonte=w.get("type"),
                veiculo=src.get("display_name"), doi=(w.get("doi") or "").replace("https://doi.org/", "") or None,
                url=loc.get("landing_page_url"), resumo=abstract_openalex(w.get("abstract_inverted_index")),
                idioma=w.get("language"), assuntos=[pt.get("display_name") or "", (pt.get("field") or {}).get("display_name") or ""],
                instituicao=None, grau=None))
        cursor = d["meta"].get("next_cursor")
        if not d["results"]:
            break
    return recs, None


def crossref(termo, limite, refresh):
    # relevância: guarda só o que menciona o termo (sem aspas) em título/veículo/resumo
    alvo = norm(termo.replace('"', "")).split()
    d = get_json("crossref", termo, 1, lambda: requests.get(
        "https://api.crossref.org/works", headers=UA, timeout=90, params={
            "query.bibliographic": termo.replace('"', ""), "rows": min(limite, 500),
            "mailto": MAILTO}), refresh, pausa=1)
    if not d:
        return [], None
    recs = []
    for it in d["message"]["items"]:
        titulo = " ".join(it.get("title") or [])
        resumo = re.sub(r"<[^>]+>", " ", it.get("abstract") or "")
        texto = norm(" ".join([titulo, resumo, " ".join(it.get("container-title") or [])]))
        if not all(t in texto for t in alvo):
            continue
        ano = None
        for k in ("published-print", "published-online", "issued", "created"):
            dp = (it.get(k) or {}).get("date-parts")
            if dp and dp[0] and dp[0][0]:
                ano = dp[0][0]
                break
        recs.append(dict(
            fonte="crossref", id_fonte=it.get("DOI"), titulo=titulo,
            autores=[f"{a.get('family', '')}, {a.get('given', '')}".strip(", ") for a in it.get("author", [])],
            ano=ano, tipo_fonte=it.get("type"), veiculo=" ".join(it.get("container-title") or []) or it.get("publisher"),
            doi=it.get("DOI"), url=it.get("URL"), resumo=resumo.strip(), idioma=it.get("language"),
            assuntos=it.get("subject") or [], instituicao=None, grau=None))
    return recs, d["message"].get("total-results")


def semantic_scholar(termo, limite, refresh):
    d = get_json("s2", termo, 1, lambda: requests.get(
        "https://api.semanticscholar.org/graph/v1/paper/search/bulk", headers=UA, timeout=60, params={
            "query": termo, "fields": "title,year,authors,venue,externalIds,abstract,url,publicationTypes,fieldsOfStudy"}),
        refresh, pausa=2, tentativas=3)  # sem chave: 429 frequente; não insistir
    if not d:
        return [], None
    recs = []
    for p in (d.get("data") or [])[:limite]:
        ext = p.get("externalIds") or {}
        recs.append(dict(
            fonte="s2", id_fonte=p.get("paperId"), titulo=p.get("title") or "",
            autores=[a.get("name") for a in p.get("authors") or []], ano=p.get("year"),
            tipo_fonte=",".join(p.get("publicationTypes") or []), veiculo=p.get("venue") or None,
            doi=ext.get("DOI"), url=p.get("url"), resumo=p.get("abstract") or "", idioma=None,
            assuntos=p.get("fieldsOfStudy") or [], instituicao=None, grau=None))
    return recs, d.get("total")


def bdtd(termo, limite, refresh):
    recs, pagina, total = [], 0, None
    campos = ["id", "title", "authors", "publicationDates", "institutions", "summary",
              "urls", "formats", "subjects", "languages"]
    while len(recs) < limite:
        pagina += 1
        d = get_json("bdtd", termo, pagina, lambda: requests.get(
            "https://bdtd.ibict.br/vufind/api/v1/search", headers=UA, timeout=60, params=[
                ("lookfor", termo), ("type", "AllFields"), ("limit", 100), ("page", pagina)]
            + [("field[]", c) for c in campos]), refresh)
        if not d or not d.get("records"):
            break
        total = d.get("resultCount")
        for r in d["records"]:
            aut = list(((r.get("authors") or {}).get("primary") or {}).keys())
            urls = [u.get("url") for u in r.get("urls") or []]
            recs.append(dict(
                fonte="bdtd", id_fonte=r.get("id"), titulo=r.get("title") or "", autores=aut,
                ano=int(r["publicationDates"][0][:4]) if r.get("publicationDates") else None,
                tipo_fonte=",".join(r.get("formats") or []), veiculo=None, doi=None,
                url=urls[0] if urls else f"https://bdtd.ibict.br/vufind/Record/{r.get('id')}",
                resumo=" ".join(r.get("summary") or []), idioma=",".join(r.get("languages") or []),
                assuntos=[s for grp in r.get("subjects") or [] for s in grp],
                instituicao=",".join(r.get("institutions") or []), grau=",".join(r.get("formats") or [])))
        if total is not None and pagina * 100 >= total:
            break
    return recs, total


class _CurlResp:
    """Resposta mínima compatível com `get_json` para chamadas via curl."""

    def __init__(self, out: str):
        corpo, _, cod = out.rpartition("\n")
        self.status_code, self._corpo = int(cod or 0), corpo

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)

    def json(self):
        return json.loads(self._corpo)


def _curl_post_json(url: str, payload: dict) -> _CurlResp:
    # o servidor da CAPES não envia a cadeia intermediária do certificado: `requests`/certifi
    # falha (SSLError) e o curl do sistema valida pela keychain do macOS — sem desligar TLS.
    out = subprocess.run(["curl", "-s", "-m", "90", "-X", "POST", url, "-H", "Content-Type: application/json",
                          "-d", json.dumps(payload), "-w", "\n%{http_code}"],
                         capture_output=True, text=True, check=False).stdout
    return _CurlResp(out)


def capes(termo, limite, refresh):
    recs, pagina, total = [], 0, None
    while len(recs) < limite:
        pagina += 1
        d = get_json("capes", termo, pagina, lambda: _curl_post_json(
            "https://catalogodeteses.capes.gov.br/catalogo-teses/rest/busca",
            {"termo": termo, "filtros": [], "pagina": pagina, "registrosPorPagina": 20}), refresh, pausa=1)
        if not d or not d.get("tesesDissertacoes"):
            break
        total = d.get("total")
        for r in d["tesesDissertacoes"]:
            recs.append(dict(
                fonte="capes", id_fonte=r.get("id"), titulo=r.get("titulo") or "",
                autores=[r.get("autor") or ""], ano=int(r["dataDefesa"][:4]) if r.get("dataDefesa") else None,
                tipo_fonte=r.get("grauAcademico"), veiculo=r.get("nomePrograma"), doi=None, url=r.get("link"),
                resumo="", idioma=None, assuntos=[r.get("nomePrograma") or ""],
                instituicao=r.get("instituicao"), grau=r.get("grauAcademico")))
        if total is not None and len(recs) >= total:  # a API devolve no máx. 20 por página
            break
    return recs, total


FONTES = {"openalex": openalex, "crossref": crossref, "s2": semantic_scholar, "bdtd": bdtd, "capes": capes}


# --- deduplicação e classificação ---------------------------------------------

def area_auto(r) -> str:
    txt = norm(" ".join([r["titulo"], " ".join(r["assuntos"] or []), r.get("veiculo") or ""]))
    if GEO_PAT.search(txt + " ") or any(t in GEO_TOPIC for t in r["assuntos"] or []):
        # geografia humana/planejamento que cite "mineração" não deve cair aqui:
        if re.search(r"urban|cidade|municip|migra|moradia|social|saude|trabalh|planej|popula|territ", norm(r["titulo"])):
            return "outra"
        return "geociencias"
    return "outra"


def menciona_nucleo(r) -> bool:
    return bool(re.search(r"canaa (dos? )?carajas", norm(" ".join([r["titulo"], r["resumo"] or "",
                                                                    " ".join(r["assuntos"] or [])]))))


def deduplicar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["doi"] = df["doi"].str.lower().str.strip()
    df["tkey"] = df["titulo"].map(titulo_chave)
    prioridade = {"crossref": 0, "openalex": 1, "bdtd": 2, "s2": 3, "capes": 4}
    df["prio"] = df["fonte"].map(prioridade)
    df = df.sort_values(["prio"])
    grupos: dict[str, int] = {}
    gid = []
    for _, r in df.iterrows():
        k_doi = f"doi:{r['doi']}" if isinstance(r["doi"], str) and r["doi"] else None
        k_t = f"t:{r['tkey']}"
        g = grupos.get(k_doi) if k_doi else None
        g = g if g is not None else grupos.get(k_t)
        if g is None:
            g = len(gid)  # índice da linha: único e estável
        for k in (k_doi, k_t):
            if k:
                grupos.setdefault(k, g)
        gid.append(g)
    df["grupo"] = gid

    def combinar(g: pd.DataFrame) -> pd.Series:
        base = g.iloc[0].to_dict()
        for col in ("doi", "resumo", "veiculo", "url", "instituicao", "grau", "idioma"):
            if not base.get(col):
                vals = [v for v in g[col] if isinstance(v, str) and v]
                base[col] = max(vals, key=len) if vals else base.get(col)
        if not base.get("ano"):
            anos = [a for a in g["ano"] if pd.notna(a)]
            base["ano"] = anos[0] if anos else None
        base["fontes"] = sorted(set(g["fonte"]))
        base["termos"] = sorted(set(g["termo"]))
        base["camada"] = "nucleo" if (g["camada"] == "nucleo").any() else "contexto"
        base["ids_fonte"] = {f: i for f, i in zip(g["fonte"], g["id_fonte"])}
        base["assuntos"] = sorted({s for lst in g["assuntos"] for s in (lst or []) if s})
        return pd.Series(base)

    out = pd.DataFrame([combinar(g) for _, g in df.groupby("grupo", sort=False)])
    return out.drop(columns=["prio", "tkey", "grupo", "fonte", "id_fonte", "termo"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    todos, log = [], []
    plano = [(t, "nucleo", 2000) for t in TERMOS_NUCLEO] + [(t, "contexto", 200) for t in TERMOS_CONTEXTO]
    for termo, camada, limite in plano:
        for nome, fn in FONTES.items():
            try:
                recs, total = fn(termo, limite, a.refresh)
            except requests.HTTPError as e:
                print(f"  {nome} '{termo}': HTTP {e.response.status_code}")
                recs, total = [], None
            for r in recs:
                r.update(termo=termo, camada=camada)
            todos += recs
            log.append(dict(fonte=nome, termo=termo, camada=camada, total_fonte=total, n=len(recs), data=HOJE))
            print(f"{nome:9s} {camada:8s} {termo[:40]:40s} total={total} guardados={len(recs)}")

    df = pd.DataFrame(todos)
    cand = deduplicar(df)
    for col in ("titulo", "resumo", "veiculo", "url", "instituicao", "grau", "idioma", "tipo_fonte", "doi"):
        cand[col] = cand[col].map(lambda v: v if isinstance(v, str) else "")
    cand["menciona_canaa"] = cand.apply(menciona_nucleo, axis=1)
    cand["area_auto"] = cand.apply(area_auto, axis=1)
    cand["ano"] = pd.to_numeric(cand["ano"], errors="coerce").astype("Int64")
    cand = cand.sort_values(["camada", "area_auto", "ano"], ascending=[False, False, True]).reset_index(drop=True)
    cand.insert(0, "cid", [f"c{i:04d}" for i in range(len(cand))])
    cand["data_busca"] = HOJE
    cand = sem_dados_pessoais(cand)
    cand.to_parquet(OUT / "candidatos.parquet", index=False)
    pd.DataFrame(log).to_parquet(OUT / "log_buscas.parquet", index=False)

    # lista compacta para triagem humana/modelo: fora geociências e (núcleo ou contexto)
    tri = cand[cand["area_auto"] != "geociencias"]
    linhas = []
    for _, r in tri.iterrows():
        aut = (r["autores"][0].split(",")[0] if len(r["autores"]) else "?")[:25]
        linhas.append(f"{r['cid']}|{r['camada'][:3]}|{'C' if r['menciona_canaa'] else '-'}|{r['ano']}|"
                      f"{aut}|{(r['grau'] or r['tipo_fonte'] or '')[:12]}|{r['titulo'][:150]}|{(r['veiculo'] or r['instituicao'] or '')[:40]}")
    (OUT / "triagem.txt").write_text("\n".join(linhas) + "\n")

    print(f"\nregistros brutos: {len(df)}; candidatos únicos: {len(cand)}")
    print(cand.groupby(["camada", "area_auto"]).size().to_string())
    print(f"mencionam Canaã (título/resumo/assunto): {int(cand['menciona_canaa'].sum())}")
    print(f"lista de triagem: {len(tri)} linhas → {OUT / 'triagem.txt'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
