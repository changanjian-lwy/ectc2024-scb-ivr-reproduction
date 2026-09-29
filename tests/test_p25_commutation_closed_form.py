"""D24 symbolic expressions checked against the unchanged full KKT network."""
from dataclasses import replace
import unittest
import numpy as np
import test_p25_commutation_cycle as fixtures
from scb_ivr.p25_local_flow import LocalFlow
from scb_ivr.p25_nodal_contract import incidence,SWITCHES
from scb_ivr.p25_cycle_modes import cycle_mode,commutation_target
from scb_ivr.p25_commutation_closed_form import normalized_capacitance


class ClosedFormCommutationTests(unittest.TestCase):
    def test_asymmetric_capacitor_banks_match_full_network_for_every_phase(self):
        f=fixtures.CommutationCycleTests();f.setUp()
        # Deterministic algebra fixtures across scales, not device fitting.
        for scale in (1.,1e-9):
            parts=replace(f.parts,coss_f=tuple(scale*x for x in (1.,2.,3.,4.,5.,6.)),
                          snubber_f=tuple(scale*x for x in (.1,.2,.3,.4,.5,.6)),
                          series_f=(17*scale,19*scale),output_f=23*scale)
            for mode in ("M5","M10","M15"):
                s=f.state(mode)
                flow=LocalFlow(s,parts,mode,f.ports,voltage_tolerance_v=1e-8)
                w=incidence()[1:,SWITCHES.index(commutation_target(mode))]@flow.generator[:6]
                q=cycle_mode(mode).next_phase-1
                cn=normalized_capacitance(s.boundary,parts,mode)
                self.assertAlmostEqual(cn*w[6+q],1.,places=12)
                # Dimensionless normalization of all unused columns.
                np.testing.assert_allclose(np.delete(w,6+q)*cn,0.,atol=1e-12)

    def test_equal_switch_banks_do_not_imply_equal_phase_normalization(self):
        f=fixtures.CommutationCycleTests(); f.setUp()
        values=[normalized_capacitance(f.state(m).boundary,f.parts,m) for m in ("M5","M10","M15")]
        self.assertAlmostEqual(values[0],3.219298245614,places=10)
        self.assertEqual(len(set(values)),3)

    def test_output_capacitance_and_inductance_not_in_instantaneous_transfer_coefficient(self):
        f=fixtures.CommutationCycleTests(); f.setUp()
        varied=replace(f.parts,output_f=99.,inductance_h=(7.,8.,9.))
        for m in ("M5","M10","M15"):
            self.assertEqual(normalized_capacitance(f.state(m).boundary,f.parts,m),
                             normalized_capacitance(f.state(m).boundary,varied,m))
        # These quantities still affect iq(t) and therefore event timing.

    def test_non_native_module_or_down_commutation_rejected(self):
        f=fixtures.CommutationCycleTests();f.setUp();b=f.state("M5").boundary
        with self.assertRaises(ValueError): normalized_capacitance(replace(b,nM=2),f.parts,"M5")
        with self.assertRaises(ValueError): normalized_capacitance(b,f.parts,"M2")


if __name__=="__main__":unittest.main()
