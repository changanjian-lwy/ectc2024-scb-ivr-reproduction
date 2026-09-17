import unittest

from scb_ivr.assembly_planner import assemble
from scb_ivr.candidate_adapters import CANDIDATE_ADAPTERS
from scb_ivr.evidence import Evidence
from scb_ivr.four_phase_readiness import P24_SINGLE_MODULE_FOUR_PHASE
from scb_ivr.model_contracts import ExperimentRequest, Slot
from scb_ivr.module_registry import MODULES


class CandidateAdapterTests(unittest.TestCase):
    def test_candidates_do_not_fill_primary_capability_names(self):
        request = ExperimentRequest(
            P24_SINGLE_MODULE_FOUR_PHASE.experiment_id,
            P24_SINGLE_MODULE_FOUR_PHASE.required_capabilities,
            P24_SINGLE_MODULE_FOUR_PHASE.allowed_evidence
            | frozenset({Evidence.CROSS_PAPER_EXTENSION}),
        )
        plan = assemble(request, MODULES + CANDIDATE_ADAPTERS)
        self.assertFalse(plan.ready)
        self.assertIn("negative_current_detector", plan.missing_capabilities)
        self.assertIn("startup_initialization", plan.missing_capabilities)

    def test_candidate_use_exposes_compatibility_requirement(self):
        request = ExperimentRequest(
            "STARTUP_CANDIDATE_AUDIT",
            frozenset({"candidate_startup_initialization"}),
            frozenset({Evidence.CROSS_PAPER_EXTENSION}),
            preferred_modules={Slot.STARTUP: "epe2019_auxiliary_startup_candidate"},
        )
        plan = assemble(request, CANDIDATE_ADAPTERS)
        self.assertFalse(plan.ready)
        self.assertEqual(
            plan.missing_capabilities,
            ("p24_startup_topology_compatibility",),
        )


if __name__ == "__main__":
    unittest.main()
