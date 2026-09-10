"""
Estimação ponderada com erro-padrão por bootstrap de domicílios — E2 (Fase 2 passo 3).

Por que bootstrap de domicílios e não réplicas por área de ponderação: Canaã tem
UMA área de ponderação em 2000 e 2010 (o município inteiro) e cinco em 2022; a
unidade primária de seleção da amostra do Censo é o DOMICÍLIO dentro do setor.
Reamostrar domicílios com reposição (estratificado por área de ponderação quando
ela existe, Rao-Wu com multiplicadores multinomiais) reproduz a estrutura de
conglomerado da amostra — pessoas do mesmo domicílio são correlacionadas — e dá
um erro-padrão conservador para totais, proporções e médias. As réplicas são
geradas uma vez por (censo, geografia) e reutilizadas em todas as células.

Uso:
    rep = Replicas(df, col_peso="peso", col_controle="controle", col_estrato="ap", B=200)
    est, ep = rep.total(mask)
    est, ep = rep.proporcao(mask_num, mask_den)
    est, ep = rep.media(mask, df["renda_total_r2022"])
"""
from __future__ import annotations

import numpy as np
import pandas as pd


class Replicas:
    def __init__(self, df: pd.DataFrame, col_peso: str = "peso", col_controle: str = "controle",
                 col_estrato: str | None = "ap", B: int = 200, seed: int = 20260910):
        self.n = len(df)
        self.w = df[col_peso].to_numpy(dtype="float64")
        codes, uniques = pd.factorize(df[col_controle].astype(str), sort=False)
        self.h = codes
        self.H = len(uniques)
        self.B = B
        rng = np.random.default_rng(seed)
        # estrato de cada domicílio (área de ponderação); sem estrato = um só
        if col_estrato and col_estrato in df and df[col_estrato].notna().any():
            estr = pd.factorize(df[col_estrato].astype(str).fillna("_"))[0]
        else:
            estr = np.zeros(self.n, dtype=int)
        estrato_dom = np.zeros(self.H, dtype=int)
        estrato_dom[self.h] = estr
        M = np.zeros((self.H, B), dtype="float32")
        for e in np.unique(estrato_dom):
            idx = np.flatnonzero(estrato_dom == e)
            k = len(idx)
            if k == 1:
                M[idx, :] = 1.0
                continue
            # Rao-Wu: reamostra k-1 domicílios com reposição e reescala por k/(k-1)
            counts = rng.multinomial(k - 1, np.full(k, 1.0 / k), size=B).T  # k x B
            M[idx, :] = counts * (k / (k - 1))
        self.M = M

    def _soma_dom(self, mask: np.ndarray, y: np.ndarray | None = None) -> np.ndarray:
        wy = self.w if y is None else self.w * y
        return np.bincount(self.h[mask], weights=wy[mask], minlength=self.H)

    def total(self, mask) -> tuple[float, float]:
        mask = np.asarray(mask, dtype=bool)
        hh = self._soma_dom(mask)
        est = float(hh.sum())
        reps = hh @ self.M
        return est, float(reps.std(ddof=1))

    def proporcao(self, mask_num, mask_den) -> tuple[float, float]:
        mask_num, mask_den = np.asarray(mask_num, dtype=bool), np.asarray(mask_den, dtype=bool)
        hn, hd = self._soma_dom(mask_num & mask_den), self._soma_dom(mask_den)
        den = hd.sum()
        if den <= 0:
            return float("nan"), float("nan")
        est = float(hn.sum() / den)
        rn, rd = hn @ self.M, hd @ self.M
        with np.errstate(invalid="ignore", divide="ignore"):
            reps = np.where(rd > 0, rn / rd, np.nan)
        return est, float(np.nanstd(reps, ddof=1))

    def media(self, mask, y: pd.Series) -> tuple[float, float]:
        yv = pd.to_numeric(y, errors="coerce").to_numpy(dtype="float64")
        mask = np.asarray(mask, dtype=bool) & ~np.isnan(yv)
        yv = np.nan_to_num(yv)
        hn, hd = self._soma_dom(mask, yv), self._soma_dom(mask)
        den = hd.sum()
        if den <= 0:
            return float("nan"), float("nan")
        est = float(hn.sum() / den)
        rn, rd = hn @ self.M, hd @ self.M
        with np.errstate(invalid="ignore", divide="ignore"):
            reps = np.where(rd > 0, rn / rd, np.nan)
        return est, float(np.nanstd(reps, ddof=1))

    def mediana(self, mask, y: pd.Series) -> tuple[float, float]:
        """Mediana ponderada e EP por bootstrap (só nas réplicas, mais caro: usa
        no máximo 60 réplicas)."""
        yv = pd.to_numeric(y, errors="coerce").to_numpy(dtype="float64")
        mask = np.asarray(mask, dtype=bool) & ~np.isnan(yv)
        idx = np.flatnonzero(mask)
        if len(idx) == 0:
            return float("nan"), float("nan")
        ordem = idx[np.argsort(yv[idx])]
        ys = yv[ordem]

        def _med(w):
            cw = np.cumsum(w)
            if cw[-1] <= 0:
                return np.nan
            return ys[np.searchsorted(cw, 0.5 * cw[-1])]

        est = float(_med(self.w[ordem]))
        reps = [_med(self.w[ordem] * self.M[self.h[ordem], b]) for b in range(min(self.B, 60))]
        return est, float(np.nanstd(reps, ddof=1))

    def n_amostral(self, mask) -> tuple[int, int]:
        """(pessoas/registros amostrais, domicílios distintos) na célula."""
        mask = np.asarray(mask, dtype=bool)
        return int(mask.sum()), int(len(np.unique(self.h[mask])))
