"""Regulated, self-consistent P24 periodic orbits in the timed-low-side event map (LowPredEventMap): the one outer
iteration behind D47-D51.

Outer iteration (until |Vo - 1| < 1e-6 V and every delay is self-consistent to 2 ps, at most `iters` times):
1. the periodic orbit for the current Ton, high-side delays d, low-side dead times dl (and slot base t0) by the
   chord-Newton orbit solver (accepted if its last residual is <= 10 * tol);
2. each phase's natural valley after its low-side turn-off (nl_valley_after_lowoff) and natural zero crossing after
   its high-side turn-off (low_cross_probe), from the orbit's section;
3. new delays from the variant's rules: d_k = high_rule(valley_k) (kept if no valley), dl_k = low_rule(crossing_k);
   with follow_slots, t0 = the orbit's period (slots at k*T/N);
4. Ton += (1 - Vo) / 0.054e9 V/s.

Rules of the variants (scripts/p24_orbits.py):
- D47 (A88's corrector): d = valley, dl = crossing + 1 ps;  D48: the same at 125 C (circuit R, Vf, R per device);
- D49 (A91's static driver mismatch m): dl = crossing + m;
- D50 (A92's error-based fixed point): d = max(valley + e_h, -m), dl = max(crossing + e_l, m);
- D51 (A93's period-following slots): D50's rules with t0 = period.

Derived from scripts/audit_p24_lowpred_orbits.py and its copies (hot, offset, errcorr, followslot), whose
arithmetic it keeps; the record is the union of their records. Gate: scripts/p24_orbits.py --gate.
"""
from __future__ import annotations

import dataclasses

import numpy as np

from scb_ivr.p24_exact_event_map import Circuit, section_full
from scb_ivr.p24_lowpred_event_map import ControlLP, LowPredEventMap
from scb_ivr.p24_nonlinear_event_map import nl_valley_after_lowoff, orbit_chord

PEAK = 125.0            # A peak phase current of the P24 target sweep (scripts/audit_p24_exact_orbits.PEAK)
T_RS = 20e-9            # high-side restart time
MARGIN = 1e-12          # D47's low-side margin after the crossing
DVDT = 0.054e9          # V per s of Ton, the outer Ton step


def low_cross_probe(emap, v, i, phase):
    """Natural zero-crossing time of phase `phase`'s low-side V_DS after its high-side turn-off (that low side held
    off to 5 ns; everything before its crossing is unchanged)."""
    dl = list(emap.ctl.d_low); dl[phase - 1] = 5e-9
    _, _, lg = emap.clone(dataclasses.replace(emap.ctl, d_low=tuple(dl))).run_cycle(v, i)
    return lg["low_cross_rel"][phase - 1]


def solve(coss, pct, ton, d0, dl0, s0, high_rule, low_rule, ckt=None, vf=None, r_dev=None, t0=None,
          follow_slots=False, iters=40, tol=1e-8, record=None, final=None):
    """The outer iteration above. high_rule(valley) and low_rule(crossing) return the new delay in s. Returns the
    record (dict): inputs, the outer trace, and at convergence the orbit's section, timing, currents, turn-on
    voltages, Floquet moduli and reverse-conduction energy; final(rec, cross, valley, sx, emap), if given, adds a
    variant's own fields at convergence."""
    ckt = Circuit() if ckt is None else ckt
    target = -pct / 100 * PEAK
    d, dl, s, J = list(d0), list(dl0), np.array(s0, float), None
    rec = dict(record or {}); rec.setdefault("outer", [])
    for _ in range(iters):
        kw = dict(ton=ton, i_target=target, d_high=tuple(d), t_restart_high=T_RS, d_low=tuple(dl))
        if t0 is not None:
            kw["t0"] = t0
        ctl = ControlLP(**kw)
        emap = LowPredEventMap(ckt, ctl, coss=coss, vf=vf, r_dev=r_dev)
        try:
            sx, J, hist, log = orbit_chord(emap, s, J=J, tol=tol)
        except (RuntimeError, ValueError, np.linalg.LinAlgError) as exc:
            rec.update(status="no_orbit", error=str(exc)); return rec
        if hist[-1] > 10 * tol:
            rec.update(status="no_orbit", newton_residuals=hist); return rec
        v, i = section_full(sx, emap.ckt)
        _, _, lg = emap.run_cycle(v, i)
        new_d, valley = list(d), [None] * 4
        for ph in range(4):
            r = nl_valley_after_lowoff(emap, v, i, ph + 1)
            if r is not None:
                valley[ph] = r[0]
                new_d[ph] = high_rule(r[0])
        cross = [low_cross_probe(emap, v, i, ph + 1) for ph in range(4)]
        new_dl = [low_rule(c) for c in cross]
        a, b = new_d + new_dl, d + dl
        if follow_slots:
            a, b = a + [lg["period"]], b + [t0]
        dd = max(abs(x - y) for x, y in zip(a, b))
        rec["outer"].append({"vo": float(sx[3]), "ton_ns": ton * 1e9, "dd_ns": dd * 1e9, "newton_iters": len(hist),
                             "d_low_ns": [x * 1e9 for x in new_dl], "period_ns": lg["period"] * 1e9,
                             "t0_ns": None if t0 is None else t0 * 1e9})
        print(f"  outer: Vo {sx[3]:.6f} Ton {ton * 1e9:.4f} dd {dd * 1e9:.4f} ns", flush=True)
        if abs(sx[3] - 1.0) < 1e-6 and dd < 2e-12:
            lo = {x["phase"]: x["i"] for x in lg["lowoff"]}
            ton_ev = {x["phase"]: x for x in lg["turnon"]}
            hows = [ton_ev[k]["how"] for k in range(1, 5)]
            rec.update(status="soft" if all(h == "high_on" for h in hows) else "restart", section_free=sx.tolist(),
                       ton_ns=ton * 1e9, period_ns=lg["period"] * 1e9, vo_v=float(sx[3]), d_ns=[x * 1e9 for x in d],
                       d_low_ns=[x * 1e9 for x in dl], crossing_ns=[x * 1e9 for x in cross],
                       valley_ns=[None if x is None else x * 1e9 for x in valley], low_on_vds=lg["low_on_vds"],
                       lowoff_i=[lo[k] for k in range(1, 5)], turnon_vds=[ton_ev[k]["vds"] for k in range(1, 5)],
                       turnon_how=hows, floquet_abs=sorted(np.abs(np.linalg.eigvals(J)).tolist(), reverse=True),
                       rev_energy_uj=[e * 1e6 for e in lg["rev_energy_j"]], rev_time_ns=[x * 1e9 for x in lg["rev_time_s"]],
                       p_rev_w=sum(lg["rev_energy_j"]) / lg["period"])
            if t0 is not None:
                rec.update(t0_ns=t0 * 1e9, slots_ns=[k * t0 / 4 * 1e9 for k in range(1, 4)])
            if final is not None:
                final(rec, cross, valley, sx, emap)
            return rec
        ton = ton + (1.0 - sx[3]) / DVDT
        d, dl, s = new_d, new_dl, sx
        if follow_slots:
            t0 = lg["period"]
    rec.update(status="not_consistent")
    return rec
