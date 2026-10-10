"""A191 analysis: A187's per-run criteria (a187_analyze.run: c1, c2, c3, c7; step phase, late fires on phases 3-4 in the
first 30 us after the step) for the 9.5 ns lead, printed against A187's run of the same name. Writes a191_summary.json.
  python3 a191_analyze.py"""
from __future__ import annotations

import glob
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("a187", HERE.parent / "A187_p24_slow_corner_inductance_hot" / "a187_analyze.py")
A187 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A187)
REF = json.loads((HERE.parent / "A187_p24_slow_corner_inductance_hot" / "a187_summary.json").read_text())


def main():
    res = dict(A187.run(f) for f in sorted(glob.glob(str(HERE / "cosim" / "run_*.json"))))
    for k, s in res.items():
        s["a187"] = {x: REF[k][x] for x in ("post_pk", "step_phase", "late_ph34_30us", "vo_min_post")}
    (HERE / "a191_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    for k, s in res.items():
        r = s["a187"]
        print(f"{k:11s} phase {s['step_phase']:.2f} ({r['step_phase']:.2f}) post {s['post_pk']:5.1f} ({r['post_pk']:5.1f}) A late3-4 "
              f"{s['late_ph34_30us']:3d} ({r['late_ph34_30us']:3d}) Vo min {s['vo_min_post']:.3f} ({r['vo_min_post']:.3f}) | start "
              f"{s['start_pk']:5.1f} hand {s['hand_pk']:5.1f} V {s['vds_max_v']:.1f} {s['criteria']}")


if __name__ == "__main__":
    main()
