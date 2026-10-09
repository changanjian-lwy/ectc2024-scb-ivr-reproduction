"""D46 audit: P24 periodic orbits with the datasheet Coss(V) and the reverse-conduction drop (symbolic_derivations/
03_P24_native/D46), the mathematical-model counterpart of A87.

Regulated (Vo = 1 V via Ton), valley-consistent orbits (corrected valley time), 20 ns restart, low-side turn-on t_d
after the ZVS comparator, as A87. Seed: D45's orbit at the same target (datasheet Coss, ideal diodes), Ton + 2 ns.

python3 -m scripts.audit_p24_drop_orbits --pct 3 [--td 10]   (writes diagnostics/D46_orbit_<pct>pct_td<td>.json)
"""
from __future__ import annotations

import argparse
import json
import time

import numpy as np

from scripts.audit_p24_exact_orbits import ROOT, PEAK
from scripts.audit_p24_nonlinear_orbits import DIAG, T_RS, epc2067
from scb_ivr.p24_exact_event_map import Circuit, Control, section_full
from scb_ivr.p24_nonlinear_event_map import nl_valley_after_lowoff, orbit_chord, section_jacobian
from scb_ivr.p24_drop_event_map import DropEventMap

VF, R_DEV = 2.0894454508, 6.0134369436e-3        # A87's fit to Fig. 8 at 25 C, 10-100 A per device


def solve(coss, pct, td, ton, d0, s0, iters=30, tol=1e-8):
    target = -pct / 100 * PEAK
    d, s, J, dvdt = list(d0), np.array(s0, float), None, 0.054e9
    rec = {"pct": pct, "td_ns": td * 1e9, "vf_v": VF, "r_ohm_per_device": R_DEV, "outer": []}
    for _ in range(iters):
        ctl = Control(ton=ton, i_target=target, d_high=tuple(d), t_restart_high=T_RS, t_d_low=td)
        emap = DropEventMap(Circuit(), ctl, coss=coss, vf=VF, r_dev=R_DEV)
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
        dd = max(abs(a - b) for a, b in zip(new_d, d))
        rec["outer"].append({"vo": float(sx[3]), "ton_ns": ton * 1e9, "dd_ns": dd * 1e9, "newton_iters": len(hist)})
        print(f"  outer: Vo {sx[3]:.6f} Ton {ton * 1e9:.4f} ns dd {dd * 1e9:.4f} ns d {np.round(np.array(new_d) * 1e9, 3)}",
              flush=True)
        if abs(sx[3] - 1.0) < 1e-6 and dd < 2e-12:
            _, _, lg = emap.run_cycle(v, i)
            lo = {x["phase"]: x["i"] for x in lg["lowoff"]}
            ton_ev = {x["phase"]: x for x in lg["turnon"]}
            valleys = [nl_valley_after_lowoff(emap, v, i, ph) for ph in range(1, 5)]
            hows = [ton_ev[k]["how"] for k in range(1, 5)]
            rec.update(status="soft" if all(h == "high_on" for h in hows) else "restart", section_free=sx.tolist(),
                       ton_ns=ton * 1e9, period_ns=lg["period"] * 1e9, vo_v=float(sx[3]), d_ns=[x * 1e9 for x in d],
                       lowoff_i=[lo[k] for k in range(1, 5)], turnon_vds=[ton_ev[k]["vds"] for k in range(1, 5)],
                       turnon_how=hows,
                       floquet_abs=sorted(np.abs(np.linalg.eigvals(section_jacobian(emap, sx)[0])).tolist(), reverse=True),
                       natural_valley=[None if r is None else {"t_ns": r[0] * 1e9, "vds_v": r[1]} for r in valleys],
                       rev_energy_uj=[e * 1e6 for e in lg["rev_energy_j"]], rev_time_ns=[x * 1e9 for x in lg["rev_time_s"]],
                       p_rev_w=sum(lg["rev_energy_j"]) / lg["period"], events=[(t * 1e9, k, j) for t, k, j in lg["events"]])
            return rec
        ton = ton + (1.0 - sx[3]) / dvdt
        d, s = new_d, sx
    rec.update(status="not_consistent")
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pct", type=float, required=True)
    ap.add_argument("--td", type=float, default=10.0, help="ns, ZVS comparator to low-side gate")
    a = ap.parse_args()
    t0 = time.time()
    coss = epc2067()
    seed = None
    for part in ("A", "B"):
        for r in json.loads((DIAG / f"D45_orbits_{part}.json").read_text())["rows"]:
            if r["pct"] == a.pct and "section_free" in r:
                seed = r
    rec = solve(coss, a.pct, a.td * 1e-9, (seed["ton_ns"] + 2.0) * 1e-9, [x * 1e-9 for x in seed["d_ns"]],
                seed["section_free"])
    rec["seed"] = {"source": "D45", "ton_ns": seed["ton_ns"], "lowoff_i": seed["lowoff_i"]}
    rec["wall_s"] = time.time() - t0
    name = f"D46_orbit_{str(a.pct).replace('.', 'p')}pct_td{a.td:g}.json"
    (DIAG / name).write_text(json.dumps(rec, indent=1, default=float))
    keys = ("status", "ton_ns", "period_ns", "lowoff_i", "turnon_vds", "p_rev_w", "rev_time_ns")
    print({k: rec.get(k) for k in keys}, f"wrote {name} ({rec['wall_s']:.0f} s)")


if __name__ == "__main__":
    main()
