"""src/scb_ivr/cosim/matrix.py: the shared standard matrix reproduces A105's and A106's configurations and statistics,
and the interleave statistics reproduce C01's."""
import importlib.util
import json
import unittest

from scb_ivr.cosim.circuit import TRACK_A
from scb_ivr.cosim.matrix import ROWS, configs, gaps_per_cycle, lsoff_after, output_ripple, ref_turnons, step_stats, window_stats

A105 = TRACK_A / "A105_p24_integrated_standard_matrix"
A106 = TRACK_A / "A106_p24_line_steps"
C01 = TRACK_A.parent / "track_C_multi_module" / "C01_four_modules_baseline"


def close(a, b, rel=1e-12):
    """Equal up to the last bits: C01's stored values were computed on another platform, whose summation order
    over the large waveform arrays can differ in the final bit."""
    return abs(a - b) <= rel * max(abs(a), abs(b))


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

    def test_interleave_stats_equal_c01s(self):
        old = json.loads((C01 / "c01_summary.json").read_text())
        for name in ("m4_n0", "m4_L5"):
            d = json.loads((C01 / "cosim" / f"run_{name}.json").read_text())
            mods = [d] + d["modules_rest"]
            dtp = d["dt_pred_final_ns"][0] * 1e-9
            _, per = ref_turnons(d)
            shifts = {"actual": None, "slaves_ref_master_lsoff": lambda m, k: -dtp if m else 0.0,
                      "uniform": lambda m, k: (-dtp if m else 0.0) + (dtp if k == 1 else 0.0),
                      "no_module_interleave": lambda m, k: -m * per / 16}
            for case, f in shifts.items():
                r = output_ripple(mods, shift=f)
                for key in ("pkpk_a", "rms_ac_a"):
                    self.assertTrue(close(r[key], old[name]["ripple"][case][key]), (name, case, key, r[key]))
            for m, md in enumerate(mods):
                for a, b in zip(lsoff_after(d, md), old[name]["modules"][m]["lsoff_after_master_ns"]):
                    self.assertTrue(close(a * 1e9, b), (name, m, a * 1e9, b))

    def test_step_stats_not_recovered_is_inf(self):
        """A trace that steps to 0.98 V and stays there has not recovered (the 2026-10-03 review's counterexample);
        one that returns inside the band reports the last exit."""
        secs = [{"t_s": 390e-6 + i * 1e-7, "vo": 1.0 if 390e-6 + i * 1e-7 < 400e-6 else 0.98, "vin_v": 48.0,
                 "vcs_v": [36.0, 24.0, 12.0]} for i in range(400)]
        self.assertEqual(step_stats({"sections": secs})["back_within_1pct_us"], float("inf"))
        secs2 = [dict(x, vo=1.0) if x["t_s"] >= 410e-6 else x for x in secs]
        self.assertTrue(9.0 < step_stats({"sections": secs2})["back_within_1pct_us"] < 10.0)

    def test_gaps_per_cycle_c03_n0(self):
        """The cycle-by-cycle 16-phase spacing of C03 n0 over its last 200 master periods: max 0.578 ns, sd 0.028 ns
        (the mean positions are within 0.05 ns)."""
        d = json.loads((C01.parent / "C03_four_module_standard_matrix" / "cosim" / "run_n0.json").read_text())
        t, _ = ref_turnons(d)
        g = gaps_per_cycle([d] + d["modules_rest"], t[0], t[-1])
        self.assertAlmostEqual(g["max_abs_ns"], 0.578, places=3)
        self.assertAlmostEqual(g["sd_ns"], 0.028, places=3)


if __name__ == "__main__":
    unittest.main()
