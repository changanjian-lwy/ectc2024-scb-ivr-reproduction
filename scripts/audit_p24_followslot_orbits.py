"""D51 audit: P24 orbits with period-following slots (symbolic_derivations/03_P24_native/D51), the mathematical
counterpart of A93's cfg_slot_follow.

D50's error-based fixed point (D47's map: datasheet Coss(V), reverse drop, timed low side; 25 C; low side at
max(crossing + e_l, m), high side at max(valley + e_h, -m)), with phases 2..N's low-side turn-offs at k*T/N after
phase 1's turn-on, T being the orbit's own period (the map's slot base t0 is iterated to the period). Regulated
(Vo = 1 V via Ton). D47-D50's scripts are not changed.

python3 -m scripts.audit_p24_followslot_orbits --pct 5.0 --el-ps 93.75 --eh-ps 93.75 --m-ns 0 [--tol 1e-7]
(writes diagnostics/D51_orbit_<pct>pct_m<m>.json)
"""
from __future__ import annotations

import argparse
import json
import time

import numpy as np

from scripts.audit_p24_exact_orbits import PEAK
from scripts.audit_p24_nonlinear_orbits import DIAG, T_RS, epc2067
from scripts.audit_p24_drop_orbits import R_DEV, VF
from scripts.audit_p24_lowpred_orbits import low_cross_probe
from scb_ivr.p24_exact_event_map import Circuit, section_full
from scb_ivr.p24_nonlinear_event_map import nl_valley_after_lowoff, orbit_chord
from scb_ivr.p24_lowpred_event_map import ControlLP, LowPredEventMap


def solve(coss, pct, el, eh, m, ton, t0, d0, dl0, s0, iters=40, tol=1e-8):
    target = -pct / 100 * PEAK
    d, dl, s, J, dvdt = list(d0), list(dl0), np.array(s0, float), None, 0.054e9
    rec = {"pct": pct, "el_ps": el * 1e12, "eh_ps": eh * 1e12, "m_ns": m * 1e9, "vf_v": VF,
           "r_ohm_per_device": R_DEV, "outer": []}
    for _ in range(iters):
        ctl = ControlLP(ton=ton, t0=t0, i_target=target, d_high=tuple(d), t_restart_high=T_RS, d_low=tuple(dl))
        emap = LowPredEventMap(Circuit(), ctl, coss=coss, vf=VF, r_dev=R_DEV)
        try:
            sx, J, hist, log = orbit_chord(emap, s, J=J, tol=tol)
        except (RuntimeError, ValueError, np.linalg.LinAlgError) as exc:
            rec.update(status="no_orbit", error=str(exc)); return rec
        if hist[-1] > 10 * tol:
            rec.update(status="no_orbit", newton_residuals=hist); return rec
        v, i = section_full(sx, emap.ckt)
        _, _, lg0 = emap.run_cycle(v, i)
        period = lg0["period"]
        new_d, valley = list(d), [None] * 4
        for ph in range(4):
            r = nl_valley_after_lowoff(emap, v, i, ph + 1)
            if r is not None:
                valley[ph] = r[0]
                new_d[ph] = max(r[0] + eh, -m)
        cross = [low_cross_probe(emap, v, i, ph + 1) for ph in range(4)]
        new_dl = [max(c + el, m) for c in cross]
        dd = max(abs(a - b) for a, b in zip(new_d + new_dl + [period], d + dl + [t0]))
        rec["outer"].append({"vo": float(sx[3]), "ton_ns": ton * 1e9, "t0_ns": t0 * 1e9, "period_ns": period * 1e9,
                             "dd_ns": dd * 1e9})
        print(f"  outer: Vo {sx[3]:.6f} Ton {ton * 1e9:.4f} t0 {t0 * 1e9:.3f} T {period * 1e9:.3f} dd {dd * 1e9:.4f} ns",
              flush=True)
        if abs(sx[3] - 1.0) < 1e-6 and dd < 2e-12:
            lg = lg0
            lo = {x["phase"]: x["i"] for x in lg["lowoff"]}
            ton_ev = {x["phase"]: x for x in lg["turnon"]}
            rec.update(status="soft" if all(ton_ev[k]["how"] == "high_on" for k in range(1, 5)) else "restart",
                       ton_ns=ton * 1e9, period_ns=period * 1e9, t0_ns=t0 * 1e9,
                       slots_ns=[k * t0 / 4 * 1e9 for k in range(1, 4)], d_ns=[x * 1e9 for x in d],
                       d_low_ns=[x * 1e9 for x in dl], crossing_ns=[x * 1e9 for x in cross],
                       valley_ns=[None if x is None else x * 1e9 for x in valley],
                       low_on_vds=lg["low_on_vds"], lowoff_i=[lo[k] for k in range(1, 5)],
                       turnon_vds=[ton_ev[k]["vds"] for k in range(1, 5)],
                       floquet_abs=sorted(np.abs(np.linalg.eigvals(J)).tolist(), reverse=True),
                       rev_energy_uj=[e * 1e6 for e in lg["rev_energy_j"]], rev_time_ns=[x * 1e9 for x in lg["rev_time_s"]],
                       p_rev_w=sum(lg["rev_energy_j"]) / lg["period"], section_free=sx.tolist(),
                       vcs_v=[float(emap.ckt.vin - sx[0]), float(sx[1]), float(sx[2])])   # a_k - x_k at the section
            return rec
        ton = ton + (1.0 - sx[3]) / dvdt
        d, dl, s, t0 = new_d, new_dl, sx, period
    rec.update(status="not_consistent")
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pct", type=float, required=True)
    ap.add_argument("--el-ps", type=float, required=True)
    ap.add_argument("--eh-ps", type=float, required=True)
    ap.add_argument("--m-ns", type=float, required=True)
    ap.add_argument("--tol", type=float, default=1e-8, help="Newton tolerance (accepted up to 10x); D48 Section 7")
    a = ap.parse_args()
    t0w = time.time()
    tag = str(a.m_ns).replace('.', 'p').replace('-', 'n')
    seed = json.loads((DIAG / f"D50_orbit_{str(a.pct).replace('.', 'p')}pct_m{tag}.json").read_text())
    rec = solve(epc2067(), a.pct, a.el_ps * 1e-12, a.eh_ps * 1e-12, a.m_ns * 1e-9, seed["ton_ns"] * 1e-9,
                seed["period_ns"] * 1e-9, [x * 1e-9 for x in seed["d_ns"]], [x * 1e-9 for x in seed["d_low_ns"]],
                seed["section_free"], tol=a.tol)
    rec["newton_tol"] = a.tol
    rec["wall_s"] = time.time() - t0w
    name = f"D51_orbit_{str(a.pct).replace('.', 'p')}pct_m{tag}.json"
    (DIAG / name).write_text(json.dumps(rec, indent=1, default=float))
    print({k: rec.get(k) for k in ("status", "ton_ns", "period_ns", "slots_ns", "lowoff_i", "turnon_vds", "p_rev_w",
                                   "vcs_v")}, f"wrote {name} ({rec['wall_s']:.0f} s)")


if __name__ == "__main__":
    main()
