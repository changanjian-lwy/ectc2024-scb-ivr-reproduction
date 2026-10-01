"""D55: dlo rules for the timed phase-1 turn-off - load-step tracking against jitter (A100).

    python3 scripts/p24_dlo_rules.py

1. Tracking: each rule replayed against the required on-low interval of phase 1 measured in A100's reference runs
   (the comparator design under +-25 and +-62.5 A load steps): per cycle, R(n) = phase 1's low-on to low-off interval
   and Ton(n). dlo (integer LSB) follows the rule; the turn-off error is dlo - R - 3 LSB, and phase 1's turn-off
   current error is -Vo/L times it. Without noise, and with the turn-off error's noise at 30 ps (D54: 0.56 ns).
2. Jitter: D54's Monte Carlo (linearised circuit, exact rules, average slots) for each rule at 0, 30 and 100 ps.
Writes symbolic_derivations/03_P24_native/diagnostics/D55_dlo_rules_5p0pct.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT))
import numpy as np  # noqa: E402

from scb_ivr import p24_jitter as pj  # noqa: E402
from scripts.p24_orbits import DIAG  # noqa: E402

REF = ROOT / "experiments" / "track_A_periodic_steady_state" / "A100_timed_turn_off_load_steps" / "cosim"
STEPS = ("ref_p25", "ref_m25", "ref_p62", "ref_m62")
RULES = {  # name: (adm, smax, ff, kff)
    "S": (False, 1, False, 0), "ADM8": (True, 8, False, 0), "ADM16": (True, 16, False, 0),
    "ADM32": (True, 32, False, 0), "ADM64": (True, 64, False, 0),
    "FF10+S": (False, 1, True, 10), "FF10+ADM8": (True, 8, True, 10), "FF10+ADM16": (True, 16, True, 10)}
LSB_NS, TGT, S_A_PER_NS = pj.LSB, 3, -pj.SLOPE_LOW
T_STEP = 400e-6


def trajectory(name):
    """Per phase-1 cycle from 380 us: (t, R in LSB, Ton in LSB) from a reference run."""
    d = json.loads((REF / f"run_{name}.json").read_text())
    lon = np.array([o["t_s"] for o in d["lowons_last"] if o["phase"] == 1])
    sec_t = np.array([s["t_s"] for s in d["sections"]]); sec_ton = np.array([s["ton_lsb"] for s in d["sections"]])
    rows = []
    for o in d["lowoffs_last"]:
        if o["phase"] != 1 or o["t_s"] < 380e-6:
            continue
        prev = lon[lon < o["t_s"]]
        k = np.searchsorted(sec_t, o["t_s"]) - 1
        if len(prev) and k >= 0:
            rows.append((o["t_s"], (o["t_s"] - prev[-1]) * 1e9 / LSB_NS, sec_ton[k]))
    return np.array(rows)


def replay(traj, adm, smax, ff, kff, noise_ns=0.0, seed=1):
    """dlo against the trajectory; returns the turn-off current error (A) per cycle."""
    rng = np.random.default_rng(seed)
    t, R, ton = traj[:, 0], traj[:, 1], traj[:, 2]
    dlo = int(round(R[0] + TGT)); step, last, seen = 1, False, False
    err_a = []
    for n in range(len(R)):
        if ff and n > 0 and ton[n] != ton[n - 1]:
            dlo = max(dlo + kff * int(ton[n] - ton[n - 1]), 0)
        e_ns = (dlo - R[n]) * LSB_NS + rng.normal(0.0, noise_ns) if noise_ns else (dlo - R[n]) * LSB_NS
        err_a.append(-S_A_PER_NS * ((dlo - R[n]) - TGT) * LSB_NS)
        up = e_ns < TGT * LSB_NS
        step = (min(2 * step, smax) if (seen and up == last) else 1) if adm else 1
        last, seen = up, True
        dlo = max(dlo + (step if up else -step), 0)
    return t, np.array(err_a)


def track_metrics(t, err):
    after = t >= T_STEP
    e = err[after]
    bad = np.where(np.abs(e) > 2 * LSB_NS * S_A_PER_NS)[0]
    return {"max_abs_current_error_a": float(np.max(np.abs(e))), "rms_current_error_a": float(np.sqrt(np.mean(e ** 2))),
            "last_cycle_outside_2lsb": int(bad[-1]) if len(bad) else 0}


def main():
    d54 = json.loads((DIAG / "D54_timed_turnoff_5p0pct_m0p0.json").read_text())
    J, p0, q0 = np.array(d54["jacobian"]), np.array(d54["p0"]), np.array(d54["q0"])
    names = pj.P_NAMES
    k_jac = -J[pj.Q_LO, pj.I_TON] / J[pj.Q_LO, pj.I_U]
    trajs = {s: trajectory(s) for s in STEPS}
    k_meas = {s: float((tr[-30:, 1].mean() - tr[:30, 1].mean()) / (tr[-30:, 2].mean() - tr[:30, 2].mean())) for s, tr in trajs.items()}
    out = {"k_from_jacobian": float(k_jac), "k_from_reference_runs": k_meas, "rules": {}, "tracking": {}, "jitter": {}}
    print(f"feedforward gain: from D54's Jacobian K = {k_jac:.2f}; from the reference runs dR/dTon = "
          + ", ".join(f"{s} {v:.2f}" for s, v in k_meas.items()))
    for rule, (adm, smax, ff, kff) in RULES.items():
        out["rules"][rule] = {"adm": adm, "smax": smax, "ff": ff, "kff": kff}
        tr = {}
        for s, traj in trajs.items():
            t, e0 = replay(traj, adm, smax, ff, kff)
            _, e1 = replay(traj, adm, smax, ff, kff, noise_ns=0.56)
            tr[s] = {"no_noise": track_metrics(t, e0), "noise_30ps": track_metrics(t, e1)}
        out["tracking"][rule] = tr
        jit = {}
        for sig in (0.0, 0.03, 0.1):
            r = pj.monte_carlo(p0, q0, J, "avg", sig, seed=1, timed1=True, lo_sign=True, lo_adm=adm, lo_smax=smax,
                               lo_ff=ff, lo_kff=kff)
            st = pj.mc_stats(r)
            jit[f"{int(sig * 1e3)}ps"] = {"ilo_sd_a": st["ilo_sd_a"], "period_sd_ns": st["period_sd_ns"],
                                          "dither_a": st["dither_window_mean_sd_a"][0],
                                          "phase1_mean_a": float(r["ilo"][:, 0].mean()),
                                          "early_high_ph2_4": st["early_high_frac"][1:]}
        out["jitter"][rule] = jit
        mx = [tr[s]["no_noise"]["max_abs_current_error_a"] for s in STEPS]
        mxn = [tr[s]["noise_30ps"]["max_abs_current_error_a"] for s in STEPS]
        j30, j100 = jit["30ps"], jit["100ps"]
        print(f"{rule:11s} step tracking, max |phase-1 current error| (A) +25/-25/+62.5/-62.5: "
              f"{[round(x, 2) for x in mx]} | with 30 ps noise {[round(x, 2) for x in mxn]} | jitter 30 ps: ilo sd "
              f"{[round(x, 3) for x in j30['ilo_sd_a']]} T {j30['period_sd_ns']:.3f} ph1 mean {j30['phase1_mean_a']:.2f} | "
              f"100 ps: ph2-4 {[round(x, 2) for x in j100['ilo_sd_a'][1:]]} ph1 {j100['ilo_sd_a'][0]:.2f} | 0 ps ilo sd {jit['0ps']['ilo_sd_a'][1]:.3f}")
    (DIAG / "D55_dlo_rules_5p0pct.json").write_text(json.dumps(out, indent=1))
    print("wrote", DIAG / "D55_dlo_rules_5p0pct.json")


if __name__ == "__main__":
    main()
