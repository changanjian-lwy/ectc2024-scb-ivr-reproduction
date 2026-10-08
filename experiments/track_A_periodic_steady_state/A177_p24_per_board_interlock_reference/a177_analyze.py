"""A177 analysis: A174's criterion 4 (a174_analyze.judge_fr) for each per-board-reference run against A173's
t_il 0.5 run of the same row, with A174's fixed-reference run alongside. Writes a177_summary.json."""
from __future__ import annotations

import glob
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a174_analyze", TA / "A174_p24_final_plant_margins" / "a174_analyze.py")
A4 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A4)
KEYS = ("peak_post", "late", "oracle_new", "extreme_mv", "start_pk", "hand_pk")


def main():
    runs, verdict = {}, {}
    for f in sorted(glob.glob(str(HERE / "cosim" / "run_*.json"))):
        name = Path(f).stem[4:]
        row = name.split("_", 1)[1]
        st = A4.stats(f)
        b = A4.A8.safe_stats(str(A4.A173C / f"run_{row}.json"))
        fx = A4.A8.safe_stats(str(TA / "A174_p24_final_plant_margins" / "cosim" / f"run_fr_{row}.json"))
        st["a173"], st["a174_fixed"] = {k: b.get(k) for k in KEYS}, {k: fx.get(k) for k in KEYS}
        runs[name], verdict[name] = st, {"4": A4.judge_fr(st, b)}
    (HERE / "a177_summary.json").write_text(json.dumps({"runs": runs, "verdict": verdict}, indent=1, default=float))
    for name, st in runs.items():
        a, x, miss = st["a173"], st["a174_fixed"], verdict[name]["4"]
        print(f"{name:22s} post {st['peak_post']:.1f} ({a['peak_post']:.1f} / {x['peak_post']:.1f}) late {st['late']} "
              f"({a['late']} / {x['late']}) NEW {st['oracle_new']} ({a['oracle_new']} / {x['oracle_new']}) ext "
              f"{st['extreme_mv']:.1f} ({a['extreme_mv']:.1f} / {x['extreme_mv']:.1f}) holds {sum(st['il_holds'] or [])} "
              f"max {st['il_hold_max_ns']:.1f}", "PASS" if not miss else "miss " + ", ".join(miss))


if __name__ == "__main__":
    main()
