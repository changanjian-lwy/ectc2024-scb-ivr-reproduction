"""Tests of the D56 single-phase edge and auxiliary-branch model (src/scb_ivr/extensions/p24_aux_commutation.py; an extension)."""
import json
import unittest
from dataclasses import replace
from pathlib import Path

from scb_ivr.extensions.p24_aux_commutation import AuxBranch, Model, phase_circuits

ORBIT = Path(__file__).resolve().parents[2] / "symbolic_derivations" / "03_P24_native" / "diagnostics" / "D51_orbit_5p0pct_m0p0.json"


class AuxCommutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = Model()

    def test_edge_matches_the_full_model_valley(self):
        # nl_valley_after_lowoff on the full four-phase nonlinear map, phase 1 from D47's 5% state
        for i_neg, v_full in ((6.25, 8.98), (18.75, 5.01), (31.25, 0.77)):
            _, v = self.m.valley_free(i_neg)
            self.assertAlmostEqual(v, v_full, delta=0.05)

    def test_four_phases_match_the_orbit(self):
        orbit = json.loads(ORBIT.read_text())
        for k, ckt in enumerate(phase_circuits(orbit)):
            t, v = Model(ckt).valley_free(-orbit["lowoff_i"][k])
            self.assertAlmostEqual(v, orbit["turnon_vds"][k], delta=0.06)
            self.assertAlmostEqual(t * 1e9, orbit["valley_ns"][k], delta=0.06)

    def test_branch_to_the_output_needs_the_filter_floor(self):
        # with Lr >> Lf the node sees Lf alone: the injected current tends to ~33 A minus the 6.25 A already there
        ir = self.m.min_ir_for_zvs(6.25, AuxBranch(10e-9, "vo", alpha=1.0, r_lr=0.0))
        self.assertGreater(ir, 25.0)
        self.assertLess(ir, 33.0)

    def test_branch_to_a_capacitor_above_half_the_rail_needs_no_boost(self):
        self.assertEqual(self.m.min_ir_for_zvs(6.25, AuxBranch(0.5e-9, "cm", vm=8.0, alpha=1.0, r_lr=0.0)), 0.0)

    def test_capacitor_balance_is_stable(self):
        # the charge drawn from Cm per cycle rises with Vm, so Cm settles at the root
        a = AuxBranch(1.0e-9, "cm", alpha=0.3)
        q_lo = self.m.cycle(6.25, replace(a, vm=7.0))["q_aux"]
        q_hi = self.m.cycle(6.25, replace(a, vm=10.0))["q_aux"]
        self.assertLess(q_lo, 0.0)
        self.assertGreater(q_hi, 0.0)

    def test_no_branch_keeps_the_hard_turn_on(self):
        r = self.m.cycle(6.25)
        self.assertAlmostEqual(r["vds_on"], 8.96, delta=0.05)
        lo, hi = r["a91_bounds"]
        self.assertTrue(lo < r["e_hard_on"] < hi)


if __name__ == "__main__":
    unittest.main()
