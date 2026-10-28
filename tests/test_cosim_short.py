"""A259: the output short (bridge cfg "short") changes the plant's r_load through set_r_load, which drops every cached
system. From an A92 n0 section (as test_cosim_plants): a plant whose caches were dropped and rebuilt steps bit for bit
like one that kept them; a real change of r_load takes effect at once and rebuilds the systems of a plant built with
the new value; KernelPlant2's C table is emptied too (skipped where the C kernel cannot be built)."""
import json
import shutil
import sys
import unittest
from dataclasses import replace

import numpy as np

import test_cosim_plants as fx
from scb_ivr.cosim.circuit import TRACK_A
from scb_ivr.cosim.plant import FastPlant, FastSim

N = fx.N
R_SHORT = 1.0 / (1.0 / 4e-3 + 1.0 / 0.5e-3)          # 4 mOhm load with a 0.5 mOhm short across it


class OutputShort(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        d = json.loads((TRACK_A / "A92_verilog_error_based_correctors" / "cosim" / "run_n0_nominal.json").read_text())
        cls.s = min(d["sections"], key=lambda x: abs(x["t_s"] - 300e-6))
        cls.p = fx.params()

    def plant(self, cls, r):
        p = replace(self.p, r_load=r)
        gh, gl = [True] + [False] * (N - 1), [False] + [True] * (N - 1)
        f = cls(p, self.s["v"] + self.s["i"], gh, gl)
        f.t = self.s["t_s"]; f.load_on = True
        return f

    def run_pair(self, cls, flush):
        """Plants a (flush(a) half way) and b (never flushed), both built with R_SHORT, on the same gate schedule."""
        a, b = self.plant(cls, R_SHORT), self.plant(cls, R_SHORT)
        go = {}
        for f in (a, b):                                   # KernelPlant2: its C loop, which fills the table
            if hasattr(f, "attach_monitors"):
                from scb_ivr.cosim.plant import Monitors
                m = Monitors(N); f.attach_monitors(m)
                go[f] = lambda t, f=f, m=m: f.integrate_to(t, None, monitors=m)
            else:
                go[f] = lambda t, f=f: f.integrate_to(t, lambda: None)
        t_end = a.t + 300e-9
        sched = fx.schedule(np.random.default_rng(5), a.t, t_end)
        self.assertGreater(len(sched), 8)
        for i, (te, j, lvl) in enumerate(sched):
            for f in (a, b):
                go[f](te)
                f.set_gate(j, lvl)
            if i == len(sched) // 2:
                flush(a)
        for f in (a, b):
            go[f](t_end)
        return a, b

    def test_rebuilt_systems_step_alike(self):
        def flush(a):
            self.assertGreater(len(a.sim.cache), 0)
            a.set_r_load(4e-3); a.set_r_load(R_SHORT)
            self.assertEqual(len(a.sim.cache), 0)
        a, b = self.run_pair(FastPlant, flush)
        self.assertEqual(fx.bits(a.y), fx.bits(b.y))

    def test_change_takes_effect(self):
        a, b = self.run_pair(FastPlant, lambda a: a.set_r_load(4e-3))
        self.assertNotEqual(fx.bits(a.y), fx.bits(b.y))
        self.assertEqual(a.p.r_load, 4e-3)
        cond = tuple([True] + [False] * (N - 1) + [False] + [True] * (N - 1))
        fresh = FastSim(replace(self.p, r_load=4e-3)).system(cond, True)[0]
        self.assertEqual(fx.bits(a.sim.system(cond, True)[0].ravel()), fx.bits(fresh.ravel()))

    @unittest.skipUnless(sys.platform == "darwin" and shutil.which("cc"), "C kernel needs macOS Accelerate and cc")
    def test_kernel_table_is_emptied(self):
        from scb_ivr.cosim.plant import KernelPlant2

        def flush(a):
            self.assertGreater(len(a._table_keep), 0)
            keys = list(a._table_keep)
            a.set_r_load(4e-3); a.set_r_load(R_SHORT)
            self.assertEqual((len(a._table_keep), len(a.sim._kent)), (0, 0))
            self.assertTrue(all(a._table[k] is None for k in keys))
        a, b = self.run_pair(KernelPlant2, flush)
        self.assertEqual(fx.bits(a.y), fx.bits(b.y))


if __name__ == "__main__":
    unittest.main()
