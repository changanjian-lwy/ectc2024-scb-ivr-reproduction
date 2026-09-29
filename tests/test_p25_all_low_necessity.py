"""D22 symbolic-order tests against unchanged synthetic affine trajectories."""
from dataclasses import replace
import unittest
import test_p25_three_phase_handoff as fixtures
from scb_ivr.p25_all_low_necessity import all_low_necessity
from scb_ivr.p25_handoff import reach_next_current_zero
from scb_ivr.p25_negative_handoff import reach_negative_target


class AllLowNecessityTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.ThreePhaseHandoffTests(); self.f.setUp()

    def check(self,m,parts=None):
        return all_low_necessity(m.last_event,parts or self.f.parts,
            f"M{5*(m.phase-1)+3}",negative_target_a=-1.,flux_tolerance_vs=1e-8)

    def test_all_three_exact_budgets_match_dynamic_output_integration(self):
        for p in (1,2,3):
            m=self.f.fixture(p); a=self.check(m)
            n=self.f.invoke(reach_next_current_zero,m).memory
            n=self.f.invoke(reach_negative_target,n,current_rate_tolerance_a_s=1e-10).memory
            self.assertEqual(a.status,"NECESSARY_CURRENT_ORDER_PASSED_NOT_SUFFICIENT")
            for row in a.rows:
                actual=self.f.parts.inductance_h[row.phase-1]*n.last_event.current_a[row.phase-1]
                self.assertAlmostEqual(row.margin_at_target_vs,actual,places=7)

    def test_small_other_phase_budget_proves_early_zero(self):
        for p in (1,2,3):
            m=self.f.fixture(p); i=list(m.last_event.current_a); i[p-1]=.001
            m=replace(m,last_event=replace(m.last_event,current_a=tuple(i)))
            a=self.check(m)
            self.assertEqual(a.status,"TARGET_BEFORE_ALL_OTHER_ZEROS_IMPOSSIBLE")
            r=self.f.invoke(reach_next_current_zero,m)
            self.assertEqual(r.scan.candidates,(f"domain.iL{p}",))

    def test_equal_budget_is_not_strict_success(self):
        m=self.f.fixture(1)
        # q=2: required=3*(.5+1)=4.5 V*s; phase1 budget=2*2.25.
        m=replace(m,last_event=replace(m.last_event,current_a=(2.25,.5,20.)))
        self.assertEqual(self.check(m).status,"NECESSARY_CHECK_INCOMPLETE")

    def test_nonzero_node_residual_is_not_deleted(self):
        m=self.f.fixture(1)
        v=list(m.last_event.voltage_v); v[2]=1e-14
        a=self.check(replace(m,last_event=replace(m.last_event,voltage_v=tuple(v))))
        self.assertEqual(a.unsupported_phases,(1,))
        self.assertEqual(a.status,"NECESSARY_CHECK_INCOMPLETE")
        v[3]=1e-14
        with self.assertRaises(ValueError):
            self.check(replace(m,last_event=replace(m.last_event,voltage_v=tuple(v))))

    def test_winding_resistance_not_silently_omitted(self):
        m=self.f.fixture(1)
        a=self.check(m,replace(self.f.parts,winding_ohm=(.001,0.,0.)))
        self.assertEqual(a.unsupported_phases,(1,))
        with self.assertRaises(ValueError):
            self.check(m,replace(self.f.parts,winding_ohm=(0.,.001,0.)))


if __name__=="__main__": unittest.main()
