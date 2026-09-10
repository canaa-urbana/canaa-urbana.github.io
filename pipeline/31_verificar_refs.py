"""
E4 / Fase 4 passo 2 (PLANO.md) — verificação das referências triadas e exportação.

Entrada:
    data/processed/bibliografia/candidatos.parquet   (saída de 30_bibliografia.py)
    artigo/bibliografia/triagem.json                 (decisões de triagem: candidatos incluídos
                                                     por `cid` + entradas manuais, com eixos,
                                                     período, método e achados)

Cada entrada só vai para `referencias.json` depois de conferida nesta execução:
  1. DOI → metadados no Crossref (ou DataCite) — título (similaridade ≥ 0,80), ano (±1) e
     sobrenome do 1º autor;
  2. sem DOI → página do repositório/periódico responde 200 e contém o título (≥ 75 % dos
     termos) e o sobrenome do 1º autor;
  3. teses/dissertações sem página acessível → registro no Catálogo de Teses da CAPES com
     mesmo título e autor.
`verificado_em` guarda a URL usada e o que foi confirmado. Entradas que falham ficam fora e
são listadas em `data/processed/bibliografia/verificacao.parquet` (status + motivo).

Saídas:
    artigo/bibliografia/referencias.json   (formato dos projetos irmãos, ABNT autor-data)
    artigo/bibliografia/referencias.bib
    docs/revisao_bibliografica.md          (matriz entre marcadores MATRIZ; texto fora deles é manual)

Uso:
    .venv/bin/python pipeline/31_verificar_refs.py
"""
from __future__ import annotations

import difflib
import hashlib
import html
import json
import re
import subprocess
import sys
import time
import unicodedata
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BIB = ROOT / "artigo/bibliografia"
PROC = ROOT / "data/processed/bibliografia"
CACHE = ROOT / "data/interim/bibliografia/verif"
DOC = ROOT / "docs/revisao_bibliografica.md"
HOJE = date.today().isoformat()
MAILTO = "urban-canaa@example.org"

EIXOS = {
    "urbanizacao": "Urbanização e produção do espaço",
    "moradia": "Moradia e habitação",
    "migracao": "Migração e população",
    "trabalho": "Trabalho e renda",
    "economia_mineral": "Economia mineral, royalties e finanças públicas",
    "meio_ambiente": "Meio ambiente e uso da terra",
    "saude": "Saúde",
    "planejamento": "Planejamento e gestão urbana",
    "historia": "Colonização, história e conflitos agrários",
    "sociedade": "Sociedade, cultura e educação",
}
SUFIXOS = {"junior", "júnior", "filho", "neto", "sobrinho", "jr", "jr."}
PARTICULAS = {"da", "de", "do", "das", "dos", "e"}


# --- utilitários -------------------------------------------------------------

def norm(s: str | None) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", s.lower())).strip()


def curl(url: str, timeout: int = 40) -> tuple[int, str]:
    """GET via curl do sistema (valida TLS pela keychain; segue redirecionamentos)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / (hashlib.sha1(url.encode()).hexdigest()[:16] + ".txt")
    if p.exists():
        cod, _, corpo = p.read_text(errors="ignore").partition("\n")
        return int(cod), corpo
    r = subprocess.run(["curl", "-s", "-L", "-m", str(timeout), "-A",
                        f"urban-canaa-bibliografia/0.1 (mailto:{MAILTO})", "-w", "\n%{http_code}", url],
                       capture_output=True, check=False)
    out = r.stdout.decode("utf-8", errors="ignore")
    corpo, _, cod = out.rpartition("\n")
    cod = int(cod) if cod.strip().isdigit() else 0
    if cod:
        p.write_text(f"{cod}\n{corpo}")
    time.sleep(0.3)
    return cod, corpo


def texto_pagina(corpo: str) -> str:
    corpo = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", corpo)
    return norm(html.unescape(re.sub(r"<[^>]+>", " ", corpo)))


def sim_titulo(a: str, b: str) -> float:
    a, b = norm(a), norm(b)
    if not a or not b:
        return 0.0
    if a in b or b in a:
        return 1.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def cobertura(titulo: str, texto: str) -> float:
    termos = [t for t in norm(titulo).split() if len(t) > 3]
    return sum(t in texto for t in termos) / len(termos) if termos else 0.0


def nome_abnt(nome: str) -> tuple[str, str]:
    """Devolve (sobrenome, prenomes) a partir de 'Sobrenome, Nome' ou 'Nome Sobrenome'."""
    nome = re.sub(r"\s*\[[^\]]*\]", "", re.sub(r"\s+", " ", (nome or "").strip()))  # "[UNESP]"
    nome = re.sub(r",\s*\d{4}-?\d{0,4}\s*$", "", nome)  # datas de autoridade ("Tonelli, Lívia Maria, 1986-")
    if "," in nome:
        sob, pre = [x.strip() for x in nome.split(",", 1)]
        m = re.match(r"(?i)^(da|de|do|das|dos)\s+(.+)$", sob)  # "Da Silva, Maria" → "Silva, Maria da"
        if m:
            sob, pre = m.group(2), f"{pre} {m.group(1).lower()}".strip()
    else:
        partes = nome.split(" ")
        if len(partes) == 1:
            return partes[0], ""
        k = 2 if partes[-1].lower() in SUFIXOS and len(partes) > 2 else 1
        sob, pre = " ".join(partes[-k:]), " ".join(partes[:-k])
    cap = lambda s: " ".join(w.upper() if re.fullmatch(r"(?i)([a-z]\.)+", w) else w.lower() if w.lower() in PARTICULAS else (w[:1].upper() + w[1:].lower()) if w.isupper() or w.islower() else w
                             for w in s.split(" "))
    return cap(sob), cap(pre)


def autores_fmt(autores: list[str]) -> list[str]:
    out = []
    for a in autores:
        sob, pre = nome_abnt(a)
        out.append(f"{sob}, {pre}".strip(", "))
    return out


def sobrenome1(autores: list[str]) -> str:
    return norm(nome_abnt(autores[0])[0]).split(" ")[-1] if autores else ""


# --- verificação -------------------------------------------------------------

def meta_doi(doi: str) -> dict | None:
    cod, corpo = curl(f"https://api.crossref.org/works/{doi}?mailto={MAILTO}")
    if cod == 200:
        m = json.loads(corpo)["message"]
        ano = None
        for k in ("published-print", "published-online", "issued"):
            dp = (m.get(k) or {}).get("date-parts")
            if dp and dp[0] and dp[0][0]:
                ano = dp[0][0]
                break
        return dict(origem="Crossref", titulo=" ".join(m.get("title") or []), ano=ano,
                    autores=[a.get("family", "") for a in m.get("author", [])],
                    veiculo=" ".join(m.get("container-title") or []) or None, volume=m.get("volume"),
                    numero=m.get("issue"), paginas=m.get("page"), publicador=m.get("publisher"))
    cod, corpo = curl(f"https://api.datacite.org/dois/{doi}")
    if cod == 200:
        a = json.loads(corpo)["data"]["attributes"]
        return dict(origem="DataCite", titulo=(a.get("titles") or [{}])[0].get("title", ""),
                    ano=a.get("publicationYear"), autores=[c.get("familyName") or c.get("name", "") for c in a.get("creators", [])],
                    veiculo=(a.get("container") or {}).get("title"), volume=None, numero=None, paginas=None,
                    publicador=a.get("publisher") if isinstance(a.get("publisher"), str) else (a.get("publisher") or {}).get("name"))
    return None


def verificar(e: dict) -> tuple[bool, str, dict]:
    """Retorna (ok, verificado_em, metadados_extra)."""
    if not [a for a in e["autores"] if norm(a)]:
        return False, "sem autoria nos metadados (completar em `correcoes` da triagem)", {}
    s1 = sobrenome1(e["autores"])
    if e.get("doi"):
        m = meta_doi(e["doi"])
        if m:
            st = sim_titulo(e["titulo"], m["titulo"])
            ano_ok = m["ano"] is None or e.get("ano") is None or abs(int(m["ano"]) - int(e["ano"])) <= 1
            aut_ok = not m["autores"] or not s1 or any(s1 in norm(x) for x in m["autores"])
            if st >= 0.80 and ano_ok and aut_ok:
                extra = {k: m[k] for k in ("volume", "numero", "paginas", "publicador") if m.get(k)}
                if m.get("veiculo"):
                    extra["veiculo"] = m["veiculo"]
                if m.get("ano"):
                    extra["ano"] = int(m["ano"])
                return True, (f"https://doi.org/{e['doi']} — {m['origem']}: título/ano/1º autor conferidos "
                              f"(sim. título {st:.2f}) em {HOJE}"), extra
            motivo = f"DOI diverge (sim {st:.2f}, ano_ok={ano_ok}, autor_ok={aut_ok})"
        else:
            motivo = "DOI não resolvido em Crossref/DataCite"
    else:
        motivo = "sem DOI"

    for url in [u for u in [e.get("url"), *(e.get("urls_alt") or [])] if u and u != "undefined"]:
        if url.lower().endswith(".pdf"):  # PDF não é página de registro
            motivo += f"; {url} → PDF (ignorado)"
            continue
        cod, corpo = curl(url)
        if cod != 200:
            motivo += f"; {url} → HTTP {cod}"
            continue
        txt = texto_pagina(corpo)
        cob = cobertura(e["titulo"], txt)
        aut_ok = not s1 or s1 in txt
        if cob >= 0.75 and aut_ok:
            return True, f"{url} — página conferida: título ({cob:.0%} dos termos) e 1º autor em {HOJE}", {}
        motivo += f"; {url} → título {cob:.0%}, autor {'ok' if aut_ok else 'ausente'}"

    if e.get("bdtd_id"):
        ok, onde = bdtd_confirma(e)
        if ok:
            return True, onde, {}
        motivo += "; BDTD (API) sem correspondência"
    if e.get("capes_id") or e.get("tipo") in ("tese", "dissertacao"):
        ok, onde = capes_confirma(e)
        if ok:
            return True, onde, {}
        motivo += "; CAPES sem registro correspondente"
    return False, motivo, {}


def ano_ok(e: dict, ano) -> bool:
    try:
        return e.get("ano") is None or ano is None or abs(int(str(ano)[:4]) - int(e["ano"])) <= 1
    except ValueError:
        return True


def bdtd_confirma(e: dict) -> tuple[bool, str]:
    """Registro no catálogo da BDTD pela API (a página do registro tem desafio anti-bot)."""
    cod, corpo = curl(f"https://bdtd.ibict.br/vufind/api/v1/record?id={e['bdtd_id']}")
    if cod != 200:
        return False, ""
    regs = json.loads(corpo).get("records") or []
    s1 = sobrenome1(e["autores"])
    for g in regs:
        aut = " ".join(((g.get("authors") or {}).get("primary") or {}).keys())
        anos = g.get("publicationDates") or [None]
        if sim_titulo(e["titulo"], g.get("title", "")) >= 0.85 and (not s1 or s1 in norm(aut)) and ano_ok(e, anos[0]):
            return True, (f"https://bdtd.ibict.br/vufind/Record/{e['bdtd_id']} — registro BDTD/IBICT (API) com "
                          f"título/autor/ano conferidos em {HOJE}")
    return False, ""


def capes_confirma(e: dict) -> tuple[bool, str]:
    termo = " ".join(re.sub(r"[\"“”:;]", " ", e["titulo"]).split()[:8])
    g = capes_registro(e)
    if g:
        return True, (f"https://catalogodeteses.capes.gov.br (registro {g['id']}; {g.get('instituicao')}; "
                      f"{g.get('nomePrograma')}) — título/autor/ano de defesa conferidos em {HOJE}")
    return False, ""


def capes_registro(e: dict) -> dict | None:
    """Registro correspondente no Catálogo de Teses da CAPES (busca por trecho do título; cache local)."""
    termo = " ".join(re.sub(r"[\"“”:;]", " ", e["titulo"]).split()[:8])
    p = CACHE / ("capes_" + hashlib.sha1(termo.encode()).hexdigest()[:16] + ".json")
    if p.exists():
        out = p.read_text()
    else:
        payload = json.dumps({"termo": termo, "filtros": [], "pagina": 1, "registrosPorPagina": 20})
        out = subprocess.run(["curl", "-s", "-m", "60", "-X", "POST",
                              "https://catalogodeteses.capes.gov.br/catalogo-teses/rest/busca",
                              "-H", "Content-Type: application/json", "-d", payload],
                             capture_output=True, text=True).stdout
        if out.startswith("{"):
            p.write_text(out)
    try:
        regs = json.loads(out).get("tesesDissertacoes") or []
    except json.JSONDecodeError:
        return None
    s1 = sobrenome1(e["autores"])
    for g in regs:
        mesmo = str(g.get("id")) == str(e.get("capes_id")) or sim_titulo(e["titulo"], g.get("titulo", "")) >= 0.85
        if mesmo and (not s1 or s1 in norm(g.get("autor"))) and ano_ok(e, g.get("dataDefesa")):
            return g
    return None


GRAU = {"Mestrado": "dissertacao", "Mestrado Profissional": "dissertacao", "Doutorado": "tese",
        "Doutorado Profissional": "tese", "masterThesis": "dissertacao", "doctoralThesis": "tese"}


def enriquecer_trabalho_academico(e: dict) -> None:
    """Grau, instituição e programa pelos registros oficiais (CAPES; BDTD) — o OpenAlex chama
    tudo de 'dissertation' e usa o nome do repositório como veículo."""
    g = capes_registro(e)
    if g:
        e["tipo"] = GRAU.get(g.get("grauAcademico"), e["tipo"])
        e["instituicao"] = titulo_caso(g.get("instituicao") or "") or e.get("instituicao")
        e["veiculo"] = titulo_caso(g.get("nomePrograma") or "") or None
        return
    if e.get("bdtd_id"):
        cod, corpo = curl(f"https://bdtd.ibict.br/vufind/api/v1/record?id={e['bdtd_id']}")
        if cod == 200:
            for r in json.loads(corpo).get("records") or []:
                for f in r.get("formats") or []:
                    if f in GRAU:
                        e["tipo"] = GRAU[f]
                e["instituicao"] = e.get("instituicao") or ",".join(r.get("institutions") or []) or None
    e["veiculo"] = None  # sem programa conferido: não usar o nome do repositório


SIGLAS = {"ufpa", "ufmg", "usp", "ufrrj", "unicamp", "unesp", "unb", "ufrn", "ufop", "uft", "ufra", "ufu", "iec",
          "unifesspa", "pa", "s11d", "cfem", "mst", "covid", "hiv", "aids", "ods", "onu", "pmcmv", "sig", "itv",
          "ence", "ibge", "naea", "ii", "iii", "xxi", "xx", "cedere", "getat"}
NOMES = ["Canaã dos Carajás", "Canaã", "Carajás", "Parauapebas", "Marabá", "Curionópolis", "Pará", "Vale",
         "Amazônia", "Amazônica", "Brasil", "Serra Sul", "Sossego", "Ferro Carajás", "Maranhão", "Xikrin",
         "Cateté", "Rio de Janeiro", "Minas Gerais", "Itabira", "Paraíso das Águas", "Minha Casa Minha Vida",
         "Oziel Alves", "Planalto Serra Dourada", "Racha Placa", "Bom Jesus", "Ourilândia do Norte", "Tucumã",
         "Sudeste Paraense", "Oriental", "Legal"]


def titulo_caso(s: str) -> str:
    """Caixa alta integral (CAPES) → caixa de sentença, preservando siglas e nomes próprios."""
    s = re.sub(r"\s+", " ", html.unescape(s or "")).strip()
    letras = [c for c in s if c.isalpha()]
    if not letras or sum(c.isupper() for c in letras) / len(letras) < 0.8:
        return s
    out = []
    for i, w in enumerate(s.lower().split(" ")):
        base = norm(w)
        if base in SIGLAS:
            w = w.upper()
        elif i == 0 or (out and out[-1].endswith((":", "?", "!", "."))):
            w = w[:1].upper() + w[1:]
        out.append(w)
    s = " ".join(out)
    for n in NOMES:
        s = re.sub(rf"(?i)\b{re.escape(n)}\b", n, s)
    return re.sub(r"(?i)-pa\b", "-PA", s)


# --- montagem das entradas ---------------------------------------------------

TIPO_MAP = {"article": "artigo", "journal-article": "artigo", "proceedings-article": "anais", "book": "livro",
            "book-chapter": "capitulo", "dissertation": "tese", "report": "relatorio", "posted-content": "preprint",
            "masterThesis": "dissertacao", "doctoralThesis": "tese", "bachelorThesis": "tcc",
            "Mestrado": "dissertacao", "Doutorado": "tese", "Mestrado Profissional": "dissertacao"}


def tipo_de(r: dict) -> str:
    for campo in ("grau", "tipo_fonte"):
        for v in str(r.get(campo) or "").split(","):
            if v.strip() in TIPO_MAP:
                return TIPO_MAP[v.strip()]
    return "artigo"


def entrada_de_candidato(r: dict) -> dict:
    ids = r.get("ids_fonte") or {}
    urls_alt = []
    return dict(
        tipo=tipo_de(r), autores=autores_fmt(list(r["autores"])), ano=int(r["ano"]) if pd.notna(r["ano"]) else None,
        titulo=re.sub(r"\s+", " ", r["titulo"]).strip(), veiculo=r.get("veiculo"), doi=(r.get("doi") or None),
        url=r.get("url") if r.get("url") != "undefined" else None, urls_alt=urls_alt,
        instituicao=r.get("instituicao"), capes_id=ids.get("capes"), bdtd_id=ids.get("bdtd"),
        fontes_busca=[] if r.get("fontes") is None else list(r["fontes"]), resumo=r.get("resumo") or "")


def slug_de(e: dict, usados: set) -> str:
    sob = norm(nome_abnt(e["autores"][0])[0]).replace(" ", "") if e["autores"] else "anon"
    pal = next((w for w in norm(e["titulo"]).split() if len(w) > 3), "x")
    base = f"{sob}{e.get('ano') or 'sd'}{pal}"[:40]
    s, i = base, 1
    while s in usados:
        i += 1
        s = f"{base}{i}"
    usados.add(s)
    return s


def abnt(e: dict) -> str:
    aut = []
    for a in e["autores"][:3]:
        sob, pre = nome_abnt(a)
        aut.append(f"{sob.upper()}, {pre}".strip(", "))
    autores = "; ".join(aut) + (" et al" if len(e["autores"]) > 3 else "")
    ano = e.get("ano") or "[s.d.]"
    t = e["tipo"]
    if t in ("tese", "dissertacao", "tcc"):
        grau = {"tese": "Tese (Doutorado)", "dissertacao": "Dissertação (Mestrado)", "tcc": "Trabalho de Conclusão de Curso"}[t]
        prog = f" em {e['veiculo']}" if e.get("veiculo") and t != "tcc" else ""
        return f"{autores}. {e['titulo']}. {ano}. {grau.replace(')', prog + ')') if prog else grau} – {e.get('instituicao') or '[s.l.]'}, {ano}."
    if t in ("livro", "relatorio", "plano", "eia_rima"):
        return f"{autores}. {e['titulo']}. {e.get('publicador') or e.get('veiculo') or '[s.l.: s.n.]'}, {ano}."
    partes = [f"{autores}. {e['titulo']}."]
    if e.get("veiculo"):
        partes.append(f"{'In: ' if t in ('anais', 'capitulo') else ''}{e['veiculo']},")
    for k, rot in (("volume", "v."), ("numero", "n."), ("paginas", "p.")):
        if e.get(k):
            partes.append(f"{rot} {e[k]},")
    partes.append(f"{ano}.")
    s = " ".join(partes)
    if e.get("doi"):
        s += f" DOI: {e['doi']}."
    return s


def bibtex(e: dict) -> str:
    tipo = {"artigo": "article", "anais": "inproceedings", "livro": "book", "capitulo": "incollection",
            "tese": "phdthesis", "dissertacao": "mastersthesis", "tcc": "misc"}.get(e["tipo"], "techreport")
    campos = {"author": " and ".join(e.get("autores", [])), "title": e["titulo"], "year": e.get("ano"),
              "journal" if tipo == "article" else "booktitle" if tipo in ("inproceedings", "incollection") else "howpublished":
                  e.get("veiculo"),
              "school" if "thesis" in tipo else "institution": e.get("instituicao"),
              "volume": e.get("volume"), "number": e.get("numero"), "pages": e.get("paginas"),
              "doi": e.get("doi"), "url": e.get("url"), "publisher": e.get("publicador")}
    corpo = ",\n".join(f"  {k} = {{{v}}}" for k, v in campos.items() if v)
    return f"@{tipo}{{{e['slug']},\n{corpo}\n}}\n"


def matriz_md(refs: list[dict]) -> str:
    linhas = [f"_Gerado por `pipeline/31_verificar_refs.py` em {HOJE}: {len(refs)} referências verificadas._\n"]
    for chave, rotulo in EIXOS.items():
        sel = sorted([r for r in refs if chave in r.get("eixos", [])], key=lambda r: (r.get("ano") or 0, r["slug"]))
        if not sel:
            continue
        linhas.append(f"\n### {rotulo} ({len(sel)})\n")
        linhas.append("| Referência | Tipo | Camada | Período | Método | Principais achados |")
        linhas.append("|---|---|---|---|---|---|")
        for r in sel:
            sob = nome_abnt(r["autores"][0])[0] if r["autores"] else "?"
            etal = " et al." if len(r["autores"]) > 2 else (f" e {nome_abnt(r['autores'][1])[0]}" if len(r["autores"]) == 2 else "")
            cel = lambda s: (s or "—").replace("|", "/").replace("\n", " ")
            linhas.append(f"| {sob}{etal} ({r.get('ano')}) `{r['slug']}` | {r['tipo']} | {r.get('camada', '')} | "
                          f"{cel(r.get('periodo'))} | {cel(r.get('metodo'))} | {cel(r.get('achados'))} |")
    return "\n".join(linhas) + "\n"


def main() -> int:
    tri = json.loads((BIB / "triagem.json").read_text())
    cand = pd.read_parquet(PROC / "candidatos.parquet").set_index("cid")

    entradas = []
    for it in tri.get("incluidos", []):
        if it["cid"] not in cand.index:
            print(f"cid inexistente: {it['cid']}")
            continue
        e = entrada_de_candidato(cand.loc[it["cid"]].to_dict())
        e.update({k: v for k, v in (it.get("correcoes") or {}).items()})
        e.update({k: it[k] for k in ("eixos", "camada", "periodo", "metodo", "achados", "uso", "slug") if k in it})
        e["urls_alt"] = e["urls_alt"] + it.get("urls_alt", [])  # registros oficiais achados à mão (ex.: API DSpace)
        e["origem"] = it["cid"]
        entradas.append(e)
    for it in tri.get("manuais", []):
        e = dict(it)
        e["autores"] = autores_fmt(e.get("autores") or [])
        e["origem"] = "manual"
        entradas.append(e)

    # slugs estáveis entre execuções: a E6 cita <cite:slug>
    antigos = {}
    if (BIB / "referencias.json").exists():
        for r in json.loads((BIB / "referencias.json").read_text()).get("referencias", []):
            antigos[norm(r["titulo"])] = r["slug"]
    usados: set[str] = set()
    refs, status = [], []
    for e in entradas:
        ok, onde, extra = verificar(e)
        for k, v in extra.items():
            if k == "veiculo" and e.get("veiculo") and e["tipo"] in ("tese", "dissertacao"):
                continue
            e[k] = v if k in ("ano", "veiculo") or not e.get(k) else e[k]
        if ok and e["tipo"] in ("tese", "dissertacao"):
            enriquecer_trabalho_academico(e)
        e["titulo"] = titulo_caso(e["titulo"]).rstrip(" .")
        for k in ("veiculo", "instituicao", "publicador"):
            if e.get(k):
                e[k] = titulo_caso(e[k])
        e["slug"] = e.get("slug") or (antigos.get(norm(e["titulo"])) if antigos.get(norm(e["titulo"])) not in usados
                                       else None) or slug_de(e, usados)
        usados.add(e["slug"])
        status.append(dict(slug=e["slug"], origem=e["origem"], titulo=e["titulo"][:120], ok=ok, detalhe=onde))
        if not ok:
            continue
        e["verificado_em"] = onde
        e["nacional"] = e.get("nacional", True)
        e["abnt"] = abnt(e)
        for k in ("urls_alt", "resumo", "capes_id", "bdtd_id", "origem"):
            e.pop(k, None)
        refs.append({k: v for k, v in e.items() if v not in (None, "", [])})

    ordem = ["slug", "tipo", "autores", "ano", "titulo", "veiculo", "instituicao", "volume", "numero", "paginas",
             "publicador", "doi", "url", "nacional", "camada", "eixos", "periodo", "metodo", "achados", "uso",
             "fontes_busca", "abnt", "verificado_em"]
    refs = [{k: r[k] for k in sorted(r, key=lambda k: ordem.index(k) if k in ordem else 99)} for r in refs]
    refs.sort(key=lambda r: r["slug"])
    out = {"_leiame": ("Base de referências do projeto urban-canaa (E4), ABNT autor-data. Cada entrada foi "
                       "conferida por `pipeline/31_verificar_refs.py` (DOI no Crossref/DataCite, página do "
                       "repositório ou Catálogo de Teses CAPES) — `verificado_em` = URL e o que foi confirmado. "
                       "Chave = slug citado em <cite:slug> no artigo. `camada`: nucleo = sobre Canaã dos Carajás; "
                       "contexto = Carajás/Parauapebas/cidades mineradoras. `eixos`, `periodo`, `metodo`, `achados` "
                       "alimentam docs/revisao_bibliografica.md."),
           "gerado_em": HOJE, "referencias": refs}
    (BIB / "referencias.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    (BIB / "referencias.bib").write_text("\n".join(bibtex(r) for r in refs))
    pd.DataFrame(status).to_parquet(PROC / "verificacao.parquet", index=False)

    ini, fim = "<!-- MATRIZ:INICIO -->", "<!-- MATRIZ:FIM -->"
    doc = DOC.read_text() if DOC.exists() else f"# Revisão bibliográfica\n\n{ini}\n{fim}\n"
    a, _, resto = doc.partition(ini)
    _, _, b = resto.partition(fim)
    DOC.write_text(f"{a}{ini}\n{matriz_md(refs)}{fim}{b}")

    st = pd.DataFrame(status)
    print(f"entradas: {len(st)}; verificadas: {int(st['ok'].sum())}; falharam: {int((~st['ok']).sum())}")
    for _, r in st[~st["ok"]].iterrows():
        print(f"  FALHOU {r['slug']}: {r['detalhe'][:200]}")
    print(pd.Series([x for r in refs for x in r.get("eixos", [])]).value_counts().to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
