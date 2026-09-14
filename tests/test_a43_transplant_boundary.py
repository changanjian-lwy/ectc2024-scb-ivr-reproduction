import json
from pathlib import Path
import unittest

from experiments.track_A_periodic_steady_state.build_a43_full_machine_transplant import (
    PARENT,
    build,
)


class A43TransplantBoundaryTests(unittest.TestCase):
    def test_only_parameter_line_and_documentation_are_changed(self):
        child = build()
        parent_lines = PARENT.read_text().splitlines()
        child_lines = child.read_text().splitlines()
        parent_machine = parent_lines[parent_lines.index(".machine 1p"):]
        child_machine = child_lines[child_lines.index(".machine 1p"):]
        self.assertEqual(parent_machine, child_machine)

    def test_threshold_and_all_seed_coordinates_are_preserved_as_intended(self):
        child_text = build().read_text()
        self.assertIn("NEG_FRAC=.0777", child_text)
        self.assertNotIn("NEG_FRAC=.09 ", child_text)
        self.assertIn(
            ".param IL1_INIT=5.2947 IL2_INIT=21.205095337 "
            "IL3_INIT=41.5782701063 IL4_INIT=84.1447433786",
            child_text,
        )
        self.assertIn(
            ".param VC1_INIT=36.000066454 VC2_INIT=23.9999142326 "
            "VC3_INIT=12.0006048777",
            child_text,
        )

    def test_recorded_first_failure_is_h2_zvs_guard(self):
        result = json.loads(
            (build().parent / "result.json").read_text()
        )
        self.assertEqual(result["first_failure"], "P1_M5_WAITING_FOR_H2_VDS_ZERO")
        self.assertFalse(result["h2_admitted"])
        self.assertEqual(result["final_state"], 4)
        self.assertTrue(result["controller_guard_pass"])


if __name__ == "__main__":
    unittest.main()
