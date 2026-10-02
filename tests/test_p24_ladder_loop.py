"""D60 (src/scb_ivr/p24_ladder_loop.py): the series-capacitor ladder relaxes in mode P."""
import json
import unittest

import numpy as np

from scb_ivr.cosim.circuit import TRACK_A
from scb_ivr.p24_ladder_loop import metrics, relaxation_us, run
from scb_ivr.p24_startup_averaged import LSB, Module
from scb_ivr.p24_voltage_loop import design_pi


class LadderLoop(unittest.TestCase):
    def test_time_constants_follow_the_closed_form(self):
        m = Module()
        q = (568 * LSB) ** 2 / (2 * m.lf)
        r = relaxation_us(3e-6, m)
        self.assertAlmostEqual(r[0], 232.2e-9 * 3e-6 / (q * (2 - np.sqrt(2))) * 1e6, places=9)
        self.assertAlmostEqual(relaxation_us(6e-6, m)[0] / r[0], 2.0, places=12)    # proportional to Cs

    def test_the_ladder_does_not_ring(self):
        kp, ki = design_pi(100e3)
        t, vo, ton, dev = run(kp, ki, cs=8.7e-6, dvin=4.8, t_slew=1e-6, t_end=120e-6)
        a = dev[t > 21e-6 + 2e-6]                       # after the ramp and its peak
        self.assertLess(np.max(np.diff(a)), 1e-6)       # monotonic decay: no resonance

    def test_peaks_against_a106(self):
        kp, ki = design_pi(100e3)
        s = json.loads((TRACK_A / "A106_p24_line_steps" / "a106_summary.json").read_text())
        for row, dv in (("p48_1us", 4.8), ("m48_1us", -4.8)):
            x = metrics(*[v for i, v in enumerate(run(kp, ki, cs=3e-6, dvin=dv, t_slew=1e-6)) if i in (0, 1, 3)], base_dev=0.0047)
            self.assertLess(abs(x["ladder_dev_peak"] / s[f"pi100_{row}"]["ladder_dev_peak"] - 1), 0.3)


if __name__ == "__main__":
    unittest.main()
