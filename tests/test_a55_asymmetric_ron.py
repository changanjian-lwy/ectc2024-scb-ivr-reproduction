import json
import runpy
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MODULE = (
    ROOT
    / "experiments"
    / "track_A_periodic_steady_state"
    / "A55_joint_lphase_deadtime_total_loss_optimization"
    / "asymmetric_ron_dynamics.py"
)


class A55AsymmetricRonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = runpy.run_path(str(MODULE))

    def test_effective_resistances_are_population_corrected(self):
        boundary = self.module["AsymmetricRonBoundary"]()
        self.assertAlmostEqual(boundary.high_side_on_resistance_ohm, 1.55e-3 / 2)
        self.assertAlmostEqual(boundary.low_side_on_resistance_ohm, 1.55e-3 / 3)

    def test_low_side_matrix_differs_from_uniform_reference_by_expected_conductance(self):
        D = self.module["D"]
        boundary = self.module["AsymmetricRonBoundary"]()
        mode = D.Mode(
            high_side_on=(True, False, False, False),
            low_side_on=(False, True, True, True),
            precharge_diode_on=(False, False, False),
        )
        original = self.module["ORIGINAL_ASSEMBLE_DESCRIPTOR"](boundary, mode, 0.0)
        corrected = self.module["assemble_descriptor"](boundary, mode, 0.0)
        delta = corrected.a - original.a
        node_index = {name: index for index, name in enumerate(corrected.node_names)}
        expected_x2_diagonal = (
            1.0 / boundary.low_side_on_resistance_ohm
            - 1.0 / boundary.switch_on_resistance_ohm
        )
        self.assertAlmostEqual(delta[node_index["x2"], node_index["x2"]], expected_x2_diagonal)
        self.assertAlmostEqual(delta[node_index["vin"], node_index["vin"]], 0.0)
        self.assertTrue(np.allclose(delta, delta.T))

    def test_context_restores_historical_module_hooks(self):
        M = self.module["M"]
        H = self.module["H"]
        old_m = M.assemble_descriptor
        old_h = H.assemble_descriptor
        with self.module["asymmetric_ron_context"]():
            self.assertIs(M.assemble_descriptor, self.module["assemble_descriptor"])
            self.assertIs(H.assemble_descriptor, self.module["assemble_descriptor"])
        self.assertIs(M.assemble_descriptor, old_m)
        self.assertIs(H.assemble_descriptor, old_h)

    def test_nominal_smoke_converges_inside_current_limit(self):
        payload = json.loads(
            (MODULE.parent / "asymmetric_nominal_smoke.json").read_text()
        )
        self.assertEqual(
            payload["classification"], "DYNAMICS_GATE_NOMINAL_SMOKE_ONLY"
        )
        self.assertTrue(payload["not_an_optimization"])
        self.assertTrue(payload["solve"]["converged"])
        self.assertLess(payload["solve"]["relative_residual"], 1e-9)
        self.assertTrue(payload["solve"]["within_current_limit"])

    def test_nominal_smoke_keeps_unmodelled_dead_time_visible(self):
        payload = json.loads(
            (MODULE.parent / "asymmetric_nominal_smoke.json").read_text()
        )
        self.assertTrue(
            payload["path_check"]["unmodelled_dead_time_current_present"]
        )
        self.assertFalse(payload["path_check"]["complete_total_loss"])

    def test_critical_and_margin_recalculations_converge_safely(self):
        payload = json.loads(
            (MODULE.parent / "asymmetric_baseline_points.json").read_text()
        )
        for name in ("critical", "margin"):
            point = payload["points"][name]
            self.assertTrue(point["converged"])
            self.assertLess(point["relative_residual"], 1e-8)
            self.assertTrue(point["within_current_limit"])

    def test_old_a54_critical_point_is_not_all_phase_zvs_after_dynamics_correction(self):
        payload = json.loads(
            (MODULE.parent / "asymmetric_baseline_points.json").read_text()
        )
        self.assertEqual(
            payload["points"]["critical"]["natural_zvs_flags"],
            [False, False, False, True],
        )
        self.assertEqual(
            payload["points"]["margin"]["natural_zvs_flags"],
            [True, True, True, True],
        )

    def test_recalculated_points_remain_partial_loss_only(self):
        payload = json.loads(
            (MODULE.parent / "asymmetric_baseline_points.json").read_text()
        )
        for point in payload["points"].values():
            self.assertTrue(point["unmodelled_dead_time_current_present"])
            self.assertFalse(point["complete_total_loss"])


if __name__ == "__main__":
    unittest.main()
