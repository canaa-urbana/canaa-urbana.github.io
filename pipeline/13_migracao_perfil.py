"""
E2 / Fase 2 passos 3-4 — perfil demográfico, migração de data fixa, perfil dos
migrantes e condições domiciliares, por censo (1991 proxy Parauapebas, 2000,
2010, 2022) e geografia (sede urbana, município, Parauapebas, Pará), com
erro-padrão por bootstrap de domicílios (`lib/estimacao.py`), CV e classe de
precisão — e com as regras de revelação de `disclosure_rules.py` aplicadas NO
MOMENTO da estimação (supressão primária R1, secundária/complementar R8 e
diferenciação sede×município R7), de modo que nenhuma célula abaixo do limiar
chega a ser gravada.

R7 é verificada de forma exata: para cada célula de uma sede, a MESMA célula é
recontada na área rural do município (município − sede) e precisa cumprir R1;
senão a célula entra na supressão do grupo como qualquer outra.

R8: as categorias suprimidas de um grupo viram uma única célula rotulada
`outros:<cat_a+cat_b+...>` (constituintes explícitos — o gate reconta a união)
ou, em dimensões abertas (municípios de origem), `outros` (complemento das
categorias publicadas).

Entrada: `data/interim/microdados/{pessoas,domicilios}_{censo}.parquet` (12_).
Saída:   `data/processed/microdados/estimativas.parquet` — tabela longa:
    censo, geografia, universo, estatistica (contagem | proporcao | media | mediana),
    variavel (só média/mediana), dim1, cat1, dim2, cat2, valor, ep, cv,
    classe_precisao, n_faixa, n_dom_faixa
  `data/processed/microdados/resumo_supressao.json` — células suprimidas por
    censo/geografia (auditoria, sem microdado).

Uso:
    .venv/bin/python pipeline/13_migracao_perfil.py [--censos 2010 2022] [--B 200]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "pipeline"))
import disclosure_rules as R  # noqa: E402
from lib import dimensoes as D  # noqa: E402
from lib.estimacao import Replicas  # noqa: E402

INTERIM = BASE / "data/interim/microdados"
OUT = BASE / "data/processed/microdados"
OUT.mkdir(parents=True, exist_ok=True)

TOP_ORIGEM_MUN = 30   # municípios de origem publicados nominalmente (o resto vira 'outros')


class Celula:
    __slots__ = ("mask", "n", "ndom", "mask_r")

    def __init__(self, mask, n, ndom, mask_r=None):
        self.mask, self.n, self.ndom, self.mask_r = mask, n, ndom, mask_r


class Recorte:
    """Um recorte geográfico (pessoas + domicílios) com contagem amostral de células."""

    def __init__(self, pessoas: pd.DataFrame, domicilios: pd.DataFrame):
        self.p, self.d = pessoas, domicilios
        self.ctrl = {"pessoas": pessoas["controle"].astype(str).to_numpy(),
                     "domicilios": domicilios["controle"].astype(str).to_numpy()}
        self.pess_por_dom = pessoas.groupby(pessoas["controle"].astype(str)).size()

    def df(self, nivel):
        return self.p if nivel == "pessoas" else self.d

    def n(self, nivel, mask) -> tuple[int, int]:
        ctrl = self.ctrl[nivel][mask]
        ndom = len(np.unique(ctrl))
        if nivel == "pessoas":
            return int(mask.sum()), ndom
        return int(self.pess_por_dom.reindex(ctrl).fillna(0).sum()), ndom


class Publicador:
    def __init__(self, censo: int, geografia: str, sede: Recorte, rural: Recorte | None, B: int):
        self.censo, self.geo = censo, geografia
        self.s, self.r = sede, rural
        self.rep = {"pessoas": Replicas(sede.p, B=B), "domicilios": Replicas(sede.d, B=B)}
        self.linhas: list[dict] = []
        self.supr = {"celulas": 0, "grupos_sem_detalhe": 0, "outros": 0, "r7": 0}

    # ---- utilidades -----------------------------------------------------------
    def _ok(self, n, ndom) -> bool:
        return R.cumpre_r1(self.censo, n, ndom)

    def _celula(self, nivel, mask, mask_r) -> Celula:
        n, nd = self.s.n(nivel, mask)
        return Celula(mask, n, nd, mask_r)

    def _publicavel(self, nivel, cel: Celula) -> bool:
        if not self._ok(cel.n, cel.ndom):
            return False
        if self.r is not None:
            nr, ndr = self.r.n(nivel, cel.mask_r)
            # zero estrutural na área rural (sede = município) não identifica ninguém
            if nr > 0 and not self._ok(nr, ndr):
                self.supr["r7"] += 1
                return False
        return True

    def _linha(self, universo, estatistica, dim1, cat1, dim2, cat2, valor, ep, n, ndom, variavel=None):
        cv = 100 * ep / valor if (valor and valor == valor and valor != 0) else float("nan")
        self.linhas.append(dict(
            censo=self.censo, geografia=self.geo, universo=universo, estatistica=estatistica,
            variavel=variavel, dim1=dim1, cat1=cat1, dim2=dim2, cat2=cat2,
            valor=valor, ep=ep, cv=cv, classe_precisao=R.classe_precisao(cv),
            n_faixa=R.faixa_n(n), n_dom_faixa=R.faixa_n(ndom),
        ))

    def _cats_de(self, dim, base_mask) -> list[str]:
        cats = D.DIMENSOES[dim]["cats"]
        if cats is not None:
            return cats
        nivel = D.nivel_universo(D.DIMENSOES[dim]["universo"])
        vals = self.s.df(nivel).loc[base_mask, D.DIMENSOES[dim]["col"]].dropna().astype(str)
        return vals.value_counts().index[:TOP_ORIGEM_MUN].tolist()

    def _mascaras(self, nivel, dim, base: Celula) -> tuple[dict[str, Celula], bool]:
        """Células de cada categoria de `dim` dentro da base (sede e rural)."""
        cats = self._cats_de(dim, base.mask)
        df_s = self.s.df(nivel)
        df_r = self.r.df(nivel) if self.r is not None else None
        out = {}
        for c in cats:
            m = base.mask & D.mascara_categoria(df_s, dim, c)
            mr = (base.mask_r & D.mascara_categoria(df_r, dim, c)) if df_r is not None else None
            out[c] = self._celula(nivel, m, mr)
        return out, D.DIMENSOES[dim]["cats"] is None

    # ---- supressão de um grupo de categorias -------------------------------------
    def _resolver_grupo(self, nivel, dim, base: Celula, cels: dict[str, Celula], aberta: bool) -> dict[str, Celula]:
        """Devolve as células publicáveis do grupo (rótulo -> Celula): categorias que
        cumprem R1 (e R7, se sede) e, havendo suprimidas, uma célula agregada
        'outros:<a+b+...>' (R8: ≥ 2 categorias e acima do limiar). Vazio = só total."""
        col = D.DIMENSOES[dim]["col"]
        # categorias sem nenhum registro na amostra (zero estrutural: ex. coorte
        # posterior ao censo) saem do grupo — não há o que proteger nem publicar
        cels = {c: cel for c, cel in cels.items() if cel.n > 0}
        S = {c for c, cel in cels.items() if not self._publicavel(nivel, cel)}
        restantes = sorted(set(cels) - S, key=lambda c: cels[c].n)

        def uniao(S) -> Celula:
            if aberta:   # complemento das publicadas dentro da base
                pub = [c for c in cels if c not in S]
                df = self.s.df(nivel)
                m = base.mask & df[col].notna().to_numpy() & ~df[col].astype("object").isin(pub).to_numpy()
                mr = None
                if self.r is not None:
                    dr = self.r.df(nivel)
                    mr = base.mask_r & dr[col].notna().to_numpy() & ~dr[col].astype("object").isin(pub).to_numpy()
            else:
                m = np.logical_or.reduce([cels[c].mask for c in S])
                mr = np.logical_or.reduce([cels[c].mask_r for c in S]) if self.r is not None else None
            return self._celula(nivel, m, mr)

        def uniao_ok(S):
            return not S or (len(S) >= 2 and self._publicavel(nivel, uniao(S)))

        def proximo(S):
            """Próxima categoria a fundir: vizinho ordinal ou parceiro de FUSAO de algum
            membro de S, se ainda disponível; senão a menor restante (ver lib.dimensoes)."""
            if dim in D.ORDINAIS:
                ordem = list(cels)
                viz = [c for m in S if m in ordem for c in (ordem[ordem.index(m) - 1: ordem.index(m)] + ordem[ordem.index(m) + 1: ordem.index(m) + 2])]
                viz = [c for c in viz if c in restantes]
                if viz:
                    return min(viz, key=lambda c: cels[c].n)
            for m in sorted(S, key=lambda c: cels[c].n):
                parc = D.FUSAO.get(dim, {}).get(m)
                if parc in restantes:
                    return parc
            return restantes[0]

        while restantes and not uniao_ok(S):
            S.add(restantes.pop(restantes.index(proximo(S))))
        if S and not uniao_ok(S):
            S = set(cels)
        if S:
            self.supr["celulas"] += len(S)
        out = {c: cels[c] for c in cels if c not in S}
        if not out:
            self.supr["grupos_sem_detalhe"] += 1
            return {}
        if S:
            self.supr["outros"] += 1
            out["outros" if aberta else "outros:" + "+".join(sorted(S))] = uniao(S)
        return out

    def _emitir(self, nivel, universo, dim1, cat1, dim2, base: Celula, cels: dict[str, Celula]):
        rep = self.rep[nivel]
        for c, i in cels.items():
            pos = (dim1, c, None, None) if dim2 is None else (dim1, cat1, dim2, c)
            est, ep = rep.total(i.mask)
            self._linha(universo, "contagem", *pos, R.arredondar(est), round(ep, 1), i.n, i.ndom)
            pr, epr = rep.proporcao(i.mask, base.mask)
            self._linha(universo, "proporcao", *pos, round(100 * pr, 2), round(100 * epr, 2), i.n, i.ndom)

    def _base_universo(self, universo) -> tuple[str, Celula]:
        nivel = D.nivel_universo(universo)
        m = D.mascara_universo(self.s.df(nivel), universo)
        mr = D.mascara_universo(self.r.df(nivel), universo) if self.r is not None else None
        return nivel, self._celula(nivel, m, mr)

    # ---- tabelas ------------------------------------------------------------------
    def rodar(self):
        bases = {}
        for universo in D.UNIVERSOS:
            nivel, base = self._base_universo(universo)
            if not self._publicavel(nivel, base):
                self.supr["celulas"] += 1
                continue
            bases[universo] = (nivel, base)
            est, ep = self.rep[nivel].total(base.mask)
            self._linha(universo, "contagem", None, None, None, None, R.arredondar(est), round(ep, 1), base.n, base.ndom)
        # 1 dimensão
        for dim in D.DIMENSOES:
            universo = D.DIMENSOES[dim]["universo"]
            if universo not in bases:
                continue
            nivel, base = bases[universo]
            cels, aberta = self._mascaras(nivel, dim, base)
            self._emitir(nivel, universo, dim, None, None, base, self._resolver_grupo(nivel, dim, base, cels, aberta))
        # 2 dimensões: as categorias de dim1 seguem a MESMA supressão de grupo das
        # tabelas de 1 dimensão (senão o total de uma categoria isolada vazaria)
        for dim1, dim2 in D.CRUZAMENTOS:
            universo = D.universo_cruzamento(dim1, dim2)
            if universo not in bases:
                continue
            nivel, base = bases[universo]
            cels1, aberta1 = self._mascaras(nivel, dim1, base)
            for c1, cel1 in self._resolver_grupo(nivel, dim1, base, cels1, aberta1).items():
                est, ep = self.rep[nivel].total(cel1.mask)
                self._linha(universo, "contagem", dim1, c1, None, None, R.arredondar(est), round(ep, 1), cel1.n, cel1.ndom)
                cels2, aberta2 = self._mascaras(nivel, dim2, cel1)
                self._emitir(nivel, universo, dim1, c1, dim2, cel1, self._resolver_grupo(nivel, dim2, cel1, cels2, aberta2))
        # médias e medianas
        for variavel, universo, dim in D.MEDIAS:
            if universo not in bases:
                continue
            nivel, base = bases[universo]
            df = self.s.df(nivel)
            if variavel not in df or df[variavel].notna().sum() == 0:
                continue
            ok_s = df[variavel].notna().to_numpy()
            ok_r = self.r.df(nivel)[variavel].notna().to_numpy() if self.r is not None else None
            base_v = self._celula(nivel, base.mask & ok_s, (base.mask_r & ok_r) if ok_r is not None else None)
            if not self._publicavel(nivel, base_v):
                continue
            if dim is None:
                grupos = {None: base_v}
            else:
                cels, aberta = self._mascaras(nivel, dim, base_v)
                grupos = self._resolver_grupo(nivel, dim, base_v, cels, aberta)
            for c, cel in grupos.items():
                est, ep = self.rep[nivel].media(cel.mask, df[variavel])
                self._linha(universo, "media", dim, c, None, None, round(est, 2), round(ep, 2), cel.n, cel.ndom, variavel)
                if variavel.startswith("renda"):
                    est, ep = self.rep[nivel].mediana(cel.mask, df[variavel])
                    self._linha(universo, "mediana", dim, c, None, None, round(est, 2), round(ep, 2), cel.n, cel.ndom, variavel)


def processar_censo(censo: int, B: int) -> tuple[pd.DataFrame, dict]:
    t0 = time.time()
    p = pd.read_parquet(INTERIM / f"pessoas_{censo}.parquet")
    d = pd.read_parquet(INTERIM / f"domicilios_{censo}.parquet")
    p, d = D.preparar(p, d)
    linhas, resumo = [], {}
    for geo, (mun, sit) in R.GEOGRAFIAS.items():
        if censo == 1991 and geo.startswith("canaa"):
            continue
        pm, dm = D.geografia_mascara(p, geo, R.GEOGRAFIAS), D.geografia_mascara(d, geo, R.GEOGRAFIAS)
        sede = Recorte(p[pm].reset_index(drop=True), d[dm].reset_index(drop=True))
        rural = None
        if sit == "urbana":   # R7: recorte rural = município − sede
            pr = (p["mun"] == mun) & (p["situacao"] != "urbana")
            dr = (d["mun"] == mun) & (d["situacao"] != "urbana")
            rural = Recorte(p[pr].reset_index(drop=True), d[dr].reset_index(drop=True))
        pub = Publicador(censo, geo, sede, rural, B=B)
        pub.rodar()
        linhas += pub.linhas
        resumo[geo] = {**pub.supr, "linhas": len(pub.linhas)}
        print(f"  {censo} {geo}: {len(pub.linhas):,} linhas publicadas; supressões {pub.supr} ({time.time() - t0:,.0f}s)")
    return pd.DataFrame(linhas), resumo


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--censos", nargs="*", type=int, default=R.CENSOS)
    ap.add_argument("--B", type=int, default=200)
    args = ap.parse_args()
    tabelas, resumo = [], {}
    for censo in args.censos:
        print(f"Censo {censo}")
        t, r = processar_censo(censo, args.B)
        tabelas.append(t)
        resumo[str(censo)] = r
    df = pd.concat(tabelas, ignore_index=True)
    for c in ["variavel", "dim1", "cat1", "dim2", "cat2"]:
        df[c] = df[c].astype("string")
    df.to_parquet(OUT / "estimativas.parquet", index=False)
    (OUT / "resumo_supressao.json").write_text(json.dumps(resumo, indent=1, ensure_ascii=False))
    print(f"\n{len(df):,} linhas em {OUT / 'estimativas.parquet'}")
