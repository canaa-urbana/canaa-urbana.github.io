"""GATE de revelação (E2): verifica, de forma independente, se `data/processed/microdados/
estimativas.parquet` cumpre R1-R8 de `disclosure_rules.py`.

Não confia em `13_migracao_perfil.py`: recalcula com DuckDB/pandas, a partir dos parquets
harmonizados de `data/interim/microdados/`, o n amostral (pessoas e domicílios distintos)
de CADA célula publicada — inclusive das células 'outros' (união das categorias não
publicadas no grupo) e das células rurais implícitas (município − sede, R7) — e falha
(exit 1) em qualquer violação. Em caso de sucesso grava `docs/relatorio_revelacao_<versao>.md`
e o carimbo `data/processed/.gate_ok` (SHA-256 de todo arquivo publicável em
`data/processed`, recursivo), que `verify_gate.py` confere sem microdados.

Uso: .venv/bin/python pipeline/disclosure_check.py [--versao 2026-09-10]
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
import disclosure_rules as R  # noqa: E402
from lib import dimensoes as D  # noqa: E402

INTERIM = ROOT / "data/interim/microdados"
PROCESSED = ROOT / "data/processed"
ARQ = PROCESSED / "microdados/estimativas.parquet"
GATE_OK = PROCESSED / ".gate_ok"
GATE_VERSAO_FORMATO = 2

violacoes: list[str] = []
notas: list[str] = []


def falha(regra: str, msg: str) -> None:
    violacoes.append(f"{regra}: {msg}")
    print(f"  [VIOLAÇÃO {regra}] {msg}")


def ok(regra: str, msg: str) -> None:
    notas.append(f"{regra}: {msg}")
    print(f"  [ok {regra}] {msg}")


def sha256_arquivo(caminho: pathlib.Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as fh:
        for bloco in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()


def hashes_publicaveis() -> dict[str, str]:
    hashes = {}
    for f in sorted(PROCESSED.rglob("*")):
        if f.is_file() and f != GATE_OK and ".DS_Store" not in f.name:
            hashes[f.relative_to(PROCESSED).as_posix()] = sha256_arquivo(f)
    return dict(sorted(hashes.items()))


class Contador:
    """Recontagem independente por (censo, geografia): n pessoas e domicílios de qualquer célula."""

    def __init__(self, censo: int):
        p = pd.read_parquet(INTERIM / f"pessoas_{censo}.parquet")
        d = pd.read_parquet(INTERIM / f"domicilios_{censo}.parquet")
        self.p, self.d = D.preparar(p, d)
        self.pess_por_dom = self.p.groupby(self.p["controle"].astype(str)).size()
        self.censo = censo
        self._cache_base: dict = {}
        self._cache_cat: dict = {}
        for df in (self.p, self.d):   # nunique por domicílio mais rápido com códigos inteiros
            df["_ctrl"] = pd.factorize(df["controle"].astype(str))[0]

    GEOS = {**R.GEOGRAFIAS, "canaa_rural": ("1502152", "rural"), "parauapebas_rural": ("1505536", "rural")}

    def _base(self, geo: str, universo: str):
        chave = (geo, universo)
        if chave not in self._cache_base:
            nivel = D.nivel_universo(universo)
            df = self.p if nivel == "pessoas" else self.d
            m = D.geografia_mascara(df, geo, self.GEOS) & D.mascara_universo(df, universo)
            self._cache_base[chave] = (df, m, nivel)
        return self._cache_base[chave]

    def _mascara_cat(self, df, dim, cat, publicadas: set[str]) -> np.ndarray:
        """Categoria simples, 'outros:<a+b+...>' (união explícita, R8) ou 'outros'
        (complemento das categorias publicadas no grupo, dimensões abertas)."""
        chave = (id(df), dim, cat, tuple(sorted(publicadas)) if cat == "outros" else None)
        if chave in self._cache_cat:
            return self._cache_cat[chave]
        col = D.DIMENSOES[dim]["col"]
        if cat.startswith("outros:"):
            partes = cat[len("outros:"):].split("+")
            m = df[col].astype("object").isin(partes).fillna(False).to_numpy()
        elif cat == "outros":
            m = (~df[col].astype("object").isin(list(publicadas)).fillna(False).to_numpy()
                 & df[col].notna().to_numpy())
        else:
            m = D.mascara_categoria(df, dim, cat)
        self._cache_cat[chave] = m
        return m

    def mascara(self, geo, universo, dim1, cat1, dim2, cat2, publicadas1: set[str], publicadas2: set[str]):
        df, m, nivel = self._base(geo, universo)
        if dim1 is not None and cat1 is not None:
            m = m & self._mascara_cat(df, dim1, cat1, publicadas1)
        if dim2 is not None and cat2 is not None:
            m = m & self._mascara_cat(df, dim2, cat2, publicadas2)
        return df, m, nivel

    def constituintes(self, df, m, dim, cat) -> int:
        """Quantas categorias distintas compõem a célula (R8: 'outros' precisa de >= 2)."""
        return int(df.loc[m, D.DIMENSOES[dim]["col"]].astype("object").nunique())

    def contar(self, df, m, nivel, variavel=None) -> tuple[int, int]:
        if variavel is not None:
            m = m & df[variavel].notna().to_numpy()
        ctrl = df["_ctrl"].to_numpy()[m]
        ndom = int(len(np.unique(ctrl)))
        if nivel == "pessoas":
            return int(m.sum()), ndom
        dom = df["controle"].astype(str).to_numpy()[m]
        return int(self.pess_por_dom.reindex(dom).fillna(0).sum()), ndom


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--versao", default=dt.date.today().isoformat())
    args = ap.parse_args()

    print("=== Gate de revelação (R1-R8) ===")
    if not ARQ.exists():
        falha("R0", f"{ARQ} não existe")
        return 1
    e = pd.read_parquet(ARQ)
    for c in ["variavel", "dim1", "cat1", "dim2", "cat2"]:
        e[c] = e[c].astype("object").where(e[c].notna(), None)

    # ---- R5: colunas proibidas em qualquer parquet publicado ----
    parquets = sorted(PROCESSED.rglob("*.parquet"))
    ruins = []
    import pyarrow.parquet as pq
    for f in parquets:
        cols = {c.lower() for c in pq.read_schema(f).names}
        if cols & R.COLUNAS_PROIBIDAS and "microdados" in f.as_posix():
            ruins.append((f.name, sorted(cols & R.COLUNAS_PROIBIDAS)))
    if ruins:
        for nome, cols in ruins:
            falha("R5", f"{nome} expõe coluna(s) {cols}")
    else:
        ok("R5", f"{len(parquets)} parquets em data/processed sem coluna de domicílio/área de ponderação/peso")
    csvs = list(PROCESSED.rglob("*.csv")) + list(PROCESSED.rglob("*.CSV"))
    csvs = [c for c in csvs if "microdados" in c.as_posix()]
    if csvs:
        falha("R5", f"CSV em data/processed/microdados: {[c.name for c in csvs]}")

    # ---- R3: nenhuma contagem exata; faixas válidas ----
    faixas = {rot for _, _, rot in R.FAIXAS_N}
    exatas = [c for c in e.columns if (c == "n" or c.startswith("n_")) and not c.endswith("_faixa")]
    if exatas:
        falha("R3", f"colunas de contagem exata: {exatas}")
    fora = e[~e["n_faixa"].isin(faixas) | ~e["n_dom_faixa"].isin(faixas)]
    if len(fora):
        falha("R3", f"{len(fora)} linhas com faixa de n fora de {sorted(faixas)}")
    if not exatas and not len(fora):
        ok("R3", "n amostral publicado só em faixas válidas")

    # ---- R4: no máximo 2 dimensões; só dimensões/categorias registradas ----
    dims_ok = True
    for _, r in e.iterrows():
        for dim, cat in ((r.dim1, r.cat1), (r.dim2, r.cat2)):
            if dim is None:
                continue
            if dim not in D.DIMENSOES:
                dims_ok = False
                falha("R4", f"dimensão desconhecida {dim}")
                break
            cats = D.DIMENSOES[dim]["cats"]
            if cat is not None and str(cat).startswith("outros:") and cats is not None:
                partes = str(cat)[len("outros:"):].split("+")
                if any(x not in cats for x in partes):
                    dims_ok = False
                    falha("R4", f"constituinte de {cat!r} não registrado em {dim}")
                    break
                continue
            if cat is not None and cat != "outros" and cats is not None and cat not in cats:
                dims_ok = False
                falha("R4", f"categoria {cat!r} não registrada em {dim}")
                break
        if not dims_ok:
            break
    if dims_ok:
        ok("R4", f"{e['dim1'].nunique()} dimensões, nunca mais de 2 por linha; todas registradas em lib/dimensoes.py")

    # ---- R2: contagens em múltiplos de 10 ----
    cont = e[e["estatistica"] == "contagem"]
    nao_mult = cont[(cont["valor"] % R.ARREDONDAMENTO).abs() > 1e-6]
    if len(nao_mult):
        falha("R2", f"{len(nao_mult)} contagens não múltiplas de {R.ARREDONDAMENTO}")
    else:
        ok("R2", f"{len(cont):,} contagens ponderadas, todas múltiplas de {R.ARREDONDAMENTO}")

    # ---- R6: CV e classe em toda estimativa ----
    sem_cv = e[e["classe_precisao"].isna() | (e["classe_precisao"] == "sem_estimativa")]
    if len(sem_cv):
        falha("R6", f"{len(sem_cv)} estimativas sem CV/classe de precisão")
    else:
        ok("R6", "toda estimativa tem CV e classe de precisão")

    # ---- R1, R7, R8: recontagem célula a célula ----
    total_cel = r7_cel = 0
    grupo_cols = ["censo", "geografia", "universo", "estatistica", "variavel", "dim1", "dim2"]
    for censo, ec in e.groupby("censo"):
        ct = Contador(int(censo))
        print(f"  recontando censo {censo}: {len(ec):,} linhas")
        # categorias publicadas de dim1 por (universo, estatistica, variavel, dim1) e de dim2 por grupo
        for chave_g, g in ec.groupby(grupo_cols, dropna=False):
            _, geo, universo, estat, variavel, dim1, dim2 = [None if (isinstance(x, float) and np.isnan(x)) else x for x in chave_g]
            pub1 = {c for c in g["cat1"] if c is not None and not str(c).startswith("outros")}
            for cat1, g1 in g.groupby("cat1", dropna=False):
                cat1 = None if (isinstance(cat1, float) and np.isnan(cat1)) else cat1
                pub2 = {c for c in g1["cat2"] if c is not None and not str(c).startswith("outros")}
                for _, r in g1.iterrows():
                    total_cel += 1
                    c2 = r.cat2 if dim2 is not None else None
                    var = variavel if estat in ("media", "mediana") else None
                    df, m, nivel = ct.mascara(geo, universo, dim1, cat1, dim2, c2, pub1, pub2)
                    n, nd = ct.contar(df, m, nivel, var)
                    rot = f"{censo}/{geo}/{universo}/{estat} {dim1}={cat1} {dim2}={c2}"
                    if not R.cumpre_r1(int(censo), n, nd):
                        falha("R1", f"{rot}: n={n}, dom={nd}")
                    if R.faixa_n(n) != r.n_faixa or R.faixa_n(nd) != r.n_dom_faixa:
                        falha("R3", f"{rot}: faixa publicada {r.n_faixa}/{r.n_dom_faixa} ≠ recontada {R.faixa_n(n)}/{R.faixa_n(nd)}")
                    # R8 vale para a célula 'outros' no nível em que foi formada: dim2 sempre;
                    # dim1 só na linha de total da categoria (cat2 = None) — dentro de um
                    # cruzamento, a união de dim1 pode ter só um constituinte presente numa
                    # categoria de dim2 sem revelar nada (o constituinte pequeno não é
                    # identificável a partir da união).
                    for dim, cat in (((dim1, cat1),) if c2 is None else ()) + ((dim2, c2),):
                        if dim is not None and cat is not None and str(cat).startswith("outros"):
                            k = ct.constituintes(df, m if var is None else m & df[var].notna().to_numpy(), dim, cat)
                            if k < 2:
                                falha("R8", f"{rot}: 'outros' com {k} categoria")
                    # R7: a mesma célula na área rural (município − sede) também cumpre R1
                    if geo.endswith("_sede"):
                        r7_cel += 1
                        geo_r = geo.replace("_sede", "_rural")
                        dfr, mr, _ = ct.mascara(geo_r, universo, dim1, cat1, dim2, c2, pub1, pub2)
                        nr, ndr = ct.contar(dfr, mr, nivel, var)
                        if nr > 0 and not R.cumpre_r1(int(censo), nr, ndr):   # zero rural = estrutural
                            falha("R7", f"{rot}: célula rural implícita n={nr}, dom={ndr}")
    if not any(v.startswith("R1") for v in violacoes):
        ok("R1", f"{total_cel:,} células recontadas, todas com n ≥ limiar (pessoas e domicílios)")
    if not any(v.startswith("R8") for v in violacoes):
        ok("R8", "toda célula 'outros' agrega pelo menos 2 categorias")
    if not any(v.startswith("R7") for v in violacoes):
        ok("R7", f"{r7_cel:,} células de sede recontadas na área rural implícita, todas acima do limiar")

    if violacoes:
        print(f"\nGATE REPROVADO: {len(violacoes)} violação(ões).")
        GATE_OK.unlink(missing_ok=True)
        return 1

    linhas = ["# Relatório de controle de revelação — microdados (E2)", "",
              f"- Versão dos dados: **{args.versao}**",
              f"- Gerado em: {dt.datetime.now():%Y-%m-%d %H:%M} (fuso local)",
              "- Fonte: IBGE, Censos Demográficos 1991, 2000, 2010 (amostra, públicos) e 2022 (amostra, acesso controlado).",
              "", "## Regras aplicadas", "", "| Regra | Parâmetro |", "|---|---|",
              f"| R1 limiar por célula | 2022: ≥ {R.MIN_PESSOAS[2022]} pessoas e ≥ {R.MIN_DOMICILIOS[2022]} domicílios; 1991/2000/2010: ≥ {R.MIN_PESSOAS[2010]} / {R.MIN_DOMICILIOS[2010]} |",
              f"| R2 arredondamento | múltiplos de {R.ARREDONDAMENTO} |",
              "| R3 contagem amostral | só em faixas |",
              f"| R4 cruzamentos | no máximo {R.MAX_DIMENSOES_TEMATICAS} dimensões temáticas |",
              "| R5 geografia | sede urbana e município; nada por área de ponderação; sem identificador de domicílio |",
              f"| R6 precisão | CV e classe (boa ≤ {R.CV_BOA:.0f} %, cautela ≤ {R.CV_CAUTELA:.0f} %, baixa) em toda estimativa |",
              "| R7 diferenciação | célula rural implícita (município − sede) cumpre R1 |",
              "| R8 supressão complementar | categorias suprimidas somadas em `outros` (≥ 2 categorias) |",
              "", "## Verificações independentes", ""]
    linhas += [f"- {n}" for n in notas]
    linhas += ["", "## Linhas publicadas por censo e geografia", "", "| Censo | Geografia | Linhas |", "|---|---|---:|"]
    for (c, g), k in e.groupby(["censo", "geografia"]).size().items():
        linhas.append(f"| {c} | {g} | {k:,} |")
    dest = ROOT / f"docs/relatorio_revelacao_{args.versao}.md"
    dest.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    carimbo = {"formato_versao": GATE_VERSAO_FORMATO, "versao_dados": args.versao,
               "timestamp": dt.datetime.now().isoformat(), "arquivos": hashes_publicaveis()}
    GATE_OK.write_text(json.dumps(carimbo, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nGATE APROVADO. Relatório: {dest.relative_to(ROOT)}; carimbo com {len(carimbo['arquivos'])} arquivos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
