"""A61 - how much inductor loss would erase the tuned large-ripple advantage?

Replays two regulated periodic orbits (a large-ripple point and a baseline
point, A59/A60 records) and extracts each phase current. It computes the DC
value, rms, AC rms, peak-to-peak ripple, peak and harmonic amplitudes at
k*f_sw (the orbit is exactly one period, so a DFT of the uniformly
resampled current is exact up to resampling). It then reports the break-even
inductor parameters at which the given advantage vanishes:

* equal DC winding resistance R in every phase inductor of both designs:
  R* = advantage / sum_phases (Irms_zvs^2 - Irms_base^2); and, for scaled
  inductors, the baseline resistance R_b* when R_zvs = R_b (L_zvs/L_b)^a
  (a = 0 equal, 0.5 same structure with fewer turns, 1 resistance per nH);
* equal AC resistance at the fundamental: R1* from the 5 MHz harmonic, and,
  with skin-effect scaling R(k f_sw) = R1 sqrt(k) over harmonics 1-4,
  R1_sqrtf*;
* core loss: any extra core loss of the four large-ripple inductors above
  the baseline's must stay below the advantage (reported with the
  flux-swing ratio dI_pp * L, i.e. the volt-second ratio, for context).

Usage: python3 inductor_break_even.py <zvs_run.json> <baseline_run.json> --advantage-w X
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TRACK = HERE.parent
sys.path.insert(0, str(TRACK / "A60_temperature_ron_sensitivity"))
sys.path.insert(0, str(TRACK / "A59_nonlinear_coss_epc2067"))
import a59_nonlinear as N  # noqa: E402
import run_a60 as T  # noqa: E402

S, R, O = N.S, N.R, T.A58.O


def boundary_from_record(d):
    fb = d["full_boundary"]
    b = N.build_nl_boundary(phase_inductance_h=d["phase_inductance_h"], dead_time_rise_s=d["dead_time_rise_s"],
                            dead_time_fall_s=d["dead_time_fall_s"], ton_cmd_s=d["regulated"]["ton_cmd_s"],
                            coss_model_id=fb.get("coss_model_id", "fig5a_pchip"))
    rds_device = fb["high_side_on_resistance_ohm"] * R.B.NHS
    return T.with_ron(b, rds_device)


def phase_currents(d):
    b = boundary_from_record(d)
    z = np.array(d["regulated"]["z_star"], float)
    with S.asym_schedule_context(), N.nonlinear_coss_context():
        _, steps, index = O.accepted_orbit(b, z, coarse_step_s=d["coarse_step_s"], sub_step_s=d["sub_step_s"])
    t = np.array([s.time_s for s in steps])
    out = []
    for name in ("L1", "L2", "L3", "L4"):
        i = np.array([s.state[index[name]] for s in steps])
        out.append((t, i))
    return b, out


def stats(t, i, period, harmonics=4, samples=8192):
    grid = t[0] + np.arange(samples) * period / samples
    x = np.interp(grid, t, i)
    spec = np.fft.rfft(x) / samples
    dc = float(np.trapezoid(i, t) / period)
    rms = float(np.sqrt(np.trapezoid(i * i, t) / period))
    return dict(dc_a=dc, rms_a=rms, ac_rms_a=float(np.sqrt(max(rms * rms - dc * dc, 0.0))),
                peak_a=float(np.max(np.abs(i))), ripple_pp_a=float(np.max(i) - np.min(i)),
                harmonic_rms_a=[float(np.sqrt(2) * abs(spec[k])) for k in range(1, harmonics + 1)])


def scaled_break_even(rows, advantage_w, exponents=(0.0, 0.5, 1.0)):
    """Baseline winding resistance R_b* that erases the advantage when
    R_zvs = R_b * (L_zvs / L_b)**a in every phase."""
    zvs = sum(p["rms_a"] ** 2 for p in rows["zvs"]["phases"])
    base = sum(p["rms_a"] ** 2 for p in rows["baseline"]["phases"])
    ratio = rows["zvs"]["inductance_h"] / rows["baseline"]["inductance_h"]
    out = {}
    for a in exponents:
        den = ratio ** a * zvs - base
        out[f"R_proportional_to_L^{a:g}"] = advantage_w / den if den > 0 else None
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("zvs")
    p.add_argument("baseline")
    p.add_argument("--advantage-w", type=float, required=True)
    p.add_argument("--out", default=None)
    a = p.parse_args()
    rows = {}
    for key, path in (("zvs", a.zvs), ("baseline", a.baseline)):
        d = json.loads(Path(path).read_text())
        b, currents = phase_currents(d)
        rows[key] = dict(run=Path(path).name, inductance_h=b.phase_inductance_h,
                         phases=[stats(t, i, b.period_s) for t, i in currents])
    z, bl = rows["zvs"]["phases"], rows["baseline"]["phases"]
    d_rms2 = sum(p["rms_a"] ** 2 for p in z) - sum(p["rms_a"] ** 2 for p in bl)
    d_h1 = sum(p["harmonic_rms_a"][0] ** 2 for p in z) - sum(p["harmonic_rms_a"][0] ** 2 for p in bl)
    d_hk = [sum(p["harmonic_rms_a"][k] ** 2 for p in z) - sum(p["harmonic_rms_a"][k] ** 2 for p in bl) for k in range(4)]
    vs_ratio = (np.mean([p["ripple_pp_a"] for p in z]) * rows["zvs"]["inductance_h"]) / (
        np.mean([p["ripple_pp_a"] for p in bl]) * rows["baseline"]["inductance_h"])
    result = dict(experiment="A61", classification="SENSITIVITY_ONLY (break-even analysis)",
                  advantage_w=a.advantage_w, designs=rows,
                  sum_rms2_difference_a2=d_rms2, sum_h1_rms2_difference_a2=d_h1,
                  sum_harmonic_rms2_difference_a2=d_hk,
                  break_even_equal_dc_resistance_ohm=a.advantage_w / d_rms2 if d_rms2 > 0 else None,
                  break_even_baseline_resistance_scaled_ohm=scaled_break_even(rows, a.advantage_w),
                  break_even_equal_fundamental_ac_resistance_ohm=a.advantage_w / d_h1 if d_h1 > 0 else None,
                  break_even_sqrt_f_ac_resistance_at_fsw_ohm=(
                      a.advantage_w / sum(dh * (k + 1) ** 0.5 for k, dh in enumerate(d_hk))
                      if sum(dh * (k + 1) ** 0.5 for k, dh in enumerate(d_hk)) > 0 else None),
                  break_even_extra_core_loss_w=a.advantage_w,
                  volt_second_ratio_zvs_over_baseline=float(vs_ratio),
                  peak_ratio=max(p["peak_a"] for p in z) / max(p["peak_a"] for p in bl))
    text = json.dumps(result, indent=1)
    if a.out:
        out = Path(a.out)
        if out.exists():
            raise SystemExit(f"refusing to overwrite {out}")
        out.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
