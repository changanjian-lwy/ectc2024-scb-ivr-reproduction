"""D37 preserves path, node residuals and bound applicability."""
import unittest
from scripts.audit_p25_negative_stage_budget import run_negative_budget_audit


class NegativeBudgetTests(unittest.TestCase):
    def test_same_path_budget_distinguishes_before_and_after_target_failure(self):
        a,b = run_negative_budget_audit()["cases"]
        self.assertEqual((a["failed_mode"],b["failed_mode"]),("M4","M5"))
        m4a,m4b = a["stages"][0],b["stages"][0]
        self.assertLess(m4a["integral_Vo_vs"],m4a["required_output_flux_for_negative_target_vs"])
        self.assertAlmostEqual(m4b["integral_Vo_vs"],m4b["required_output_flux_for_negative_target_vs"],places=8)
        self.assertGreater(m4b["final_L1i1_vs"],0.)
        # The gate changes; time, capacitor voltages and currents do not.
        for field in ("time_s","node_voltage_v","inductor_current_a"):
            self.assertEqual(m4b["end"][field],b["stages"][1]["start"][field])
        for c in (a,b):
            for s in c["stages"]:
                self.assertLess(abs(s["flux_balance_residual_vs"]),1e-12)

    def test_decreasing_output_cannot_borrow_previous_monotone_bound(self):
        m5 = run_negative_budget_audit()["cases"][1]["stages"][1]
        self.assertLess(m5["entry_output_derivative_v_s"],0.)
        self.assertEqual(m5["conditional_bound"]["status"],"NOT_APPLICABLE")
        self.assertLess(m5["charge"]["negative_phase_charge_c"],m5["charge"]["required_normalized_charge_c"])
        self.assertNotEqual(m5["integral_x1_vs"],0.)


if __name__ == "__main__":
    unittest.main()
