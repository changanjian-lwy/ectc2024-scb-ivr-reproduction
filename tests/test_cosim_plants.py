"""The co-simulation plants (src/scb_ivr/cosim/plant.py) step bit for bit alike: FastPlant, KernelPlant and
KernelPlant2 (C step loop with the bridge's monitors) against ReferencePlant, from an A92 n0 section at about 300 us (48 V, load on, datasheet Coss(V), reverse drop), with a
jittered four-phase gate pattern whose edges fall between 10 ps steps. KernelPlant is skipped where its C kernel
cannot be built (it needs macOS Accelerate and a C compiler). The full gates are A94, A95 and
scripts/cosim_regression.py; this is the quick guard run with the portable suite."""
import json
import shutil
import sys
import unittest
from dataclasses import replace
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



class CosimPlantLineStep(CosimPlantEquivalence):
    """A106: the same lockstep with an input step of -4.8 V starting 5 ns into the window, over 10 ns."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.p = replace(cls.p, vin_step=-4.8, t_vstep=cls.s["t_s"] + 5e-9, t_vslew=10e-9)

    def test_the_step_is_inside_the_window(self):
        t0 = self.s["t_s"]
        self.assertEqual(self.p.vin_at(t0), 48.0)
        self.assertAlmostEqual(self.p.vin_at(t0 + 10e-9), 45.6)
        self.assertAlmostEqual(self.p.vin_at(t0 + 20e-9), 43.2)


class CosimPlantAuxEquivalence(unittest.TestCase):
    """A101: the same lockstep with an auxiliary branch on every phase (Lr 0.75 nH, Cm 1 uF at 9 V), whose switches
    follow the low sides and open at zero current; the C loop with the high side's minimum stopped at V_DS <= 0."""

    @classmethod
    def setUpClass(cls):
        d = json.loads((TRACK_A / "A92_verilog_error_based_correctors" / "cosim" / "run_n0_nominal.json").read_text())
        s = min(d["sections"], key=lambda x: abs(x["t_s"] - 300e-6))
        cls.p = replace(params(), aux_phases=(1, 2, 3, 4), aux_l=0.75e-9, aux_r=2 * 1.3e-3 / 0.3 + 0.2e-3, aux_c=1e-6)
        cls.y0, cls.t0 = s["v"] + [9.0] * N + s["i"] + [0.0] * N, s["t_s"]

    def check(self, r, f):
        self.assertEqual(bits(r.y), bits(f.y)); self.assertEqual(r.t, f.t)
        self.assertEqual([bool(x) for x in r.diode], [bool(x) for x in f.diode])
        self.assertEqual([bool(x) for x in r.aux_on], [bool(x) for x in f.aux_on])
        self.assertEqual(bits(list(r.aux_e2) + list(r.aux_imax) + list(r.aux_imin)),
                         bits(list(f.aux_e2) + list(f.aux_imax) + list(f.aux_imin)))
        self.assertEqual(bits(r.vds_max), bits(f.vds_max)); self.assertEqual(r.ipk, f.ipk)

    def lockstep(self, other_cls):
        p = self.p
        gh, gl = [True] + [False] * (N - 1), [False] + [True] * (N - 1)
        r, f = ReferencePlant(p, self.y0, gh, gl), other_cls(p, self.y0, gh, gl)
        r.t = f.t = self.t0; r.load_on = f.load_on = True
        opened = [0]
        for te, j, lvl in schedule(np.random.default_rng(5), r.t, r.t + 300e-9):
            while r.t < te - 1e-18:
                hh = min(p.h, te - r.t)
                before = list(r.aux_on)
                r._advance(hh); f._advance(hh)
                opened[0] += sum(1 for a, b in zip(before, r.aux_on) if a and not b)
                self.check(r, f)
            r.set_gate(j, lvl); f.set_gate(j, lvl)
        self.assertGreater(opened[0], 2)                         # branches opened at zero current
        self.assertGreater(max(r.aux_imax), 5.0); self.assertLess(min(r.aux_imin), -5.0)

    def test_fast_plant_is_bit_identical(self):
        self.lockstep(FastPlant)

    @unittest.skipUnless(sys.platform == "darwin" and shutil.which("cc"), "C kernel needs macOS Accelerate and cc")
    def test_kernel_plant_is_bit_identical(self):
        from scb_ivr.cosim.plant import KernelPlant
        self.lockstep(KernelPlant)

    @unittest.skipUnless(sys.platform == "darwin" and shutil.which("cc"), "C kernel needs macOS Accelerate and cc")
    def test_kernel_plant2_loop_is_bit_identical(self):
        from scb_ivr.cosim.plant import KernelPlant2, Monitors
        p = self.p
        gh, gl = [True] + [False] * (N - 1), [False] + [True] * (N - 1)
        r, f = ReferencePlant(p, self.y0, gh, gl), KernelPlant2(p, self.y0, gh, gl)
        mr, mf = Monitors(N, vmin_zero=1), Monitors(N, vmin_zero=1)
        f.attach_monitors(mf)
        r.t = f.t = self.t0; r.load_on = f.load_on = True
        for te, j, lvl in schedule(np.random.default_rng(13), r.t, r.t + 300e-9):
            r.integrate_to(te, lambda: mr.py_step(r))
            f.integrate_to(te, None, monitors=mf, latch=(False, 0.0, None))
            self.check(r, f); self.assertEqual(r.steps, f.steps)
            for nm in ("hoff_set", "cross_set", "vprev_valid", "vmin_set", "t_cross", "v_prev", "t_prev", "vmin", "t_vmin"):
                self.assertEqual(bits(getattr(mr, nm)), bits(getattr(mf, nm)), nm)
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
        self.assertGreater(r.steps, 20000)


class CosimPlantAuxEnable(CosimPlantAuxEquivalence):
    """A102: the same branches disarmed for the first 150 ns (they ignore their low sides' edges and carry no current),
    then armed (each starts at its next low-side turn-off); per-branch precharges 8.5-9.4 V."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.y0 = cls.y0[:2 * N] + [8.5, 8.8, 9.1, 9.4] + cls.y0[3 * N:]

    def lockstep(self, other_cls):
        p = self.p
        gh, gl = [True] + [False] * (N - 1), [False] + [True] * (N - 1)
        r, f = ReferencePlant(p, self.y0, gh, gl), other_cls(p, self.y0, gh, gl)
        for pl in (r, f):
            pl.t = self.t0; pl.load_on = True
            pl.aux_armed = [False] * N; pl.aux_cmd = [False] * N; pl.aux_on = [False] * N
        t_arm, armed, opened = self.t0 + 150e-9, False, 0
        for te, j, lvl in schedule(np.random.default_rng(5), r.t, r.t + 300e-9):
            while r.t < te - 1e-18:
                hh = min(p.h, te - r.t)
                before = list(r.aux_on)
                r._advance(hh); f._advance(hh)
                opened += sum(1 for a, b in zip(before, r.aux_on) if a and not b)
                self.check(r, f)
                if not armed:
                    self.assertEqual([r.y[c] for c in r.aux_col], [0.0] * N)
                    self.assertFalse(any(r.aux_on))
            if not armed and te >= t_arm:
                r.aux_armed = [True] * N; f.aux_armed = [True] * N; armed = True
            r.set_gate(j, lvl); f.set_gate(j, lvl)
        self.assertTrue(armed)
        self.assertGreater(opened, 0)
        self.assertGreater(max(r.aux_imax), 5.0); self.assertLess(min(r.aux_imin), -5.0)

    def test_kernel_plant2_loop_is_bit_identical(self):
        self.skipTest("the C loop is covered by CosimPlantAuxEquivalence; arming is Python-side (_aux_gate)")


if __name__ == "__main__":
    unittest.main()
