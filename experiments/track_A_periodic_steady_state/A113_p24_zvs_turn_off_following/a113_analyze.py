"""A113 analysis against BOUNDARY Section 2: for each option (ff, cmp) and row, A112's statistics (a112_analyze.summarise:
peaks, high-side and low-side turn-on V_DS, turn-off spread, the step) against A112's p25 row; for n0 also the D62
middle-case efficiency (a110_analyze.row). Writes a113_summary.json."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


A112 = module(HERE.parent / "A112_p24_zvs_designs_matrix" / "a112_analyze.py", "a112_analyze")
A110 = module(HERE.parent / "A110_p24_high_side_zvs" / "a110_analyze.py", "a110_analyze")
R112 = HERE.parent / "A112_p24_zvs_designs_matrix" / "cosim"
ROWS = ("n0", "s_m62", "l_m48_1us", "l_m80_10us")


def load(p):
    return json.loads(Path(p).read_text())


def main():
    res = {}
    for v in ("ff", "cmp"):
        for row in ROWS:
            p = HERE / "cosim" / f"run_{v}_{row}.json"
            if not p.exists():
                continue
            stepped = row != "n0"
            d, r = load(p), load(R112 / f"run_p25_{row}.json")
            x, b = A112.summarise(d, stepped), A112.summarise(r, stepped)
            c = {"no_overlap": x["overlaps"] == 0}
            if row == "n0":
                e, eb = A110.row(d), A110.row(r)
                x["efficiency_pct"], x["a112_efficiency_pct"] = e["efficiency_pct"], eb["efficiency_pct"]
                c["hs_0p3V"] = all(abs(a - q) <= 0.3 for a, q in zip(x["hs_on_vds_v"], b["hs_on_vds_v"]))
                c["sd"] = max(x["off_sd_a"]) <= (0.3 if v == "ff" else 0.8)
                c["peak_after_200a"] = x["peak_after_150us_a"] <= 200.0
            else:
                s = x["step"]
                c["back"] = s["back_within_1pct_us"] <= (15.0 if row == "s_m62" else 25.0)
                if row == "s_m62":
                    c["overshoot_30pct"] = abs(s["extreme_mv"] / 11.65 - 1) <= 0.3
                    c["peak_after_200a"] = x["peak_after_150us_a"] <= 200.0
                else:
                    c["peak_le_a112"] = x["peak_after_150us_a"] <= b["peak_after_150us_a"]
            x["criteria"] = c; x["a112"] = b
            res[f"{v}_{row}"] = x
            line = (f"{v:3s} {row:11s} ipk {x['ipk_a']:5.1f} after150 {x['peak_after_150us_a']:5.1f} A (A112 {b['peak_after_150us_a']:5.1f}) HS "
                    + "/".join(f"{q:+.2f}" for q in x["hs_on_vds_v"]) + " sd " + "/".join(f"{q:.2f}" for q in x["off_sd_a"]))
            if stepped:
                line += (f" | step {x['step']['extreme_mv']:+.2f} mV back {x['step']['back_within_1pct_us']:.2f} us "
                         f"(A112 {b['step']['extreme_mv']:+.2f} / {b['step']['back_within_1pct_us']:.2f})")
            else:
                line += f" | efficiency {x['efficiency_pct']:.2f}% (A112 {x['a112_efficiency_pct']:.2f}%)"
            miss = [k for k, q in c.items() if not q]
            print(line + (" | MISS " + ",".join(miss) if miss else " | ok"))
    (HERE / "a113_summary.json").write_text(json.dumps(res, indent=1, default=float))
    print("wrote a113_summary.json")


if __name__ == "__main__":
    main()
