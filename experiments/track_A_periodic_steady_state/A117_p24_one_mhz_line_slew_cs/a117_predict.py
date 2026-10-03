"""A117 registered predictions (before any run): D63 (scripts/p24_valley_map.py's designs) for every step row of
make_cfgs.py, with D63's outcome rule:
- runaway: the map diverges (its memory unbounded);
- slow or runaway: phase 1 crosses its threshold by more than 8 A for more than 5 us (D63 Section 3, 7 cases);
- peak: otherwise, a peak above 200 A;
- ok: otherwise.
Rows where D63 is known to be unreliable (the timed turn-off with the 60 kHz loop on a rising step, D63 Section 3) are
flagged. Writes a117_predictions.json."""
from __future__ import annotations

import importlib.util
import json
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("d63", PROJECT / "scripts" / "p24_valley_map.py")
D63 = importlib.util.module_from_spec(spec); spec.loader.exec_module(D63)
spec = importlib.util.spec_from_file_location("a117_cfgs", HERE / "make_cfgs.py")
CF = importlib.util.module_from_spec(spec); spec.loader.exec_module(CF)


def outcome(m, period_s):
    if m["diverged_us"] is not None:
        return "runaway"
    if m["ph1_depth_a"] > 8.0 and m["ph1_crossing_periods"] * period_s > 5e-6:
        return "slow_or_runaway"
    return "peak" if m["peak_max_a"] > 200.0 else "ok"


def main():
    _, d1 = D63.designs(D63.ith_table())
    res = {}
    for name, (cs, rule, dv, slew, di) in CF.ROWS.items():
        if dv is None and di is None:
            continue
        d = replace(d1(10, "cmp" if rule == "cmp" else "timed"), cs=cs * 1e-6)
        kw = {"dvin": dv, "t_slew": slew * 1e-6} if dv is not None else {"i_step": di}
        m = D63.run_case(d, kw, t_end=600e-6)
        o = outcome(m, 1.195e-6)
        flag = rule == "tim" and dv is not None and dv > 0
        res[name] = {"model": m, "outcome": o, "unreliable_timed_rising": flag}
        print(f"{name:20s}: {o:16s} peak {m['peak_max_a']:6.0f} A, Vo {m['extreme_mv']:+8.1f} mV, back {m['back_us']:6.1f} us, phase 1 crossing "
              f"{m['ph1_depth_a']:5.1f} A x {m['ph1_crossing_periods']:3d}" + ("  [D63 unreliable here]" if flag else ""))
    (HERE / "a117_predictions.json").write_text(json.dumps(res, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
