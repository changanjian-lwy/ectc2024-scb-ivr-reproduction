import unittest
from scb_ivr import ivr_framework

from scb_ivr.ivr_framework import (
    SystemSpec,
    critical_inductance,
    duty_cycle,
    high_side_on_time,
    inductor_peak_current,
    parallel_embedded_inductors,
    unit_embedded_inductance,
)
from scb_ivr.apec2025_supplements import inductance_for_negative_peak_fraction
from scb_ivr.evidence import Evidence
from scb_ivr.interactive_design import calculate
from scb_ivr.topology_components import paper_topology
from scripts.reproduce_table1_4phase_4module import build_audit
from scb_ivr.ectc2024_mode_spec import (
    BLOCKING_UNCERTAINTIES,
    CONNECTIONS,
    CROSS_PAPER_CANDIDATE_COMMAND_TABLE,
    LEGACY_CROSS_PAPER_PHASE1_TO_PHASE2_CANDIDATE,
    PROJECT_DECISIONS,
    publication_locked_spice_ready,
)
from scb_ivr.p24_operating_sequence import P24_PHASE1_INTERVALS
from scb_ivr.p25_operating_supplement import P25_PHASE1_TO_PHASE2_MODES
from scb_ivr.sequence_resolution import (
    Resolution,
    SEQUENCE_RESOLUTIONS,
    assert_publication_sequence_ready,
    publication_sequence_ready,
)
from scb_ivr.assembly_planner import assemble
from scb_ivr.model_contracts import ExperimentRequest, Module, Slot
from scb_ivr.framework_modules import (
    CANDIDATE_MODULES,
    PRIMARY_EMPTY_SLOTS,
    Compatibility,
    minimum_commutation_current_a,
    primary_slots_complete,
    quarter_cycle_dead_time_s,
)


class PaperEquationTests(unittest.TestCase):
    def setUp(self):
        self.spec = SystemSpec()

    def test_four_phase_duty_cycle(self):
        self.assertAlmostEqual(duty_cycle(self.spec, 4), 1 / 12)

    def test_table1_four_phase_two_module_peak_current(self):
        self.assertAlmostEqual(inductor_peak_current(self.spec, 4, 2), 250.0)

    def test_table1_four_phase_two_module_lcrit_at_1mhz(self):
        value_nh = critical_inductance(self.spec, 4, 2, 1e6) * 1e9
        self.assertAlmostEqual(value_nh, 3.6666666667)

    def test_high_side_on_time_at_5mhz(self):
        value_ns = high_side_on_time(self.spec, 4, 5e6) * 1e9
        self.assertAlmostEqual(value_ns, 16.6666666667)

    def test_p25_generalized_ten_percent_negative_inductance(self):
        result = inductance_for_negative_peak_fraction(
            self.spec, 4, 4, 5e6, 0.10
        )
        value_nh = result.value * 1e9
        self.assertAlmostEqual(value_nh, 1.32)
        self.assertIs(result.evidence, Evidence.CROSS_PAPER_EXTENSION)

    def test_negative_fraction_boundary_is_rejected(self):
        with self.assertRaises(ValueError):
            inductance_for_negative_peak_fraction(self.spec, 4, 4, 5e6, 1.0)

    def test_invalid_frequency_is_rejected(self):
        with self.assertRaises(ValueError):
            high_side_on_time(self.spec, 4, 0.0)

    def test_high_side_on_time_rejects_invalid_phase_count(self):
        with self.assertRaises(ValueError):
            high_side_on_time(self.spec, 0, 5e6)

    def test_p24_formula_core_does_not_export_p25_generalization(self):
        self.assertFalse(
            hasattr(ivr_framework, "inductance_for_negative_peak_fraction")
        )

    def test_invalid_step_down_boundary_is_rejected(self):
        with self.assertRaises(ValueError):
            duty_cycle(SystemSpec(vin_v=4.0, vout_v=1.0), 4)

    def test_table1_eq4_conflict_is_preserved(self):
        calculated_nh = critical_inductance(self.spec, 4, 4, 1e6) * 1e9
        printed_table1_nh = 13.44
        self.assertAlmostEqual(calculated_nh, 7.3333333333)
        self.assertGreater(
            abs(calculated_nh - printed_table1_nh) / printed_table1_nh,
            0.40,
        )

    def test_table1_audit_reports_partial_result_not_reproduction(self):
        report = build_audit()
        self.assertTrue(report["summary"]["eq3_all_rows_pass_tolerance"])
        self.assertFalse(report["summary"]["eq4_matches_table1"])
        self.assertEqual(
            report["summary"]["overall_status"],
            "PARTIAL_WITH_DOCUMENTED_CONFLICT",
        )

    def test_four_phase_module_has_one_output_inductor_per_phase(self):
        inductors = {c.component for c in CONNECTIONS if c.component.startswith("L")}
        self.assertEqual(inductors, {"L1", "L2", "L3", "L4"})

    def test_low_side_reference_is_not_mislabeled_as_2024_explicit(self):
        low_sides = [c for c in CONNECTIONS if c.component.endswith("b")]
        self.assertEqual(len(low_sides), 4)
        self.assertTrue(
            all(c.evidence is not Evidence.P24_EXPLICIT for c in low_sides)
        )

    def test_project_decisions_lock_low_side_and_negative_current_range(self):
        self.assertEqual(
            PROJECT_DECISIONS["U01_LOW_SIDE_REFERENCE"]["status"], "RESOLVED"
        )
        self.assertEqual(
            PROJECT_DECISIONS["U02_NEGATIVE_CURRENT_TARGET"]["p24_value"],
            (0.01, 0.02),
        )
        self.assertEqual(
            PROJECT_DECISIONS["U02_NEGATIVE_CURRENT_TARGET"][
                "p25_mode_text"
            ],
            (0.05, 0.10),
        )
        self.assertEqual(
            PROJECT_DECISIONS["U02_NEGATIVE_CURRENT_TARGET"][
                "selected_bringup_value"
            ],
            0.10,
        )
        self.assertAlmostEqual(
            PROJECT_DECISIONS["U06_INDUCTANCE_CONFLICT"]["selected_lcrit_h"],
            1.4666666666666667e-9,
        )

    def test_cross_paper_candidate_table_has_20_safe_states(self):
        self.assertEqual(len(CROSS_PAPER_CANDIDATE_COMMAND_TABLE), 20)
        for state in CROSS_PAPER_CANDIDATE_COMMAND_TABLE:
            commanded = set(state.commanded_on)
            for phase in range(1, 5):
                self.assertFalse({f"S{phase}a", f"S{phase}b"} <= commanded)

    def test_p24_first_rotation_releases_only_the_next_low_side(self):
        commutation_states = [
            state
            for state in CROSS_PAPER_CANDIDATE_COMMAND_TABLE
            if state.name.endswith("_NEXT_HS_COMMUTATION")
        ]
        self.assertEqual(len(commutation_states), 4)
        for state in commutation_states:
            self.assertNotIn(f"S{state.next_phase}b", state.commanded_on)

    def test_source_sequences_are_separate(self):
        self.assertEqual(len(P24_PHASE1_INTERVALS), 3)
        self.assertEqual(len(P25_PHASE1_TO_PHASE2_MODES), 6)
        self.assertEqual(
            len(LEGACY_CROSS_PAPER_PHASE1_TO_PHASE2_CANDIDATE), 6
        )

    def test_sequence_conflicts_block_compilation(self):
        self.assertFalse(publication_sequence_ready())
        conflicts = [
            item for item in SEQUENCE_RESOLUTIONS
            if item.resolution is Resolution.CONFLICT_REQUIRES_DECISION
        ]
        self.assertEqual(len(conflicts), 2)
        with self.assertRaises(RuntimeError):
            assert_publication_sequence_ready()

    def test_analytical_experiment_assembles_only_requested_capabilities(self):
        request = ExperimentRequest(
            "ANALYTICAL_ONLY",
            frozenset({"duty", "critical_inductance"}),
            frozenset({Evidence.P24_EXPLICIT}),
        )
        plan = assemble(request)
        self.assertTrue(plan.ready)
        self.assertEqual(
            {m.module_id for m in plan.selected_modules},
            {"p24_equations_1_to_6"},
        )

    def test_full_commutation_reports_exact_missing_slots(self):
        request = ExperimentRequest(
            "P24_NUMERIC_COMMUTATION",
            frozenset(
                {
                    "four_phase_power_topology",
                    "phase_local_three_interval_sequence",
                    "symbolic_coss_commutation",
                }
            ),
            frozenset({Evidence.P24_EXPLICIT, Evidence.P25_SUPPLEMENT}),
        )
        plan = assemble(request)
        self.assertFalse(plan.ready)
        self.assertEqual(
            set(plan.missing_capabilities),
            {"commutation_capacitance", "dead_time"},
        )

    def test_external_module_can_fill_one_slot_without_changing_framework(self):
        external = Module(
            "example_device_commutation_data",
            Slot.DEVICE,
            Evidence.EXTERNAL_DEVICE_DATA,
            "device datasheet",
            "Coss and timing table",
            frozenset({"commutation_capacitance", "dead_time"}),
        )
        from scb_ivr.module_registry import MODULES

        request = ExperimentRequest(
            "EXPLORATORY_NUMERIC_COMMUTATION",
            frozenset(
                {
                    "four_phase_power_topology",
                    "phase_local_three_interval_sequence",
                    "symbolic_coss_commutation",
                }
            ),
            frozenset(
                {
                    Evidence.P24_EXPLICIT,
                    Evidence.P25_SUPPLEMENT,
                    Evidence.EXTERNAL_DEVICE_DATA,
                }
            ),
        )
        plan = assemble(request, MODULES + (external,))
        self.assertTrue(plan.ready)
        self.assertIn(external, plan.selected_modules)

    def test_requesting_both_sequence_families_reports_slot_conflict(self):
        request = ExperimentRequest(
            "INVALID_MIXED_SEQUENCE",
            frozenset(
                {
                    "four_phase_power_topology",
                    "phase_local_three_interval_sequence",
                    "p25_cross_phase_handoff_sequence",
                }
            ),
            frozenset({Evidence.P24_EXPLICIT, Evidence.P25_SUPPLEMENT}),
        )
        plan = assemble(request)
        self.assertFalse(plan.ready)
        self.assertTrue(
            any(item.startswith("slot:sequence:") for item in plan.unresolved_conflicts)
        )

    def test_unresolved_items_block_publication_locked_spice(self):
        self.assertEqual(len(BLOCKING_UNCERTAINTIES), 3)
        self.assertFalse(publication_locked_spice_ready())

    def test_primary_slots_stay_unresolved_when_candidates_are_registered(self):
        self.assertFalse(primary_slots_complete())
        self.assertIs(
            PRIMARY_EMPTY_SLOTS.startup_strategy.compatibility,
            Compatibility.UNRESOLVED,
        )
        self.assertEqual(len(CANDIDATE_MODULES["startup_strategy"]), 1)

    def test_no_unrelated_controller_is_silently_inserted(self):
        self.assertEqual(CANDIDATE_MODULES["boundary_controller"], ())

    def test_thesis_commutation_relations_are_executable_but_not_direct(self):
        module = CANDIDATE_MODULES["commutation_parameters"][0]
        self.assertIs(module.compatibility, Compatibility.GENERAL_PHYSICS_ONLY)
        self.assertGreater(quarter_cycle_dead_time_s(180e-9, 1.5e-9), 0)
        self.assertGreater(minimum_commutation_current_a(180e-9, 1.5e-9, 12), 0)

    def test_table3_rounding_difference_is_preserved(self):
        exact, engineering = parallel_embedded_inductors(
            self.spec, phases=4, modules=8, peak_rating_a=5
        )
        self.assertEqual(exact, 12.5)
        self.assertEqual(engineering, 13)

    def test_table3_unit_inductor_at_5mhz(self):
        value_nh = unit_embedded_inductance(
            self.spec, phases=4, switching_frequency_hz=5e6, peak_rating_a=5
        ) * 1e9
        self.assertAlmostEqual(value_nh, 36.6666666667)

    def test_modular_topology_counts(self):
        topology = paper_topology(4, 8, 3, 0.001)
        self.assertEqual(topology.total_electrical_phases, 32)
        self.assertEqual(topology.total_shared_series_capacitors, 24)
        self.assertAlmostEqual(
            topology.phase_template.total_series_resistance_ohm, 0.001
        )

    def test_interactive_record_default_case(self):
        record = calculate(
            {
                "vin_v": 48.0,
                "vout_v": 1.0,
                "pout_w": 1000.0,
                "phases": 4,
                "modules": 8,
                "shared_series_capacitors_per_module": 3,
                "extra_series_resistance_ohm": 0.0,
                "switching_frequency_hz": 5e6,
                "minimum_on_time_s": 3.4e-9,
                "embedded_inductor_peak_rating_a": 5.0,
                "zvs_margin_fraction": 0.015,
            }
        )
        self.assertEqual(record["results"]["total_electrical_phases"], 32)
        self.assertEqual(record["results"]["total_shared_series_capacitors"], 24)
        self.assertEqual(
            record["results"]["parallel_embedded_inductors_engineering"], 13
        )
        self.assertAlmostEqual(
            record["results"]["paper_table1_critical_inductance_nh"], 5.376
        )
        self.assertLess(
            record["results"]["equation4_vs_table1_difference_percent"], -40
        )
        self.assertIn(
            "exploratory_margin_scaled_inductance_nh", record["results"]
        )


if __name__ == "__main__":
    unittest.main()
