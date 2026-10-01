"""A95: KernelSim / KernelPlant, A94's FastSim / FastPlant with the per-step solve and A86's chord iteration done by
plant_kernel.c (one C call per step), with the same floating-point operations (BOUNDARY.md).

The C library is built from plant_kernel.c on first use (clang, -O2 -ffp-contract=off, Accelerate) next to this
file. If the chord iteration does not converge in 8 iterations the step is redone by A94's Python code, which takes
A88's full-Newton fallback; a non-finite right-hand side raises ValueError as scipy's lu_solve does.
"""
from __future__ import annotations

import ctypes
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy.linalg import lu_factor

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "A94_cosim_plant_speedup"))
from fast_plant import FastPlant, FastSim, Params, fit_fig8  # noqa: E402,F401  (re-exported)

SRC, LIB = HERE / "plant_kernel.c", HERE / "plant_kernel.so"
CFLAGS = ["-O2", "-ffp-contract=off", "-fno-fast-math", "-shared", "-fPIC"]


def _load():
    if not LIB.exists() or LIB.stat().st_mtime < SRC.stat().st_mtime:
        subprocess.run(["cc", *CFLAGS, "-o", str(LIB), str(SRC), "-framework", "Accelerate"], check=True)
    lib = ctypes.CDLL(str(LIB))
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
