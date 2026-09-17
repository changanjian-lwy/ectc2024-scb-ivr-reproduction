import unittest

from scb_ivr.device_library import (
    CapacitanceView,
    GS61008T,
    P25_GS61008T_POPULATION,
)
from scb_ivr.evidence import Evidence


class DeviceLibraryTests(unittest.TestCase):
    def test_gs61008t_datasheet_values(self):
        self.assertEqual(GS61008T.evidence, Evidence.EXTERNAL_DEVICE_DATA)
        self.assertAlmostEqual(GS61008T.rds_on_typ_ohm, 7e-3)
        self.assertAlmostEqual(GS61008T.coss_typ_f, 250e-12)
        self.assertAlmostEqual(GS61008T.co_er_f, 302e-12)
        self.assertAlmostEqual(GS61008T.co_tr_f, 385e-12)

    def test_p25_parallel_population_is_applied_outside_device(self):
        population = P25_GS61008T_POPULATION
        self.assertEqual(population.high_side_parallel, 1)
        self.assertEqual(population.low_side_parallel, 2)
        self.assertAlmostEqual(
            GS61008T.capacitance(
                CapacitanceView.TIME_EQUIVALENT,
                population.high_side_parallel,
            ),
            385e-12,
        )
        self.assertAlmostEqual(
            GS61008T.capacitance(
                CapacitanceView.TIME_EQUIVALENT,
                population.low_side_parallel,
            ),
            770e-12,
        )
        self.assertAlmostEqual(GS61008T.rds_on(2), 3.5e-3)

    def test_capacitance_view_cannot_be_implicit(self):
        with self.assertRaises(KeyError):
            GS61008T.capacitance("coss", 1)


if __name__ == "__main__":
    unittest.main()
