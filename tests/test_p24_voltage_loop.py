"""D59 (src/scb_ivr/p24_voltage_loop.py): the sampled PI voltage loop on D58's averaged plant."""
import json
import unittest

import numpy as np

from scb_ivr.cosim.circuit import TRACK_A
from scb_ivr.p24_startup_averaged import LSB
from scb_ivr.p24_voltage_loop import design_pi, ladder_f, margins, step, step_metrics


class VoltageLoop(unittest.TestCase):
    def test_present_integral_loop_reproduces_a100_steps(self):
        ki = 0.25 / (LSB * 1e9)
        for tag, i_step in (("m62", -62.5), ("p62", 62.5)):
            x = step_metrics(*step(i_step, 0.0, ki))
            d = json.loads((TRACK_A / "A100_timed_turn_off_load_steps" / "cosim" / f"run_ref_{tag}.json").read_text())
            dv = [s["vo"] - 1.0 for s in d["sections"] if s["t_s"] >= 400e-6]
            ext = dv[int(np.argmax(np.abs(dv)))] * 1e3
            self.assertLess(abs(x["extreme_mv"] - ext), 5.0)

    def test_designs_reach_their_crossover(self):
        for fc in (30e3, 100e3):
            kp, ki = design_pi(fc)
            f, pm = margins(kp, ki)
            self.assertLess(abs(f / fc - 1), 0.05)
            self.assertGreater(pm, 60)

    def test_ladder_resonance_matches_the_roberts_derivation(self):
        # ROBERTS_SOFTSTART_P24_MODEL_DERIVATION.md: f1,4 = 153.04 kHz at D = 0.083335, Cs = 3 uF
        self.assertLess(abs(ladder_f(3e-6, d=0.083335)[0] / 153.04e3 - 1), 0.002)

    def test_pi_cuts_the_step_excursion(self):
        ki0 = 0.25 / (LSB * 1e9)
        kp, ki = design_pi(60e3)
        a = step_metrics(*step(62.5, 0.0, ki0))
        b = step_metrics(*step(62.5, kp, ki))
        self.assertLess(abs(b["extreme_mv"]), abs(a["extreme_mv"]) / 3)


if __name__ == "__main__":
    unittest.main()
