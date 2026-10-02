"""A103 analysis: the start-up sequences in the Verilog co-simulation against D58's predictions and BOUNDARY Section 5.

Per run, from the sections (Vo sampled at phase 1's turn-on): Vo's maximum and its time, Vo at the handover (the
first section at or after t_hand), the minimum after it, the time above 1 V in the maximum's excursion, the last
exit from 1 V +/- 1% (D58's metrics on the sampled series); overlaps, peak V_DS and phase current; the ladder
deviation, A73's max |VCs_k / Vin - (4 - k) / 4| (sections with Vin >= 12 V before the handover; also Vin >= 24 V and at
the handover); the final state over the
last 200 periods (Vo, per-phase high-side turn-on V_DS, low-side turn-on V_DS maximum, low-side turn-off current)
against c0. c0 is also compared section by section with A100's reference run before its step (same design).
Writes a103_summary.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.p24_startup_averaged import Sequence, metrics  # noqa: E402

N, LAST = 4, 200
RUNS = ("c0_reference", "c1_load_from_0", "c1b_load_from_0_hand_72", "c1d_load_from_0_hand_72_ton568")


def load(name):
    return json.loads((HERE / "cosim" / f"run_{name}.json").read_text())


def final_state(d):
    sec = d["sections"][-LAST:]
    out = {"vo_v": float(np.mean([s["vo"] for s in sec])), "phases": []}
    for k in range(N):
        on = [r["vds_v"] for r in d["turnons_last"] if r["phase"] == k + 1][-LAST:]
        lo = [r["vds_v"] for r in d["lowons_last"] if r["phase"] == k + 1][-LAST:]
        off = [r["i_a"] for r in d["lowoffs_last"] if r["phase"] == k + 1][-LAST:]
        out["phases"].append({"hs_on_vds_v": float(np.mean(on)), "ls_on_vds_max_v": float(np.max(lo)),
                              "i_lowoff_a": float(np.mean(off))})
    return out


def main():
    pred = json.loads((HERE / "d58_predictions.json").read_text())
    out = {"runs": {}}
    a100 = json.loads((PROJECT / "experiments" / "track_A_periodic_steady_state" / "A100_timed_turn_off_load_steps" / "cosim"
                       / "run_ref_m62.json").read_text())
    c0 = load("c0_reference")
    n = sum(1 for s in a100["sections"] if s["t_s"] < 300e-6)
    same = c0["sections"][:n] == a100["sections"][:n]
    out["c0_equals_a100_ref_before_300us"] = same
    print(f"c0 against A100's reference, {n} sections before 300 us: {'identical' if same else 'DIFFERENT'}")
    fin0 = final_state(c0)
    for name in RUNS:
        d = load(name)
        cfg = d["cfg"]
        t_hand = cfg.get("t_hand_us", 88.61) * 1e-6
        t_load = cfg.get("t_load_us", 88.61) * 1e-6
        sq = Sequence(t_load=t_load, t_hand=t_hand)
        t = np.array([s["t_s"] for s in d["sections"]]); vo = np.array([s["vo"] for s in d["sections"]])
        x = metrics(t, vo, sq)
        x["vo_at_handover_v"] = float(vo[t >= t_hand][0])
        vin = np.array([s["vin_v"] for s in d["sections"]])
        vcs = np.array([s["vcs_v"] for s in d["sections"]])
        dev = np.max(np.abs(vcs / np.maximum(vin, 1e-9)[:, None] - np.array([0.75, 0.5, 0.25])), axis=1)   # A73's formula
        x["ladder_dev_before_handover"] = float(dev[(vin >= 12.0) & (t < t_hand)].max())
        x["ladder_dev_vin_ge_24"] = float(dev[(vin >= 24.0) & (t < t_hand)].max())
        x["ladder_dev_at_handover"] = float(dev[np.argmax(t >= t_hand)])
        x.update(status=d["status"], overlaps=d["overlaps"], vds_max_v=float(max(d["vds_max_v"])), ipk_a=float(d["ipk_a"]))
        fs = final_state(d)
        x["final"] = fs
        p = pred[name]
        crit = {"no_overlap": d["overlaps"] == 0,
                "peaks_vs_a73_24p8v": x["vds_max_v"] <= 24.8 + 0.5 and x["ipk_a"] <= c0["ipk_a"] + 1.0,
                "ladder": x["ladder_dev_before_handover"] <= 0.03,
                "vo_max": abs(x["vo_max_v"] - p["vo_max_v"]) <= 0.015 and abs(x["t_vo_max_us"] - p["t_vo_max_us"]) <= 15,
                "handover_min": abs(x["vo_at_handover_v"] - p["vo_at_handover_v"]) <= 0.03
                and abs(x["vo_min_after_handover_v"] - p["vo_min_after_handover_v"]) <= 0.03,
                "settle": abs(x["settle_1pct_us"] - p["settle_1pct_us"]) <= 20,
                "final_state": abs(fs["vo_v"] - fin0["vo_v"]) <= 3e-3
                and all(abs(a["hs_on_vds_v"] - b["hs_on_vds_v"]) <= 0.1 and a["ls_on_vds_max_v"] <= 0
                        and abs(a["i_lowoff_a"] - b["i_lowoff_a"]) <= 0.5 for a, b in zip(fs["phases"], fin0["phases"]))}
        if name != "c0_reference":
            crit["vrd_vos"] = x["vo_max_v"] <= 1.050
            crit["vrd_tos_reported"] = x["t_above_vid_us"] <= 25.0
        x["criteria"] = crit
        out["runs"][name] = x
        print(f"\n{name}: {d['status']}, overlaps {d['overlaps']}, peak V_DS {x['vds_max_v']:.1f} V, peak current {x['ipk_a']:.0f} A, "
              f"ladder deviation before the handover {100 * x['ladder_dev_before_handover']:.1f}% (Vin >= 24 V: "
              f"{100 * x['ladder_dev_vin_ge_24']:.1f}%, at the handover {100 * x['ladder_dev_at_handover']:.2f}%)")
        print(f"   Vo max {x['vo_max_v']:.3f} V at {x['t_vo_max_us']:.1f} us (D58 {p['vo_max_v']:.3f} at {p['t_vo_max_us']:.1f}); "
              f"{x['t_above_vid_us']:.1f} us above 1 V (D58 {p['t_above_vid_us']:.1f})")
        print(f"   at the handover {x['vo_at_handover_v']:.3f} V (D58 {p['vo_at_handover_v']:.3f}); min after {x['vo_min_after_handover_v']:.3f} V "
              f"(D58 {p['vo_min_after_handover_v']:.3f}); within 1% from {x['settle_1pct_us']:.1f} us (D58 {p['settle_1pct_us']:.1f})")
        print(f"   final: Vo {fs['vo_v']:.4f} V; HS V_DS " + " / ".join(f"{q['hs_on_vds_v']:.2f}" for q in fs["phases"])
              + "; LS on max " + " / ".join(f"{q['ls_on_vds_max_v']:+.2f}" for q in fs["phases"])
              + "; turn-off " + " / ".join(f"{q['i_lowoff_a']:.2f}" for q in fs["phases"]) + " A")
        print("   criteria: " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in crit.items()))
    (HERE / "a103_summary.json").write_text(json.dumps(out, indent=1, default=float))
    print("\nwrote a103_summary.json")


if __name__ == "__main__":
    main()
