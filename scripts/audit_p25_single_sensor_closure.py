"""D41: P25-scale periodic closure under single-sensor (phase-shift) control.

Run from the project root: python3 -m scripts.audit_p25_single_sensor_closure
Writes symbolic_derivations/02_P25_native/diagnostics/D41_single_sensor_closure.json.

Values are P25 orders of magnitude (P25_SUPPLEMENT; used for causal
understanding, not fitted). PROJECT_DECISIONs are listed in P25_SCALE:
- 30 nH (implied by P25's reported 50 A peak with its 22 nH part);
- GS61008T charge-equivalent 0.69 nF per device (0-4 V), 1 high / 2 low;
- series capacitors 100 uF (P25 assumes zero series-capacitor ripple and
  publishes no value);
- output capacitor 100 uF;
- phase shifts T/3 and 2T/3 of P25's nominal 0.5 MHz.
Ideal zero-drop reverse, zero winding resistance and zero snubber, as in the
synthetic fixture. alpha = 5% (P25's published 5-10% lower end).
"""
import json
import sys
from pathlib import Path

import numpy as np

from scb_ivr.p25_control_memory import KnownPeak, Policy, start_at_high_on
from scb_ivr.p25_cycle_modes import cycle_mode
from scb_ivr.p25_entry_direction import DirectionTolerance
from scb_ivr.p25_event_guards import Snapshot
from scb_ivr.p25_local_flow import ConstantPorts
from scb_ivr.p25_native_events import NativeBoundary, PeakReference
from scb_ivr.p25_nodal_contract import Components
from scb_ivr.p25_periodic_section import ModelIdentity, ReturnTolerance
from scb_ivr.p25_reverse_contract import ReverseModel, Tolerances
from scb_ivr.p25_root_location import RootSettings
from scb_ivr.p25_seed_evaluation import evaluate_seed
from scb_ivr.p25_shooting_contract import ShootingContract, SectionSeed

OUT = Path(__file__).resolve().parents[1] / "symbolic_derivations" / "02_P25_native" / "diagnostics" / "D41_single_sensor_closure.json"
L, TON, VIN, VO, ALPHA, PEAK, T_NOM = 30e-9, 500e-9, 12., 1., .05, 50., 2e-6
P25_SCALE = dict(coss_f=(0.69e-9,) * 3 + (1.38e-9,) * 3, series_f=(100e-6, 100e-6), output_f=100e-6,
                 inductance_h=(L,) * 3, on_time_s=TON, alpha=ALPHA, peak_ref_a=PEAK,
                 load_a=3 * (((VIN / 3 - VO) * TON / L) / 2 - ALPHA * PEAK),
                 phase_shift_s=(T_NOM / 3, 2 * T_NOM / 3))
SEED0 = (4., 4., 1., -ALPHA * PEAK, -ALPHA * PEAK + VO / L * T_NOM / 3, -ALPHA * PEAK + VO / L * 2 * T_NOM / 3)
NAMES = ("a2_v", "x1_v", "out_v", "iL1_a", "iL2_a", "iL3_a")
SCALE = np.array([1, 1, .1, 1, 1, 1.])


def context(phase_shift_s, intervals=4000):
    sc = P25_SCALE
    label = "D41 P25-scale " + ("single-sensor" if phase_shift_s else "per-phase") + " control"
    parts = Components(sc["coss_f"], (0.,) * 6, sc["series_f"], sc["output_f"], sc["inductance_h"], (0.,) * 3, label)
    policy = Policy((sc["on_time_s"],) * 3, 1e-8, 1e-8, 1e-15, True, label, phase_shift_s)
    ports = ConstantPorts(sc["load_a"], 0., label)
    reverse = ReverseModel("ideal_zero_drop", (0.,) * 6, "declared ideal mathematical branch")
    boundary = NativeBoundary(3, 1, 1, "dynamic_Co_current_ports", sc["alpha"])
    a2, x1, out, i1, i2, i3 = SEED0
    state = Snapshot(boundary, label, "absolute", 0, 0., VIN, (VIN, a2, x1, 0., 0., out), (i1, i2, i3),
                     cycle_mode("M1").gates)
    peaks = tuple(KnownPeak(PeakReference(k, sc["peak_ref_a"], "declared_design_peak", label), 0.) for k in (1, 2, 3))
    memory = start_at_high_on(state, phase=1, peaks=peaks, policy=policy)
    contract = ShootingContract(memory, ModelIdentity(parts, reverse, policy, label), ports, label)
    root = RootSettings(1e-15, 1e-8, 200, "sampled continuous local affine flow")
    options = dict(return_tolerance=ReturnTolerance(1e-8, 1e-8, 1e-12, 0.), stage_horizons_s=(200e-9, 2e-6, 2e-6, 200e-9),
                   intervals=intervals, voltage_root=root, current_root=root, electrical=Tolerances(1e-8, 1e-8, 1e-8),
                   direction=DirectionTolerance(1e-8, 1e-8, 1e-10, 1e-10))
    return contract, options


def section_map(contract, options, z):
    r = evaluate_seed(contract, SectionSeed(float(z[0]), float(z[1]), float(z[2]), tuple(float(x) for x in z[3:])), **options)
    if r.attempt.end is None:
        return None, r
    e = r.attempt.end.last_event
    return np.array([e.voltage_v[1], e.voltage_v[2], e.voltage_v[5], *e.current_a], float), r


def jacobian(contract, options, z, h0=1e-3):
    """Central differences; one-sided if a perturbed start is blocked.

    h0 = 1e-3 (V or A): the section map carries ~1e-8 event-location noise,
    so a 2e-6 step (tried first) gives ~5e-3 derivative error and hides the
    small singular values of J - I. The local flows are affine, so the larger
    step adds little curvature error.
    """
    f0, _ = section_map(contract, options, z)
    J = np.zeros((6, 6))
    for j in range(6):
        h = h0 * SCALE[j]
        zp, zm = z.copy(), z.copy()
        zp[j] += h; zm[j] -= h
        fp, _ = section_map(contract, options, zp)
        fm, _ = section_map(contract, options, zm)
        if fp is not None and fm is not None:
            J[:, j] = (fp - fm) / (2 * h)
        elif fp is not None:
            J[:, j] = (fp - f0) / h
        elif fm is not None:
            J[:, j] = (f0 - fm) / h
        else:
            raise RuntimeError("both perturbed seeds blocked; Jacobian column unavailable")
    return J


def newton(contract, options, z, iterations=20):
    rows = []
    for it in range(iterations):
        f, r = section_map(contract, options, z)
        if f is None:
            rows.append({"iter": it, "blocked_at": r.attempt.failed_mode, "status": r.status})
            return z, rows, r
        g = f - z
        rows.append({"iter": it, "z": z.tolist(), "max_dV": float(np.max(np.abs(g[:3]))),
                     "max_dI": float(np.max(np.abs(g[3:]))), "period_s": r.attempt.end.last_event.time_s,
                     "status": r.status})
        print(f"  newton {it}: |G| {rows[-1]['max_dV']:.2e} V {rows[-1]['max_dI']:.2e} A  "
              f"T {rows[-1]['period_s'] * 1e9:.4f} ns  {r.status}", flush=True)
        if r.status == "CONDITIONAL_STATE_RETURN":
            return z, rows, r
        try:
            J = jacobian(contract, options, z)
        except RuntimeError as exc:
            rows.append({"iter": it, "note": str(exc)})
            return z, rows, r
        step = np.linalg.solve(J - np.eye(6), -g)
        lam = 1.0
        while lam > 1e-4:
            ft, _ = section_map(contract, options, z + lam * step)
            if ft is not None and np.max(np.abs((ft - z - lam * step) / SCALE)) < np.max(np.abs(g / SCALE)):
                break
            lam /= 2
        else:
            rows.append({"iter": it, "note": "no descent step"})
            return z, rows, r
        z = z + lam * step
    return z, rows, r


def run():
    out = {"scope": "P25-scale orders of magnitude; ideal lossless; sampled event coverage (not certified)",
           "p25_scale": {k: (list(v) if isinstance(v, tuple) else v) for k, v in P25_SCALE.items()}}
    for tag, shift in (("single_sensor", P25_SCALE["phase_shift_s"]), ("per_phase", None)):
        print(f"== {tag}", flush=True)
        contract, options = context(shift)
        z, rows, r = newton(contract, options, np.array(SEED0, float))
        entry = {"newton": rows, "final_status": r.status}
        if r.attempt.end is not None:
            J = jacobian(contract, options, z)
            w = np.linalg.eigvals(J)
            _, s, vt = np.linalg.svd(J - np.eye(6))
            entry.update({"z_star": dict(zip(NAMES, z.tolist())), "eigenvalues": [[float(x.real), float(x.imag)] for x in w],
                          "max_abs_eigenvalue": float(np.max(np.abs(w))), "singular_values_J_minus_I": s.tolist(),
                          "weakest_direction": dict(zip(NAMES, vt[-1].tolist())),
                          "period_s": r.attempt.end.last_event.time_s})
            print(f"  |eig| {np.round(np.sort(np.abs(w))[::-1], 4)}  sv(J-I) {np.array2string(s, precision=2)}", flush=True)
        out[tag] = entry
    OUT.write_text(json.dumps(out, indent=1, default=float))
    return out


if __name__ == "__main__":
    run()
    sys.exit(0)
