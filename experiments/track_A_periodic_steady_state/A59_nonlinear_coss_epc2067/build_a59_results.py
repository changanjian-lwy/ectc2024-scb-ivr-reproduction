"""A59 - build results.json with A58's unchanged summarizer, pointed at A59's runs.

Usage: python3 build_a59_results.py [--replace]
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "A58_asymmetric_fixed_deadtime_tuning"))
import build_a58_results as B  # noqa: E402

B.HERE = HERE
B.OUT = HERE / "results.json"

if __name__ == "__main__":
    B.main()
