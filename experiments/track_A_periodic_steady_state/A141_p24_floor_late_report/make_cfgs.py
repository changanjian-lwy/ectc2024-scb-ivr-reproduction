"""A141 cosim cfgs and registered predictions. Arm F = the adopted design (C10 template: g125 + vff rel_q8 320,
rel_lp 1, seed 2) with cfg floor_late 1. Rows: A140's L x 0.7 rising rows (R), two falling A124 rows at L0 (D), the
single-module A124 rising rows at L0 / L x 1.3 (A), C10's four-module rising rows (C), and two identity replays (I0: an
A140 cfg verbatim on the new code; I1: C10 s100_n0 with floor_late 1). Predictions: each row's reference record with
the floor-first duplicate periods taken out (stats). Writes cosim/cfg_*.json and a141_predictions.json."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
COS = HERE / "cosim"
A140 = PROJECT / "experiments/track_A_periodic_steady_state/A140_p24_slew_nonmonotone/cosim"
C10 = PROJECT / "experiments/track_C_multi_module/C10_seed_before_entry/cosim"
TEMPLATE = C10 / "cfg_s100_l_p48_1us.json"
T_STEP_US, T_END_US, DT_POS_US = 1000.0, 1200.0, 0.125
DUP_S, AFTER_S = 20e-9, 60e-9

# name -> (L x, dv, slew, step position) for the A140-style rows; reference record (project-relative)
ROWS = {"F_L070_p4.8_s1.0": ((0.7, 4.8, 1.0, 0), "experiments/track_A_periodic_steady_state/A137_p24_vff_restart_at_handover/cosim/run_s070_l_p48_1us.json"),
        "F_L070_p4.8_s5.0": ((0.7, 4.8, 5.0, 0), "experiments/track_A_periodic_steady_state/A137_p24_vff_restart_at_handover/cosim/run_s070_l_p48_5us.json"),
        "F_L070_p4.8_s10.0": ((0.7, 4.8, 10.0, 0), None),
        "F_L070_p4.8_s20.0": ((0.7, 4.8, 20.0, 0), "extensions/ml_design_assist/experiments/A139_gp_boundary_noise_floor/cosim/run_ur01.json"),
        "F_L070_p4.8_s20.0_q1": ((0.7, 4.8, 20.0, 1), None),
        "F_L070_p4.8_s20.0_q2": ((0.7, 4.8, 20.0, 2), None),
        "F_L070_p4.8_s20.0_q3": ((0.7, 4.8, 20.0, 3), None),
        "F_L070_p4.8_s40.0": ((0.7, 4.8, 40.0, 0), None),
        "F_L070_p8.0_s20.0": ((0.7, 8.0, 20.0, 0), None),
        "F_L070_p8.0_s50.0": ((0.7, 8.0, 50.0, 0), None),
        "F_L100_m4.8_s1.0": ((1.0, -4.8, 1.0, 0), "extensions/ml_design_assist/experiments/A138_gp_boundary_map/cosim/run_vf05.json"),
        "F_L100_m8.0_s10.0": ((1.0, -8.0, 10.0, 0), None)}
# C10 cfgs taken with floor_late 1 (A: one module, C: four modules)
C10_ROWS = ["s100_l_p48_1us", "s100_l_p48_5us", "s130_l_p48_1us", "s130_l_p48_5us", "l_p48_1us", "l_p48_5us"]


def ref_path(n):
    if n.startswith("F_L"):
        p = ROWS[n][1]
        return PROJECT / p if p else A140 / f"run_B{n[1:]}.json"
    return C10 / f"run_{n[2:]}.json"


def floor_first(md):
    """Floor-first duplicate turn-ons: an off-grid (front-end) turn-on, then an on-grid (clocked) one of the same
    phase < DUP_S later. Returns (floor-first list of the second turn-ons, count of other duplicates)."""
    lsb, tdrv = md["lsb_s"], md["cfg"]["t_drv_ns"] * 1e-9

    def grid(t):
        q = (t - tdrv) / lsb
        return abs(q - round(q)) < 1e-3
    ons = sorted(md["turnons_last"], key=lambda o: (o["phase"], o["t_s"]))
    ff, other = [], 0
    for a, b in zip(ons, ons[1:]):
        if a["phase"] == b["phase"] and b["t_s"] - a["t_s"] < DUP_S:
            if not grid(a["t_s"]) and grid(b["t_s"]):
                ff.append(b)
            else:
                other += 1
    return ff, other


def module_stats(md, ts):
    ff, other = floor_first(md)
    his = [q for q in md["highoffs_last"] if q["t_s"] >= ts]
    hi = max(his, key=lambda q: q["i_a"])
    dup_hit = [q for q in his if any(o["phase"] == q["phase"] and 0 < q["t_s"] - o["t_s"] < AFTER_S for o in ff)]
    clean = [q for q in his if q not in dup_hit]
    ys = [q["i_a"] for q in his if q["phase"] == hi["phase"]]
    env3 = max(float(np.median(ys[i:i + 3])) for i in range(len(ys) - 2))
    return {"peak": hi["i_a"], "phase": hi["phase"], "t_pk_us": (hi["t_s"] - ts) * 1e6,
            "nodup": max(q["i_a"] for q in clean), "env3": env3,
            "ff_all": len(ff), "ff_post": sum(o["t_s"] >= ts for o in ff), "other_dup": other}


def stats(path):
    """Per module and system (max over modules) after the line step."""
    d = json.loads(Path(path).read_text())
    ts = d["cfg"]["line_step"]["t_us"] * 1e-6
    mods = [module_stats(md, ts) for md in [d] + d.get("modules_rest", [])]
    k = max(range(len(mods)), key=lambda i: mods[i]["peak"])
    return {"peak": mods[k]["peak"], "module": k + 1, "env3": mods[k]["env3"],
            "nodup": max(m["nodup"] for m in mods), "ff_all": sum(m["ff_all"] for m in mods),
            "ff_post": sum(m["ff_post"] for m in mods), "other_dup": sum(m["other_dup"] for m in mods),
            "modules": mods, "late": sum(d["late_fires"]), "overlaps": d["overlaps"]}


def write(name, t, note):
    t["note"] = f"A141 {name}: {note}"
    t["out"] = f"run_{name}.json"
    (COS / f"cfg_{name}.json").write_text(json.dumps(t, indent=1) + "\n")


def main():
    COS.mkdir(exist_ok=True)
    tpl = json.loads(TEMPLATE.read_text())
    for n, ((m, dv, slew, pos), _) in ROWS.items():
        t = json.loads(json.dumps(tpl))
        t["circuit"] = dict(t["circuit"], L=t["circuit"]["L"] * m)
        t_step = T_STEP_US + pos * DT_POS_US
        t["line_step"] = {"t_us": t_step, "dv": dv, "slew_us": slew}
        t["t_end_us"] = T_END_US
        t["floor_late"] = 1
        write(n, t, f"adopted single-module design + floor_late 1, L x {m}, line step {dv:+.1f} V over {slew} us at "
                    f"{t_step:.3f} us (A140 row B{n[1:]}).")
    for r in C10_ROWS:
        t = json.loads((C10 / f"cfg_{r}.json").read_text())
        t["floor_late"] = 1
        write(f"F_{r}", t, f"C10 {r} + floor_late 1.")
    t = json.loads((A140 / "cfg_B_L070_p4.8_s10.0.json").read_text())       # I0: verbatim, no floor_late
    write("I0_B_L070_p4.8_s10.0", t, "identity replay of A140 B_L070_p4.8_s10.0 on the A141 code (floor_late absent).")
    t = json.loads((C10 / "cfg_s100_n0.json").read_text())
    t["floor_late"] = 1
    write("I1_s100_n0", t, "C10 s100_n0 + floor_late 1 (no floor-first event on record: must replay bit for bit).")
    pred = {"note": "reference record of each F row: peak (with the duplicates), nodup (the periods ending within 60 ns "
                    "after a floor-first duplicate turn-on taken out), env3 (median-of-3 envelope of the peaking phase); "
                    "predicted F peak = nodup (A139 noise floor ~1 A, heavy tail removed)", "runs": {}}
    for n in list(ROWS) + [f"F_{r}" for r in C10_ROWS]:
        s = stats(ref_path(n))
        pred["runs"][n] = {"ref": str(ref_path(n).relative_to(PROJECT)),
                           **{k: s[k] for k in ("peak", "nodup", "env3", "ff_all", "ff_post", "module")}}
    (HERE / "a141_predictions.json").write_text(json.dumps(pred, indent=1) + "\n")
    for n, p in pred["runs"].items():
        print(f"{n:24s} ref peak {p['peak']:6.1f}  nodup {p['nodup']:6.1f}  env3 {p['env3']:6.1f}  ff {p['ff_post']}/{p['ff_all']}")


if __name__ == "__main__":
    main()
