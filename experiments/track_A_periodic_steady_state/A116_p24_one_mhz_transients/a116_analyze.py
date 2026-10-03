"""A116 analysis against BOUNDARY Section 2. n0 rows against A115 n10 (A115's row statistics); step rows by
matrix.step_stats at 2000 us, with each phase's valley range after the step (low-side turn-off currents) and phase 1's;
t30_s_m62 classified for H1 / H2. Writes a116_summary.json."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.cosim.matrix import step_stats  # noqa: E402

spec = importlib.util.spec_from_file_location("a115_analyze", HERE.parent / "A115_p24_one_mhz_design_point" / "a115_analyze.py")
A115 = importlib.util.module_from_spec(spec); spec.loader.exec_module(A115)
A115R = HERE.parent / "A115_p24_one_mhz_design_point" / "cosim"
T_STEP, I_TGT = 2000e-6, -12.5
BANDS = {   # registered (BOUNDARY Section 2): (extreme mV, +/- mV, back us limit)
    ("t30", "s_m62"): (32.0, 10.0, 60.0), ("c60", "s_m62"): (19.0, 6.0, 30.0), ("c30", "s_m62"): (32.0, 10.0, 60.0),
    ("t30", "s_p62"): (-33.0, 10.0, None), ("c60", "s_p62"): (-20.0, 6.0, None), ("c30", "s_p62"): (-33.0, 10.0, None),
}


def load(p):
    return json.loads(Path(p).read_text())


def valleys_after(d, t0=T_STEP):
    out = []
    for k in (1, 2, 3, 4):
        v = [x["i_a"] for x in d["lowoffs_last"] if x["phase"] == k and x["t_s"] >= t0]
        out.append((min(v), max(v)) if v else (None, None))
    return out


def main():
    res = {}
    ref = A115.row(load(A115R / "run_n10.json"))
    for v in ("t30", "c60", "c30"):
        p = HERE / "cosim" / f"run_{v}_n0.json"
        if not p.exists():
            continue
        x = A115.row(load(p))
        c = {"no_overlap": x["overlaps"] == 0, "peak_200a": x["ipk_a"] <= 200.0, "vo_1mV": abs(x["vo_mean_v"] - 1.0) <= 1e-3,
             "late_5": sum(x["late_fires"]) <= 5,
             "hs_0p2V": all(abs(a - b) <= 0.2 for a, b in zip(x["hs_on_vds_v"], ref["hs_on_vds_v"])),
             "efficiency_0p1": abs(x["efficiency_pct"] - ref["efficiency_pct"]) <= 0.1,
             "ripple_1A": all(abs(a - b) <= 1.0 for a, b in zip(x["ripple_a"], ref["ripple_a"]))}
        if v.startswith("c"):
            c["phase1_valley_1A"] = abs(x["valleys_a"][0] - I_TGT) <= 1.0
        x["criteria"] = c
        res[f"{v}_n0"] = x
        print(f"{v}_n0: HS on " + "/".join(f"{a:+.2f}" for a in x["hs_on_vds_v"]) + " V (A115 " + "/".join(f"{a:+.2f}" for a in ref["hs_on_vds_v"])
              + "), valleys " + "/".join(f"{a:+.2f}" for a in x["valleys_a"]) + ", ripple " + "/".join(f"{a:.1f}" for a in x["ripple_a"])
              + f", efficiency {x['efficiency_pct']:.2f}% (A115 {ref['efficiency_pct']:.2f}), sd " + "/".join(f"{a:.2f}" for a in x["off_sd_a"])
              + f", Vo {x['vo_mean_v']:.5f}, ipk {x['ipk_a']:.0f} A, late {x['late_fires']}; "
              + ", ".join(f"{k} {'ok' if b else 'MISS'}" for k, b in c.items()))
    for row in ("s_m62", "s_p62", "l_p48_1us", "l_m48_1us"):
        for v in ("t60", "t30", "c60", "c30"):
            name = f"{v}_{row}"
            p = HERE / "cosim" / f"run_{name}.json"
            if not p.exists():
                continue
            d = load(p)
            st = step_stats(d, t_step=T_STEP)
            va = valleys_after(d)
            x = {"step": st, "ipk_a": d["ipk_a"], "overlaps": d["overlaps"], "late_fires": d["late_fires"], "valleys_after_a": va}
            c = {"no_overlap": d["overlaps"] == 0}
            back = st["back_within_1pct_us"]
            if (v, row) in BANDS:
                mv, tol, lim = BANDS[(v, row)]
                c["peak_200a"] = d["ipk_a"] <= 200.0
                c["extreme_band"] = abs(st["extreme_mv"] - mv) <= tol
                if lim is not None:
                    c[f"back_{lim:.0f}us"] = back <= lim
                if v.startswith("c"):
                    lo, hi = va[0]
                    c["phase1_valley_3A"] = lo >= I_TGT - 3.0 and hi <= I_TGT + 3.0
            elif row == "l_m48_1us":
                c["peak_200a"] = d["ipk_a"] <= 200.0
                c["back_60us"] = back <= 60.0
            elif row == "l_p48_1us" and v.startswith("t"):
                c["peak_ge_207a"] = d["ipk_a"] >= 207.0                    # registered: at least the 5 MHz design's
            elif row == "l_p48_1us":
                c["runs_away_gt_200a"] = d["ipk_a"] > 200.0                # registered as the expected failure (A114)
            if name == "t30_s_m62":
                x["h1_valley_below_15a"] = min(a for a, _ in va) < -15.0
                x["hypothesis"] = "H2" if (d["ipk_a"] <= 200.0 and back <= 60.0) else "H1"
            x["criteria"] = c
            res[name] = x
            print(f"{name}: step {st['extreme_mv']:+.2f} mV at {st['t_extreme_us']:.1f} us, back {back:.2f} us, ladder peak "
                  f"{st['ladder_dev_peak'] * 100:.2f}%, ipk {d['ipk_a']:.0f} A, late {d['late_fires']}, valleys after "
                  + " ".join(f"[{a:+.1f},{b:+.1f}]" for a, b in va)
                  + (f", {x['hypothesis']} (valley below -15 A: {x['h1_valley_below_15a']})" if "hypothesis" in x else "") + "; "
                  + ", ".join(f"{k} {'ok' if b else 'MISS'}" for k, b in c.items()))
    (HERE / "a116_summary.json").write_text(json.dumps(res, indent=1, default=float))
    print("wrote a116_summary.json")


if __name__ == "__main__":
    main()
