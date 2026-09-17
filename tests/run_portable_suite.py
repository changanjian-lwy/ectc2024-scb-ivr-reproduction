"""Run tests that do not require locally generated LTspice log files."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"

# These modules validate recorded LTspice measurements. Their source netlists
# remain public, but generated .log files are intentionally git-ignored.
LOG_BACKED_MODULES = {
    "test_inactive_low_side_branches",
    "test_module_diagnostics",
    "test_r04a_regression",
    "test_r04c_regression",
    "test_r04d0_regression",
    "test_r04d1b2_regression",
    "test_r04d1b_regression",
    "test_r04d2_regression",
    "test_r04d3_regression",
    "test_r04d3c_regression",
    "test_r04d3d_regression",
    "test_r04d3e_regression",
    "test_r04d4a_regression",
    "test_r04d5a_d6a_regression",
    "test_two_branch_revalidation",
}


def iter_cases(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from iter_cases(item)
        else:
            yield item


def build_suite() -> unittest.TestSuite:
    discovered = unittest.defaultTestLoader.discover(
        str(TESTS), pattern="test_*.py", top_level_dir=str(TESTS)
    )
    portable = [
        case
        for case in iter_cases(discovered)
        if case.__class__.__module__ not in LOG_BACKED_MODULES
    ]
    return unittest.TestSuite(portable)


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    result = unittest.TextTestRunner(verbosity=1).run(build_suite())
    raise SystemExit(not result.wasSuccessful())
