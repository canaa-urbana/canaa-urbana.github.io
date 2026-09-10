#!/usr/bin/env python3
"""Auditoria de publicação (E8): nada de dado pessoal, credencial ou informação sigilosa nos
arquivos versionados.

Complementa o gitleaks (segredos) e o `verify_gate.py` (agregados × gate). Varre o CONTEÚDO
DECODIFICADO de cada arquivo rastreado pelo git — texto, JSON, parquet (colunas de texto e
metadados), DOCX (XML interno), PDF (texto e metadados), SVG e metadados de PNG — atrás de:

  - e-mails (exceto os genéricos `example.org` e o no-reply do GitHub);
  - CPF, telefone celular brasileiro;
  - caminhos locais de máquina (`/Users/…`, `/Volumes/…`, `/home/…`, `C:\\Users`);
  - URLs assinadas ou com chave (`sig=`, `token=`, `api_key=`, `X-Amz-Signature` …);
  - chaves conhecidas (AWS, GitHub, Google, Slack, chave privada PEM);
  - arquivos de microdados ou intermediários (`data/raw`, `data/interim`, `*_controlado*`, CSV/TXT/DBF).

Uso: python pipeline/auditoria_publicacao.py [--staged]   (sem --staged: arquivos rastreados)
Sai com código 1 se encontrar qualquer ocorrência.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent

PADROES = {
    "e-mail": re.compile(r"[A-Za-z0-9._%+-]+@(?!users\.noreply\.github\.com|example\.org)[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "CPF": re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),
    "telefone": re.compile(r"\(\d{2}\)\s?9\d{4}-\d{4}"),
    "caminho local": re.compile(r"/Users/[A-Za-z0-9_.-]+|/Volumes/[A-Za-z0-9_.-]+|/home/[a-z0-9_.-]+/|C:\\\\Users"),
    "URL assinada/chave": re.compile(r"[?&](sig|skoid|sktid|X-Amz-Signature|X-Amz-Credential|token|access_token|api_key|apikey)=[^&\s\"']{6,}", re.I),
    "chave conhecida": re.compile(r"AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AIza[0-9A-Za-z_-]{35}|xox[abpr]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}
# o próprio auditor e o CI citam os padrões; o .gitleaks.toml também
ISENTOS = {"pipeline/auditoria_publicacao.py", ".github/workflows/publicar.yml", ".gitleaks.toml"}
PROIBIDOS = re.compile(r"^(data/raw/|data/interim/(?!layouts/[^/]+\.json$))|_controlado|\.(csv|dbf|sas)$|(?<!requirements-ci)(?<!robots)\.txt$", re.I)


def arquivos(staged: bool) -> list[str]:
    cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"] if staged else ["git", "ls-files"]
    return [a for a in subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines() if a]


def texto(p: pathlib.Path) -> str:
    suf = p.suffix.lower()
    if suf == ".parquet":
        import pyarrow.parquet as pq

        tb = pq.read_table(p)
        partes = [" ".join(v.decode("utf-8", "ignore") for v in (tb.schema.metadata or {}).values())]
        for c in tb.column_names:
            partes += [v for v in tb.column(c).to_pylist() if isinstance(v, str)]
        return "\n".join(partes)
    if suf == ".docx":
        z = zipfile.ZipFile(p)
        return "\n".join(z.read(n).decode("utf-8", "ignore") for n in z.namelist() if n.endswith((".xml", ".rels")))
    if suf == ".pdf":
        t = subprocess.run(["pdftotext", str(p), "-"], capture_output=True, text=True).stdout
        return t + subprocess.run(["pdfinfo", str(p)], capture_output=True, text=True).stdout
    if suf in {".png", ".webp", ".jpg", ".jpeg"}:
        from PIL import Image

        return json.dumps({k: str(v)[:2000] for k, v in Image.open(p).info.items()})
    return p.read_bytes().decode("utf-8", "ignore")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--staged", action="store_true")
    args = ap.parse_args()
    achados: list[str] = []
    lista = arquivos(args.staged)
    for a in lista:
        if PROIBIDOS.search(a):
            achados.append(f"{a}: arquivo de tipo/pasta proibido no repositório")
            continue
        if a in ISENTOS:
            continue
        p = ROOT / a
        if not p.is_file():
            continue
        try:
            t = texto(p)
        except Exception as e:  # noqa: BLE001 — arquivo ilegível é reportado, não ignorado
            achados.append(f"{a}: não foi possível ler para auditoria ({e})")
            continue
        for nome, rx in PADROES.items():
            for m in rx.finditer(t):
                achados.append(f"{a}: {nome}: …{t[max(0, m.start() - 30):m.end() + 20]!r}…")
    print(f"auditoria de publicação: {len(lista)} arquivos, {len(achados)} ocorrência(s)")
    for x in achados[:50]:
        print("  [FALHA]", x)
    if not achados:
        print("AUDITORIA APROVADA: nenhum dado pessoal, credencial ou arquivo sigiloso.")
    return 1 if achados else 0


if __name__ == "__main__":
    sys.exit(main())
