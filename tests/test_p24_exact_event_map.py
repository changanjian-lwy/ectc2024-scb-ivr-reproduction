"""Tests of the D43 exact event map for P24's four-phase module (src/scb_ivr/p24_exact_event_map.py)."""
import unittest

import numpy as np

from scb_ivr.p24_exact_event_map import (Circuit, Control, ExactEventMap, orbit, section_free, section_full,
                                         valley_after_lowoff)

# D43 cross-check orbit at the A79 run 3 point (7.5% target): section coordinates x1, a2, a3, out, i1..i4
S_STAR = np.array([12.242053249, 23.885358378, 12.004905455, 0.999981176,
                   0.005900928, 24.132355716, 58.914910342, 95.97538723])
CTL = Control(ton=18.0344198276292e-9, i_target=-9.375,
              d_high=(8.200000011686706e-9, 8.260000011487177e-9, 8.310000011558438e-9, 7.040000009748423e-9))


class TopologyTests(unittest.TestCase):
    def setUp(self):
        self.m = ExactEventMap(Circuit(), CTL)

    def test_input_short_is_rejected(self):
        # SH1..SH4 and SL4 all conducting connect vin to ground
        cond = [True] * 4 + [False, False, False, True]
        with self.assertRaises(ValueError):
            self.m.topo(cond)

    def test_merged_nodes_share_one_group(self):
        tp = self.m.topo([True, False, False, False, False, True, True, True])
        self.assertEqual(tp.root["a1"], tp.root["vin"])
        for k in (2, 3, 4):
            self.assertEqual(tp.root[f"x{k}"], tp.root["gnd"])
        self.assertEqual(tp.m, 4)                   # free groups: a2, a3, x1, out

    def test_exact_flow_composes(self):
        tp = self.m.topo([True, False, False, False, False, True, True, True])
        v, i = section_full(S_STAR)
        z = tp.to_z(v, i)
        a = tp.propagate(z, 7e-9)
        b = tp.propagate(tp.propagate(z, 3e-9), 4e-9)
        np.testing.assert_allclose(a, b, rtol=1e-9, atol=1e-9)

    def test_device_current_affine_matches_direct(self):
        tp = self.m.topo([True, False, False, False, False, True, True, True])
        z = tp.to_z(*section_full(S_STAR))
        direct = tp._device_currents(z)
        for j, (a, b) in tp.device_current_affine().items():
            self.assertAlmostEqual(float(a @ z + b), direct[j], places=6)


class ChargeTests(unittest.TestCase):
    def setUp(self):
        self.m = ExactEventMap(Circuit(), CTL)
        self.ckt = Circuit()

    def _node_charge(self, v):
        vv = dict(zip(self.ckt.nodes, v)); vv["vin"] = self.ckt.vin; vv["gnd"] = 0.0
        q = dict.fromkeys(self.ckt.nodes, 0.0)
        for p, qn, c in self.ckt.capacitors:
            if p in q:
                q[p] += c * (vv[p] - vv[qn])
            if qn in q:
                q[qn] += c * (vv[qn] - vv[p])
        return q

    def test_reinit_is_identity_without_a_voltage_step(self):
        v, i = section_full(S_STAR)
        tp = self.m.topo([True, False, False, False, False, True, True, True])
        z = self.m.reinit(v, i, tp)
        v2, _ = tp.to_full(z)
        np.testing.assert_allclose(v2, v, atol=1e-9)

    def test_hard_merge_conserves_group_charge(self):
        v, i = section_full(S_STAR)
        v = v.copy(); v[self.ckt.nodes.index("x1")] = 5.0          # SL1 turned on against 5 V
        new = self.m.topo([True, False, False, False, True, True, True, True])
        q_before = self._node_charge(v)
        v2, _ = new.to_full(self.m.reinit(v, i, new))
        q_after = self._node_charge(v2)
        for grp in {new.root[n] for n in self.ckt.nodes if new.root[n] in new.free}:
            members = [n for n in self.ckt.nodes if new.root[n] == grp]
            self.assertAlmostEqual(sum(q_after[n] for n in members) / 1e-6, sum(q_before[n] for n in members) / 1e-6,
                                   places=6)
        self.assertAlmostEqual(v2[self.ckt.nodes.index("x1")], 0.0, places=12)


class OrbitTests(unittest.TestCase):
    def setUp(self):
        self.m = ExactEventMap(Circuit(), CTL)

    def test_section_round_trip(self):
        v, i = section_full(S_STAR)
        np.testing.assert_allclose(section_free(v, i), S_STAR)

    def test_reference_orbit_returns_to_itself(self):
        v, i = section_full(S_STAR)
        v1, i1, log = self.m.run_cycle(v, i)
        np.testing.assert_allclose(section_free(v1, i1), S_STAR, atol=1e-6)
        self.assertAlmostEqual(log["period"] * 1e9, 238.793, places=2)
        self.assertEqual(sorted(x["phase"] for x in log["turnon"]), [1, 2, 3, 4])
        self.assertTrue(all(x["how"] == "high_on" for x in log["turnon"]))
        self.assertAlmostEqual([x for x in log["lowoff"] if x["phase"] == 1][0]["i"], -9.375, places=6)

    def test_newton_from_a_perturbed_seed_and_stability(self):
        s0 = S_STAR + np.array([0.02, -0.01, 0.01, 0.001, 0.2, -0.3, 0.3, -0.2])
        sx, J, hist, _ = orbit(self.m, s0)
        self.assertLess(hist[-1], 1e-8)
        np.testing.assert_allclose(sx, S_STAR, atol=1e-6)
        self.assertLess(max(abs(np.linalg.eigvals(J))), 1.0)

    def test_phase1_natural_valley(self):
        t_v, v_v = valley_after_lowoff(self.m, *section_full(S_STAR), 1)
        self.assertAlmostEqual(t_v * 1e9, 7.947, delta=0.02)
        self.assertAlmostEqual(v_v, 7.958, delta=0.01)


if __name__ == "__main__":
    unittest.main()
