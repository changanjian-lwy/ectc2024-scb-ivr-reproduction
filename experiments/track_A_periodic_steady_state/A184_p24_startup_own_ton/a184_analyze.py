"""A184 analysis (BOUNDARY Section 2): g0 identity before mode P against A183, c1-c6 per run (every module of the
four-module run), against each condition's t0 = 400 ns record (REF). Writes a184_summary.json.
  python3 a184_analyze.py"""
from __future__ import annotations

import glob
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
A181, A173 = "A181_p24_locked_trim_joint_corner/cosim/", "A173_p24_final_plant_coverage/cosim/"
REF = {"S75_25": A181 + "run_S75_25_p0.json", "S75_hot": A181 + "run_S75_hot_p0.json", "N0_25": A173 + "run_nom_s_p62.json",
       "N0_hot": A181 + "run_N0_hot_p0.json", "S0_25": A173 + "run_il1p4_ss_l_p48_1us.json", "S0_hot": A181 + "run_S0_hot_p0.json",
       "N75_25": "A178_p24_inductance_tolerance_final/cosim/run_L075_sh0_l_p48_1us.json",
       "N07_25": A173 + "run_il2p0_nom_L07_l_p48_1us.json", "N13_25": A173 + "run_nom_L13_l_p48_1us.json",
       "F0_25": A173 + "run_ff_s_p62.json", "F0_hot": None, "M4_25": A173 + "run_m4_nom_s_p62.json"}
A183 = TA / "A183_p24_startup_period_ladder" / "cosim"
STEADY, VO_LO, VO_HI = (450e-6, 495e-6), 0.99, 1.17


def modules(r):
    return [r] + list(r.get("modules_rest") or [])


def entry_vo_min(r):
    tp = r["t_mode_p_s"]
    return min(q["vo"] for q in r["sections"] if tp < q["t_s"] < tp + 50e-6)


def steady_peaks(r):
    g = r["gate_offs_last"]
    return [float(np.mean([e["i_max_a"] for e in g if e["phase"] == k and STEADY[0] <= e["t_s"] < STEADY[1]])) for k in (1, 2, 3, 4)]


def mod_stats(r, t_step):
    tp, S, g = r["t_mode_p_s"], r["sections"], r["gate_offs_last"]
    pre = [q for q in S if q["t_s"] <= tp][-1]
    vin, c = pre["vin_v"], pre["vcs_v"]
    rails = [vin - c[0], c[0] - c[1], c[1] - c[2], c[2]]
    post = [q for q in S if tp < q["t_s"] < tp + 12e-6]
    lsb = r["lsb_s"]
    ov = r.get("overlaps")
    return {"vo_143_5": float(np.mean([q["vo"] for q in S if 143e-6 < q["t_s"] < 144e-6])),
            "ladder": max(rails) / min(rails), "start_pk": max(e["i_max_a"] for e in g if e["t_s"] < tp),
            "hand_pk": max(e["i_max_a"] for e in g if tp <= e["t_s"] < tp + 25e-6),
            "gap_pk": max(e["i_max_a"] for e in g if tp + 25e-6 <= e["t_s"] < min(t_step, r["t_end_s"])),
            "post_pk": max((e["i_max_a"] for e in g if e["t_s"] >= t_step), default=None),
            "vo_min_entry": entry_vo_min(r),
            "ton_max_entry_ns": max(q["ton_lsb"] for q in post) * lsb * 1e9,
            "ton_steady_ns": float(np.mean([q["ton_lsb"] for q in S if STEADY[0] <= q["t_s"] < STEADY[1]])) * lsb * 1e9,
            "steady_pk": steady_peaks(r), "vds_max_v": max(r["vds_max_v"]), "status": r["status"],
            "shoot_on": int(sum(r.get("gate_stats", {}).get("shoot_on", [0]))),
            "overlaps": ov if isinstance(ov, int) else len(ov or [])}


def identity(r, cond, k):
    """g0: every section before mode P's entry equals A183's run of the same board and condition."""
    f = A183 / f"run_{cond}_p{k}.json"
    if not f.exists():
        return None
    o = json.loads(f.read_text())
    tp = r["t_mode_p_s"]
    a = [q for q in r["sections"] if q["t_s"] <= tp]
    b = [q for q in o["sections"] if q["t_s"] <= o["t_mode_p_s"]]
    return tp == o["t_mode_p_s"] and a == b


def run(path):
    r = json.loads(Path(path).read_text())
    stem = Path(path).stem[4:]
    cond, k = stem.rsplit("_p", 1)
    c = r["cfg"]
    ls, ld = c.get("line_step") or {}, c.get("load_step") or {}
    t_step = (ls or ld)["t_us"] * 1e-6
    full = r["t_end_s"] > t_step
    mods = [mod_stats(m, t_step) for m in modules(r)]
    ref = REF.get(cond)
    refm = [mod_stats(m, json.loads((TA / ref).read_text())["cfg"].get("line_step", {}).get("t_us", 1000.0) * 1e-6)
            for m in modules(json.loads((TA / ref).read_text()))] if ref else None
    out = {"cond": cond, "k": int(k), "temp": c["gate"].get("temp", 25.0), "ton_s_ns": c.get("ton_s_ns"), "ton_ns": c["ton_ns"],
           "full": full, "modules": mods, "ref": ref, "g0_identical_pre_entry": identity(r, cond, k)}
    dev = [max(abs(a - b) for a, b in zip(m["steady_pk"], rm["steady_pk"])) for m, rm in zip(mods, refm)] if refm else None
    out["c5_dev_a"] = dev
    out["c6"] = [{"vo_min": m["vo_min_entry"], "ref": rm["vo_min_entry"]} for m, rm in zip(mods, refm)] if refm else None
    out["criteria"] = {
        "g0": out["g0_identical_pre_entry"],
        "c1": all(m["start_pk"] <= 200.0 and m["hand_pk"] <= 200.0 for m in mods),
        "c2": all(m["post_pk"] <= 200.0 for m in mods) if full else None,
        "c3": all(m["vds_max_v"] <= 40.0 and m["status"] == "COMPLETED" and m["shoot_on"] == 0 and m["overlaps"] == 0 for m in mods),
        "c4": all(VO_LO <= m["vo_143_5"] <= VO_HI for m in mods),
        "c5": all(d <= 2.0 for d in dev) if dev else None,
        "c6": all(m["vo_min_entry"] >= rm["vo_min_entry"] - 0.005 for m, rm in zip(mods, refm)) if refm else None}
    return stem, out


def main():
    res = dict(run(f) for f in sorted(glob.glob(str(HERE / "cosim" / "run_*.json"))))
    (HERE / "a184_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    for s, o in res.items():
        for j, m in enumerate(o["modules"]):
            print(f"{s:10s} m{j} Vo {m['vo_143_5']:.3f} ladder {m['ladder']:.3f} start {m['start_pk']:5.1f} hand {m['hand_pk']:5.1f} "
                  f"gap {m['gap_pk']:5.1f} post {m['post_pk'] or 0:5.1f} V {m['vds_max_v']:.1f} Vo_min {m['vo_min_entry']:.3f}"
                  + (f" (ref {o['c6'][j]['ref']:.3f}) dev {o['c5_dev_a'][j]:.2f}" if o["c6"] else "")
                  + f" Ton {m['ton_max_entry_ns']:.1f}/{m['ton_steady_ns']:.1f} ns")
        print("   ", o["criteria"], "g0", o["g0_identical_pre_entry"])


if __name__ == "__main__":
    main()
