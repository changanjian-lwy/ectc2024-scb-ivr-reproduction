"""A133 analysis against BOUNDARY Section 2 -> a133_summary.json; the peak map (corner x arm x row, against 200 A) and
the floors' fires per row. `pilot DIR`: per run - rails at fixed times, then over the last 200 periods the rails,
per-phase valley (mean / min), peak, turn-on V_DS (min), Vo peak-to-peak, late fires, the peak after mode P + 100 us."""
from __future__ import annotations

import bisect
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
import scb_ivr.p24_loss_budget as LB  # noqa: E402
from scb_ivr.cosim.matrix import step_stats, window_stats  # noqa: E402

COS = HERE / "cosim"
A129 = PROJECT / "extensions/ml_design_assist/experiments/A129_cosim_vff_slope_gate/cosim"
IDENT = PROJECT / "tmp" / "identity_a133"
T_STEP = 800e-6
STEP_ROWS = ("l_p48_5us", "l_p48_1us", "l_m48_1us", "l_m48_5us", "l_m80_10us", "s_p62", "s_m62")
MATRIX_ROWS = ("m1n", "m1p", "m3n", "m3p", "j30", "j100", "s_m25", "s_p25")

T_US = (144, 160, 200, 300, 500, 700, 1000, 1500, 2000)


def rails(s):
    v = s["vcs_v"]
    return [s["vin_v"] - v[0], v[0] - v[1], v[1] - v[2], v[2]]


def tail(d, n=200):
    secs = d["sections"][-n:]
    t0 = secs[0]["t_s"]
    m = LB.measure(d, n_periods=n)
    ph = lambda recs, k: [r for r in recs if r["phase"] == k and r["t_s"] >= t0]
    tp = (d["t_mode_p_s"] or 0.0) + 100e-6
    return {"rails_v": m["rails_v"], "period_ns": m["period_s"] * 1e9, "ton_ns": m["ton_s"] * 1e9,
            "valley_mean_a": [p["valley"] for p in m["phases"]],
            "valley_min_a": [min(r["i_a"] for r in ph(d["lowoffs_last"], k)) for k in (1, 2, 3, 4)],
            "peak_a": [p["peak"] for p in m["phases"]],
            "von_min_v": [min(r["vds_v"] for r in ph(d["turnons_last"], k)) for k in (1, 2, 3, 4)],
            "vo_pp_mv": (max(s["vo"] for s in secs) - min(s["vo"] for s in secs)) * 1e3,
            "late": d["late_fires"], "ipk_a": d["ipk_a"],
            "ipk_after_a": max((r["i_a"] for r in d["highoffs_last"] if r["t_s"] >= tp), default=None)}


def pilot(folder):
    out = {}
    for f in sorted(Path(folder).glob("run_*.json")):
        d = json.loads(f.read_text())
        ts = [s["t_s"] for s in d["sections"]]
        traj = {}
        for t in T_US:
            i = bisect.bisect_left(ts, t * 1e-6)
            if i < len(ts):
                traj[t] = [round(x, 1) for x in rails(d["sections"][i])]
        tl = tail(d)
        out[f.stem] = {"traj": traj, **tl}
        f2 = lambda xs: "/".join(f"{x:.1f}" for x in xs)
        print(f"{f.stem}: " + " | ".join(f"{t}:{f2(v)}" for t, v in traj.items()))
        print(f"   tail rails {f2(tl['rails_v'])} V, valley {f2(tl['valley_mean_a'])} (min {f2(tl['valley_min_a'])}) A, "
              f"peak {f2(tl['peak_a'])} A, V_on min {f2(tl['von_min_v'])} V, Vo pp {tl['vo_pp_mv']:.1f} mV, "
              f"T {tl['period_ns']:.0f} ns, Ton {tl['ton_ns']:.1f} ns, late {tl['late']}, ipk {tl['ipk_a']:.0f} / after {tl['ipk_after_a']:.0f} A")
    (Path(folder) / "pilot_summary.json").write_text(json.dumps(out, indent=1) + "\n")


def load(p):
    return json.loads(Path(p).read_text())


def rails_at(d, t):
    ts = [s["t_s"] for s in d["sections"]]
    return rails(d["sections"][min(bisect.bisect_left(ts, t), len(ts) - 1)])


def disturbance(d):
    st = step_stats(d, t_step=T_STEP)
    pk = max(q["i_a"] for q in d["highoffs_last"] if q["t_s"] >= T_STEP)
    late = sum(d["late_fires"])
    runaway = pk > 400 or late > 100 or (not np.isfinite(st["back_within_1pct_us"]) and pk > 300)
    fires = sum(1 for t, _ in d.get("ph_floor_log", []) if t >= T_STEP)
    return {"peak_after_a": pk, "late": late, "overlaps": d["overlaps"], "ipk_a": d["ipk_a"], "runaway": bool(runaway),
            "back_us": st["back_within_1pct_us"], "extreme_mv": st["extreme_mv"], "fires_after": fires,
            "fires": d.get("ph_floor_fires")}


def matrix_ok(d, x, w0, row):
    """A129's rule (its criterion 5): no overlap, late <= 100, run and post-step peaks <= 200 A; m / j rows: turn-on V_DS
    within 0.5 V of the corner's n0; m rows: low-side turn-on V_DS <= 0; j30: turn-off current SD <= 0.5 A; s rows:
    Vo back within 1 % in <= 60 us."""
    w = window_stats(d)
    ok = w["overlaps"] == 0 and x["late"] <= 100 and w["ipk_a"] <= 200.0 and x["peak_after_a"] <= 200.0
    if row[0] in "mj":
        ok &= all(abs(p["hs_on_vds_v"] - q["hs_on_vds_v"]) <= 0.5 for p, q in zip(w["phases"], w0["phases"]))
    if row[0] == "m":
        ok &= all(p["ls_on_vds_max_v"] <= 0.0 for p in w["phases"])
    if row == "j30":
        ok &= all(p["i_off_sd_a"] <= 0.5 for p in w["phases"])
    if row.startswith("s_"):
        ok &= np.isfinite(x["back_us"]) and x["back_us"] <= 60.0
    return bool(ok)


def balanced(d, ref):
    tl = tail(d)
    r600 = rails_at(d, 600e-6)
    checks = {"rails": max(abs(a - b) for a, b in zip(tl["rails_v"], ref["rails_v"])) <= 0.3,
              "valleys": all(-19.0 <= v <= -14.0 for v in tl["valley_mean_a"][1:]),
              "von": min(tl["von_min_v"]) > 0.0, "vo_pp": tl["vo_pp_mv"] <= 2.0,
              "settled_600us": max(abs(a - b) for a, b in zip(r600, tl["rails_v"])) <= 0.3}
    return all(checks.values()), checks, tl, r600


def main():
    c, out = {}, {"runs": {}}
    same = lambda a, b: all(a[k] == b[k] for k in ("sections", "turnons_last", "lowoffs_last", "highoffs_last"))
    c["1_identity"] = all(same(load(A129 / f"run_g125_{r}.json"), load(IDENT / f"run_g125_{r}.json")) for r in ("n0", "l_p48_1us"))
    g0, p0 = load(A129 / "run_g125_n0.json"), load(COS / "run_pnom_n0.json")
    tg, tp = tail(g0), tail(p0)
    late_fire = [t for t, _ in p0.get("ph_floor_log", []) if t >= 600e-6]
    c["2_nominal_steady"] = (max(abs(a - b) for a, b in zip(tg["valley_mean_a"] + tg["peak_a"], tp["valley_mean_a"] + tp["peak_a"])) <= 0.2
                             and max(abs(a - b) for a, b in zip(tg["rails_v"], tp["rails_v"])) <= 0.02 and not late_fire)
    out["nominal_n0"] = {"a129": tg, "p": tp, "fires": p0.get("ph_floor_fires"), "fires_after_600us": len(late_fire)}
    ok3 = True
    for corner, arms in (("nom", "p"), ("l07", "pf"), ("l12", "pf"), ("l13", "pf"), ("c07l13", "p")):
        for arm in arms:
            n0 = load(COS / f"run_{arm}{corner}_n0.json")
            w0 = window_stats(n0)
            bal = balanced(n0, tp)
            out["runs"][f"{arm}{corner}_n0"] = {"balanced": bal[0], "checks": bal[1], "tail": bal[2], "rails_600us": bal[3],
                                                 "fires": n0.get("ph_floor_fires"), "ipk_a": n0["ipk_a"]}
            rows = STEP_ROWS + (MATRIX_ROWS if arm == "p" and corner != "c07l13" else ())
            for row in rows:
                d = load(COS / f"run_{arm}{corner}_{row}.json")
                x = disturbance(d)
                if row in MATRIX_ROWS:
                    x["matrix_ok"] = matrix_ok(d, x, w0, row)
                if corner == "nom" and row in STEP_ROWS:
                    g = load(A129 / f"run_g125_{row}.json")
                    x["a129_peak_a"] = max(q["i_a"] for q in g["highoffs_last"] if q["t_s"] >= T_STEP)
                    ok3 &= x["peak_after_a"] <= x["a129_peak_a"] + 7.0
                out["runs"][f"{arm}{corner}_{row}"] = x
    R = out["runs"]
    pn = [R[f"pnom_{r}"] for r in STEP_ROWS + MATRIX_ROWS]
    c["3_nominal_disturbances"] = bool(ok3 and all(x["overlaps"] == 0 for x in pn) and all(R[f"pnom_{r}"]["matrix_ok"] for r in MATRIX_ROWS))
    c["4_l13_balanced"] = R["pl13_n0"]["balanced"]
    c["5_other_corners_balanced"] = all(R[f"p{k}_n0"]["balanced"] for k in ("l07", "l12", "c07l13"))
    good = lambda x: x["overlaps"] == 0 and not x["runaway"] and np.isfinite(x["back_us"])
    c["6_corners"] = all(good(R[f"p{k}_{r}"]) for k in ("l07", "l12", "l13") for r in STEP_ROWS) and \
        all(R[f"p{k}_{r}"]["matrix_ok"] for k in ("l07", "l12", "l13") for r in MATRIX_ROWS)
    c["7_c07l13"] = all(good(R[f"pc07l13_{r}"]) for r in STEP_ROWS)
    pred = load(HERE / "a133_predictions.json")
    out["predicted_peak_a"] = {k: {r: R[f"pnom_{r}"]["a129_peak_a"] + pred[k][r]["peak_a"] - pred["nom"][r]["peak_a"] for r in STEP_ROWS}
                               for k in ("l07", "l12", "l13", "c07l13")}
    out["criteria"] = c
    (HERE / "a133_summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print("criteria:", " ".join(f"{k}={'P' if v else 'F'}" for k, v in c.items()))
    for key in ("pnom", "pl07", "fl07", "pl12", "fl12", "pl13", "fl13", "pc07l13"):
        n0 = R[f"{key}_n0"]
        pks = [R[f"{key}_{r}"]["peak_after_a"] for r in STEP_ROWS]
        mx = [R[f"{key}_{r}"]["matrix_ok"] for r in MATRIX_ROWS] if f"{key}_m1n" in R else []
        print(f"{key:8s} bal {'Y' if n0['balanced'] else 'N'} rails {'/'.join(f'{v:.1f}' for v in n0['tail']['rails_v'])} "
              f"pk {'/'.join(f'{v:.0f}' for v in pks)} >200: {sum(v > 200 for v in pks)}"
              + (f" matrix {sum(mx)}/8" if mx else "") + f" fires_n0 {n0['fires']}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "pilot":
        pilot(sys.argv[2])
    else:
        main()
