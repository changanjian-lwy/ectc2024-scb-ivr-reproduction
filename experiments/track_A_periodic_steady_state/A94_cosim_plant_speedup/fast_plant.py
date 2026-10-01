"""A94: a faster co-simulation plant with the same arithmetic as A88's Sim and the bridges' Plant (BOUNDARY.md).

FastSim subclasses A88's Sim (imported read-only; a88_transient.py is not modified) and overrides step() and
_nonlinear(); FastPlant is a copy of the bridges' Plant (A89-A93 test_cosim.py) with a faster _advance().

What changes is Python overhead only:
- scipy's lu_solve -> the same LAPACK getrs that lu_solve calls, with the same arrays (its finiteness check kept);
- EPC2067Coss.q -> the same operations, numpy's compiled interp called directly, np.where only when needed;
- vin_at / the source terms h*f memoised per (topology, times, values): the same expressions, evaluated once;
- per-switch V_DS from one vectorised subtraction (element-wise IEEE, identical to the scalar one);
- dict lookups and generator expressions removed.
Every BLAS call (the @ products, including the transposed view r.T) keeps its operands and layout.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from numpy._core.multiarray import interp as _cinterp
from scipy.linalg import get_lapack_funcs, lu_factor

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "A88_p24_predictive_low_side_turn_on"))
from a88_transient import Params, Sim, fit_fig8  # noqa: E402,F401  (re-exported for the bridges)


class FastSim(Sim):
    def __post_init__(self):
        super().__post_init__()
        n, nv = self.p.n, self.nv
        self.dsel = np.array([nv if d == "vin" else self.idx[d] for _, d, _ in self.switches])   # nv: vin slot
        self.ssel = np.array([nv + 1 if s is None else self.idx[s] for _, _, s in self.switches])  # nv+1: 0.0 slot
        self._yext = np.zeros(nv + 2)
        self._getrs = None
        self._term = {}                     # cache key -> (t, h, vin0, vin1, ld0, ld1, term)
        self._hfrev = {}
        if self.nl is not None:
            m = self.nl["model"]
            self._q = (m.vt, m.qt, m.v_max, m.q_end, m.c_end)
            self._nvin = {}

    # ---- element-wise identical helpers ----
    def vds_all(self, y, vin):
        """V_DS of every switch: vd - vs with vd = vin for SH1 and vs = 0.0 for the low sides (A88 Sim.vds)."""
        e = self._yext
        e[:self.nv] = y[:self.nv]
        e[self.nv] = vin
        return e[self.dsel] - e[self.ssel]

    def _solve(self, lu_piv, b):
        """scipy.linalg.lu_solve((lu, piv), b) for a 1-D float64 b: its finiteness check, then the same getrs."""
        lu, piv = lu_piv
        if not np.isfinite(b).all():
            raise ValueError("array must not contain infs or NaNs")
        if self._getrs is None:
            self._getrs, = get_lapack_funcs(("getrs",), (lu, b))
        x, info = self._getrs(lu, piv, b, trans=0, overwrite_b=False)
        if info != 0:
            raise ValueError(f"illegal value in {-info}th argument of internal gesv|posv")
        return x

    def _qf(self, v):
        """EPC2067Coss.q: sign(v) * interp(|v|) with the linear extension beyond v_max (identical operations)."""
        vt, qt, v_max, q_end, c_end = self._q
        a = np.abs(v)
        out = _cinterp(a, vt, qt, None, None)
        if (a > v_max).any():
            out = np.where(a > v_max, q_end + c_end * (a - v_max), out)
        return np.sign(v) * out

    # ---- A88 Sim.step with the same arithmetic ----
    def step(self, y, conducting, h, euler, t, load_on, donly=None, vin0=None, vin1=None):
        key = (conducting, h, euler, load_on, donly)
        entry = self.cache.get(key)
        if entry is None:
            A, fv, fl, frev = self.system(conducting, load_on, donly)
            if euler:
                lhs, rhs_m = self.M - h * A, self.M
            else:
                lhs, rhs_m = self.M - 0.5 * h * A, self.M + 0.5 * h * A
            entry = (lu_factor(lhs), rhs_m, fv, fl, lhs, frev if (donly is not None and any(donly)) else None)
            if h == self.p.h:
                self.cache[key] = entry
        lu, rhs_m, fv, fl, lhs, frev = entry
        p = self.p
        if vin1 is None:
            vin1 = p.vin_at(t + h)
        if vin0 is None:
            vin0 = p.vin_at(t)
        ld1 = p.load_at(t + h)
        if euler:
            ld0 = None
            tag = (vin1, ld1)
        else:
            ld0 = p.load_at(t)
            tag = (vin0, vin1, ld0, ld1)
        ck = (key, h, tag)
        term = self._term.get(ck)
        if term is None:
            f1 = fv * vin1 + fl * ld1
            if euler:
                term = h * f1
            else:
                f0 = fv * vin0 + fl * ld0
                term = 0.5 * h * (f0 + f1)
            if len(self._term) > 4096:                 # the input ramp gives new values every step
                self._term.clear()
            self._term[ck] = term
        rhs = rhs_m @ y + term
        if frev is not None:                                   # A87: the constant Vf sources
            hk = (key, h)
            hf = self._hfrev.get(hk)
            if hf is None:
                hf = self._hfrev[hk] = h * frev
            rhs = rhs + hf
        y1 = self._solve(entry[0], rhs)
        if self.nl is None:
            return y1
        return self._nonlinear(y, y1, entry[0], lhs, rhs, vin0, vin1)

    def _nvin_of(self, vin):
        out = self._nvin.get(vin)
        if out is None:
            if len(self._nvin) > 4096:
                self._nvin.clear()
            out = self._nvin[vin] = self.nl["vin"] * vin
        return out

    def _nonlinear(self, y0, y1, lu, lhs, rhs, vin0, vin1):
        """A86's chord iteration on the cached LU, identical arithmetic (A88 Sim._nonlinear)."""
        nl = self.nl; r, n, clin = nl["r"], nl["n"], nl["clin"]
        v0 = r @ y0 + self._nvin_of(vin0)
        q0 = n * self._qf(v0)
        st = nl["stats"]; st["steps"] += 1
        nv1 = self._nvin_of(vin1)
        for it in range(1, 9):
            v1 = r @ y1 + nv1
            corr = n * self._qf(v1) - q0 - clin * (v1 - v0)
            dz = self._solve(lu, lhs @ y1 - rhs + r.T @ corr)
            y1 = y1 - dz
            if np.abs(dz).max() < 1e-7:
                st["iters"] += it; st["max_iters"] = max(st["max_iters"], it)
                return y1
        st["newton"] += 1                                          # fallback: full Newton (A88, unchanged)
        m = nl["model"]
        for it in range(1, 31):
            v1 = r @ y1 + nl["vin"] * vin1
            corr = n * m.q(v1) - q0 - clin * (v1 - v0)
            jac = lhs + (r.T * (n * m.c(v1) - clin)) @ r
            dz = np.linalg.solve(jac, lhs @ y1 - rhs + r.T @ corr)
            y1 = y1 - dz
            if np.max(np.abs(dz)) < 1e-7:
                st["iters"] += 8 + it; st["max_iters"] = max(st["max_iters"], 8 + it)
                return y1
        raise RuntimeError("nonlinear Coss step did not converge")


class FastPlant:
    """The bridges' Plant (A89-A93) with the same interface and the same arithmetic; switch order SH1..SHN,
    SL1..SLN. The bridge may reset rev_e / rev_t and set load_on between windows."""

    def __init__(self, p, y0, gh, gl):
        self.load_on = False
        self._vmax = np.zeros(2 * p.n)
        self.ipk = 0.0
        self.p, self.sim, self.n = p, FastSim(p), p.n
        self.nv = self.sim.nv
        self.y = np.array(y0, dtype=float)
        self.t = 0.0
        self.gh, self.gl = list(gh), list(gl)
        self.diode = [False] * (2 * self.n)
        self.euler_left = 2
        self.steps = 0
        self.v_on = -p.rev_vf if p.rev_drop else 0                    # A89: reverse turn-on / cut threshold
        self.rev_e = [0.0] * (2 * self.n); self.rev_t = [0.0] * (2 * self.n)
        self.last_donly = [False] * (2 * self.n)
        self._vd = None; self._vd_t = None

    @property
    def vds_max(self):
        return self._vmax.tolist()

    def gates(self):
        return self.gh + self.gl

    def _vin(self, t):
        return self.p.vin_at(t)

    def vds(self, j):
        if self._vd_t != self.t or self._vd is None:
            self._vd = self.sim.vds_all(self.y, self._vin(self.t)); self._vd_t = self.t
        return self._vd[j]

    def _advance(self, h):
        """One step with A73's diode_check: a diode-only branch whose Vds ends > 0 is cut and the step redone."""
        n2, g = 2 * self.n, self.gh + self.gl
        d = list(self.diode)
        euler = self.euler_left > 0
        rev = self.p.rev_drop
        t0, t1 = self.t, self.t + h
        vin0, vin1 = self._vin(t0), self._vin(t1)
        for _ in range(n2 + 1):
            cond = tuple([bool(a or b) for a, b in zip(g, d)])
            donly = tuple([bool(b and not a) for a, b in zip(g, d)]) if rev else None
            y1 = self.sim.step(self.y, cond, h, euler, t0, self.load_on, donly, vin0, vin1)
            cand = [j for j in range(n2) if d[j] and not g[j]]
            if not cand:
                break
            vd1 = self.sim.vds_all(y1, vin1)
            bad = [j for j in cand if vd1[j] > self.v_on]
            if not bad:
                break
            for j in bad:
                d[j] = False
        if d != self.diode:
            self.diode = d
            self.euler_left = 2
        self.last_donly = list(donly) if donly is not None else [False] * n2
        self.y = y1
        self.t = t1
        self.euler_left = max(0, self.euler_left - 1)
        vd = self.sim.vds_all(self.y, vin1)
        self._vd, self._vd_t = vd, self.t
        if rev:                                                       # A89: reverse-conduction energy (A87)
            for j in range(n2):
                if self.last_donly[j]:
                    vj = vd[j]
                    isd = self.sim.nsw[j] * (-vj - self.p.rev_vf) / self.p.rev_r
                    if isd > 0:
                        self.rev_e[j] += -vj * isd * h; self.rev_t[j] += h
        np.maximum(self._vmax, vd, out=self._vmax)                    # peak Vds per switch
        self.ipk = max(self.ipk, float(np.abs(self.y[self.nv:]).max()))   # peak phase current
        below = (vd < self.v_on).tolist()
        new_d = [(not g[j]) and below[j] for j in range(n2)]
        if new_d != self.diode:
            self.diode = new_d
            self.euler_left = 2
        self.steps += 1

    def integrate_to(self, t_target, on_step):
        while self.t < t_target - 1e-18:
            self._advance(min(self.p.h, t_target - self.t))
            on_step()

    def set_gate(self, j, level):
        if j < self.n:
            self.gh[j] = bool(level)
        else:
            self.gl[j - self.n] = bool(level)
        self.euler_left = 2
