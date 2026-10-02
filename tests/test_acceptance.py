"""scripts/acceptance.py: the gate fails on an unlisted false criterion, a missing run and an outdated exception, and
accepts a listed one (a temporary experiment folder)."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("acceptance", ROOT / "scripts" / "acceptance.py")
acc = importlib.util.module_from_spec(spec); spec.loader.exec_module(acc)


class Acceptance(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        (self.dir / "cosim").mkdir()
        for r in ("a", "b"):
            (self.dir / "cosim" / f"cfg_{r}.json").write_text(json.dumps({"out": f"run_{r}.json"}))
            (self.dir / "cosim" / f"run_{r}.json").write_text("{}")
        self.summary = {"a": {"criteria": {"x": True, "y": False}}, "b": {"criteria": {"x": True}}}
        (self.dir / "s.json").write_text(json.dumps(self.summary))
        acc.EXPERIMENTS["T"] = (self.dir, "none.py", "s.json")

    def tearDown(self):
        acc.EXPERIMENTS.pop("T"); acc.EXCEPTIONS.pop("T", None); self.tmp.cleanup()

    def test_unlisted_false_criterion_fails(self):
        self.assertEqual(acc.check("T", False)["FAIL"], ["a: y"])
        self.assertEqual(acc.main(["T"]), 1)

    def test_listed_exception_is_documented(self):
        acc.EXCEPTIONS["T"] = {("a", "y"): "why (RESULTS 1)"}
        r = acc.check("T", False)
        self.assertEqual((r["FAIL"], len(r["DOCUMENTED"]), r["PASS"]), ([], 1, 2))
        self.assertEqual(acc.main(["T"]), 0)

    def test_missing_run_and_row_fail(self):
        acc.EXCEPTIONS["T"] = {("a", "y"): "why"}
        (self.dir / "cosim" / "run_b.json").unlink()
        del self.summary["b"]; (self.dir / "s.json").write_text(json.dumps(self.summary))
        r = acc.check("T", False)
        self.assertEqual(sorted(r["MISSING"]), ["row b not in s.json", "run run_b.json"])
        self.assertEqual(acc.main(["T"]), 1)

    def test_outdated_exception_fails(self):
        acc.EXCEPTIONS["T"] = {("a", "y"): "why", ("b", "x"): "listed but passes"}
        self.assertEqual(acc.check("T", False)["OUTDATED"], ["b: x passes but is listed as an exception"])
        self.assertEqual(acc.main(["T"]), 1)


if __name__ == "__main__":
    unittest.main()
