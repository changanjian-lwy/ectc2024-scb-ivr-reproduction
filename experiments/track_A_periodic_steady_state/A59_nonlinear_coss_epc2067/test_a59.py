"""A59 proofs (BOUNDARY.md Section 2). Run from this directory: python3 test_a59.py -v"""
import json
import unittest

import numpy as np

import a59_nonlinear as N

S, R = N.S, N.R
A58_RUN = json.loads((N.A58_DIR / "runs" / "zvs_r1.900_f0.600.json").read_text())
Z = np.array(A58_RUN["regulated"]["z_star"])
KW = dict(phase_inductance_h=A58_RUN["phase_inductance_h"], dead_time_rise_s=1.9e-9,
          dead_time_fall_s=0.6e-9, ton_cmd_s=A58_RUN["regulated"]["ton_cmd_s"])


def newton_map(boundary):
    with R.asymmetric_ron_context():
        return R.S.evaluate_period_map_with_rms(boundary, Z, coarse_step_s=62.5e-12, sub_step_s=5e-12)


class Model(unittest.TestCase):
    def test_matches_printed_typical_values(self):
        m = N.MODELS["fig5a_pchip"]
        grid = np.linspace(0, 20, 20001)
        q20 = float(m.q(20.0))
        e20 = float(np.trapezoid(grid * m.c(grid), grid))
        self.assertAlmostEqual(q20 / 37e-9, 1.0, delta=0.02)            # Qoss typ
        self.assertAlmostEqual(q20 / 20 / 1860e-12, 1.0, delta=0.01)     # Co(tr) typ
        self.assertAlmostEqual(2 * e20 / 400 / 1597e-12, 1.0, delta=0.01)  # Co(er) typ
        self.assertAlmostEqual(float(m.c(20.0)) / 1071e-12, 1.0, delta=0.02)  # Coss(20 V) typ

    def test_charge_is_antiderivative_and_extension_is_odd_even(self):
        m = N.MODELS["fig5a_pchip"]
        v = np.linspace(-30, 45, 751)
        h = 1e-4
        self.assertTrue(np.allclose((m.q(v + h) - m.q(v - h)) / (2 * h), m.c(v), rtol=1e-3))
        self.assertTrue(np.allclose(m.q(-v), -m.q(v)))
        self.assertTrue(np.all(np.diff(m.c(np.linspace(0, 40, 401))) <= 1e-15))  # non-increasing


class Stepper(unittest.TestCase):
    def test_swap_is_complete_and_restored(self):
        before = N.holders()
        self.assertEqual(len(before), 2)
        with N.nonlinear_coss_context():
            self.assertEqual(N.holders(), [])
        self.assertEqual(N.holders(), before)

    def test_linear_charge_model_reproduces_linear_solver(self):
        with S.asym_schedule_context(), N.nonlinear_coss_context():
            linear = newton_map(S.build_asym_boundary(**KW))
            charge = newton_map(N.build_nl_boundary(**KW, coss_model_id="linear_cotr"))
        rel = np.max(np.abs(charge.z_next - linear.z_next)) / np.max(np.abs(linear.z_next))
        self.assertLess(rel, 1e-10)

    def test_nonlinear_newton_converges_and_changes_the_orbit(self):
        N.NEWTON_STATS.update(steps=0, iterations=0, max_iterations=0)
        with S.asym_schedule_context(), N.nonlinear_coss_context():
            linear = newton_map(S.build_asym_boundary(**KW))
            nonlinear = newton_map(N.build_nl_boundary(**KW))
        self.assertGreater(N.NEWTON_STATS["steps"], 1000)
        self.assertLessEqual(N.NEWTON_STATS["max_iterations"], 5)
        self.assertGreater(np.max(np.abs(nonlinear.z_next - linear.z_next)), 1e-3)

    def test_boundary_survives_asdict_comparison(self):
        from dataclasses import asdict
        b = N.build_nl_boundary(**KW)
        self.assertEqual(asdict(b), asdict(N.build_nl_boundary(**KW)))
        self.assertEqual(b.dead_time_s, 0.5 * (1.9e-9 + 0.6e-9))


if __name__ == "__main__":
    unittest.main()
