"""D58 (src/scb_ivr/p24_startup_averaged.py): the averaged start-up and voltage-loop model."""
import json
import unittest

import numpy as np

from scb_ivr.cosim.circuit import TRACK_A
from scb_ivr.p24_startup_averaged import Module, Sequence, metrics, run, validate


class StartupAveraged(unittest.TestCase):
    def test_calibration_reproduces_the_full_load_steady_state(self):
        t, vo, ton, mode = run(Module(), Sequence(t_load=0.0, t_hand=72e-6, ton_s=568.0), t_end=400e-6)
        late = t > 350e-6
        self.assertLess(abs(vo[late].mean() - 1.0), 2e-3)
        self.assertLess(abs(ton[late].mean() - 568.0), 3.0)

    def test_reference_start_up_against_the_co_simulation(self):
        ref = json.loads((TRACK_A / "A100_timed_turn_off_load_steps" / "cosim" / "run_ref_m62.json").read_text())
        rows = validate([s for s in ref["sections"] if s["t_s"] < 300e-6])
        self.assertLess(max(abs(r["model_vo_v"] - r["cosim_vo_v"]) for r in rows), 0.03)
        self.assertLess(max(abs(r["model_ton_lsb"] - r["cosim_ton_lsb"]) for r in rows), 15)

    def test_load_from_the_start_removes_the_overshoot(self):
        c0 = metrics(*run(Module(), Sequence())[:2], Sequence())
        sq = Sequence(t_load=0.0)
        c1 = metrics(*run(Module(), sq)[:2], sq)
        self.assertGreater(c0["vo_max_v"], 1.2)
        self.assertLess(c1["vo_max_v"], 1.05)
        self.assertGreater(c1["vo_min_after_handover_v"], c0["vo_min_after_handover_v"])


if __name__ == "__main__":
    unittest.main()
