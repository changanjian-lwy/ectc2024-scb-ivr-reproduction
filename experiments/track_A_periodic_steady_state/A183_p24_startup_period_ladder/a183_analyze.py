"""A183 analysis. Stage 1 (screen): per start-up run - Vo(143.5 us), the Cs ladder at mode P's entry (four phase
rails, max / min), mean mode-S valleys per phase (140 us .. entry), start-up peak (physical gate turn-off peaks before
mode P), handover peak (entry .. entry + 25 us), Vo minimum and largest loop Ton / cfg Ton in entry .. entry + 12 us,
V_DS, shoot-throughs / overlaps, status. Writes a183_screen.json; pick() applies BOUNDARY Section 2's stage-1 rule
(bracketing pair around Vo 1.035 V, both runs S1-S3) -> a183_pick.json.
Stage 2 (stage2()): cosim/run_*.json against c1-c5 (BOUNDARY Section 2) -> a183_summary.json; c5 compares each
board's mean per-phase physical peak over 250-300 us with its t0 = 400 ns record (REF). Diagnostic pre_step_pk:
entry + 25 us .. step (or end), the window neither c1 nor c2 covers; flagged in RESULTS if > 200 A.
  python3 a183_analyze.py screen | stage2"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
REF = {"S75": "A181_p24_locked_trim_joint_corner/cosim/run_S75_25_p0.json",
       "S0": "A173_p24_final_plant_coverage/cosim/run_il1p4_ss_l_p48_1us.json",
       "N0": "A173_p24_final_plant_coverage/cosim/run_nom_s_p62.json",
       "N75": "A178_p24_inductance_tolerance_final/cosim/run_L075_sh0_l_p48_1us.json",
       "N07": "A173_p24_final_plant_coverage/cosim/run_il2p0_nom_L07_l_p48_1us.json",
       "N13": "A173_p24_final_plant_coverage/cosim/run_nom_L13_l_p48_1us.json",
       "F0": "A173_p24_final_plant_coverage/cosim/run_ff_s_p62.json"}


def ladder(sec):
    vin, c = sec["vin_v"], sec["vcs_v"]
    return [vin - c[0], c[0] - c[1], c[1] - c[2], c[2]]


def start_stats(path):
    r = json.loads(Path(path).read_text())
    tp, lsb, S = r["t_mode_p_s"], r["lsb_s"], r["sections"]
    g = r["gate_offs_last"]
    pre = [q for q in S if q["t_s"] <= tp][-1]
    post = [q for q in S if tp < q["t_s"] < tp + 12e-6]
    rails = ladder(pre)
    lo = r["lowoffs_last"]
    valley = [float(np.mean([e["i_a"] for e in lo if e["phase"] == k and 140e-6 < e["t_s"] < tp])) for k in (1, 2, 3, 4)]
    ton_cfg = r["cfg"]["ton_ns"] * 1e-9 / lsb
    return {"t0_ns": r["cfg"]["t0_ns"], "ton_ns": r["cfg"]["ton_ns"], "status": r["status"],
            "vo_143_5": float(np.mean([q["vo"] for q in S if 143e-6 < q["t_s"] < 144e-6])),
            "rails_v": [round(x, 3) for x in rails], "rail_ratio": max(rails) / min(rails),
            "valley_a": [round(x, 1) for x in valley],
            "start_pk": max(e["i_max_a"] for e in g if e["t_s"] < tp),
            "hand_pk": max((e["i_max_a"] for e in g if tp <= e["t_s"] < tp + 25e-6), default=None),
            "vo_min_hand": min(q["vo"] for q in post), "ton_max_hand": max(q["ton_lsb"] for q in post) / ton_cfg,
            "vds_max_v": max(r["vds_max_v"]), "shoot_on": int(sum(r.get("gate_stats", {}).get("shoot_on", [0]))),
            "overlaps": r.get("overlaps"), "late": r["late_fires"]}


VO_TGT = 1.035


def passes(s):
    ov = s["overlaps"] if isinstance(s["overlaps"], int) else len(s["overlaps"] or [])
    return {"S1": s["start_pk"] <= 200.0, "S2": (s["hand_pk"] or 0.0) <= 200.0,
            "S3": s["vds_max_v"] <= 40.0 and s["shoot_on"] == 0 and ov == 0 and s["status"] == "COMPLETED"}


def pick(out):
    res = {}
    for t0 in sorted({s["t0_ns"] for s in out.values()}):
        runs = [(k, s) for k, s in out.items() if s["t0_ns"] == t0]
        lo = max((x for x in runs if x[1]["vo_143_5"] <= VO_TGT), default=None, key=lambda x: x[1]["vo_143_5"])
        hi = min((x for x in runs if x[1]["vo_143_5"] >= VO_TGT), default=None, key=lambda x: x[1]["vo_143_5"])
        if not (lo and hi):
            res[t0] = {"bracketed": False}
            continue
        pair = {k: passes(s) for k, s in (lo, hi)}
        (a, sa), (b, sb) = lo, hi
        trim = sa["ton_ns"] + (VO_TGT - sa["vo_143_5"]) * (sb["ton_ns"] - sa["ton_ns"]) / (sb["vo_143_5"] - sa["vo_143_5"])
        res[t0] = {"bracketed": True, "pair": [a, b], "checks": pair, "pass": all(all(c.values()) for c in pair.values()),
                   "worst_a": max(max(s["start_pk"], s["hand_pk"] or 0.0) for _, s in (lo, hi)), "trim_ns": round(trim, 3)}
    ok = {t0: r for t0, r in res.items() if r.get("pass")}
    t0s = min(ok, key=lambda t0: ok[t0]["worst_a"]) if ok else None
    return {"per_t0": res, "t0_star": t0s}


def screen():
    out = {Path(f).stem[4:]: start_stats(f) for f in sorted(glob.glob(str(HERE / "cosim_screen" / "run_*.json")))}
    (HERE / "a183_screen.json").write_text(json.dumps(out, indent=1) + "\n")
    pk = pick(out)
    (HERE / "a183_pick.json").write_text(json.dumps(pk, indent=1) + "\n")
    for k, s in sorted(out.items(), key=lambda kv: (kv[1]["t0_ns"], kv[1]["ton_ns"])):
        print(f"{k:16s} Vo {s['vo_143_5']:.3f} rails {' '.join(f'{x:5.2f}' for x in s['rails_v'])} ({s['rail_ratio']:.2f}) "
              f"valley {' '.join(f'{x:6.1f}' for x in s['valley_a'])} | start {s['start_pk']:5.1f} hand {s['hand_pk'] or 0:5.1f} "
              f"Vo min {s['vo_min_hand']:.3f} Ton {s['ton_max_hand']:.2f}x | V {s['vds_max_v']:.1f} shoot {s['shoot_on']} {s['status']}")
    for t0, r in pk["per_t0"].items():
        print(t0, r)
    print("t0* =", pk["t0_star"])


def steady_peaks(r):
    g = r["gate_offs_last"]
    return [float(np.mean([e["i_max_a"] for e in g if e["phase"] == k and 250e-6 <= e["t_s"] < 300e-6])) for k in (1, 2, 3, 4)]


def run_stats(path):
    st = start_stats(path)
    r = json.loads(Path(path).read_text())
    c = r["cfg"]
    board = Path(path).stem[4:].split("_")[0]
    t_step = c["line_step"]["t_us"] * 1e-6
    full = r["t_end_s"] > t_step
    post = [e["i_max_a"] for e in r["gate_offs_last"] if e["t_s"] >= t_step]
    gap = [e["i_max_a"] for e in r["gate_offs_last"] if r["t_mode_p_s"] + 25e-6 <= e["t_s"] < min(t_step, r["t_end_s"])]
    tp = r["t_mode_p_s"]
    after = [q["vo"] for q in r["sections"] if tp < q["t_s"] < tp + 50e-6]
    ref = steady_peaks(json.loads((TA / REF[board]).read_text()))
    sp = steady_peaks(r)
    st.update(board=board, temp=c["gate"].get("temp", 25.0), t_step_us=c["line_step"]["t_us"] if full else None,
              peak_post=max(post) if full else None, pre_step_pk=max(gap), vo_max_hand=max(after), steady_pk=[round(x, 2) for x in sp],
              steady_ref=[round(x, 2) for x in ref], steady_dev=max(abs(a - b) for a, b in zip(sp, ref)))
    ok = passes(st)
    st["criteria"] = {"c1": ok["S1"] and ok["S2"], "c2": (st["peak_post"] <= 200.0) if full else None, "c3": ok["S3"],
                      "c4": (0.99 <= st["vo_143_5"] <= 1.17) if st["temp"] != 25.0 else None, "c5": st["steady_dev"] <= 2.0}
    return st


def stage2():
    out = {Path(f).stem[4:]: run_stats(f) for f in sorted(glob.glob(str(HERE / "cosim" / "run_*.json")))}
    (HERE / "a183_summary.json").write_text(json.dumps(out, indent=1) + "\n")
    for k, s in out.items():
        print(f"{k:12s} Vo {s['vo_143_5']:.3f} ladder {s['rail_ratio']:.2f} start {s['start_pk']:5.1f} hand {s['hand_pk'] or 0:5.1f} "
              f"gap {s['pre_step_pk']:5.1f} post {s['peak_post'] or 0:5.1f} V {s['vds_max_v']:.1f} Vo {s['vo_min_hand']:.3f}-{s['vo_max_hand']:.3f} "
              f"Ton {s['ton_max_hand']:.2f}x steady dev {s['steady_dev']:.2f} A {s['criteria']}")


if __name__ == "__main__":
    {"screen": screen, "stage2": stage2}[sys.argv[1]]()
