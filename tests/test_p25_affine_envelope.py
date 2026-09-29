"""D39 analytic comparison bound, floating-point regression only."""
import unittest
import numpy as np
import test_p25_commutation_cycle as fixtures
from scb_ivr.p25_affine_envelope import affine_envelope
from scripts.audit_p25_zvs_rise_window import run_rise_window_audit


class AffineEnvelopeTests(unittest.TestCase):
    def test_zero_duration_retains_entry_residuals(self):
        f=fixtures.CommutationCycleTests();f.setUp();flow=f.flow("M5")
        b=affine_envelope(flow,flow.start.time_s)
        self.assertEqual(b.change_bound,(0.,)*9)
        self.assertEqual(b.lower,(*flow.start.voltage_v,*flow.start.current_a))

    def test_six_modes_sampled_regression_stays_inside_analytic_envelope(self):
        f=fixtures.CommutationCycleTests();f.setUp()
        for mode in ("M2","M5","M7","M10","M12","M15"):
            flow=f.flow(mode);b=affine_envelope(flow,.1)
            for t in np.linspace(0,.1,21):
                s=flow.at(t);y=np.r_[s.voltage_v,s.current_a]
                self.assertTrue(np.all(y>=np.array(b.lower)-1e-12))
                self.assertTrue(np.all(y<=np.array(b.upper)+1e-12))

    def test_d38_full_window_has_negative_rise_upper_bound(self):
        r=run_rise_window_audit()
        self.assertEqual(r["rise_status"],"POSITIVE_ENTRY_RISE_EXCLUDED_ON_DECLARED_WINDOW")
        self.assertLess(r["inductor_voltage_upper_v"],-1.)
        self.assertLess(r["current_derivative_upper_a_s"],0.)

    def test_backward_endpoint_rejected(self):
        f=fixtures.CommutationCycleTests();f.setUp()
        with self.assertRaises(ValueError):affine_envelope(f.flow("M5"),-.1)


if __name__=="__main__":unittest.main()
