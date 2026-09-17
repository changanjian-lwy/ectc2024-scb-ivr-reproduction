import unittest

from scb_ivr.parameter_contract import (
    ClaimLevel,
    SWEEP_VARIABLES,
    missing_requirements,
    request_payload,
)


class ParameterContractTests(unittest.TestCase):
    def test_equation_audit_needs_no_unreported_hardware_data(self):
        self.assertEqual(missing_requirements(ClaimLevel.EQUATION_AUDIT), ())

    def test_local_zvs_does_not_request_periodic_or_thermal_inputs(self):
        keys = {item.key for item in missing_requirements(ClaimLevel.LOCAL_ZVS)}
        self.assertIn("nonlinear_qoss_model", keys)
        self.assertIn("dead_time_and_driver_delay", keys)
        self.assertNotIn("flying_capacitor_network", keys)
        self.assertNotIn("thermal_operating_conditions", keys)

    def test_periodic_claim_adds_state_charge_and_scheduler_inputs(self):
        keys = {
            item.key
            for item in missing_requirements(ClaimLevel.PERIODIC_MULTIPHASE)
        }
        self.assertIn("flying_capacitor_network", keys)
        self.assertIn("complete_gate_timing_policy", keys)
        self.assertIn("periodic_state_or_waveforms", keys)

    def test_supplied_parameter_is_removed_from_request(self):
        missing = missing_requirements(
            ClaimLevel.LOCAL_ZVS, {"nonlinear_qoss_model"}
        )
        self.assertNotIn("nonlinear_qoss_model", {item.key for item in missing})

    def test_request_payload_is_machine_readable(self):
        payload = request_payload(ClaimLevel.LOCAL_ZVS)
        self.assertEqual(payload["target_claim"], "LOCAL_ZVS")
        self.assertTrue(payload["missing"])
        self.assertTrue(payload["safe_sweeps_while_waiting"])

    def test_safe_sweeps_do_not_erase_source_branches(self):
        negative = next(
            item for item in SWEEP_VARIABLES if item.key == "negative_current_fraction"
        )
        self.assertIn("P24 native 1-2%", negative.range_or_rule)
        self.assertIn("P25 supplement 5-10%", negative.range_or_rule)


if __name__ == "__main__":
    unittest.main()
