#!/usr/bin/env python3
"""Verifica o carimbo do gate de revelação (`data/processed/.gate_ok`) SEM acesso a microdados.

Complementa `disclosure_check.py` (que reconta células a partir de `data/interim/microdados/`
e só roda na máquina com os microdados): este script roda em qualquer clone do repositório
— inclusive no CI — porque só lê `data/processed` e o carimbo.

Checagens:
  (a) `.gate_ok` existe e tem o formato esperado (formato_versao 2, E2);
  (b) o SHA-256 de cada arquivo publicável em `data/processed` (recursivo) bate com o
      carimbo — nada mudou, nada sumiu, nada foi adicionado depois do gate;
  (c) estruturais, sem microdado, em `data/processed/microdados/*.parquet`:
      - nenhum CSV;
      - nenhuma coluna de `disclosure_rules.COLUNAS_PROIBIDAS` (identificador de domicílio,
        área de ponderação, peso);
      - nenhuma coluna de contagem amostral exata (`n`, `n_*` sem sufixo `_faixa`) e só faixas
        válidas em `n_faixa` / `n_dom_faixa`;
      - contagens ponderadas (`estatistica == 'contagem'`) múltiplas de `ARREDONDAMENTO`;
      - no máximo 2 dimensões por linha (colunas dim1/dim2), e toda estimativa com classe de
        precisão.
  Os demais diretórios de `data/processed` (ibge/, setores/, geo/) contêm agregados públicos
  do IBGE e produtos de sensoriamento remoto — entram só na checagem de integridade (b).

Uso: python pipeline/verify_gate.py [--dir data/processed] [--clone]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

import pyarrow.parquet as pq

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
import disclosure_rules as R  # noqa: E402

COLUNAS_PROIBIDAS = {c.lower() for c in R.COLUNAS_PROIBIDAS}
IGNORADOS_GIT = {".csv", ".tif", ".tiff", ".txt"}  # espelha o .gitignore (modo --clone)
FAIXAS_VALIDAS = {rot for _, _, rot in R.FAIXAS_N}


def sha256_arquivo(caminho: pathlib.Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as fh:
        for bloco in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()


class Verificador:
    def __init__(self, processed: pathlib.Path, clone: bool = False):
        self.processed = processed
        self.clone = clone
        self.gate_ok = processed / ".gate_ok"
        self.erros: list[str] = []

    def falha(self, msg: str) -> None:
        self.erros.append(msg)
        print(f"  [FALHA] {msg}")

    def ok(self, msg: str) -> None:
        print(f"  [ok] {msg}")

    def arquivos_atuais(self) -> dict[str, pathlib.Path]:
        return {f.relative_to(self.processed).as_posix(): f
                for f in sorted(self.processed.rglob("*"))
                if f.is_file() and f != self.gate_ok and ".DS_Store" not in f.name}

    def verificar_carimbo(self) -> dict | None:
        print("=== (a) Carimbo do gate ===")
        if not self.gate_ok.exists():
            self.falha(f"{self.gate_ok} não existe -- rode pipeline/disclosure_check.py")
            return None
        try:
            carimbo = json.loads(self.gate_ok.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            self.falha(f"{self.gate_ok} não é um JSON válido: {e}")
            return None
        faltando = {"formato_versao", "versao_dados", "timestamp", "arquivos"} - carimbo.keys()
        if faltando:
            self.falha(f"carimbo sem os campos obrigatórios: {sorted(faltando)}")
            return None
        if not isinstance(carimbo["arquivos"], dict) or not carimbo["arquivos"]:
            self.falha("carimbo não lista nenhum arquivo")
            return None
        self.ok(f"carimbo válido -- versão dos dados {carimbo['versao_dados']!r}, gerado em "
                f"{carimbo['timestamp']}, {len(carimbo['arquivos'])} arquivos registrados")
        return carimbo

    def verificar_hashes(self, carimbo: dict) -> None:
        print("=== (b) Integridade dos arquivos publicados (SHA-256) ===")
        registrados: dict[str, str] = carimbo["arquivos"]
        atuais = self.arquivos_atuais()
        faltando = sorted(set(registrados) - set(atuais))
        extras = sorted(set(atuais) - set(registrados))
        diferentes = [rel for rel in sorted(set(registrados) & set(atuais))
                      if sha256_arquivo(atuais[rel]) != registrados[rel]]
        if faltando and self.clone:
            # num clone do repositório os tipos ignorados pelo .gitignore (CSV espelho dos parquets,
            # rasters TIF) não existem: não foram publicados, então não há o que conferir
            nao_versionados = [f for f in faltando if pathlib.Path(f).suffix.lower() in IGNORADOS_GIT]
            if nao_versionados:
                self.ok(f"{len(nao_versionados)} arquivo(s) do carimbo não versionados (CSV/TIF, ignorados pelo git) — fora do clone")
            faltando = [f for f in faltando if f not in nao_versionados]
        if faltando:
            self.falha(f"{len(faltando)} arquivo(s) do carimbo não existem mais: {faltando}")
        if extras:
            self.falha(f"{len(extras)} arquivo(s) fora do carimbo (adicionados depois do gate): {extras}")
        if diferentes:
            self.falha(f"{len(diferentes)} arquivo(s) alterados depois do gate: {diferentes}")
        if not (faltando or extras or diferentes):
            self.ok(f"{len(registrados)} arquivos conferem exatamente com o carimbo")

    def verificar_estrutura(self) -> None:
        print("=== (c) Estrutura de data/processed/microdados ===")
        md = self.processed / "microdados"
        csvs = list(md.rglob("*.csv")) + list(md.rglob("*.CSV"))
        if csvs:
            self.falha(f"CSV em microdados/: {[c.name for c in csvs]}")
        else:
            self.ok("nenhum *.csv em microdados/")
        for f in sorted(md.rglob("*.parquet")):
            rel = f.relative_to(self.processed).as_posix()
            tab = pq.read_table(f)
            cols = list(tab.column_names)
            low = {c.lower() for c in cols}
            proib = low & COLUNAS_PROIBIDAS
            if proib:
                self.falha(f"{rel}: coluna(s) proibida(s) {sorted(proib)}")
            exatas = [c for c in low if (c == "n" or c.startswith("n_")) and not c.endswith("_faixa")]
            if exatas:
                self.falha(f"{rel}: contagem amostral exata em {exatas}")
            df = tab.to_pandas()
            for c in [c for c in cols if c.endswith("_faixa")]:
                fora = int((~df[c].isin(FAIXAS_VALIDAS)).sum())
                if fora:
                    self.falha(f"{rel}.{c}: {fora} valores fora das faixas {sorted(FAIXAS_VALIDAS)}")
            if {"estatistica", "valor"} <= set(cols):
                cont = df[df["estatistica"] == "contagem"]
                ruim = int(((cont["valor"] % R.ARREDONDAMENTO).abs() > 1e-6).sum())
                if ruim:
                    self.falha(f"{rel}: {ruim} contagens não múltiplas de {R.ARREDONDAMENTO}")
                else:
                    self.ok(f"{rel}: {len(cont):,} contagens múltiplas de {R.ARREDONDAMENTO}")
            if "dim3" in low:
                self.falha(f"{rel}: coluna dim3 (mais de {R.MAX_DIMENSOES_TEMATICAS} dimensões)")
            if "classe_precisao" in cols:
                sem = int((df["classe_precisao"].isna() | (df["classe_precisao"] == "sem_estimativa")).sum())
                if sem:
                    self.falha(f"{rel}: {sem} estimativas sem classe de precisão")
            if not proib and not exatas:
                self.ok(f"{rel}: {len(df):,} linhas, sem coluna proibida nem contagem exata")

    def rodar(self) -> int:
        carimbo = self.verificar_carimbo()
        if carimbo:
            self.verificar_hashes(carimbo)
        self.verificar_estrutura()
        if self.erros:
            print(f"\nVERIFICAÇÃO REPROVADA: {len(self.erros)} falha(s).")
            return 1
        print("\nVERIFICAÇÃO APROVADA: data/processed íntegro e conforme o carimbo do gate.")
        return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(ROOT / "data/processed"))
    ap.add_argument("--clone", action="store_true",
                    help="CI: aceita a ausência dos tipos ignorados pelo git (CSV, TIF) — não publicados")
    args = ap.parse_args()
    raise SystemExit(Verificador(pathlib.Path(args.dir), clone=args.clone).rodar())
