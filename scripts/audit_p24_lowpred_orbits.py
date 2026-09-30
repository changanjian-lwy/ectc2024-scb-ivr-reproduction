"""D47 audit: P24 periodic orbits with the datasheet Coss(V), the reverse drop and a timed low-side turn-on
(symbolic_derivations/03_P24_native/D47), the mathematical-model counterpart of A88.

Regulated (Vo = 1 V via Ton) orbits in which each high-side delay equals its natural valley time (corrected timing)
and each low-side dead time equals its node's natural zero-crossing time after the high-side turn-off plus 1 ps. The
crossing is measured by a probe (that phase's low side held off to 5 ns), as the valley is, so it is observed even
when the current dead time is early (D47 Section 7). Seed: D45's orbit at the same target.

python3 -m scripts.audit_p24_lowpred_orbits --pct 3.0   (writes diagnostics/D47_orbit_<pct>pct.json)
"""
from __future__ import annotations

import argparse
import json
import time

import numpy as np

from scripts.audit_p24_exact_orbits import PEAK
from scripts.audit_p24_nonlinear_orbits import DIAG, T_RS, epc2067
from scripts.audit_p24_drop_orbits import R_DEV, VF
from scb_ivr.p24_exact_event_map import Circuit, section_full
from scb_ivr.p24_nonlinear_event_map import nl_valley_after_lowoff, orbit_chord
from scb_ivr.p24_lowpred_event_map import ControlLP, LowPredEventMap

MARGIN = 1e-12


def low_cross_probe(emap, v, i, phase):
    """Natural zero-crossing time of phase `phase`'s low-side V_DS after its high-side turn-off (that low side held
    off to 5 ns; everything before its crossing is unchanged)."""
    import dataclasses
    dl = list(emap.ctl.d_low); dl[phase - 1] = 5e-9
    _, _, lg = emap.clone(dataclasses.replace(emap.ctl, d_low=tuple(dl))).run_cycle(v, i)
    return lg["low_cross_rel"][phase - 1]


def solve(coss, pct, ton, d0, dl0, s0, iters=40, tol=1e-8):
    target = -pct / 100 * PEAK
    d, dl, s, J, dvdt = list(d0), list(dl0), np.array(s0, float), None, 0.054e9
    rec = {"pct": pct, "vf_v": VF, "r_ohm_per_device": R_DEV, "margin_s": MARGIN, "outer": []}
    for _ in range(iters):
        ctl = ControlLP(ton=ton, i_target=target, d_high=tuple(d), t_restart_high=T_RS, d_low=tuple(dl))
        emap = LowPredEventMap(Circuit(), ctl, coss=coss, vf=VF, r_dev=R_DEV)
        try:
            sx, J, hist, log = orbit_chord(emap, s, J=J, tol=tol)
        except (RuntimeError, ValueError, np.linalg.LinAlgError) as exc:
            rec.update(status="no_orbit", error=str(exc)); return rec
        if hist[-1] > 10 * tol:
            rec.update(status="no_orbit", newton_residuals=hist); return rec
        v, i = section_full(sx, emap.ckt)
        new_d = list(d)
        for ph in range(4):
            r = nl_valley_after_lowoff(emap, v, i, ph + 1)
            if r is not None:
                new_d[ph] = r[0]
        _, _, lg = emap.run_cycle(v, i)
        new_dl = [low_cross_probe(emap, v, i, ph + 1) + MARGIN for ph in range(4)]
        dd = max(abs(a - b) for a, b in zip(new_d + new_dl, d + dl))
        rec["outer"].append({"vo": float(sx[3]), "ton_ns": ton * 1e9, "dd_ns": dd * 1e9, "newton_iters": len(hist),
                             "d_low_ns": [x * 1e9 for x in new_dl]})
        print(f"  outer: Vo {sx[3]:.6f} Ton {ton * 1e9:.4f} dd {dd * 1e9:.4f} ns d {np.round(np.array(new_d) * 1e9, 3)} "
              f"d_low {np.round(np.array(new_dl) * 1e9, 4)}", flush=True)
        if abs(sx[3] - 1.0) < 1e-6 and dd < 2e-12:
            lo = {x["phase"]: x["i"] for x in lg["lowoff"]}
            ton_ev = {x["phase"]: x for x in lg["turnon"]}
            hows = [ton_ev[k]["how"] for k in range(1, 5)]
            rec.update(status="soft" if all(h == "high_on" for h in hows) else "restart", section_free=sx.tolist(),
                       ton_ns=ton * 1e9, period_ns=lg["period"] * 1e9, vo_v=float(sx[3]), d_ns=[x * 1e9 for x in d],
                       d_low_ns=[x * 1e9 for x in dl], low_on_vds=lg["low_on_vds"],
                       lowoff_i=[lo[k] for k in range(1, 5)], turnon_vds=[ton_ev[k]["vds"] for k in range(1, 5)],
                       turnon_how=hows, floquet_abs=sorted(np.abs(np.linalg.eigvals(J)).tolist(), reverse=True),
                       rev_energy_uj=[e * 1e6 for e in lg["rev_energy_j"]], rev_time_ns=[x * 1e9 for x in lg["rev_time_s"]],
                       p_rev_w=sum(lg["rev_energy_j"]) / lg["period"])
            return rec
        ton = ton + (1.0 - sx[3]) / dvdt
        d, dl, s = new_d, new_dl, sx
    rec.update(status="not_consistent")
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pct", type=float, required=True)
    a = ap.parse_args()
    t0 = time.time()
    coss = epc2067()
    seed = None
    for part in ("A", "B"):
        for r in json.loads((DIAG / f"D45_orbits_{part}.json").read_text())["rows"]:
            if r["pct"] == a.pct and "section_free" in r:
                seed = r
    rec = solve(coss, a.pct, seed["ton_ns"] * 1e-9, [x * 1e-9 for x in seed["d_ns"]], [1.2e-9] * 4, seed["section_free"])
    rec["seed"] = {"source": "D45", "ton_ns": seed["ton_ns"]}
    rec["wall_s"] = time.time() - t0
    name = f"D47_orbit_{str(a.pct).replace('.', 'p')}pct.json"
    (DIAG / name).write_text(json.dumps(rec, indent=1, default=float))
    keys = ("status", "ton_ns", "period_ns", "lowoff_i", "turnon_vds", "d_low_ns", "p_rev_w", "low_on_vds")
    print({k: rec.get(k) for k in keys}, f"wrote {name} ({rec['wall_s']:.0f} s)")


if __name__ == "__main__":
    main()
