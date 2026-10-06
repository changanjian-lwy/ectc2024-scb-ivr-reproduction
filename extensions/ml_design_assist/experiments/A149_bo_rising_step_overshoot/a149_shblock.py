"""A149 SH_k overshoot block: f(turn-on V_DS of phase k-1) = SH_k's window peak - its blocking voltage (rail_(k-1) +
rail_k), per (loop L, edge rate), from cosim records with cfg "vds_win" (A144 mechanism B).
Calibration: A144 (Q 7 loops, instantaneous edges) and A145 (72 / 144 A/ns) records, frozen controller.
Held out (criterion 1): the A148 loop + edge records; each run's max SH2-4 after 150 us from its own B and V_DS.
Window: the sections' vds_win_v (peak since the previous section, 0.4 us); B from the previous section's rails; V_DS the
largest turn-on V_DS of phase k-1 with t + 5 ns inside the window.
Writes a149_sh_table.json (tables) and a149_shblock.json (criterion 1); prints <= 15 lines."""
from __future__ import annotations

import glob
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJ = HERE.parents[3]
TA = PROJ / "experiments" / "track_A_periodic_steady_state"
CAL = [TA / "A144_p24_commutation_loop_inductance" / "cosim" / "run_q7_l*.json",
       TA / "A145_p24_finite_switching_edges" / "cosim" / "run_e*_l[1-9]*.json"]
HELD = [HERE.parent / "A148_rl_zvs_line_step" / "cosim" / "run_*_e72_*.json"]
T_MIN = 150e-6
BIN = 1.0
N_MIN = 3
TOL = 1.0


def windows(path):
    """(key, rows): key (L pH, didt A/ns); rows [V_DS, B, SH peak, k] per window after T_MIN with a turn-on of k-1."""
    r = json.loads(Path(path).read_text())
    c, sec = r["cfg"], r["sections"]
    t = np.array([s["t_s"] for s in sec])
    vw = np.array([s["vds_win_v"] for s in sec])
    vin = np.array([s["vin_v"] for s in sec])
    vcs = np.array([s["vcs_v"] for s in sec])
    rails = np.stack([vin - vcs[:, 0], vcs[:, 0] - vcs[:, 1], vcs[:, 1] - vcs[:, 2], vcs[:, 2]], 1)
    dv = np.full((len(t), 4), -np.inf)
    for x in r["turnons_last"]:
        i = int(np.searchsorted(t, x["t_s"] + 5e-9))
        if i < len(t):
            dv[i, x["phase"] - 1] = max(dv[i, x["phase"] - 1], x["vds_v"])
    rows = []
    for i in range(1, len(t)):
        if t[i] <= T_MIN:
            continue
        for k in (1, 2, 3):                                  # SH(k+1), upstream phase k (0-based k-1)
            if np.isfinite(dv[i, k - 1]):
                rows.append((dv[i, k - 1], rails[i - 1, k - 1] + rails[i - 1, k], vw[i, k], k + 1))
    key = (float(c.get("loop", {}).get("l_ph", 0.0)), float(c.get("edge", {}).get("didt_a_ns", 0.0)))
    sh_max = float(vw[t > T_MIN, 1:4].max())
    return key, np.array(rows), sh_max


def fit(rows):
    """Bin medians of the excess over 1 V bins of V_DS (>= N_MIN windows), made non-decreasing."""
    x = rows[:, 2] - rows[:, 1]
    lo, hi = np.floor(rows[:, 0].min()), np.ceil(rows[:, 0].max())
    grid, med, p90, n = [], [], [], []
    for a in np.arange(lo, hi, BIN):
        m = (rows[:, 0] >= a) & (rows[:, 0] < a + BIN)
        if m.sum() >= N_MIN:
            grid.append(float(np.median(rows[m, 0]))); med.append(float(np.median(x[m])))
            p90.append(float(np.percentile(x[m], 90))); n.append(int(m.sum()))
    return {"grid": grid, "x": [float(v) for v in np.maximum.accumulate(med)], "x_raw": med, "p90": p90, "n": n}


def tkey(key):
    return f"L{key[0]:g}_e{key[1]:g}"


def predict(tab, rows):
    return float(np.max(rows[:, 1] + np.interp(rows[:, 0], tab["grid"], tab["x"])))


def main():
    cal = {}
    for p in CAL:
        for f in sorted(glob.glob(str(p))):
            key, rows, _ = windows(f)
            if len(rows):
                cal.setdefault(key, []).append(rows)
    tables = {tkey(k): fit(np.vstack(v)) for k, v in sorted(cal.items())}
    (HERE / "a149_sh_table.json").write_text(json.dumps(tables, indent=1) + "\n")
    held = []
    for p in HELD:
        for f in sorted(glob.glob(str(p))):
            key, rows, sh_max = windows(f)
            pred = predict(tables[tkey(key)], rows)
            held.append({"run": Path(f).stem, "table": tkey(key), "sh_max": sh_max, "pred": pred, "err": pred - sh_max})
    ok = all(abs(h["err"]) <= TOL for h in held)
    out = {"criterion_1": {"pass": ok, "tol_v": TOL, "max_abs_err": max(abs(h["err"]) for h in held)}, "held_out": held,
           "calibration_runs": sum(len(v) for v in cal.values())}
    (HERE / "a149_shblock.json").write_text(json.dumps(out, indent=1) + "\n")
    for k in ("L50_e72", "L100_e72"):
        t = tables[k]
        print(k, "f at 4/8/12/16 V:", [round(float(np.interp(v, t["grid"], t["x"])), 1) for v in (4, 8, 12, 16)])
    for h in held:
        print(f"{h['run']:28s} {h['sh_max']:5.1f} pred {h['pred']:5.1f} err {h['err']:+.2f}")
    print("criterion 1:", "PASS" if ok else "FAIL", f"max |err| {out['criterion_1']['max_abs_err']:.2f} V")


if __name__ == "__main__":
    main()
