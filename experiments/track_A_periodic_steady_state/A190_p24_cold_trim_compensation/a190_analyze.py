"""A190 analysis: A189's per-run criteria (c1 peaks, c3 safety, c4 entry Vo >= 0.99 V) plus c8: the compensated trim puts
Vo(143.5 us) within 1.035 +- 0.015 V. Hold-out boards S0 / S80 / N13 / N75; in-sample S75 / N0. Writes a190_summary.json.
  python3 a190_analyze.py"""
from __future__ import annotations

import glob
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("a189", HERE.parent / "A189_p24_cold_startup" / "a189_analyze.py")
A189 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A189)
HOLD_OUT = ("S0", "S80", "N13", "N75")


def main():
    res = {}
    for f in sorted(glob.glob(str(HERE / "cosim" / "run_*.json"))):
        k, st = A189.run(f)
        st["hold_out"] = k.split("_")[0] in HOLD_OUT
        st["criteria"]["c8"] = abs(st["vo_143_5"] - 1.035) <= 0.015
        res[k] = st
    (HERE / "a190_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    for k, s in res.items():
        print(f"{k:8s} {'hold-out' if s['hold_out'] else 'in-sample':9s} {s['temp']:5.0f} C Vo(143.5) {s['vo_143_5']:.4f} entry {s['vo_entry']:.3f} "
              f"start {s['start_pk']:5.1f} hand {s['hand_pk']:5.1f} Vo min {s['vo_min_entry']:.3f} V {s['vds_max_v']:.1f} {s['criteria']}")


if __name__ == "__main__":
    main()
