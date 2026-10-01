"""The co-simulation plants (src/scb_ivr/cosim/plant.py) step bit for bit alike: FastPlant, KernelPlant and
KernelPlant2 (C step loop with the bridge's monitors) against ReferencePlant, from an A92 n0 section at about 300 us (48 V, load on, datasheet Coss(V), reverse drop), with a
jittered four-phase gate pattern whose edges fall between 10 ps steps. KernelPlant is skipped where its C kernel
cannot be built (it needs macOS Accelerate and a C compiler). The full gates are A94, A95 and
scripts/cosim_regression.py; this is the quick guard run with the portable suite."""
import json
import shutil
import sys
import unittest
from pathlib import Path

import numpy as np

from scb_ivr.cosim.circuit import TRACK_A, CircuitParams, fit_fig8
from scb_ivr.cosim.plant import FastPlant, ReferencePlant

N, STEPS = 4, 3000


def params():
    pr = json.loads((TRACK_A / "A79_p24_output_voltage_loop" / "run_r1_ki0p25.json").read_text())["params"]
    keep = ("n", "vin", "L", "R", "c_high", "c_low", "cs", "co", "load_kind", "r_load", "i_load", "g_on", "h",
            "t_ramp", "t_load", "t_hand")
    vf, rr, _ = fit_fig8(10.0, 100.0)
    return CircuitParams(**{k: pr[k] for k in keep}, diode_check=True, nonlinear_coss=True, rev_drop=True,
                         rev_vf=vf, rev_r=rr)


def schedule(rng, t0, t_end, ton=17.75e-9, period=232e-9, d_lo=1.2e-9, d_hi=9.0e-9, jit=0.3e-9):
    ev = []
    for c in range(int((t_end - t0) / period) + 2):
        base = t0 + c * period
        for k in range(N):
            th = base + k * period / N + rng.normal(0, jit)
            ev += [(th - d_hi + rng.normal(0, jit), N + k, 0), (th, k, 1), (th + ton + rng.normal(0, jit), k, 0),
                   (th + ton + d_lo + rng.normal(0, jit), N + k, 1)]
    return sorted(e for e in ev if t0 < e[0] < t_end)


def bits(x):
    return np.asarray(x, dtype=float).view(np.int64).tolist()


class CosimPlantEquivalence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        d = json.loads((TRACK_A / "A92_verilog_error_based_correctors" / "cosim" / "run_n0_nominal.json").read_text())
        cls.s = min(d["sections"], key=lambda x: abs(x["t_s"] - 300e-6))
        cls.p = params()

    def lockstep(self, other_cls):
        s, p = self.s, self.p
        gh, gl = [True] + [False] * (N - 1), [False] + [True] * (N - 1)
        r, f = ReferencePlant(p, s["v"] + s["i"], gh, gl), other_cls(p, s["v"] + s["i"], gh, gl)
        r.t = f.t = s["t_s"]; r.load_on = f.load_on = True
        steps = 0

        def advance_to(te):
            nonlocal steps
            while r.t < te - 1e-18 and steps < STEPS:
                hh = min(p.h, te - r.t)
                r._advance(hh); f._advance(hh); steps += 1
                self.assertEqual(bits(r.y), bits(f.y), f"y at step {steps}")
                self.assertEqual(r.t, f.t)
                self.assertEqual([bool(x) for x in r.diode], [bool(x) for x in f.diode])
                self.assertEqual(bits(r.rev_e + r.rev_t), bits(f.rev_e + f.rev_t))
                self.assertEqual(bits(r.vds_max), bits(f.vds_max))
                self.assertEqual(r.ipk, f.ipk)

        t_end = r.t + STEPS * p.h * 1.05
        for te, j, lvl in schedule(np.random.default_rng(7), r.t, t_end):
            advance_to(te)
            if steps >= STEPS:
                break
            r.set_gate(j, lvl); f.set_gate(j, lvl)
        advance_to(t_end)
        self.assertEqual(steps, STEPS)

    def test_fast_plant_is_bit_identical(self):
        self.lockstep(FastPlant)

    @unittest.skipUnless(sys.platform == "darwin" and shutil.which("cc"), "C kernel needs macOS Accelerate and cc")
    def test_kernel_plant_is_bit_identical(self):
        from scb_ivr.cosim.plant import KernelPlant
        self.lockstep(KernelPlant)

    @unittest.skipUnless(sys.platform == "darwin" and shutil.which("cc"), "C kernel needs macOS Accelerate and cc")
    def test_kernel_plant2_loop_and_monitors_are_bit_identical(self):
        """KernelPlant2.integrate_to (C loop) against ReferencePlant stepped in Python with Monitors.py_step, over a
        few gate intervals, with the bridge's monitor starts at the edges; state and monitors compared per interval."""
        from scb_ivr.cosim.plant import KernelPlant2, Monitors
        s, p = self.s, self.p
        gh, gl = [True] + [False] * (N - 1), [False] + [True] * (N - 1)
        r, f = ReferencePlant(p, s["v"] + s["i"], gh, gl), KernelPlant2(p, s["v"] + s["i"], gh, gl)
        mr, mf = Monitors(N), Monitors(N)
        f.attach_monitors(mf)
        r.t = f.t = s["t_s"]; r.load_on = f.load_on = True
        fires_r, fires_f = [], []
        for idx, (te, j, lvl) in enumerate(schedule(np.random.default_rng(11), r.t, r.t + 80e-9)):
            thr = float(r.y[r.nv]) - 0.5
            armed = {"on": idx % 2 == 0}

            def r_step():
                mr.py_step(r)
                if armed["on"] and r.y[r.nv] <= thr:
                    armed["on"] = False; fires_r.append(r.t)
            r.integrate_to(te, r_step)
            f.integrate_to(te, None, monitors=mf, latch=(idx % 2 == 0, thr, lambda: fires_f.append(f.t)))
            self.assertEqual(bits(r.y), bits(f.y)); self.assertEqual(r.t, f.t); self.assertEqual(r.steps, f.steps)
            self.assertEqual([bool(x) for x in r.diode], [bool(x) for x in f.diode])
            self.assertEqual(bits(list(r.rev_e) + list(r.rev_t)), bits(list(f.rev_e) + list(f.rev_t)))
            self.assertEqual(bits(r.vds_max), bits(f.vds_max)); self.assertEqual(r.ipk, f.ipk)
            for nm in ("hoff_set", "cross_set", "vprev_valid", "vmin_set", "t_cross", "v_prev", "t_prev", "vmin", "t_vmin"):
                self.assertEqual(bits(getattr(mr, nm)), bits(getattr(mf, nm)), nm)
            self.assertEqual(fires_r, fires_f)
            k = j % N
            for mon, pl in ((mr, r), (mf, f)):
                if j < N and lvl:
                    mon.vmin_set[k] = 0
                if j < N and not lvl:
                    mon.hoff_set[k] = 1; mon.t_hoff[k] = pl.t; mon.cross_set[k] = 0; mon.vprev_valid[k] = 0
                if j >= N and lvl:
                    mon.hoff_set[k] = 0; mon.cross_set[k] = 0
                if j >= N and not lvl:
                    mon.vmin_set[k] = 1; mon.vmin[k] = pl.vds(k); mon.t_vmin[k] = pl.t
            r.set_gate(j, lvl); f.set_gate(j, lvl)
        self.assertGreater(r.steps, 3000)


if __name__ == "__main__":
    unittest.main()
