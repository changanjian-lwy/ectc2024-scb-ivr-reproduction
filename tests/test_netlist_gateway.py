import unittest

from assembly_planner import assemble
from evidence import Evidence
from experiment_profiles import R04A_LOCAL_BOUNDARY_REPLAY
from four_phase_readiness import (
    P24_SINGLE_MODULE_FOUR_PHASE,
    readiness_report,
)
from netlist_gateway import generate_netlist


def tiny_emitter(plan, parameters):
    return f"V1 in 0 {parameters['vin']}\n.end"


class NetlistGatewayTests(unittest.TestCase):
    def test_ready_plan_emits_provenance_header(self):
        plan = assemble(R04A_LOCAL_BOUNDARY_REPLAY)
        result = generate_netlist(plan, {"vin": 48.0}, tiny_emitter)
        self.assertTrue(result.generated)
        self.assertIn("experiment_id=R04A_LOCAL_BOUNDARY_REPLAY", result.text)
        self.assertIn("evidence=P24_EXPLICIT", result.text)

    def test_blocked_four_phase_plan_emits_no_netlist(self):
        plan = assemble(P24_SINGLE_MODULE_FOUR_PHASE)
        result = generate_netlist(plan, {"vin": 48.0}, tiny_emitter)
        self.assertFalse(result.generated)
        self.assertIsNone(result.text)
        self.assertTrue(any("startup_initialization" in x for x in result.blockers))

    def test_four_phase_report_assigns_every_missing_capability(self):
        report = readiness_report()
        self.assertFalse(report["ready"])
        self.assertTrue(report["missing"])
        self.assertTrue(
            all(item["responsible_slot"] != "unassigned interface" for item in report["missing"])
        )


if __name__ == "__main__":
    unittest.main()
