"""A250: D57's zero-voltage thresholds (p24_valley_map.thresholds) for L 2.2 and 2.933 nH over rails 3-20 V (the
start-up's low rails are below A124's 8-17 V grid). About 3 min.
  python3 a250_ith.py -> a250_ith.json"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scb_ivr.p24_valley_map import thresholds

HERE = Path(__file__).resolve().parent


def main():
    out = {f"{lf * 1e9:.3f}": thresholds(lf, rails=np.arange(3.0, 20.01, 0.5)) for lf in (2.2e-9, 2.9333333e-9)}
    (HERE / "a250_ith.json").write_text(json.dumps(out))


if __name__ == "__main__":
    main()
