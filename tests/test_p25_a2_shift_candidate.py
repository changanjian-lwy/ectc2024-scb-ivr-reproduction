"""D38: local affine symmetry is not extrapolated past SH2-on."""
import unittest
from scripts.audit_p25_a2_shift_candidate import run_a2_shift_audit


class A2ShiftCandidateTests(unittest.TestCase):
    def test_candidate_within_derived_window_passes_first_high_handoff(self):
        r=run_a2_shift_audit()
        self.assertEqual(r["pre_SH2_null_column_max"],[0.]*5)
        lo,hi=r["conditional_open_a2_window_v"]
        self.assertLess(lo,r["candidate_a2_v"]); self.assertLess(r["candidate_a2_v"],hi)
        self.assertEqual([s["mode"] for s in r["stages"] if s["accepted_after"] is not None],
                         ["M1","M2","M3","M4","M5"])
        s=r["stages"][4]["accepted_after"]
        self.assertLess(abs(s["node_voltage_v"][0]-s["node_voltage_v"][1]),1e-8)
        self.assertLess(s["inductor_current_a"][1],0.)

    def test_next_high_off_failure_not_hidden_by_local_success(self):
        r=run_a2_shift_audit(); step=r["stages"][-1]
        self.assertEqual(r["failed_mode"],"M6")
        self.assertEqual(step["status"],"HIGH_OFF_EVENT_REJECTED")
        self.assertEqual(step["entry_rise_direction"],"NONPOSITIVE")
        self.assertLess(step["unaccepted_high_off_continuation"]["inductor_current_a"][1],0.)
        self.assertIsNone(r["state_return"])

    def test_grid_refinement_keeps_candidate_and_event_classification(self):
        a,b=run_a2_shift_audit(200),run_a2_shift_audit(400)
        self.assertAlmostEqual(a["candidate_a2_v"],b["candidate_a2_v"],places=10)
        self.assertEqual([s["status"] for s in a["stages"]],[s["status"] for s in b["stages"]])


if __name__=="__main__":unittest.main()
