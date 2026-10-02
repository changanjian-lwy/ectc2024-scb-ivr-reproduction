"""C02 analysis against BOUNDARY Section 4, on the shared statistics (scb_ivr.cosim.matrix). Over the last 200 periods
(before the step for step runs):
A. one module (s1_*) against A105 i2_*: the sections before 72 us identical; the low-side turn-offs after phase 1's,
   against (k - 1) T/4; the module's output current ripple; valleys, high-side turn-on V_DS, low-side turn-on V_DS,
   turn-off sd; late fires; Vo, the step and the start-up.
B. four modules (m4_*) against C01's runs: the 16 low-side turn-offs' gaps; the system's output current ripple; locked
   periods; currents (piecewise-linear, normalised to the load) and valleys against C01; steps, start-up, join,
   overlaps, peak, late fires.
Writes c02_summary.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.cosim.matrix import GRID_S, lsoff_after, output_ripple, phase_waveform, ref_turnons, step_stats, window_stats  # noqa: E402

A105 = PROJECT / "experiments" / "track_A_periodic_steady_state" / "A105_p24_integrated_standard_matrix" / "cosim"
C01 = HERE.parent / "C01_four_modules_baseline" / "cosim"
PART_A = {"s1_n0": "i2_n0", "s1_j30": "i2_j30", "s1_s_m62": "i2_s_m62", "s1_s_p62": "i2_s_p62"}
PART_B = ("m4_n0", "m4_L5", "m4_j30", "m4_s_m250", "m4_s_p250")
T_HAND = 72e-6
R_SYS = 1e-3
RIPPLE_A = (100.9, 29.4)                     # C01's re-placement of one module (pk-pk, rms), A
RIPPLE_B = {"m4_n0": (31.3, 6.6), "m4_L5": (69.7, 9.0)}


def load(path):
    return json.loads(path.read_text())


def t1_of(name):
    return 400e-6 if "_s_" in name else None


def late(d):
    return int(sum(d["late_fires"])) if isinstance(d["late_fires"], list) else int(d["late_fires"])


def gaps(offsets, period):
    """Sorted low-side turn-off times modulo the period -> the gaps between neighbours (s)."""
    t = np.sort(np.mod(np.array(offsets), period))
    return np.diff(np.append(t, t[0] + period))


def module_stats(d, t1):
    w = window_stats(d, t1=t1)
    return {"valleys_a": [p["i_off_mean_a"] for p in w["phases"]], "hs_on_vds_v": [p["hs_on_vds_v"] for p in w["phases"]],
            "ls_on_vds_max_v": [p["ls_on_vds_max_v"] for p in w["phases"]], "off_sd_a": [p["i_off_sd_a"] for p in w["phases"]],
            "period_ns": w["period_ns"], "vo_mean_v": w["vo_mean_v"], "overlaps": d["overlaps"], "ipk_a": d["ipk_a"],
            "late_fires": late(d)}


def startup_max(d):
    return float(max(s["vo"] for s in d["sections"] if s["t_s"] < 400e-6))


def part_a():
    res = {}
    for name, ref_name in PART_A.items():
        p = HERE / "cosim" / f"run_{name}.json"
        if not p.exists():
            continue
        d, ref = load(p), load(A105 / f"run_{ref_name}.json")
        t1 = t1_of(name)
        x, r = module_stats(d, t1), module_stats(ref, t1)
        pre = [s for s in d["sections"] if s["t_s"] < T_HAND]
        pre_ref = [s for s in ref["sections"] if s["t_s"] < T_HAND]
        x["identical_before_72us"] = json.dumps(pre) == json.dumps(pre_ref)
        _, per = ref_turnons(d, t1)
        off = lsoff_after(d, d, t1)
        x["lsoff_after_on_ns"] = [o * 1e9 for o in off]
        x["lsoff_after_phase1_ns"] = [((o - off[0]) % per) * 1e9 for o in off]
        x["period_ns_ref"] = per * 1e9
        x["ripple"], r["ripple"] = output_ripple([d], t1=t1), output_ripple([ref], t1=t1)
        x["startup_max_v"], r["startup_max_v"] = startup_max(d), startup_max(ref)
        if t1:
            x["step"], r["step"] = step_stats(d), step_stats(ref)
        c = {"identical_before_72us": x["identical_before_72us"],
             "uniform_T4": all(abs(x["lsoff_after_phase1_ns"][k] - k * per / 4 * 1e9) <= 0.1 for k in range(4)),
             "valleys_0p5A": all(abs(a - b) <= 0.5 for a, b in zip(x["valleys_a"], r["valleys_a"])),
             "hs_on_0p2V": all(abs(a - b) <= 0.2 for a, b in zip(x["hs_on_vds_v"], r["hs_on_vds_v"])),
             "no_overlap": x["overlaps"] == 0, "peak_200a": x["ipk_a"] <= 200.0,
             "late_fires_not_more": x["late_fires"] <= r["late_fires"], "vo_1mV": abs(x["vo_mean_v"] - 1.0) <= 1e-3,
             "startup": x["startup_max_v"] <= 1.05}
        if name == "s1_n0":
            c["ls_zvs"] = max(x["ls_on_vds_max_v"]) <= 0.0
            c["ripple_pred"] = all(abs(x["ripple"][k] / v - 1) <= 0.2 for k, v in zip(("pkpk_a", "rms_ac_a"), RIPPLE_A))
        if name == "s1_j30":
            c["sd_band"] = all(abs(a / b - 1) <= 0.3 for a, b in zip(x["off_sd_a"], r["off_sd_a"]))
        if t1:
            c["step_10pct"] = abs(x["step"]["extreme_mv"] / r["step"]["extreme_mv"] - 1) <= 0.1
        res[name] = {"c02": x, "a105": r, "criteria": c}
        print(f"{name} (vs A105 {ref_name}): status {d['status']}, overlaps {x['overlaps']}, ipk {x['ipk_a']:.1f} A, late fires {x['late_fires']} (A105 {r['late_fires']}), "
              f"identical before 72 us {x['identical_before_72us']}")
        print(f"   T {per * 1e9:.2f} ns; low-side turn-offs after phase 1's: " + "/".join(f"{v:.2f}" for v in x["lsoff_after_phase1_ns"])
              + f" ns (T/4 = {per / 4 * 1e9:.2f}); after phase 1's turn-on: " + "/".join(f"{v:.2f}" for v in x["lsoff_after_on_ns"]))
        print("   valleys " + "/".join(f"{v:+.2f}" for v in x["valleys_a"]) + " (A105 " + "/".join(f"{v:+.2f}" for v in r["valleys_a"]) + "), HS on "
              + "/".join(f"{v:.2f}" for v in x["hs_on_vds_v"]) + " (" + "/".join(f"{v:.2f}" for v in r["hs_on_vds_v"]) + "), LS max "
              + "/".join(f"{v:+.2f}" for v in x["ls_on_vds_max_v"]) + " (" + "/".join(f"{v:+.2f}" for v in r["ls_on_vds_max_v"]) + "), sd "
              + "/".join(f"{v:.2f}" for v in x["off_sd_a"]) + " (" + "/".join(f"{v:.2f}" for v in r["off_sd_a"]) + ")")
        print(f"   ripple {x['ripple']['pkpk_a']:.1f} A pk-pk / {x['ripple']['rms_ac_a']:.2f} A rms (A105 {r['ripple']['pkpk_a']:.1f} / {r['ripple']['rms_ac_a']:.2f}); "
              f"Vo {x['vo_mean_v']:.5f} (A105 {r['vo_mean_v']:.5f}); start-up {x['startup_max_v']:.4f} V")
        if t1:
            print(f"   step {x['step']['extreme_mv']:+.2f} mV at {x['step']['t_extreme_us']:.2f} us, back {x['step']['back_within_1pct_us']:.2f} us "
                  f"(A105 {r['step']['extreme_mv']:+.2f} / {r['step']['t_extreme_us']:.2f} / {r['step']['back_within_1pct_us']:.2f})")
        print("   criteria: " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in c.items()))
    return res


def system(d, t1):
    mods = [d] + d["modules_rest"]
    t_on, per = ref_turnons(d, t1)
    g = np.arange(t_on[0], t_on[-1], GRID_S)
    pl = [float(sum(phase_waveform(r, k, g).mean() for k in range(1, 5))) for r in mods]
    vo = window_stats(d, t1=t1)["vo_mean_v"]
    offs = [o for r in mods for o in lsoff_after(d, r, t1)]
    out = {"modules": [module_stats(r, t1) for r in mods], "period_ns": per * 1e9,
           "currents_norm_a": [x / sum(pl) * vo / R_SYS for x in pl], "lsoff_after_master_ns": [o * 1e9 for o in offs],
           "gaps_ns": [x * 1e9 for x in gaps(offs, per)], "ripple": output_ripple(mods, t1=t1),
           "join_max_v": d["system"]["equalisation_max_v"], "startup_max_v": startup_max(d), "vo_mean_v": vo}
    if t1:
        out["step"] = step_stats(d)
    return out


def part_b():
    res = {}
    for name in PART_B:
        p = HERE / "cosim" / f"run_{name}.json"
        if not p.exists():
            continue
        t1 = t1_of(name)
        x, r = system(load(p), t1), system(load(C01 / f"run_{name}.json"), t1)
        mx, mr = x["modules"], r["modules"]
        c = {"uniform_T16": max(abs(gp - x["period_ns"] / 16) for gp in x["gaps_ns"]) <= 0.1 if name != "m4_j30" else True,
             "locked": all(abs(m["period_ns"] - mx[0]["period_ns"]) <= 0.1 for m in mx[1:]),
             "currents_1A": all(abs(a - b) <= 1.0 for a, b in zip(x["currents_norm_a"], r["currents_norm_a"])),
             "valleys_0p5A": all(abs(a - b) <= 0.5 for m, n in zip(mx, mr) for a, b in zip(m["valleys_a"], n["valleys_a"])),
             "no_overlap": all(m["overlaps"] == 0 for m in mx), "peak_200a": max(m["ipk_a"] for m in mx) <= 200.0,
             "join_0p1mV": x["join_max_v"] <= 1e-4, "startup": x["startup_max_v"] <= 1.05,
             "late_fires_not_more": sum(m["late_fires"] for m in mx) <= sum(m["late_fires"] for m in mr)}
        if name in RIPPLE_B:
            c["ripple_pred"] = all(abs(x["ripple"][k] / v - 1) <= 0.3 for k, v in zip(("pkpk_a", "rms_ac_a"), RIPPLE_B[name]))
        if t1:
            c["step_10pct"] = abs(x["step"]["extreme_mv"] / r["step"]["extreme_mv"] - 1) <= 0.1
        res[name] = {"c02": x, "c01": r, "criteria": c}
        print(f"{name}: overlaps {[m['overlaps'] for m in mx]}, ipk {[round(m['ipk_a']) for m in mx]} A, late fires {[m['late_fires'] for m in mx]} "
              f"(C01 {[m['late_fires'] for m in mr]}), join {x['join_max_v'] * 1e6:.1f} uV, T {x['period_ns']:.2f} ns (C01 {r['period_ns']:.2f})")
        print(f"   gaps {min(x['gaps_ns']):.2f}-{max(x['gaps_ns']):.2f} ns (C01 {min(r['gaps_ns']):.2f}-{max(r['gaps_ns']):.2f}); ripple {x['ripple']['pkpk_a']:.1f} A pk-pk / "
              f"{x['ripple']['rms_ac_a']:.2f} A rms (C01 {r['ripple']['pkpk_a']:.1f} / {r['ripple']['rms_ac_a']:.2f})")
        print("   currents " + "/".join(f"{v:.1f}" for v in x["currents_norm_a"]) + " (C01 " + "/".join(f"{v:.1f}" for v in r["currents_norm_a"]) + ") A; Vo "
              f"{x['vo_mean_v']:.5f}; start-up {x['startup_max_v']:.4f} V")
        for m, (a, b) in enumerate(zip(mx, mr)):
            print(f"   module {m}: valleys " + "/".join(f"{v:+.2f}" for v in a["valleys_a"]) + " (C01 " + "/".join(f"{v:+.2f}" for v in b["valleys_a"]) + "), HS on "
                  + "/".join(f"{v:.2f}" for v in a["hs_on_vds_v"]) + ", LS max " + "/".join(f"{v:+.2f}" for v in a["ls_on_vds_max_v"]) + ", sd "
                  + "/".join(f"{v:.2f}" for v in a["off_sd_a"]))
        if t1:
            print(f"   step {x['step']['extreme_mv']:+.2f} mV at {x['step']['t_extreme_us']:.2f} us, back {x['step']['back_within_1pct_us']:.2f} us "
                  f"(C01 {r['step']['extreme_mv']:+.2f} / {r['step']['t_extreme_us']:.2f} / {r['step']['back_within_1pct_us']:.2f})")
        print("   criteria: " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in c.items()))
    return res


def main():
    out = {"part_a": part_a(), "part_b": part_b()}
    (HERE / "c02_summary.json").write_text(json.dumps(out, indent=1, default=float))
    print("\nwrote c02_summary.json")


if __name__ == "__main__":
    main()
