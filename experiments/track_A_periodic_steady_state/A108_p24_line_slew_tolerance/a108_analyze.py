"""A108 analysis against BOUNDARY Section 4. Per run, in the 30 us from the step's start, per phase: the valleys (low-side
turn-off current, min and max), the peak (high-side turn-off current), the high-side and low-side turn-on V_DS maxima;
the run's overlaps, peak and late fires; Vo's extreme and the ladder (scb_ivr.cosim.matrix.step_stats). Compared with
A106 at 1 and 10 us. The window is 30 us, or the slew + 20 us when longer (the 20 and 50 us slews, added after
the first ten runs). Soft switching is judged by the valleys' sign (every valley < 0); the high-side turn-on V_DS
limit of BOUNDARY 4.4 scales with the rail and is reported only. Writes a108_summary.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.cosim.matrix import step_stats  # noqa: E402

A106 = HERE.parent / "A106_p24_line_steps" / "cosim"
SLEWS = (1, 2, 3, 5, 10)
SLEWS_ADDED = (20, 50)
T0 = 400e-6
ZVS_VDS = 9.5


def transient(d):
    t1 = T0 + max(30e-6, d["cfg"]["line_step"]["slew_us"] * 1e-6 + 20e-6)
    sel = lambda key, k: [x for x in d[key] if x["phase"] == k and T0 <= x["t_s"] <= t1]
    out = []
    for k in range(1, 5):
        lo, hi, on, lon = sel("lowoffs_last", k), sel("highoffs_last", k), sel("turnons_last", k), sel("lowons_last", k)
        out.append({"valley_min_a": min(x["i_a"] for x in lo), "valley_max_a": max(x["i_a"] for x in lo),
                    "peak_a": max(x["i_a"] for x in hi), "hs_on_vds_max_v": max(x["vds_v"] for x in on),
                    "ls_on_vds_max_v": max(x["vds_v"] for x in lon)})
    return out


def summary(d):
    ph = transient(d)
    s = step_stats(d)
    return {"phases": ph, "overlaps": d["overlaps"], "ipk_a": d["ipk_a"], "late_fires": d["late_fires"],
            "valley_max_a": max(p["valley_max_a"] for p in ph), "valley_min_a": min(p["valley_min_a"] for p in ph),
            "peak_a": max(p["peak_a"] for p in ph), "hs_on_vds_max_v": max(p["hs_on_vds_max_v"] for p in ph),
            "zvs_kept": all(p["valley_max_a"] < 0 and p["hs_on_vds_max_v"] <= ZVS_VDS for p in ph),
            "valleys_negative": all(p["valley_max_a"] < 0 for p in ph),
            "vo_extreme_mv": s["extreme_mv"], "back_within_1pct_us": s["back_within_1pct_us"],
            "ladder_dev_peak": s["ladder_dev_peak"], "ladder_back_below_1pct_us": s["ladder_back_below_1pct_us"]}


def main():
    res = {}
    for sign in ("p", "m"):
        for slew in SLEWS + SLEWS_ADDED:
            name = f"{sign}48_{slew}us"
            p = HERE / "cosim" / f"run_{name}.json"
            if not p.exists():
                continue
            x = res[name] = summary(json.loads(p.read_text()))
            a106 = A106 / f"run_pi100_{name}.json"
            if a106.exists():
                x["a106"] = summary(json.loads(a106.read_text()))
            print(f"{name}: overlaps {x['overlaps']}, ipk {x['ipk_a']:.1f} A, phase peaks " + "/".join(f"{q['peak_a']:.0f}" for q in x["phases"])
                  + ", valleys " + " ".join(f"[{q['valley_min_a']:+.1f},{q['valley_max_a']:+.1f}]" for q in x["phases"])
                  + ", HS-on max " + "/".join(f"{q['hs_on_vds_max_v']:.1f}" for q in x["phases"])
                  + f" V, ZVS kept {x['zvs_kept']}, valleys negative {x['valleys_negative']}, Vo {x['vo_extreme_mv']:+.2f} mV, back {x['back_within_1pct_us']:.2f} us, ladder {x['ladder_dev_peak']:.4f}, late {x['late_fires']}")
            if "a106" in x:
                b = x["a106"]
                print(f"   A106 (no slot_lo): ipk {b['ipk_a']:.1f} A, valleys {b['valley_min_a']:+.1f}..{b['valley_max_a']:+.1f} A, HS-on max {b['hs_on_vds_max_v']:.1f} V, "
                      f"Vo {b['vo_extreme_mv']:+.2f} mV")
    for sign in ("p", "m"):
        rows = [res[f"{sign}48_{s}us"] for s in SLEWS if f"{sign}48_{s}us" in res]
        if len(rows) == len(SLEWS):
            mono = lambda key, f=abs: all(f(a[key]) >= f(b[key]) - 1e-9 for a, b in zip(rows, rows[1:]))
            c = {"no_overlap": all(r["overlaps"] == 0 for r in rows), "peak_monotone": mono("ipk_a"),
                 "valley_max_monotone": mono("valley_max_a", lambda v: v), "valley_min_monotone": mono("valley_min_a", lambda v: -v),
                 "vo_monotone": mono("vo_extreme_mv")}
            if sign == "p":
                c["peak_200_from_2us"] = all(r["ipk_a"] <= 200 for r in rows[1:])
                c["peak_1us_200_215"] = 200 <= rows[0]["ipk_a"] <= 215
                c["valley_1us_45_65"] = 45 <= rows[0]["valley_max_a"] <= 65
                c["valley_5us_le_10"] = rows[3]["valley_max_a"] <= 10
            else:
                c["peak_200_all"] = all(r["ipk_a"] <= 200 for r in rows)
            c["vo_1us_vs_a106"] = abs(rows[0]["vo_extreme_mv"] / (11.8 if sign == "p" else -18.5) - 1) <= 0.15
            c["vo_10us_vs_a106"] = abs(rows[-1]["vo_extreme_mv"] / (4.2 if sign == "p" else -3.9) - 1) <= 0.15
            res[f"criteria_{sign}"] = c
            print(f"criteria {sign}: " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in c.items())
                  + "; ZVS kept at slews " + str([s for s, r in zip(SLEWS, rows) if r["zvs_kept"]]))
        added = [(s, res[f"{sign}48_{s}us"]) for s in SLEWS_ADDED if f"{sign}48_{s}us" in res]
        print(f"added {sign}: valleys negative (all slews) at " + str([s for s, r in zip(SLEWS, rows) if r["valleys_negative"]] + [s for s, r in added if r["valleys_negative"]]))
    (HERE / "a108_summary.json").write_text(json.dumps(res, indent=1, default=float))
    print("wrote a108_summary.json")


if __name__ == "__main__":
    main()
