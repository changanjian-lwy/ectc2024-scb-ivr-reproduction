"""A104 analysis: the PI voltage loops in the Verilog co-simulation against D59 (d59_predictions.json) and BOUNDARY
Section 5.

Per run (sections: Vo and Ton at phase 1's turn-on; records: the edges):
- before the step (350-400 us): Vo and Ton peak-to-peak, per-phase high-side turn-on V_DS (mean), low-side turn-on
  V_DS (maximum), low-side turn-off current (mean, sd);
- the step at 400 us: Vo's extreme and its time, the last exit from 1 V +/- 1%, Vo peak-to-peak over the last 50 us;
  the same switching statistics over the last 200 periods;
- the start-up (before 400 us): Vo's maximum, the time above 1 V and above 1.005 V in its excursion.
Writes a104_summary.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
N = 4
DESIGNS = ("ref", "fc30", "fc60", "fc100", "fc150")
T_STEP = 400e-6


def load(name):
    p = HERE / "cosim" / f"run_{name}.json"
    return json.loads(p.read_text()) if p.exists() else None


def switching(d, t0, t1):
    out = []
    for k in range(N):
        on = [r["vds_v"] for r in d["turnons_last"] if r["phase"] == k + 1 and t0 <= r["t_s"] < t1]
        lo = [r["vds_v"] for r in d["lowons_last"] if r["phase"] == k + 1 and t0 <= r["t_s"] < t1]
        off = [r["i_a"] for r in d["lowoffs_last"] if r["phase"] == k + 1 and t0 <= r["t_s"] < t1]
        out.append({"hs_on_vds_v": float(np.mean(on)), "ls_on_vds_max_v": float(np.max(lo)),
                    "i_lowoff_mean_a": float(np.mean(off)), "i_lowoff_sd_a": float(np.std(off)), "n": len(on)})
    return out


def above(t, v, level):
    i = int(np.argmax(v))
    if v[i] <= level:
        return 0.0
    a = b = i
    while a > 0 and v[a - 1] > level:
        a -= 1
    while b < len(v) - 1 and v[b + 1] > level:
        b += 1
    return float((t[b] - t[a]) * 1e6)


def stats(d):
    t = np.array([s["t_s"] for s in d["sections"]]); vo = np.array([s["vo"] for s in d["sections"]])
    ton = np.array([s["ton_lsb"] for s in d["sections"]])
    pre = (t >= 350e-6) & (t < T_STEP)
    aft = t >= T_STEP
    ta, va = t[aft], vo[aft]
    i = int(np.argmax(np.abs(va - 1.0)))
    bad = np.nonzero(np.abs(va - 1.0) > 0.01)[0]
    last = ta > ta[-1] - 50e-6
    su = t < T_STEP
    return {"status": d["status"], "overlaps": d["overlaps"],
            "pre_vo_pp_mv": float((vo[pre].max() - vo[pre].min()) * 1e3), "pre_ton_pp_lsb": float(ton[pre].max() - ton[pre].min()),
            "pre_vo_mean_v": float(vo[pre].mean()), "pre_ton_mean_lsb": float(ton[pre].mean()),
            "extreme_mv": float((va[i] - 1.0) * 1e3), "t_extreme_us": float((ta[i] - T_STEP) * 1e6),
            "back_within_1pct_us": float((ta[bad[-1]] - T_STEP) * 1e6) if len(bad) else 0.0,
            "last50_vo_pp_mv": float((va[last].max() - va[last].min()) * 1e3), "last50_ton_pp_lsb": float(np.ptp(ton[aft][last])),
            "startup_vo_max_v": float(vo[su].max()), "startup_t_vo_max_us": float(t[su][np.argmax(vo[su])] * 1e6),
            "startup_above_1v_us": above(t[su], vo[su], 1.0), "startup_above_1v005_us": above(t[su], vo[su], 1.005),
            "sw_pre": switching(d, 350e-6, T_STEP), "sw_post": switching(d, t[-1] - 46e-6, t[-1] + 1e-9)}


def main():
    pred = json.loads((HERE / "d59_predictions.json").read_text())
    out = {}
    for dn in DESIGNS:
        for tag in ("m62", "p62"):
            d = load(f"{dn}_{tag}")
            if d is not None:
                out[f"{dn}_{tag}"] = stats(d)
    for dn in DESIGNS:
        for tag in ("m62", "p62"):
            name = f"{dn}_{tag}"
            if name not in out:
                continue
            x, p = out[name], pred[dn][tag]
            r = out.get(f"ref_{tag}")
            sd = lambda sw: max(q["i_lowoff_sd_a"] for q in sw[1:])
            crit = {"no_overlap": x["overlaps"] == 0,
                    "stable_before": x["pre_vo_pp_mv"] <= 5.0 and x["pre_ton_pp_lsb"] <= 12,
                    "no_oscillation_after": x["last50_vo_pp_mv"] <= 5.0,
                    "low_side_zvs": all(q["ls_on_vds_max_v"] <= 0 for q in x["sw_pre"] + x["sw_post"]),
                    "high_side_vs_ref": r is not None and all(abs(a["hs_on_vds_v"] - b["hs_on_vds_v"]) <= 0.3
                                                              for a, b in zip(x["sw_pre"], r["sw_pre"])),
                    "turnoff_spread": r is not None and sd(x["sw_pre"]) <= 1.5 * max(sd(r["sw_pre"]), 1e-9),
                    "d59_extreme": abs(x["extreme_mv"] / p["extreme_mv"] - 1) <= 0.3,
                    "d59_recovery": abs(x["back_within_1pct_us"] - p["back_within_1pct_us"]) <= max(0.5 * p["back_within_1pct_us"], 5.0),
                    "startup_vos": x["startup_vo_max_v"] <= 1.05}
            x["criteria"] = crit
            print(f"{name}: {x['status']}, overlaps {x['overlaps']}")
            print(f"   before: Vo {x['pre_vo_mean_v']:.4f} V p-p {x['pre_vo_pp_mv']:.2f} mV, Ton {x['pre_ton_mean_lsb']:.1f} p-p {x['pre_ton_pp_lsb']:.0f} LSB; "
                  f"HS V_DS " + "/".join(f"{q['hs_on_vds_v']:.2f}" for q in x["sw_pre"]) + "; LS max " + "/".join(f"{q['ls_on_vds_max_v']:+.2f}" for q in x["sw_pre"])
                  + "; turn-off sd " + "/".join(f"{q['i_lowoff_sd_a']:.2f}" for q in x["sw_pre"]) + " A")
            print(f"   step: {x['extreme_mv']:+.1f} mV at {x['t_extreme_us']:.1f} us (D59 {p['extreme_mv']:+.1f} at {p['t_extreme_us']:.1f}); "
                  f"back within 1% {x['back_within_1pct_us']:.1f} us (D59 {p['back_within_1pct_us']:.1f}); last 50 us Vo p-p {x['last50_vo_pp_mv']:.2f} mV, Ton p-p {x['last50_ton_pp_lsb']:.0f}")
            print(f"   after: HS V_DS " + "/".join(f"{q['hs_on_vds_v']:.2f}" for q in x["sw_post"]) + "; LS max " + "/".join(f"{q['ls_on_vds_max_v']:+.2f}" for q in x["sw_post"])
                  + "; turn-off sd " + "/".join(f"{q['i_lowoff_sd_a']:.2f}" for q in x["sw_post"]) + " A")
            print(f"   start-up: max {x['startup_vo_max_v']:.4f} V at {x['startup_t_vo_max_us']:.1f} us; above 1 V {x['startup_above_1v_us']:.1f} us, "
                  f"above 1.005 V {x['startup_above_1v005_us']:.1f} us")
            print("   criteria: " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in crit.items()))
    (HERE / "a104_summary.json").write_text(json.dumps(out, indent=1, default=float))
    print("\nwrote a104_summary.json")


if __name__ == "__main__":
    main()
