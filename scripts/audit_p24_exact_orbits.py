"""D43 audit: P24 four-phase periodic orbits in the exact event map (symbolic_derivations/03_P24_native/D43).

1. Cross-check at the Track A reference points (A79 runs 1, 2, 3): the orbit with the physical model's Ton and
   predictive delays, its Floquet multipliers, and each phase's natural valley against its delay.
2. Regulated, corrector-consistent orbits (Vo = 1 V by Ton; each soft phase's delay equal to its natural valley
   time; a restart phase at 20 ns) on two branches: all soft, and phase 4 restart. Swept over the negative-
   current target from 3% to 9% of the 125 A peak. For each: convergence, Floquet maximum, phase-4 low-off
   current and the depth of phase 4's natural dip (what the physical corrector's 0.05 V dip test sees).

python3 -m scripts.audit_p24_exact_orbits   (writes symbolic_derivations/03_P24_native/diagnostics/D43_orbits.json)
"""
from __future__ import annotations

import dataclasses
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from scb_ivr.p24_exact_event_map import (Circuit, Control, ExactEventMap, orbit, section_free,  # noqa: E402
                                         section_full, valley_after_lowoff)

TRACK_A = ROOT / "experiments" / "track_A_periodic_steady_state"
OUT = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics" / "D43_orbits.json"
REFS = {  # Track A reference runs (A79): target, loop gain, phase-4 state there
    "A79_r1_5pct_soft": "A79_p24_output_voltage_loop/run_r1_ki0p25.json",
    "A79_r2_5pct_restart": "A79_p24_output_voltage_loop/run_r2_ki1p0.json",
    "A79_r3_7p5pct_soft": "A79_p24_output_voltage_loop/run_r3_itgt9p375_ki0p25.json",
}
PEAK = 125.0
DIP_TEST_V = 0.05          # the physical corrector's dip threshold (A75 rule, v_hys)


def phys_summary(d):
    secs = d["sections"]; s = secs[-1]
    per = np.diff([x["t_s"] for x in secs[-21:]])
    return {"period_ns": float(np.mean(per) * 1e9), "vo_v": s["vo"], "section_v": s["v"], "section_i": s["i"],
            "ton_ns": s["ton_cmd_ns"], "dt_pred_ns": [x * 1e9 for x in d["end"]["dt_pred_s"]]}


def orbit_report(emap, sx, J, hist, log):
    v, i = section_full(sx, emap.ckt)
    valleys = []
    for ph in range(1, emap.ckt.n + 1):
        r = valley_after_lowoff(emap, v, i, ph)
        valleys.append(None if r is None else {"t_ns": r[0] * 1e9, "vds_v": r[1]})
    lo = {x["phase"]: x["i"] for x in log["lowoff"]}
    ton = {x["phase"]: x for x in log["turnon"]}
    pre_v, pre_i = log["pre_section"]
    return {
        "converged": hist[-1] < 1e-8, "newton_residuals": hist, "section_free": sx.tolist(),
        "pre_section_v": pre_v.tolist(), "pre_section_i": pre_i.tolist(),
        "period_ns": log["period"] * 1e9, "vo_v": float(sx[emap.ckt.n - 1]),  # out is the last voltage coordinate
        "floquet_abs": sorted(np.abs(np.linalg.eigvals(J)).tolist(), reverse=True),
        "lowoff_i": [lo.get(k) for k in range(1, emap.ckt.n + 1)],
        "turnon_vds": [ton[k]["vds"] if k in ton else None for k in range(1, emap.ckt.n + 1)],
        "turnon_how": [ton[k]["how"] if k in ton else None for k in range(1, emap.ckt.n + 1)],
        "d_ns": [x * 1e9 for x in emap.ctl.d_high], "natural_valley": valleys,
    }


def phase4_dip(emap, sx):
    """Depth of phase 4's natural dip after its low-side turn-off (Vds at turn-off minus the minimum)."""
    v, i = section_full(sx, emap.ckt)
    trace = []

    def hook(topo, z, t, state):
        if state[3] == "UP":
            trace.append(topo.vds(z, 3))

    ctl = emap.ctl
    d = list(ctl.d_high); d[3] = 40e-9
    probe = ExactEventMap(emap.ckt, dataclasses.replace(ctl, d_high=tuple(d), t_restart_high=41e-9), emap.h)
    probe._hook = hook
    try:
        probe.run_cycle(v, i)
    except RuntimeError:
        pass
    return (trace[0] - min(trace)) if trace else None


def consistent_orbit(ckt, target, ton, d0, s0, restart=(), iters=12, t_rs=20e-9):
    """Regulated (Vo = 1 V via Ton) orbit whose soft phases' delays equal their natural valley times."""
    d = list(d0)
    for ph in restart:
        d[ph] = t_rs
    s, dvdt = np.array(s0, float), 0.054e9          # dVo/dTon ~ 54 mV/ns (A79)
    for _ in range(iters):
        emap = ExactEventMap(ckt, Control(ton=ton, i_target=target, d_high=tuple(d), t_restart_high=t_rs))
        try:
            sx, J, hist, log = orbit(emap, s)
        except (RuntimeError, ValueError) as exc:          # the seed itself does not complete a cycle
            return None, emap, (s, np.eye(len(s)), [float('inf')], {'error': str(exc)})
        if hist[-1] > 1e-8:
            return None, emap, (sx, J, hist, log)
        vo = sx[3]
        v, i = section_full(sx, ckt)
        new_d = list(d)
        for ph in range(ckt.n):
            if ph in restart:
                continue
            r = valley_after_lowoff(emap, v, i, ph + 1)
            if r is not None:
                new_d[ph] = r[0]
        dd = max(abs(a - b) for a, b in zip(new_d, d))
        if abs(vo - 1.0) < 1e-6 and dd < 1e-12:
            return True, emap, (sx, J, hist, log)
        ton = ton + (1.0 - vo) / dvdt
        d, s = new_d, sx
    return False, emap, (sx, J, hist, log)


def main():
    ckt = Circuit()
    out = {"cross_check": {}, "sweep": {}}
    t0 = time.time()
    seeds = {}
    for name, rel in REFS.items():
        d = json.loads((TRACK_A / rel).read_text())
        ph = phys_summary(d)
        tgt = d["params"]["i_target"]
        restart = (3,) if "restart" in name else ()
        dd = list(d["end"]["dt_pred_s"])
        if restart:
            dd[3] = 20e-9
        emap = ExactEventMap(ckt, Control(ton=ph["ton_ns"] * 1e-9, i_target=tgt, d_high=tuple(dd)))
        v1, i1, _ = emap.run_cycle(np.array(ph["section_v"]), np.array(ph["section_i"]))
        sx, J, hist, log = orbit(emap, section_free(v1, i1, ckt))
        rep = orbit_report(emap, sx, J, hist, log)
        rep["phase4_dip_v"] = phase4_dip(emap, sx)
        out["cross_check"][name] = {"physical": ph, "exact": rep, "target_a": tgt}
        seeds[name] = (sx, ph["ton_ns"] * 1e-9, dd)
        print(f"{name}: converged {rep['converged']} T {rep['period_ns']:.2f} ns (phys {ph['period_ns']:.2f}) "
              f"Vo {rep['vo_v']:.5f} |mu|max {rep['floquet_abs'][0]:.4f} lowoff4 {rep['lowoff_i'][3]:.3f} A "
              f"Vds_on {np.round(rep['turnon_vds'], 3)} dip4 {rep['phase4_dip_v']:.4f} V", flush=True)
    for branch, seed, restart in (("soft", "A79_r1_5pct_soft", ()), ("phase4_restart", "A79_r2_5pct_restart", (3,))):
        rows = []
        sx0, ton0, d0 = seeds[seed]
        for pct in np.round(np.arange(3.0, 9.01, 0.5), 2):
            target = -pct / 100 * PEAK
            ok, emap, (sx, J, hist, log) = consistent_orbit(ckt, target, ton0, d0, sx0, restart)
            row = {"pct": float(pct), "target_a": target, "status": {True: "consistent", False: "not_consistent",
                                                                     None: "no_orbit"}[ok]}
            if ok is not None and "error" not in log:
                rep = orbit_report(emap, sx, J, hist, log)
                rep["phase4_dip_v"] = phase4_dip(emap, sx)
                rep["ton_ns"] = emap.ctl.ton * 1e9
                row.update(rep)
                if ok:
                    sx0, ton0, d0 = sx, emap.ctl.ton, emap.ctl.d_high
                print(f"  {branch:15s} {pct:4.1f}% {row['status']:15s} Ton {rep['ton_ns']:.3f} ns Vo {rep['vo_v']:.5f} "
                      f"|mu|max {rep['floquet_abs'][0]:.4f} lowoff4 {rep['lowoff_i'][3]:+.3f} A dip4 "
                      f"{rep['phase4_dip_v'] if rep['phase4_dip_v'] is None else round(rep['phase4_dip_v'], 4)} V "
                      f"how4 {rep['turnon_how'][3]} Vds4 {rep['turnon_vds'][3]:.3f}", flush=True)
            else:
                print(f"  {branch:15s} {pct:4.1f}% no orbit", flush=True)
            rows.append(row)
        out["sweep"][branch] = rows
    # 3. Escape test (after the first sweep, D43 Section 7): from each restart orbit, let phase 4's delay also follow its
    #    natural valley (a corrector that learns at restart edges). Where does it land?
    esc = []
    for row in out["sweep"]["phase4_restart"]:
        if row["status"] != "consistent":
            continue
        ok, emap, (sx, J, hist, log) = consistent_orbit(
            ckt, row["target_a"], row["ton_ns"] * 1e-9, [x * 1e-9 for x in row["d_ns"][:3]] + [row["natural_valley"][3]["t_ns"] * 1e-9],
            np.array(row["section_free"]), ())
        rec = {"pct": row["pct"], "status": {True: "consistent", False: "not_consistent", None: "no_orbit"}[ok]}
        if ok is not None and "error" not in log:
            rep = orbit_report(emap, sx, J, hist, log)
            rec.update(lowoff4=rep["lowoff_i"][3], d4_ns=rep["d_ns"][3], vds4_on=rep["turnon_vds"][3],
                       floquet_max=rep["floquet_abs"][0], section_free=rep["section_free"])
            soft = next(r for r in out["sweep"]["soft"] if r["pct"] == row["pct"])
            rec["max_diff_to_soft_orbit"] = float(np.max(np.abs(np.array(rep["section_free"]) - np.array(soft["section_free"]))))
        esc.append(rec)
        print(f"  escape from restart orbit at {row['pct']}%: {rec['status']} "
              f"d4 {rec.get('d4_ns', float('nan')):.2f} ns lowoff4 {rec.get('lowoff4', float('nan')):+.3f} A "
              f"Vds4 {rec.get('vds4_on', float('nan')):.3f} V, max |diff| to the soft orbit {rec.get('max_diff_to_soft_orbit')}", flush=True)
    out["escape_from_restart"] = esc
    # 4. The restart branch below 3%: is phase 4's natural valley still before the 20 ns restart?
    low = []
    first = next(r for r in out["sweep"]["phase4_restart"] if r["pct"] == 3.0)
    sx0, ton0, d0 = np.array(first["section_free"]), first["ton_ns"] * 1e-9, [x * 1e-9 for x in first["d_ns"]]
    for pct in (2.5, 2.0, 1.5, 1.0):
        ok, emap, (sx, J, hist, log) = consistent_orbit(ckt, -pct / 100 * PEAK, ton0, d0, sx0, (3,))
        rec = {"pct": pct, "status": {True: "consistent", False: "not_consistent", None: "no_orbit"}[ok]}
        if ok is not None and "error" not in log:
            rep = orbit_report(emap, sx, J, hist, log)
            nv = rep["natural_valley"][3]
            rec.update(lowoff4=rep["lowoff_i"][3], vds4_on=rep["turnon_vds"][3], floquet_max=rep["floquet_abs"][0],
                       valley4=nv, turnon_how=rep["turnon_how"], lowoff_i=rep["lowoff_i"])
            if ok:
                sx0, ton0, d0 = sx, emap.ctl.ton, list(emap.ctl.d_high)
        low.append(rec)
        print(f"  restart branch {pct}%: {rec['status']} lowoff4 {rec.get('lowoff4', float('nan')):+.3f} A "
              f"valley4 {rec.get('valley4')} how {rec.get('turnon_how')}", flush=True)
    out["restart_branch_low_targets"] = low
    # 5. The soft branch below 3% with a 30 ns restart timer (longer than phase 4's late valley at 1-2%)
    soft_low = []
    first = next(r for r in out["sweep"]["soft"] if r["pct"] == 3.0)
    sx0, ton0, d0 = np.array(first["section_free"]), first["ton_ns"] * 1e-9, [x * 1e-9 for x in first["d_ns"]]
    for pct in (2.5, 2.0, 1.5, 1.0):
        ok, emap, (sx, J, hist, log) = consistent_orbit(ckt, -pct / 100 * PEAK, ton0, d0, sx0, (), t_rs=30e-9)
        rec = {"pct": pct, "t_restart_high_ns": 30.0, "status": {True: "consistent", False: "not_consistent", None: "no_orbit"}[ok]}
        if ok is not None and "error" not in log:
            rep = orbit_report(emap, sx, J, hist, log)
            rec.update(lowoff_i=rep["lowoff_i"], d_ns=rep["d_ns"], turnon_vds=rep["turnon_vds"], turnon_how=rep["turnon_how"],
                       floquet_max=rep["floquet_abs"][0], ton_ns=emap.ctl.ton * 1e9, period_ns=rep["period_ns"])
            if ok:
                sx0, ton0, d0 = sx, emap.ctl.ton, list(emap.ctl.d_high)
        soft_low.append(rec)
        print(f"  soft branch, 30 ns restart, {pct}%: {rec['status']} d {np.round(rec.get('d_ns', []), 2)} "
              f"lowoff {np.round(rec.get('lowoff_i', []), 2)} Vds_on {np.round(rec.get('turnon_vds', []), 3)} "
              f"how {rec.get('turnon_how')} |mu|max {rec.get('floquet_max')}", flush=True)
    out["soft_branch_low_targets_30ns_restart"] = soft_low
    out["wall_s"] = time.time() - t0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, default=float))
    print(f"wrote {OUT.relative_to(ROOT)} ({out['wall_s']:.0f} s)")


if __name__ == "__main__":
    main()
