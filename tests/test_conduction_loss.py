import unittest

from scb_ivr.conduction_loss import (
    PathI2Accumulator,
    PathI2Integrals,
    path_resolved_conduction_loss,
)
from scb_ivr.device_library import (
    CapacitanceView,
    EPC2067,
    P24_EPC2067_POPULATION,
)


class ConductionLossTests(unittest.TestCase):
    def test_epc2067_population_changes_resistance_in_opposite_direction_to_capacitance(self):
        population = P24_EPC2067_POPULATION
        self.assertAlmostEqual(EPC2067.rds_on(population.high_side_parallel), 0.775e-3)
        self.assertAlmostEqual(
            EPC2067.rds_on(population.low_side_parallel), 1.55e-3 / 3
        )
        self.assertAlmostEqual(
            EPC2067.capacitance(
                CapacitanceView.TIME_EQUIVALENT,
                population.high_side_parallel,
            ),
            3720e-12,
        )

    def test_path_resolved_loss_uses_high_and_low_side_effective_resistance(self):
        period = 200e-9
        # One phase carrying 10 A: high side for 25% and low side for 75%.
        integrals = PathI2Integrals(
            period_s=period,
            high_side_a2s=(100.0 * 0.25 * period,),
            low_side_a2s=(100.0 * 0.75 * period,),
            dead_time_a2s=(0.0,),
        )
        result = path_resolved_conduction_loss(
            EPC2067, P24_EPC2067_POPULATION, integrals
        )
        expected = 25.0 * 0.775e-3 + 75.0 * (1.55e-3 / 3)
        self.assertAlmostEqual(result.modeled_loss_w, expected)
        self.assertFalse(result.has_unmodeled_dead_time_current)
        self.assertFalse(result.is_complete_total_loss)

    def test_dead_time_current_is_exposed_not_silently_counted_as_channel_loss(self):
        period = 200e-9
        integrals = PathI2Integrals(
            period_s=period,
            high_side_a2s=(0.0, 0.0),
            low_side_a2s=(0.0, 0.0),
            dead_time_a2s=(4.0 * period, 0.0),
        )
        result = path_resolved_conduction_loss(
            EPC2067, P24_EPC2067_POPULATION, integrals
        )
        self.assertEqual(result.modeled_loss_w, 0.0)
        self.assertTrue(result.has_unmodeled_dead_time_current)
        self.assertEqual(result.dead_time_i2_average_a2_per_phase, (4.0, 0.0))

    def test_mismatched_phase_vectors_are_rejected(self):
        with self.assertRaises(ValueError):
            PathI2Integrals(
                period_s=200e-9,
                high_side_a2s=(1.0,),
                low_side_a2s=(1.0, 2.0),
                dead_time_a2s=(0.0,),
            )

    def test_negative_integral_is_rejected(self):
        with self.assertRaises(ValueError):
            PathI2Integrals(
                period_s=200e-9,
                high_side_a2s=(-1.0,),
                low_side_a2s=(0.0,),
                dead_time_a2s=(0.0,),
            )

    def test_accumulator_separates_high_low_and_dead_time_paths(self):
        accumulator = PathI2Accumulator(phase_count=2)
        accumulator.observe(
            time_s=0.0,
            phase_currents_a=(10.0, 20.0),
            high_side_on=(True, False),
            low_side_on=(False, True),
        )
        accumulator.observe(
            time_s=1.0,
            phase_currents_a=(10.0, 20.0),
            high_side_on=(True, False),
            low_side_on=(False, True),
        )
        accumulator.observe(
            time_s=2.0,
            phase_currents_a=(5.0, 4.0),
            high_side_on=(False, False),
            low_side_on=(False, True),
        )
        result = accumulator.integrals(period_s=2.0)
        self.assertEqual(result.high_side_a2s, (100.0, 0.0))
        self.assertEqual(result.low_side_a2s, (0.0, 416.0))
        self.assertEqual(result.dead_time_a2s, (25.0, 0.0))

    def test_accumulator_rejects_shoot_through_sample(self):
        accumulator = PathI2Accumulator(phase_count=1)
        with self.assertRaises(ValueError):
            accumulator.observe(
                time_s=0.0,
                phase_currents_a=(1.0,),
                high_side_on=(True,),
                low_side_on=(True,),
            )


if __name__ == "__main__":
    unittest.main()
