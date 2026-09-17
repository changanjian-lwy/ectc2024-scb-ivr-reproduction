# Test layout

The test suite has two explicit levels:

1. `python3 tests/run_portable_suite.py` runs equation, event, boundary and
   source-separation checks that work on any Python/SciPy environment. GitHub
   Actions uses this entry point.
2. `python3 -m unittest discover -s tests -p 'test_*.py'` additionally validates
   measurements in locally generated LTspice `.log` files. Those logs are
   excluded from Git because they contain machine-specific paths and can be
   regenerated from the tracked netlists.

The portable runner lists every excluded module explicitly. A new test is
therefore included in CI by default unless it is deliberately classified as a
log-backed regression.
