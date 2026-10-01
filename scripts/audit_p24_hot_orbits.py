"""D48 audit: D47's timed-low-side P24 event map at junction temperature 125 C (symbolic_derivations/03_P24_native/D48),
the mathematical-model counterpart of A90.

D47's solver (scripts/audit_p24_lowpred_orbits.py, unchanged), copied with the circuit and the reverse-drop parameters
as inputs:
- 125 C: R per phase 0.54 mOhm x 1.5858 (EPC2067 Fig. 9, A90); reverse drop Vf 1.9483 V, 8.948 mOhm per device
  (Fig. 8 at 125 C, A90's fit);
- Coss(V) unchanged.
Seed: D47's orbit at the same target. Also the free window: on the 3% orbit the low-side edge is moved to
crossing + delta (0.10-0.26 ns in 0.01 ns steps); the first delta with reverse-conduction energy, per phase, at 25 C
(D47's orbit and parameters) and at 125 C.

python3 -m scripts.audit_p24_hot_orbits --pct 3.0         (writes diagnostics/D48_orbit_<pct>pct.json)
python3 -m scripts.audit_p24_hot_orbits --window          (writes diagnostics/D48_free_window.json; needs the 3% orbit)
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import time

import numpy as np

from scripts.audit_p24_exact_orbits import PEAK
from scripts.audit_p24_nonlinear_orbits import DIAG, T_RS, epc2067
from scripts.audit_p24_drop_orbits import R_DEV as R_DEV_25, VF as VF_25
from scripts.audit_p24_lowpred_orbits import MARGIN, low_cross_probe
from scb_ivr.p24_exact_event_map import Circuit, section_full
from scb_ivr.p24_nonlinear_event_map import nl_valley_after_lowoff, orbit_chord
from scb_ivr.p24_lowpred_event_map import ControlLP, LowPredEventMap

R_FACTOR_125 = 1.5858            # A90: Fig. 9, RDS(on)(125 C) / RDS(on)(25 C)
VF_125, R_DEV_125 = 1.9483, 8.948e-3
HOT = dict(ckt=dataclasses.replace(Circuit(), R=Circuit().R * R_FACTOR_125), vf=VF_125, r_dev=R_DEV_125)
COLD = dict(ckt=Circuit(), vf=VF_25, r_dev=R_DEV_25)


def solve(coss, par, pct, ton, d0, dl0, s0, iters=40, tol=1e-8):
    """D47's solve with the circuit and the reverse-drop parameters as inputs."""
    target = -pct / 100 * PEAK
    d, dl, s, J, dvdt = list(d0), list(dl0), np.array(s0, float), None, 0.054e9
    rec = {"pct": pct, "R_ohm": par["ckt"].R, "vf_v": par["vf"], "r_ohm_per_device": par["r_dev"], "margin_s": MARGIN,
           "outer": []}
    for _ in range(iters):
        ctl = ControlLP(ton=ton, i_target=target, d_high=tuple(d), t_restart_high=T_RS, d_low=tuple(dl))
        emap = LowPredEventMap(par["ckt"], ctl, coss=coss, vf=par["vf"], r_dev=par["r_dev"])
        try:
            sx, J, hist, log = orbit_chord(emap, s, J=J, tol=tol)
        except (RuntimeError, ValueError, np.linalg.LinAlgError) as exc:
            rec.update(status="no_orbit", error=str(exc)); return rec, None
        if hist[-1] > 10 * tol:
            rec.update(status="no_orbit", newton_residuals=hist); return rec, None
        v, i = section_full(sx, emap.ckt)
        new_d = list(d)
        for ph in range(4):
            r = nl_valley_after_lowoff(emap, v, i, ph + 1)
            if r is not None:
                new_d[ph] = r[0]
        new_dl = [low_cross_probe(emap, v, i, ph + 1) + MARGIN for ph in range(4)]
        dd = max(abs(a - b) for a, b in zip(new_d + new_dl, d + dl))
        rec["outer"].append({"vo": float(sx[3]), "ton_ns": ton * 1e9, "dd_ns": dd * 1e9, "newton_iters": len(hist)})
        print(f"  outer: Vo {sx[3]:.6f} Ton {ton * 1e9:.4f} dd {dd * 1e9:.4f} ns", flush=True)
        if abs(sx[3] - 1.0) < 1e-6 and dd < 2e-12:
            _, _, lg = emap.run_cycle(v, i)
            lo = {x["phase"]: x["i"] for x in lg["lowoff"]}
            ton_ev = {x["phase"]: x for x in lg["turnon"]}
            hows = [ton_ev[k]["how"] for k in range(1, 5)]
            rec.update(status="soft" if all(h == "high_on" for h in hows) else "restart", section_free=sx.tolist(),
                       ton_ns=ton * 1e9, period_ns=lg["period"] * 1e9, vo_v=float(sx[3]), d_ns=[x * 1e9 for x in d],
                       d_low_ns=[x * 1e9 for x in dl], low_on_vds=lg["low_on_vds"],
                       lowoff_i=[lo[k] for k in range(1, 5)], turnon_vds=[ton_ev[k]["vds"] for k in range(1, 5)],
                       turnon_how=hows, floquet_abs=sorted(np.abs(np.linalg.eigvals(J)).tolist(), reverse=True),
                       p_rev_w=sum(lg["rev_energy_j"]) / lg["period"])
            return rec, emap
        ton = ton + (1.0 - sx[3]) / dvdt
        d, dl, s = new_d, new_dl, sx
    rec.update(status="not_consistent")
    return rec, None


def free_window(coss, par, orbit):
    """First delay after the crossing (0.10-0.26 ns) at which each phase's low side conducts in reverse."""
    ctl = ControlLP(ton=orbit["ton_ns"] * 1e-9, i_target=-orbit["pct"] / 100 * PEAK,
                    d_high=tuple(x * 1e-9 for x in orbit["d_ns"]), t_restart_high=T_RS,
                    d_low=tuple(x * 1e-9 for x in orbit["d_low_ns"]))
    v, i = section_full(np.array(orbit["section_free"]), par["ckt"])
    first = [None] * 4
    rows = []
    for delta in np.round(np.arange(0.10, 0.2601, 0.01), 2):
        c = dataclasses.replace(ctl, d_low=tuple(x * 1e-9 - MARGIN + delta * 1e-9 for x in orbit["d_low_ns"]))
        _, _, lg = LowPredEventMap(par["ckt"], c, coss=coss, vf=par["vf"], r_dev=par["r_dev"]).run_cycle(v, i)
        e = lg["rev_energy_j"][4:]
        rows.append({"delta_ns": float(delta), "vds_at_edge": lg["low_on_vds"], "rev_energy_uj": [x * 1e6 for x in e]})
        for k in range(4):
            if first[k] is None and e[k] > 0.0:
                first[k] = float(delta)
    return {"first_reverse_delta_ns": first, "scan": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pct", type=float)
    ap.add_argument("--window", action="store_true")
    ap.add_argument("--tol", type=float, default=1e-8, help="Newton tolerance (accepted up to 10x); 2%% needs 1e-7 (D48 Section 7)")
    a = ap.parse_args()
    t0 = time.time()
    coss = epc2067()
    if a.window:
        hot = json.loads((DIAG / "D48_orbit_3p0pct.json").read_text())
        cold = json.loads((DIAG / "D47_orbit_3p0pct.json").read_text())
        out = {"cold_25c": free_window(coss, COLD, cold), "hot_125c": free_window(coss, HOT, hot)}
        for k, v in out.items():
            print(k, "first delta with reverse conduction (ns), phases 1-4:", v["first_reverse_delta_ns"])
        out["wall_s"] = time.time() - t0
        (DIAG / "D48_free_window.json").write_text(json.dumps(out, indent=1, default=float))
        return
    seed = json.loads((DIAG / f"D47_orbit_{str(a.pct).replace('.', 'p')}pct.json").read_text())
    rec, _ = solve(coss, HOT, a.pct, seed["ton_ns"] * 1e-9, [x * 1e-9 for x in seed["d_ns"]],
                   [x * 1e-9 for x in seed["d_low_ns"]], seed["section_free"], tol=a.tol)
    rec["newton_tol"] = a.tol
    rec["seed"] = {"source": "D47", "ton_ns": seed["ton_ns"]}
    rec["wall_s"] = time.time() - t0
    name = f"D48_orbit_{str(a.pct).replace('.', 'p')}pct.json"
    (DIAG / name).write_text(json.dumps(rec, indent=1, default=float))
    keys = ("status", "ton_ns", "period_ns", "lowoff_i", "turnon_vds", "d_low_ns", "p_rev_w")
    print({k: rec.get(k) for k in keys}, f"wrote {name} ({rec['wall_s']:.0f} s)")


if __name__ == "__main__":
    main()
