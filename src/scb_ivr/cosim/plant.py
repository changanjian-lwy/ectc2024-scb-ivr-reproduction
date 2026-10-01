"""Co-simulation plants with one interface (y, t, gh, gl, diode, vds(j), integrate_to, set_gate, rev_e/rev_t,
vds_max, ipk, steps, sim): the bridge selects one by cfg "plant_impl".

- ReferencePlant: circuit.Sim stepped in Python, as in the bridges A89-A93.
- FastPlant (A94): the same arithmetic without the Python overhead (scipy's getrs called directly, memoised source
  terms, vectorised V_DS); every BLAS product unchanged.
- KernelPlant (A95, the default): FastPlant with each step's solve and chord iteration in plant_kernel.c (one C call;
  Accelerate's dgemv/dgetrs with numpy's arguments, numpy's FMA in interp, no other contraction); a chord that does
  not converge in 8 iterations is redone by FastSim in Python (full-Newton fallback).
All three give bit-identical results on this machine (gates: A94, A95, scripts/cosim_regression.py).
"""
from __future__ import annotations

import ctypes
import hashlib
import os
import subprocess
import tempfile

import numpy as np
from numpy._core.multiarray import interp as _cinterp
from scipy.linalg import get_lapack_funcs, lu_factor

from pathlib import Path

from .circuit import PROJECT, Sim

class ReferencePlant:
    """The plant as the bridges A89-A93 stepped it (circuit.Sim, one Python step at a time); the reference for the
    equivalence gates. Switch order: SH1..SHN, SL1..SLN."""

    def __init__(self, p, y0, gh, gl):
        self.load_on = False
        self.vds_max = [0.0] * (2 * p.n)
        self.ipk = 0.0
        self.p, self.sim, self.n = p, Sim(p), p.n
        self.nv = self.sim.nv
        self.y = np.array(y0, dtype=float)
        self.t = 0.0
        self.gh, self.gl = list(gh), list(gl)
        self.diode = [False] * (2 * self.n)
        self.euler_left = 2
        self.steps = 0
        self.v_on = -p.rev_vf if p.rev_drop else 0                    # A89: reverse turn-on / cut threshold
        self.rev_e = [0.0] * (2 * self.n); self.rev_t = [0.0] * (2 * self.n)   # A89: since the last section
        self.last_donly = [False] * (2 * self.n)

    def gates(self):
        return self.gh + self.gl

    def vds(self, j):
        return self.sim.vds(self.y, j, self.p.vin_at(self.t))

    def _advance(self, h):
        """One step with A73's diode_check: a diode-only branch whose Vds ends > 0 is cut and the step redone."""
        n, g = self.n, self.gates()
        d = list(self.diode)
        euler = self.euler_left > 0
        for _ in range(2 * n + 1):
            cond = tuple(bool(a or b) for a, b in zip(g, d))
            donly = tuple(bool(b and not a) for a, b in zip(g, d)) if self.p.rev_drop else None   # A89
            y1 = self.sim.step(self.y, cond, h, euler, self.t, self.load_on, donly)
            vin1 = self.p.vin_at(self.t + h)
            bad = [j for j in range(2 * n) if d[j] and not g[j] and self.sim.vds(y1, j, vin1) > self.v_on]
            if not bad:
                break
            for j in bad:
                d[j] = False
        if d != self.diode:
            self.diode = d
            self.euler_left = 2
        self.last_donly = list(donly) if donly is not None else [False] * (2 * n)
        self.y = y1
        self.t += h
        self.euler_left = max(0, self.euler_left - 1)
        vd = [self.sim.vds(self.y, j, self.p.vin_at(self.t)) for j in range(2 * n)]
        if self.p.rev_drop:                                          # A89: reverse-conduction energy (A87)
            for j in range(2 * n):
                if self.last_donly[j]:
                    isd = self.sim.nsw[j] * (-vd[j] - self.p.rev_vf) / self.p.rev_r
                    if isd > 0:
                        self.rev_e[j] += -vd[j] * isd * h; self.rev_t[j] += h
        self.vds_max = [max(a, b) for a, b in zip(self.vds_max, vd)]          # peak Vds per switch
        self.ipk = max(self.ipk, float(np.max(np.abs(self.y[self.nv:]))))     # peak phase current
        new_d = [(not g[j]) and vd[j] < self.v_on for j in range(2 * n)]
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


SRC = Path(__file__).resolve().parent / "plant_kernel.c"
BUILD = PROJECT / "tmp" / "cosim_kernel"
CFLAGS = ["-O2", "-ffp-contract=off", "-fno-fast-math", "-shared", "-fPIC"]


def _load():
    """Build plant_kernel.c once per source and flags (content-addressed, atomic rename), then load it."""
    tag = hashlib.sha256(SRC.read_bytes() + " ".join(CFLAGS).encode()).hexdigest()[:16]
    path = BUILD / f"plant_kernel-{tag}.so"
    if not path.exists():
        BUILD.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(suffix=".so", dir=BUILD)
        os.close(fd)
        subprocess.run(["cc", *CFLAGS, "-o", tmp, str(SRC), "-framework", "Accelerate"], check=True)
        os.replace(tmp, path)
    lib = ctypes.CDLL(str(path))
    vp, d, i = ctypes.c_void_p, ctypes.c_double, ctypes.c_int
    lib.pk_step.argtypes = [vp, vp, vp, vp, d, i, d, d, d, d, ctypes.POINTER(i)]
    lib.pk_step.restype = i
    return lib


class _Ctx(ctypes.Structure):
    _fields_ = [("n", ctypes.c_int), ("m", ctypes.c_int), ("nonlinear", ctypes.c_int),
                ("r", ctypes.c_void_p), ("vinf", ctypes.c_void_p), ("nper", ctypes.c_void_p), ("clin", ctypes.c_void_p),
                ("vt", ctypes.c_void_p), ("qt", ctypes.c_void_p), ("nt", ctypes.c_int64),
                ("v_max", ctypes.c_double), ("q_end", ctypes.c_double), ("c_end", ctypes.c_double)]


class _Ent(ctypes.Structure):
    _fields_ = [("rhs_m", ctypes.c_void_p), ("lhs", ctypes.c_void_p), ("lu", ctypes.c_void_p), ("ipiv1", ctypes.c_void_p),
                ("fv", ctypes.c_void_p), ("fl", ctypes.c_void_p), ("frev", ctypes.c_void_p)]


def _f64(a, order="C"):
    out = np.require(a, dtype=np.float64, requirements=[order])
    return out


class KernelSim(FastSim):
    def __post_init__(self):
        super().__post_init__()
        self._lib = _load()
        n, m = self.nv + self.p.n, 2 * self.p.n
        keep = []
        ctx = _Ctx(n=n, m=m, nonlinear=int(self.nl is not None))
        if self.nl is not None:
            vt, qt, v_max, q_end, c_end = self._q
            arrs = dict(r=_f64(self.nl["r"]), vinf=_f64(self.nl["vin"]), nper=_f64(self.nl["n"]), clin=_f64(self.nl["clin"]),
                        vt=_f64(vt), qt=_f64(qt))
            for k, a in arrs.items():
                setattr(ctx, k, a.ctypes.data); keep.append(a)
            ctx.nt, ctx.v_max, ctx.q_end, ctx.c_end = len(vt), float(v_max), float(q_end), float(c_end)
        self._ctx, self._ctx_keep = ctx, keep
        self._ctxp = ctypes.addressof(ctx)
        self._kent = {}
        self._iters = ctypes.c_int(0)
        self.kernel_stats = {"steps": 0, "python_redo": 0}

    def _kentry(self, key, entry, cache):
        k = self._kent.get(key) if cache else None
        if k is None:
            (lu, piv), rhs_m, fv, fl, lhs, frev = entry
            arrs = dict(rhs_m=_f64(rhs_m), lhs=_f64(lhs), lu=_f64(lu, "F"), ipiv1=np.ascontiguousarray(piv + 1, dtype=np.int32),
                        fv=_f64(fv), fl=_f64(fl))
            if frev is not None:
                arrs["frev"] = _f64(frev)
            ent = _Ent(**{nm: a.ctypes.data for nm, a in arrs.items()})
            k = (ent, arrs, ctypes.addressof(ent))
            if cache:
                self._kent[key] = k
        return k

    def step(self, y, conducting, h, euler, t, load_on, donly=None, vin0=None, vin1=None):
        key = (conducting, h, euler, load_on, donly)
        entry = self.cache.get(key)
        if entry is None:                                       # A88 Sim.step's entry, unchanged
            A, fv, fl, frev = self.system(conducting, load_on, donly)
            if euler:
                lhs, rhs_m = self.M - h * A, self.M
            else:
                lhs, rhs_m = self.M - 0.5 * h * A, self.M + 0.5 * h * A
            entry = (lu_factor(lhs), rhs_m, fv, fl, lhs, frev if (donly is not None and any(donly)) else None)
            if h == self.p.h:
                self.cache[key] = entry
        kent = self._kentry(key, entry, h == self.p.h)
        p = self.p
        if vin1 is None:
            vin1 = p.vin_at(t + h)
        if vin0 is None:
            vin0 = p.vin_at(t)
        ld1 = p.load_at(t + h)
        ld0 = 0.0 if euler else p.load_at(t)
        y = np.ascontiguousarray(y, dtype=np.float64)
        y1 = np.empty(self.nv + p.n)
        rc = self._lib.pk_step(self._ctxp, kent[2], y.ctypes.data, y1.ctypes.data, h, int(bool(euler)), vin0, vin1,
                               ld0, ld1, ctypes.byref(self._iters))
        self.kernel_stats["steps"] += 1
        if rc == 0:
            if self.nl is not None:
                it = self._iters.value
                st = self.nl["stats"]; st["steps"] += 1; st["iters"] += it; st["max_iters"] = max(st["max_iters"], it)
            return y1
        if rc == 1:
            raise ValueError("array must not contain infs or NaNs")
        self.kernel_stats["python_redo"] += 1                    # chord not converged: A94's Python step, A88 fallback
        return FastSim.step(self, y, conducting, h, euler, t, load_on, donly, vin0, vin1)


class KernelPlant(FastPlant):
    """FastPlant with KernelSim (same interface; the bridge constructs it like FastPlant)."""

    def __init__(self, p, y0, gh, gl):
        super().__init__(p, y0, gh, gl)
        self.sim = KernelSim(p)
