"""D20 coordinate and boundary tests, not a periodic solution."""
from dataclasses import replace
import unittest
import test_p25_high_on as fixtures
from scb_ivr.p25_control_memory import KnownPeak
from scb_ivr.p25_native_events import PeakReference
from scb_ivr.p25_periodic_section import ModelIdentity
from scb_ivr.p25_shooting_contract import ShootingContract,SectionSeed,SEED_COORDINATES


class ShootingContractTests(unittest.TestCase):
    def setUp(self):
        f=fixtures.HighOnTests(); f.setUp(); self.f=f
        peaks=tuple(KnownPeak(PeakReference(k,20.,"declared_design_peak","synthetic fixed reference"),0.)
                    for k in (1,2,3))
        self.anchor=replace(f.memory(1),peaks=peaks)
        self.model=ModelIdentity(f.parts,f.reverse,f.policy,"constant synthetic current ports")
        self.contract=ShootingContract(self.anchor,self.model,f.ports,"synthetic fixed-boundary seed audit")

    def test_six_coordinates_preserve_all_fixed_fields(self):
        seed=SectionSeed(5.,3.,1.1,(-.1,18.,19.))
        m=self.contract.make_candidate(seed)
        self.assertEqual(len(SEED_COORDINATES),6)
        self.assertEqual(m.last_event.voltage_v,(12.,5.,3.,0.,0.,1.1))
        self.assertEqual(m.last_event.current_a,seed.current_a)
        self.assertEqual(m.peaks,self.anchor.peaks)
        self.contract.assert_frozen(m,self.model,self.f.ports)

    def test_measured_or_missing_peaks_cannot_enter_fixed_design_branch(self):
        for peaks in ((None,)*3,tuple(replace(p,reference=replace(p.reference,basis="previous_measured_peak"))
                                    for p in self.anchor.peaks)):
            with self.assertRaises(ValueError):
                replace(self.contract,anchor=replace(self.anchor,peaks=peaks))

    def test_fitting_peak_or_alpha_is_detected(self):
        m=self.contract.make_candidate(SectionSeed(4.,2.,1.,(-.1,20.,20.)))
        peaks=list(m.peaks); peaks[0]=replace(peaks[0],reference=replace(peaks[0].reference,amperes=21.))
        bad=replace(m,peaks=tuple(peaks))
        with self.assertRaises(ValueError): self.contract.assert_frozen(bad,self.model,self.f.ports)
        bad=replace(m,last_event=replace(m.last_event,boundary=replace(m.last_event.boundary,alpha=.08)))
        with self.assertRaises(ValueError): self.contract.assert_frozen(bad,self.model,self.f.ports)

    def test_device_time_and_output_port_mutations_rejected(self):
        for model in (replace(self.model,components=replace(self.f.parts,output_f=24.)),
                      replace(self.model,control=replace(self.f.policy,on_time_s=(.03,)*3))):
            with self.assertRaises(ValueError):
                self.contract.assert_frozen(self.anchor,model,self.f.ports)
        with self.assertRaises(ValueError):
            self.contract.assert_frozen(self.anchor,self.model,replace(self.f.ports,load_current_a=2.))

    def test_off_gap_and_gate_residual_not_repaired(self):
        with self.assertRaises(ValueError):
            self.contract.make_candidate(SectionSeed(13.,2.,1.,(-.1,20.,20.)))
        s=replace(self.anchor.last_event,voltage_v=(12.,4.,4.,1e-12,0.,1.))
        with self.assertRaises(ValueError):
            replace(self.contract,anchor=replace(self.anchor,last_event=s))


if __name__=="__main__":unittest.main()
