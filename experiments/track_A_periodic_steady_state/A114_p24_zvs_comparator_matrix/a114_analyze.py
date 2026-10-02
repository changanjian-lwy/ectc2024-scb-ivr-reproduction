"""A114 analysis against BOUNDARY Section 1: each design (20%, 25%) and row with the comparator turn-off against A112's
same row (the timed turn-off), on A112's statistics (a112_analyze.summarise), plus the D62 middle-case efficiency for
n0 (a110_analyze.row). Writes a114_summary.json."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.cosim.matrix import ROWS  # noqa: E402


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


A112 = module(HERE.parent / "A112_p24_zvs_designs_matrix" / "a112_analyze.py", "a112_analyze")
A110 = module(HERE.parent / "A110_p24_high_side_zvs" / "a110_analyze.py", "a110_analyze")
R112 = HERE.parent / "A112_p24_zvs_designs_matrix" / "cosim"


def load(p):
    return json.loads(Path(p).read_text())


def main():
    res = {}
    for pct in (20, 25):
        for row in ROWS:
            p = HERE / "cosim" / f"run_c{pct}_{row}.json"
            if not p.exists():
                continue
            stepped = row.startswith(("s_", "l_"))
            d, r = load(p), load(R112 / f"run_p{pct}_{row}.json")
            x, b = A112.summarise(d, stepped), A112.summarise(r, stepped)
            c = {"no_overlap": x["overlaps"] == 0}
            if row == "n0" or row[0] == "m":
                c["hs_0p3V"] = all(abs(a - q) <= 0.3 for a, q in zip(x["hs_on_vds_v"], b["hs_on_vds_v"]))
            if row[0] == "m":
                c["ls_zvs"] = max(x["ls_on_vds_max_v"]) <= 0.0
            if row == "n0":
                x["efficiency_pct"], x["a112_efficiency_pct"] = A110.row(d)["efficiency_pct"], A110.row(r)["efficiency_pct"]
                c["eff_0p2"] = abs(x["efficiency_pct"] - x["a112_efficiency_pct"]) <= 0.2
            if row[0] == "j":
                lim = 1.3 if row == "j30" else 1.8
                c["sd_bound"] = all(a <= lim * q for a, q in zip(x["off_sd_a"], b["off_sd_a"]))
            if stepped:
                back = x["step"]["back_within_1pct_us"]
                if row.startswith("s_"):
                    c["back_15us"] = back <= 15.0
                elif row == "l_m80_10us":
                    c["slow_as_registered"] = back >= 50.0
                else:
                    c["back_20us"] = back <= 20.0
                if row.startswith("l_"):
                    c["peak_a112_5A"] = x["peak_after_150us_a"] <= b["peak_after_150us_a"] + 5.0
            x["criteria"] = c; x["a112"] = b
            res[f"c{pct}_{row}"] = x
            line = (f"c{pct}_{row:11s} ipk {x['ipk_a']:5.1f} after150 {x['peak_after_150us_a']:5.1f} (A112 {b['peak_after_150us_a']:5.1f}) HS "
                    + "/".join(f"{q:+.2f}" for q in x["hs_on_vds_v"]) + " LSmax " + f"{max(x['ls_on_vds_max_v']):+.2f}" + " sd "
                    + "/".join(f"{q:.2f}" for q in x["off_sd_a"]) + " (A112 " + "/".join(f"{q:.2f}" for q in b["off_sd_a"]) + ")")
            if stepped:
                line += f" | step {x['step']['extreme_mv']:+.2f} mV back {x['step']['back_within_1pct_us']:.2f} us (A112 {b['step']['extreme_mv']:+.2f} / {b['step']['back_within_1pct_us']:.2f})"
            if row == "n0":
                line += f" | eff {x['efficiency_pct']:.2f}% (A112 {x['a112_efficiency_pct']:.2f}%)"
            miss = [k for k, q in c.items() if not q]
            print(line + (" | MISS " + ",".join(miss) if miss else " | ok"))
    (HERE / "a114_summary.json").write_text(json.dumps(res, indent=1, default=float))
    print("wrote a114_summary.json")


if __name__ == "__main__":
    main()
