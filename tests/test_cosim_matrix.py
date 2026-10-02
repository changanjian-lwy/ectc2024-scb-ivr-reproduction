"""src/scb_ivr/cosim/matrix.py: the shared standard matrix reproduces A105's and A106's configurations and statistics."""
import importlib.util
import json
import unittest

from scb_ivr.cosim.circuit import TRACK_A
from scb_ivr.cosim.matrix import ROWS, configs, step_stats, window_stats

A105 = TRACK_A / "A105_p24_integrated_standard_matrix"
A106 = TRACK_A / "A106_p24_line_steps"


def strip(c):
    return {k: v for k, v in c.items() if k not in ("note", "out")}


class Matrix(unittest.TestCase):
    def test_configs_reproduce_a105_and_a106(self):
        base = json.loads((A105 / "cosim" / "cfg_i2_n0.json").read_text())
        made = configs(base)
        for row in ("n0", "m1n", "m1p", "m3n", "m3p", "j30", "j100", "s_m25", "s_p25", "s_m62", "s_p62"):
            self.assertEqual(strip(made[row]), strip(json.loads((A105 / "cosim" / f"cfg_i2_{row}.json").read_text())), row)
        for row in ("m48_1us", "p48_1us", "m48_10us", "p48_10us", "m80_10us"):
            self.assertEqual(strip(made[f"l_{row}"]), strip(json.loads((A106 / "cosim" / f"cfg_pi100_{row}.json").read_text())), row)
        self.assertEqual(len(ROWS), 16)

    def test_window_stats_equal_a105s(self):
        spec = importlib.util.spec_from_file_location("a105_matrix_stats", A105 / "matrix_stats.py")
        old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
        for name in ("i2_n0", "i2_s_p62"):
            d = json.loads((A105 / "cosim" / f"run_{name}.json").read_text())
            self.assertEqual(json.dumps(window_stats(d)), json.dumps(old.window_stats(d)))
            self.assertEqual(json.dumps(window_stats(d, t1=400e-6)), json.dumps(old.window_stats(d, t1=400e-6)))

    def test_step_stats_equal_a106s(self):
        s = json.loads((A106 / "a106_summary.json").read_text())["pi100_p48_1us"]
        x = step_stats(json.loads((A106 / "cosim" / "run_pi100_p48_1us.json").read_text()))
        for k in ("extreme_mv", "t_extreme_us", "back_within_1pct_us", "ladder_dev_peak", "ladder_back_below_1pct_us", "ladder_dev_before"):
            self.assertEqual(x[k], s[k], k)


if __name__ == "__main__":
    unittest.main()
