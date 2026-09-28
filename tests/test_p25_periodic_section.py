from dataclasses import replace
import unittest

from scb_ivr.p25_control_memory import Policy, KnownPeak, start_at_high_on, gate_pattern, Stage
from scb_ivr.p25_event_guards import Snapshot
from scb_ivr.p25_native_events import NativeBoundary, PeakReference
from scb_ivr.p25_nodal_contract import Components
from scb_ivr.p25_reverse_contract import ReverseModel
from scb_ivr.p25_periodic_section import (
    ModelIdentity, ReturnTolerance, Coordinate, compare_sections, scaled_residual,
)


class PeriodicSectionTests(unittest.TestCase):
    def setUp(self):
        self.policy=Policy((2.,)*3,1e-9,1e-9,1e-9,True,"synthetic ideal")
        self.peaks=tuple(KnownPeak(PeakReference(k,10.,"declared_design_peak","synthetic reference policy"),0.) for k in (1,2,3))
        s=Snapshot(NativeBoundary(3,1,1,"dynamic_Co_current_ports",.05),"synthetic","absolute",0,0.,12.,
                   (12.,4.,4.,0.,0.,1.),(-.5,1.,1.),gate_pattern(1,Stage.RISE))
        self.a=start_at_high_on(s,phase=1,peaks=self.peaks,policy=self.policy)
        self.b=start_at_high_on(replace(s,time_s=18.,cycle=1),phase=1,peaks=self.peaks,policy=self.policy)
        parts=Components((2.,3.,5.,7.,11.,13.),(0.,)*6,(17.,19.),23.,(2.,3.,4.),(0.,)*3,"synthetic")
        self.model=ModelIdentity(parts,ReverseModel("ideal_zero_drop",(0.,)*6,"synthetic"),self.policy,"declared_port_law")
        self.tol=ReturnTolerance(1e-6,1e-6,1e-6,1e-6)

    def compare(self,b=None,**kw):
        args=dict(start_model=self.model,end_model=self.model,tolerance=self.tol)
        args.update(kw)
        return compare_sections(self.a,b or self.b,**args)

    def test_absolute_clock_does_not_have_to_return(self):
        r=self.compare()
        self.assertTrue(r.state_returns)
        self.assertEqual(r.period_s,18.)
        self.assertIn("unverified",r.scope)

    def test_same_output_but_changed_coss_state_fails(self):
        s=replace(self.b.last_event,voltage_v=(12.,4.1,4.,0.,0.,1.))
        r=self.compare(replace(self.b,last_event=s))
        self.assertFalse(r.state_returns)
        self.assertTrue(any(x.name=="V_SH2" and x.scaled>1 for x in r.residuals))

    def test_controller_memory_cannot_be_omitted(self):
        p=list(self.b.peaks);p[1]=replace(p[1],reference=replace(p[1].reference,amperes=11.))
        self.assertFalse(self.compare(replace(self.b,peaks=tuple(p))).state_returns)

    def test_measured_peak_age_is_relative_time_not_absolute_timestamp(self):
        a=tuple(KnownPeak(replace(p.reference,basis="previous_measured_peak"),-2.) for p in self.peaks)
        b=tuple(replace(p,available_at_s=16.) for p in a)
        self.a=replace(self.a,peaks=a)
        self.assertTrue(self.compare(replace(self.b,peaks=b)).state_returns)
        self.assertFalse(self.compare(replace(self.b,peaks=a)).state_returns)

    def test_missing_peak_is_not_zero(self):
        with self.assertRaisesRegex(ValueError,"unresolved"):
            self.compare(replace(self.b,peaks=(self.peaks[0],None,self.peaks[2])))

    def test_changed_capacitance_or_port_boundary_rejected(self):
        for model in (replace(self.model,components=replace(self.model.components,output_f=24.)),
                      replace(self.model,port_model_id="ideal_1V_clamp")):
            with self.assertRaisesRegex(ValueError,"boundary changed"):
                self.compare(end_model=model)

    def test_wrong_section_or_skipped_cycle_rejected(self):
        with self.assertRaises(ValueError): self.compare(replace(self.b,phase=2))
        with self.assertRaises(ValueError): self.compare(replace(self.b,last_event=replace(self.b.last_event,cycle=2)))

    def test_unit_rescaling_does_not_change_normalized_result(self):
        a,b=Coordinate("v","V",1.),Coordinate("v","V",1.0001)
        r=scaled_residual(a,b,self.tol).scaled
        # Numerically represent mV with the correspondingly rescaled voltage tolerance.
        s=scaled_residual(replace(a,value=a.value*1000),replace(b,value=b.value*1000),
                          replace(self.tol,voltage_v=self.tol.voltage_v*1000)).scaled
        self.assertAlmostEqual(r,s,places=7)

    def test_large_current_cannot_hide_small_voltage_error(self):
        b=replace(self.b,last_event=replace(self.b.last_event,voltage_v=(12.,4.,4.,0.,0.,1.001)))
        self.a=replace(self.a,last_event=replace(self.a.last_event,current_a=(-.5,10000.,10000.)))
        b=replace(b,last_event=replace(b.last_event,current_a=self.a.last_event.current_a))
        self.assertFalse(self.compare(b).state_returns)

    def test_stale_target_and_changed_peak_basis_rejected(self):
        with self.assertRaises(ValueError):self.compare(replace(self.b,latched_target_a=-.5))
        ps=list(self.b.peaks);ps[0]=replace(ps[0],reference=replace(ps[0].reference,source="different policy"))
        with self.assertRaises(ValueError):self.compare(replace(self.b,peaks=tuple(ps)))
