import unittest

from module_diagnostics import CheckStatus
from r04a_module_diagnostics import diagnose


class ModuleDiagnosticTests(unittest.TestCase):
    def test_r04a_reports_each_module_separately(self):
        result = diagnose()
        owners = {check["owner_module"] for check in result["module_checks"]}
        self.assertEqual(set(result["selected_modules"]), owners)
        self.assertTrue(result["summary"]["passed"])

    def test_r04a_does_not_claim_unmodelled_zvs(self):
        result = diagnose()
        zvs = next(
            check for check in result["module_checks"]
            if check["check_id"] == "R04A:coss_zvs"
        )
        self.assertEqual(zvs["status"], CheckStatus.NOT_APPLICABLE.value)


if __name__ == "__main__":
    unittest.main()
