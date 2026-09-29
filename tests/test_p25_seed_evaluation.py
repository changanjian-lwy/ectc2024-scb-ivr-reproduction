"""D21 synthetic failure diagnostics; complete-cycle success is not asserted."""
from dataclasses import replace
import unittest
import test_p25_period_attempt as fixtures
from scb_ivr.p25_control_memory import KnownPeak
from scb_ivr.p25_native_events import PeakReference
from scb_ivr.p25_periodic_section import ModelIdentity,ReturnTolerance
from scb_ivr.p25_shooting_contract import ShootingContract,SectionSeed
from scb_ivr.p25_seed_evaluation import evaluate_seed


class SeedEvaluationTests(unittest.TestCase):
    def setUp(self):
        base=fixtures.PeriodAttemptTests(); base.setUp()
        self.f=base.fixture
        peaks=tuple(KnownPeak(PeakReference(k,20.,"declared_design_peak","synthetic fixed references"),0.)
                    for k in (1,2,3))
        anchor=replace(base.start,peaks=peaks)
        model=ModelIdentity(self.f.parts,self.f.reverse,self.f.policy,"constant synthetic current")
        self.contract=ShootingContract(anchor,model,self.f.ports,"D21 synthetic fixed-reference diagnostic")
        self.seed=SectionSeed(4.,2.,1.,(20.,2.,3.))

    def evaluate(self, seed=None, **changes):
        f=self.f
        options=dict(return_tolerance=ReturnTolerance(1e-8,1e-8,1e-9,0.),
                     stage_horizons_s=(1.,10.,10.,10.),intervals=200,
                     voltage_root=f.root,current_root=f.root,electrical=f.electrical,direction=f.direction)
        options.update(changes)
        return evaluate_seed(self.contract,seed or self.seed,**options)

    def test_old_seed_has_no_fabricated_residual(self):
        r=self.evaluate()
        self.assertEqual(r.status,"TRAJECTORY_UNRESOLVED_NO_RETURN_RESIDUAL")
        self.assertEqual(r.attempt.failed_mode,"M5")
        self.assertEqual(r.attempt.steps[-1].outcome.scan.candidates,("domain.iL3",))
        self.assertIsNone(r.state_return)
        self.assertEqual(r.attempt.start.peaks,self.contract.anchor.peaks)

    def test_horizon_exhaustion_cannot_be_called_nonclosure(self):
        r=self.evaluate(stage_horizons_s=(1e-5,10.,10.,10.))
        self.assertEqual(r.status,"TRAJECTORY_UNRESOLVED_NO_RETURN_RESIDUAL")
        self.assertEqual(r.attempt.failed_mode,"M2")
        self.assertIsNone(r.state_return)

    def test_invalid_seed_or_missing_tolerance_not_converted_to_penalty(self):
        with self.assertRaises(ValueError):
            self.evaluate(replace(self.seed,a2_v=13.))
        with self.assertRaises(ValueError):
            self.evaluate(return_tolerance=None)


if __name__=="__main__":unittest.main()
