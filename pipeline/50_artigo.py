#!/usr/bin/env python
"""50_artigo.py — monta o artigo (PLANO.md, Fase 5 passo 3; etapa E6).

Entrada: `artigo/texto.md` escrito à mão com marcadores leves:
  <cite:slug>            → (SOBRENOME, ano)                 citação parentética ABNT autor-data
  <cite:slug1;slug2>     → (SOBRENOME, ano; SOBRENOME, ano)
  <citet:slug>           → Sobrenome (ano)                  citação narrativa
  <!-- tab: tab_04_coortes_chegada -->   → título, tabela e fonte de artigo/tabelas/<nome>.md
  <!-- fig: fig_06_coortes_chegada -->   → marcador de figura do md_to_docx.js com a legenda de figuras.json
  <!-- referencias -->   → lista ABNT das obras citadas (artigo/bibliografia/referencias.json)

Saídas: `artigo/texto_resolvido.md` (markdown puro), `artigo/artigo.docx` (docx_pipeline/md_to_docx.js,
identidade Ardósia) e `artigo/artigo.pdf` (LibreOffice headless). `--so-md` para só resolver o texto.

Regras: toda citação precisa existir em referencias.json (todas verificadas na E4); toda referência
listada é citada; nenhuma figura/tabela referenciada pode faltar. Falha em voz alta.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ART = BASE / "artigo"
REFS = json.loads((ART / "bibliografia" / "referencias.json").read_text(encoding="utf-8"))["referencias"]
REFS += json.loads((ART / "bibliografia" / "referencias_metodologicas.json").read_text(encoding="utf-8"))["referencias"]
POR_SLUG = {r["slug"]: r for r in REFS}
FIGS = {d["arquivo"].removesuffix(".png"): d for d in json.loads((ART / "figuras" / "figuras.json").read_text(encoding="utf-8"))}


def sobrenome(autor: str) -> str:
    return autor.split(",")[0].strip()


def autor_data(slug: str, narrativa: bool = False) -> str:
    r = POR_SLUG[slug]
    a = [sobrenome(x) for x in r["autores"]]
    if len(a) == 1:
        nome = a[0]
    elif len(a) == 2:
        nome = f"{a[0]}; {a[1]}" if not narrativa else f"{a[0]} e {a[1]}"
    else:
        nome = f"{a[0]} et al."
    if narrativa:
        return f"{nome.title() if nome.isupper() else nome} ({r['ano']})"
    return f"{nome.upper()}, {r['ano']}"


def resolver_citacoes(texto: str, citados: set[str]) -> str:
    def par(m):
        slugs = [s.strip() for s in m.group(1).split(";")]
        for s in slugs:
            if s not in POR_SLUG:
                raise SystemExit(f"citação inexistente em referencias.json: {s}")
            citados.add(s)
        return "(" + "; ".join(autor_data(s) for s in slugs) + ")"

    def narr(m):
        s = m.group(1).strip()
        if s not in POR_SLUG:
            raise SystemExit(f"citação inexistente em referencias.json: {s}")
        citados.add(s)
        return autor_data(s, narrativa=True)

    texto = re.sub(r"<citet:([^>]+)>", narr, texto)
    texto = re.sub(r"<cite:([^>]+)>", par, texto)
    return texto


def bloco_tabela(nome: str) -> str:
    p = ART / "tabelas" / f"{nome}.md"
    if not p.exists():
        raise SystemExit(f"tabela ausente: {p}")
    return p.read_text(encoding="utf-8").strip() + "\n"


def bloco_figura(nome: str) -> str:
    if nome not in FIGS:
        raise SystemExit(f"figura ausente no índice: {nome}")
    d = FIGS[nome]
    legenda = d["legenda"].replace("|", "/")
    return f"<!-- fig: figuras/{d['arquivo']} | {legenda} Fonte: {d['fonte']} -->\n"


def referencias_md(citados: set[str]) -> str:
    itens = sorted((POR_SLUG[s] for s in citados), key=lambda r: (sobrenome(r["autores"][0]).upper(), r["ano"], r["titulo"]))
    linhas = []
    for r in itens:
        linhas.append(r["abnt"].strip())
        linhas.append("")
    return "\n".join(linhas)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--so-md", action="store_true")
    a = ap.parse_args()
    md = (ART / "texto.md").read_text(encoding="utf-8")
    citados: set[str] = set()
    md = resolver_citacoes(md, citados)
    md = re.sub(r"<!--\s*tab:\s*(\S+)\s*-->", lambda m: bloco_tabela(m.group(1)), md)
    md = re.sub(r"<!--\s*fig:\s*(fig_\S+)\s*-->", lambda m: bloco_figura(m.group(1)), md)
    if "<!-- referencias -->" not in md:
        raise SystemExit("faltou o marcador <!-- referencias -->")
    md = md.replace("<!-- referencias -->", referencias_md(citados))
    sobras = re.findall(r"<cite[t]?:[^>]*>|<!--\s*tab:|<!--\s*fig:\s*fig_", md)
    if sobras:
        raise SystemExit(f"marcadores não resolvidos: {sobras[:5]}")
    out = ART / "texto_resolvido.md"
    out.write_text(md, encoding="utf-8")
    (ART / "citadas.json").write_text(json.dumps(sorted(citados), ensure_ascii=False, indent=1), encoding="utf-8")
    n_fig = len(re.findall(r"^<!-- fig:", md, flags=re.M)); n_tab = len(re.findall(r"^\*\*Tabela \d+", md, flags=re.M))
    print(f"texto resolvido: {len(md.split())} palavras, {len(citados)} obras citadas, {n_fig} figuras, {n_tab} tabelas → {out}")
    if a.so_md:
        return 0
    docx = ART / "artigo.docx"
    subprocess.run(["node", str(ART / "docx_pipeline" / "md_to_docx.js"), str(out), str(docx), f"--pasta-base={ART}"], check=True)
    soffice = shutil.which("soffice") or "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(ART), str(docx)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    pdf = ART / "artigo.pdf"
    print(f"gravado {docx.name} ({docx.stat().st_size / 1e6:.1f} MB) e {pdf.name} ({pdf.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
