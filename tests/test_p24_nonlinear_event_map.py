"""Tests of the D45 nonlinear-Coss event map (src/scb_ivr/p24_nonlinear_event_map.py)."""
import unittest

import numpy as np

from scb_ivr.p24_exact_event_map import (Circuit, Control, ExactEventMap, section_free, section_full,
                                         valley_after_lowoff)
from scb_ivr.p24_nonlinear_event_map import Coss, NonlinearEventMap, nl_valley_after_lowoff, orbit_chord, section_jacobian

# D43's cross-check orbit at the A79 run 3 point (as tests/test_p24_exact_event_map.py)
S_STAR = np.array([12.242053249, 23.885358378, 12.004905455, 0.999981176,
                   0.005900928, 24.132355716, 58.914910342, 95.97538723])
CTL = Control(ton=18.0344198276292e-9, i_target=-9.375,
              d_high=(8.200000011686706e-9, 8.260000011487177e-9, 8.310000011558438e-9, 7.040000009748423e-9))
# a smooth synthetic Coss(V) (falls from 2.5 nF to 1 nF), for tests that need a nonlinear curve without A59's file
V_PTS = np.linspace(0.0, 40.0, 81)
C_PTS = 1.0e-9 + 1.5e-9 / (1.0 + (V_PTS / 12.0) ** 2)


class LinearLimitTests(unittest.TestCase):
    def test_constant_coss_reproduces_d43(self):
        v, i = section_full(S_STAR)
        v1, i1, log1 = ExactEventMap(Circuit(), CTL).run_cycle(v, i)
        v2, i2, log2 = NonlinearEventMap(Circuit(), CTL).run_cycle(v, i)
        np.testing.assert_allclose(section_free(v2, i2), section_free(v1, i1), atol=1e-6)
        self.assertAlmostEqual(log2["period"] * 1e9, log1["period"] * 1e9, places=6)
        self.assertEqual([e[1:] for e in log2["events"]], [e[1:] for e in log1["events"]])

    def test_separate_high_and_low_curves_reproduce_d43(self):
        v, i = section_full(S_STAR)
        v1, i1, _ = ExactEventMap(Circuit(), CTL).run_cycle(v, i)
        split = (Coss.constant(1.86e-9), Coss.constant(1.86e-9))              # two objects: the per-side path
        v2, i2, _ = NonlinearEventMap(Circuit(), CTL, coss=split).run_cycle(v, i)
        np.testing.assert_allclose(section_free(v2, i2), section_free(v1, i1), atol=1e-6)

    def test_d43_valley_time_is_one_grid_step_early(self):
        emap = ExactEventMap(Circuit(), CTL)
        v, i = section_full(S_STAR)
        for ph in (1, 4):
            old, new = valley_after_lowoff(emap, v, i, ph), nl_valley_after_lowoff(emap, v, i, ph)
            self.assertAlmostEqual((new[0] - old[0]) / emap.h, 1.0, places=6)
            self.assertAlmostEqual(new[1], old[1], places=9)


class CossTests(unittest.TestCase):
    def test_q_is_the_integral_of_c(self):
        co = Coss.from_points(V_PTS, C_PTS)
        v = np.linspace(-30.0, 30.0, 601)
        dq = (co.q(v + 1e-6) - co.q(v - 1e-6)) / 2e-6
        np.testing.assert_allclose(dq, co.c(v), rtol=1e-6)
        self.assertEqual(float(co.q(0.0)), 0.0)


class NonlinearChargeTests(unittest.TestCase):
    def test_hard_merge_conserves_group_charge(self):
        m = NonlinearEventMap(Circuit(), CTL, coss=Coss.from_points(V_PTS, C_PTS))
        ckt = m.ckt
        v, i = section_full(S_STAR)
        v = v.copy(); v[ckt.nodes.index("a1")] = 38.0                  # SH1 turns on against 10 V
        new = m.topo([True, False, False, False, False, True, True, True])
        q0 = m.node_charges(v)
        v2, _ = new.to_full(m.reinit(v, i, new))
        q1 = m.node_charges(v2)
        for grp in {new.root[n] for n in ckt.nodes if new.root[n] in new.free}:
            members = [n for n in ckt.nodes if new.root[n] == grp]
            self.assertAlmostEqual(sum(q1[n] for n in members) / 1e-6, sum(q0[n] for n in members) / 1e-6, places=9)
        self.assertAlmostEqual(v2[ckt.nodes.index("a1")], ckt.vin, places=12)

    def test_reinit_is_identity_without_a_voltage_step(self):
        m = NonlinearEventMap(Circuit(), CTL, coss=Coss.from_points(V_PTS, C_PTS))
        v, i = section_full(S_STAR)
        tp = m.topo([True, False, False, False, False, True, True, True])
        v2, _ = tp.to_full(m.reinit(v, i, tp))
        np.testing.assert_allclose(v2, v, atol=1e-9)


class FloquetJacobianTests(unittest.TestCase):    # D81: the chord matrix is not the derivative at the orbit
    def test_chord_matrix_is_returned_unchanged_at_a_fixed_point(self):
        import json
        from pathlib import Path
        diag = Path(__file__).resolve().parents[1] / "symbolic_derivations" / "03_P24_native" / "diagnostics"
        r = json.loads((diag / "D45_orbits_D.json").read_text())["rows"][5]           # linear Co(tr), 5 %, soft
        emap = ExactEventMap(Circuit(), Control(ton=r["ton_ns"] * 1e-9, i_target=-r["pct"] / 100 * 125.0,
                                                d_high=tuple(x * 1e-9 for x in r["d_ns"]), t_restart_high=20e-9))
        s = np.array(r["section_free"])
        stale = 2.0 * np.eye(len(s))                                                  # moduli 2: "unstable"
        _, J, hist, _ = orbit_chord(emap, s, J=stale)
        self.assertLess(hist[-1], 1e-8)
        self.assertIs(J, stale)                                                       # converged at once, J untouched
        Jf, resid, same = section_jacobian(emap, s)
        self.assertTrue(same)
        self.assertLess(resid, 1e-8)
        self.assertAlmostEqual(max(abs(np.linalg.eigvals(Jf))), 0.98607, delta=1e-4)  # D81 recheck


if __name__ == "__main__":
    unittest.main()
