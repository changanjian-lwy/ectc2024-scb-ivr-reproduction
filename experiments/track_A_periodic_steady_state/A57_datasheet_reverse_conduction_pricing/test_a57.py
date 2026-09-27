"""A57 checks: digitized curve sanity and agreement with A56's own contract.

Run from this directory: python3 test_a57.py -v
"""
import json
import unittest

import numpy as np

import price_reverse_conduction as P


class DigitizedCurve(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.curves = P.load_curves()

    def vsd(self, temp, amps):
        current, volts = self.curves[temp]
        return float(np.interp(amps, current, volts))

    def test_monotone(self):
        for temp, (current, volts) in self.curves.items():
            self.assertTrue(np.all(np.diff(current) > 0), temp)
            self.assertTrue(np.all(np.diff(volts) >= -1e-9), temp)

    def test_values_readable_from_the_figure(self):
        # Coarse visual reads of Fig. 8 (half a grid division tolerance).
        self.assertAlmostEqual(self.vsd(25, 50), 2.4, delta=0.1)
        self.assertAlmostEqual(self.vsd(25, 400), 4.1, delta=0.1)
        self.assertAlmostEqual(self.vsd(125, 400), 5.0, delta=0.1)

    def test_curves_cross_near_50A(self):
        self.assertLess(self.vsd(125, 30), self.vsd(25, 30))
        self.assertGreater(self.vsd(125, 72), self.vsd(25, 72))

    def test_table_floor_is_below_the_curve_at_operating_currents(self):
        for temp in self.curves:
            self.assertGreater(self.vsd(temp, 20), P.TABLE_FLOOR_V)


class AgreesWithA56(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cap = json.loads((P.A56 / "capacitive_accounting.json").read_text())
        cls.res = json.loads((P.A56 / "results.json").read_text())
        cls.rows = {r["label"]: r for r in cls.res["comparison_at_250w"]["ranked_by_partial_loss_proxy"]}
        cls.orbits = {o["name"]: o for o in cls.cap["orbits"] if o["role"] == "regulated"}

    def test_population_and_ron(self):
        self.assertEqual(P.N_PAR, dict(high=2, low=3))
        self.assertAlmostEqual(P.RON["high"], 0.775e-3, places=12)
        self.assertAlmostEqual(P.RON["low"], 1.55e-3 / 3, places=12)

    def test_metered_interval_loss_reproduces_a56(self):
        for label, row in self.rows.items():
            priced = P.price_orbit(self.orbits[label], row["partial_loss_proxy_w"], lambda i: 0.0)
            self.assertAlmostEqual(priced["channel_metered_in_intervals_w"],
                                   row["channel_loss_metered_inside_surrogate_intervals_w"], places=9)

    def test_a56_break_even_drop_gives_zero_difference(self):
        base_row = self.rows[P.BASELINE]
        for be in self.res["comparison_at_250w"]["illustrative_reverse_conduction_break_even"]:
            drop = be["illustrative_break_even_reverse_drop_v"]
            const = lambda i, d=drop: d  # noqa: E731
            z = P.price_orbit(self.orbits[be["label"]], self.rows[be["label"]]["partial_loss_proxy_w"], const)
            b = P.price_orbit(self.orbits[P.BASELINE], base_row["partial_loss_proxy_w"], const)
            self.assertAlmostEqual(z["scenario_b_proxy_w"], b["scenario_b_proxy_w"], places=9, msg=be["label"])

    def test_zero_drop_keeps_only_the_ron_credit(self):
        o = self.orbits[P.BASELINE]
        row = self.rows[P.BASELINE]
        priced = P.price_orbit(o, row["partial_loss_proxy_w"], lambda i: 0.0)
        self.assertAlmostEqual(priced["scenario_b_proxy_w"],
                               row["partial_loss_proxy_w"] - row["channel_loss_metered_inside_surrogate_intervals_w"],
                               places=12)


if __name__ == "__main__":
    unittest.main()
