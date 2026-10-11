"""A197 analysis: A187's per-run criteria (a187_analyze.run: c1 start-up / handover, c2 post-step, c3 V_DS + COMPLETED +
0 shoot-throughs / overlaps, c7 Vo <= 1.05 V over 0-300 us; step phase, late fires on phases 3-4 in the first 30 us
after the step) for the adopted handover request (1.045 V), printed against A191's run of the same name (1.03 V).
Writes a197_summary.json.
  python3 a197_analyze.py"""
from __future__ import annotations

import glob
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("a187", HERE.parent / "A187_p24_slow_corner_inductance_hot" / "a187_analyze.py")
A187 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A187)
REF = json.loads((HERE.parent / "A191_p24_slow_corner_lead" / "a191_summary.json").read_text())
KEYS = ("post_pk", "hand_pk", "step_phase", "late_ph34_30us", "vo_min_post")


def main():
    res = dict(A187.run(f) for f in sorted(glob.glob(str(HERE / "cosim" / "run_*.json"))))
    for k, s in res.items():
        s["a191"] = {x: REF[k][x] for x in KEYS}
        r = json.loads((HERE / "cosim" / f"run_{k}.json").read_text())
        s["commit"], s["sources_modified"] = r["provenance"]["git_commit"][:7], r["provenance"]["cosim_sources_modified"]
    (HERE / "a197_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    for k, s in res.items():
        r = s["a191"]
        print(f"{k:11s} phase {s['step_phase']:.2f} ({r['step_phase']:.2f}) post {s['post_pk']:5.1f} ({r['post_pk']:5.1f}) A late3-4 "
              f"{s['late_ph34_30us']:3d} ({r['late_ph34_30us']:3d}) Vo min {s['vo_min_post']:.3f} ({r['vo_min_post']:.3f}) | start "
              f"{s['start_pk']:5.1f} hand {s['hand_pk']:5.1f} ({r['hand_pk']:5.1f}) V {s['vds_max_v']:.1f} {s['criteria']} {s['commit']} mod {s['sources_modified']}")


if __name__ == "__main__":
    main()
