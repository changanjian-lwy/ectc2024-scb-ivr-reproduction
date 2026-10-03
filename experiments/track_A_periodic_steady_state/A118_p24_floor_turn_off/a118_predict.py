"""A118 registered predictions (before any run): D63 for every step row (scripts/p24_valley_map.py's 1 MHz designs,
mode "floor" with floor_a 2 A or "timed", Cs 6 or 15 uF, 60 kHz), with D63's outcome rule as refitted on A117
(slow or runaway: phase 1 crosses its threshold by more than 12 A for 25 periods or more; runaway: the map diverges;
peak: a peak above 200 A; ok otherwise). Writes a118_predictions.json."""
from __future__ import annotations

import importlib.util
import json
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("d63", PROJECT / "scripts" / "p24_valley_map.py")
D63 = importlib.util.module_from_spec(spec); spec.loader.exec_module(D63)
spec = importlib.util.spec_from_file_location("a118_cfgs", HERE / "make_cfgs.py")
CF = importlib.util.module_from_spec(spec); spec.loader.exec_module(CF)


def outcome(m):
    if m["diverged_us"] is not None:
        return "runaway"
    if m["ph1_depth_a"] > 12.0 and m["ph1_crossing_periods"] >= 25:
        return "slow_or_runaway"
    return "peak" if m["peak_max_a"] > 200.0 else "ok"


def main():
    _, d1 = D63.designs(D63.ith_table())
    res = {}
    for name, cs, floor, step in CF.ROWS:
        st = CF.STEPS[step]
        if st is None:
            continue
        d = replace(d1(10, "floor" if floor else "timed"), cs=cs * 1e-6, floor_a=2.0)
        kw = {"i_step": st[1]} if st[0] == "load" else {"dvin": st[1], "t_slew": st[2] * 1e-6}
        m = D63.run_case(d, kw, t_end=600e-6)
        o = outcome(m)
        res[name] = {"model": m, "outcome": o, "ph1_valley_min_a": m["valley_min_a"][0]}
        print(f"{name:16s}: {o:16s} peak {m['peak_max_a']:5.0f} A, Vo {m['extreme_mv']:+7.1f} mV, back {m['back_us']:6.1f} us, phase 1 "
              f"valley min {m['valley_min_a'][0]:6.1f} A, crossing {m['ph1_depth_a']:4.1f} A x {m['ph1_crossing_periods']}")
    (HERE / "a118_predictions.json").write_text(json.dumps(res, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
