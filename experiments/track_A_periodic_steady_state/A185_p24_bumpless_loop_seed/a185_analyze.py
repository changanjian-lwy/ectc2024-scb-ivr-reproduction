"""A185 analysis: A184's criteria (a184_analyze) with g0 against A184's runs (mode S identical) and c6 against the
t0 = 400 records. Writes a185_summary.json.
  python3 a185_analyze.py"""
from __future__ import annotations

import glob
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("a184_analyze", HERE.parent / "A184_p24_startup_own_ton" / "a184_analyze.py")
A = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A)
A.A183 = HERE.parent / "A184_p24_startup_own_ton" / "cosim"          # g0: mode S equals A184's (only ton_ns changed)


def main():
    res = dict(A.run(f) for f in sorted(glob.glob(str(HERE / "cosim" / "run_*.json"))))
    for o in res.values():                                         # hot c6 is a diagnostic here (BOUNDARY Section 2)
        if o["temp"] != 25.0:
            o["c6_hot_diagnostic"] = o["criteria"].pop("c6")
    (HERE / "a185_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    for s, o in res.items():
        for j, m in enumerate(o["modules"]):
            print(f"{s:10s} m{j} Vo {m['vo_143_5']:.3f} start {m['start_pk']:5.1f} hand {m['hand_pk']:5.1f} gap {m['gap_pk']:5.1f} "
                  f"post {m['post_pk'] or 0:5.1f} V {m['vds_max_v']:.1f} Vo_min {m['vo_min_entry']:.3f}"
                  + (f" (ref {o['c6'][j]['ref']:.3f}) dev {o['c5_dev_a'][j]:.2f}" if o["c6"] else "")
                  + f" Ton {m['ton_max_entry_ns']:.1f}/{m['ton_steady_ns']:.1f} ns")
        print("   ", o["criteria"])


if __name__ == "__main__":
    main()
