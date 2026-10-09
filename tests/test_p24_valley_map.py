"""D63 valley map: the steady orbit, the crossing physics, and the validated load steps (thresholds from the cached
D63 diagnostics file, so no D57 solve here)."""
import json
import math
import unittest
from dataclasses import replace
from pathlib import Path

from scb_ivr.p24_valley_map import (Design, ValleyMap, _level_time, metrics, seg_end, seg_time, simulate,
                                    steady_check, steady_ton)

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics" / "D63_valley_map.json"
TH = tuple(tuple(x) for x in json.loads(DIAG.read_text())["thresholds"]["7.3333333e-09"])
D = Design(ith=TH, t_tr=(16.904e-9,) * 3 + (15.082e-9,))


class SteadyOrbit(unittest.TestCase):
    def test_matches_a115_orbit(self):
        # A115's registered orbit at 1 MHz 10%: Ton 93.80 ns, period 1195.1 ns (a115_predictions.json)
        r = simulate(D, 20e-6, 1.0)
        last = r[-1]
        self.assertAlmostEqual(last["ton"] * 1e9, 93.80, delta=0.3)
        self.assertAlmostEqual(last["period"] * 1e9, 1195.1, delta=3.0)
        self.assertTrue(all(abs(v + 12.5) < 0.3 for v in last["valley"]))   # phase 4 -12.75 (co-simulation -12.6)

    def test_steady_ton(self):
        self.assertAlmostEqual(steady_ton(D) * 1e9, 93.8, delta=0.3)


class Crossing(unittest.TestCase):
    def _i_on(self, valley, k=0):
        m = ValleyMap(D)
        s = m.init_state(steady_ton(D))
        s["valley"] = [valley] * 4
        return m.period(s, 48.0, 0.0)["i_on"][k]

    def test_within_threshold_starts_at_zero(self):
        self.assertEqual(self._i_on(-14.0), 0.0)

    def test_shallow_crossing_leaves_no_memory(self):
        # the reverse conduction ramps the current back to zero before the predictive turn-on
        self.assertEqual(self._i_on(-18.0), 0.0)

    def test_deep_crossing_leaves_memory(self):
        self.assertLess(self._i_on(-40.0), -5.0)

    def test_positive_valley_decays_before_turn_on(self):
        i0 = self._i_on(20.0)
        self.assertAlmostEqual(i0, 20.0 - (1.0 + 2.0) / 7.3333333e-9 * 16.904e-9, delta=0.3)


class LoadSteps(unittest.TestCase):
    def test_comparator_minus_62(self):        # A116 c60_s_m62: +28.04 mV, back 16.12 us
        m = metrics(simulate(D, 200e-6, 50e-6, i_step=-62.5), 50e-6)
        self.assertAlmostEqual(m["extreme_mv"], 28.04, delta=2.8)
        self.assertAlmostEqual(m["back_us"], 16.12, delta=3.0)

    def test_timed_minus_62_crosses_phase1(self):   # A115 n10_s_m62 ran away: phase 1's valley passes the threshold
        r = simulate(replace(D, mode="timed"), 200e-6, 50e-6, i_step=-62.5)
        depth = max(x["depth"][0] for x in r if x["t"] >= 50e-6)
        self.assertGreater(depth, 10.0)

    def test_floor_holds_phase1(self):
        r = simulate(replace(D, mode="floor", floor_a=2.0), 200e-6, 50e-6, i_step=-62.5)
        self.assertLess(max(x["depth"][0] for x in r if x["t"] >= 50e-6), 1.0)


class EdgeOffsetAndVds(unittest.TestCase):      # A148
    def test_zero_offset_is_identity_in_steady_state(self):
        d = replace(D, mode="floor", floor_a=2.0)
        m = ValleyMap(d)
        a, b = m.init_state(steady_ton(d)), m.init_state(steady_ton(d))
        for _ in range(300):
            ra, rb = m.period(a, d.vin, 0.0), m.period(b, d.vin, 0.0, lo_add=0.0)
            self.assertEqual(ra, rb)

    def test_offset_moves_the_valley_down(self):
        d = replace(D, mode="timed")
        m = ValleyMap(d)
        s = m.init_state(steady_ton(d))
        for _ in range(300):
            m.period(s, d.vin, 0.0)
        v0 = m.period(dict(s, vc=list(s["vc"]), valley=list(s["valley"])), d.vin, 0.0)["valley"][0]
        v1 = m.period(s, d.vin, 0.0, lo_add=lambda ton1: 20e-9)["valley"][0]
        self.assertAlmostEqual(v1 - v0, -20e-9 * d.vref / d.lf, delta=0.3)

    def test_von_block(self):
        from scb_ivr.p24_valley_map import von_point
        self.assertAlmostEqual(von_point(2.9333333e-9, 12.29, -15.6, 10.93e-9), 3.95, delta=0.1)   # cosim 3.9 V
        self.assertAlmostEqual(von_point(2.9333333e-9, 16.9, 12.6, 10.93e-9), 18.95, delta=0.3)   # cosim 19.0 V

    def test_sh_block(self):
        flat = ((-50.0, 50.0), (0.0, 30.0), ((5.0, 5.0), (5.0, 5.0)), ((5.0, 5.0), (5.0, 5.0)))   # V_DS 5 V everywhere
        d = replace(D, von=flat)
        m = ValleyMap(d)
        r = m.period(m.init_state(steady_ton(d)), d.vin, 0.0)
        self.assertNotIn("sh", r)
        d = replace(d, sh=((0.0, 10.0), (2.0, 12.0)))                                            # f(5 V) = 7 V
        m = ValleyMap(d)
        r = m.period(m.init_state(steady_ton(d)), d.vin, 0.0)
        for k in range(1, d.n):
            self.assertAlmostEqual(r["sh"][k - 1], r["rails"][k - 1] + r["rails"][k] + 7.0, places=9)


class Validity(unittest.TestCase):              # D81: the map says when it leaves its tables or a formula's range
    def test_zero_resistance_is_the_ramp_limit(self):
        i1, q = seg_end(10.0, 0.0, 1e-9, -5.0, 2e-9)
        self.assertAlmostEqual(i1, 15.0)
        self.assertAlmostEqual(q, -5.0 * 2e-9 + 0.5 * 10.0 * 4e-18 / 1e-9)
        a, b = seg_end(10.0, 1e-9, 1e-9, -5.0, 2e-9), seg_end(10.0, 0.0, 1e-9, -5.0, 2e-9)
        self.assertAlmostEqual(a[0], b[0], places=6)
        self.assertAlmostEqual(seg_time(10.0, 0.0, 1e-9, -5.0, 15.0), 2e-9)

    def test_unreachable_target_is_inf_not_negative(self):
        self.assertEqual(seg_time(-1.0, 0.54e-3, 1e-9, 0.0, 1.0), math.inf)      # falling current, target above
        self.assertEqual(seg_time(-1.0, 0.0, 1e-9, 0.0, 1.0), math.inf)
        self.assertGreater(seg_time(-1.0, 0.54e-3, 1e-9, 1.0, 0.0), 0.0)
        self.assertEqual(_level_time(-1.0, 0.54e-3, 1e-9, -20.0, -12.5), 0.0)   # comparator already past its level

    def test_rail_outside_the_threshold_table_is_flagged(self):
        m = ValleyMap(D)
        s = m.init_state(steady_ton(D))
        self.assertEqual(m.period(dict(s, vc=list(s["vc"]), valley=list(s["valley"])), D.vin, 0.0)["flags"], [])
        r = m.period(s, D.vin + 10.0, 0.0)                                      # rail 1 = 22 V, table to 17 V
        self.assertIn("ith_rail", r["flags"])

    def test_steady_ton_refuses_without_a_root(self):
        with self.assertRaises(ValueError):
            steady_ton(D, vin=4.0)                                              # rail = Vo: no current at any Ton

    def test_warm_up_is_checked_and_reported(self):
        r = simulate(D, 20e-6, 10e-6, i_step=-62.5)
        self.assertTrue(r[0]["warm"]["settled"])
        m = metrics(r, 10e-6)
        self.assertTrue(m["warm_settled"])
        self.assertEqual(m["flag_periods"], {})
        ms = ValleyMap(D)
        fresh = ms.init_state(steady_ton(D) * 1.2)                              # 20 % off: not settled
        self.assertFalse(steady_check(ms, fresh, D.vin, n=16)["settled"])


if __name__ == "__main__":
    unittest.main()
