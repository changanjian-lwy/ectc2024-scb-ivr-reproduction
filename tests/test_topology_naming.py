import unittest

from scb_ivr.topology_naming import build_name_map, phase_names


class TopologyNamingTests(unittest.TestCase):
    def test_p24_fig3_four_phase_mapping(self):
        self.assertEqual(
            build_name_map(4),
            {
                "S1a": "H1", "S1b": "L1",
                "S2a": "H2", "S2b": "L2",
                "S3a": "H3", "S3b": "L3",
                "S4a": "H4", "S4b": "L4",
            },
        )

    def test_high_and_low_are_two_positions_not_extra_alias_devices(self):
        names = phase_names(2, 4)
        self.assertEqual(names.paper_high, "S2a")
        self.assertEqual(names.paper_low, "S2b")
        self.assertEqual(names.canonical_high, "H2")
        self.assertEqual(names.canonical_low, "L2")

    def test_inductor_name_cannot_collide_with_low_switch_name(self):
        names = phase_names(1, 4)
        self.assertNotEqual(names.inductor, names.canonical_low)
        self.assertEqual(names.inductor, "LIND1")


if __name__ == "__main__":
    unittest.main()
