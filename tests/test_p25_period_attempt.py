"""D19 regression: old failed seed remains failed in the full assembler."""
from dataclasses import replace
import unittest
from unittest.mock import patch
from scb_ivr.p25_control_memory import start_at_high_on,KnownPeak
from scb_ivr.p25_native_events import PeakReference
from scb_ivr.p25_period_attempt import attempt_period
import test_p25_handoff as fixtures


class PeriodAttemptTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.HandoffTests()
        self.fixture.setUp()
        f=self.fixture
        peak=KnownPeak(PeakReference(2,20.,"declared_design_peak","synthetic reference, not measured"),0.)
        self.start=start_at_high_on(f.s,phase=1,peaks=(None,peak,None),policy=f.policy)

    def run_attempt(self,start=None,**changes):
        f=self.fixture
        kwargs=dict(stage_horizons_s=(1.,10.,10.,10.),intervals=200,
                    voltage_root=f.root,current_root=f.root,
                    electrical=f.electrical,direction=f.direction)
        kwargs.update(changes)
        return attempt_period(start or self.start,f.parts,f.ports,f.policy,f.reverse,**kwargs)

    def test_old_seed_still_fails_in_m5_and_keeps_whole_trace(self):
        r=self.run_attempt()
        self.assertEqual(r.status,"STOPPED_AT_UNRESOLVED_STEP")
        self.assertEqual(r.failed_mode,"M5")
        self.assertEqual([s.mode for s in r.steps],["M1","M2","M3","M4","M5"])
        self.assertEqual(r.steps[-1].outcome.scan.candidates,("domain.iL3",))
        self.assertIsNone(r.end)
        for left,right in zip(r.steps,r.steps[1:]):
            self.assertIs(right.before,left.outcome.memory)
        self.assertIs(r.last_accepted,r.steps[-1].before)
        self.assertEqual(r.start,self.start)
        self.assertAlmostEqual(r.steps[-1].outcome.scan.windows[0].latest_s,4.137001278,places=7)

    def test_unknown_peak_stops_at_m3_not_imputed_from_turn_off(self):
        r=self.run_attempt(replace(self.start,peaks=(None,)*3))
        self.assertEqual(r.failed_mode,"M3")
        self.assertIn("peak reference unavailable",r.steps[-1].outcome.reason)
        self.assertEqual(r.last_accepted.peaks,(None,)*3)

    def test_short_search_horizon_is_not_a_forced_gate_or_infeasibility_claim(self):
        r=self.run_attempt(stage_horizons_s=(1e-5,10.,10.,10.))
        self.assertEqual(r.failed_mode,"M2")
        self.assertEqual(r.steps[-1].outcome.scan.status,"NO_DOWNWARD_BRACKET_OBSERVED")
        self.assertIsNone(r.end)
        self.assertNotIn("INFEASIBLE",r.status)

    def test_invalid_or_stale_start_and_horizon_rejected(self):
        for start in (replace(self.start,phase=2),replace(self.start,latched_target_a=-1.)):
            with self.assertRaises(ValueError):
                self.run_attempt(start)
        for horizons in ((1.,)*3,(1.,0.,1.,1.),(1.,float("nan"),1.,1.)):
            with self.assertRaises(ValueError):
                self.run_attempt(stage_horizons_s=horizons)

    def test_injected_state_reset_is_detected(self):
        # Deliberate software fault, not an alternative physical model.
        import scb_ivr.p25_period_attempt as module
        real=module.advance_high_on
        def corrupt(*args,**kwargs):
            r=real(*args,**kwargs)
            s=r.memory.last_event
            bad=replace(s,current_a=(s.current_a[0]+1.,*s.current_a[1:]))
            return replace(r,memory=replace(r.memory,last_event=bad))
        with patch.object(module,"advance_high_on",side_effect=corrupt):
            with self.assertRaisesRegex(RuntimeError,"reset or replaced"):
                self.run_attempt()


if __name__=="__main__":unittest.main()
