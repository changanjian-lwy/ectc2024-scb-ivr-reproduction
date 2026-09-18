"""A52 step 1 -- PRINT the exact commanded window boundaries (BOUNDARY Section 2).

Two INDEPENDENT derivations of the same numbers are produced and compared:

  (a) bisection of `solver_copy.zero_start_descriptor.commanded_pwm_mode`
      itself (`a52_boundary.phase_segments`) -- no offset formula written
      anywhere in A52;
  (b) A51's own already-committed `a51_period_map.period_intervals`, which is
      the schedule A51 actually integrated.

Both are then cross-checked against `BOUNDARY.md` Section 4's own quoted
absolute window instants.  Finally the common time offset that maps the
absolute solver timeline onto a netlist starting at `t = 0` is printed
explicitly, together with every window re-expressed in netlist time.

Writes `window_derivation.json`.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import a52_boundary as B

HERE = Path(__file__).resolve().parent
#: One period is built, plus a quarter period of overhang, matching this
#: project's own A37/A49 convention of running slightly past one period.
RUN_SPAN_S = 250e-9


def main() -> int:
    boundary = B.build_boundary()
    t0 = B.A51.period_start_s(boundary)

    print("=" * 78)
    print("A52 -- commanded switching-sequence derivation")
    print("=" * 78)
    print("Boundary, read back off the object actually built (not re-typed):")
    print(f"  period_s                   = {boundary.period_s!r}")
    print(f"  duty  (= nP*Vout/Vin)      = {boundary.duty!r}")
    print(f"  on_time_s (Ton)            = {boundary.on_time_s!r}")
    print(f"  dead_time_s (d)            = {boundary.dead_time_s!r}")
    print(f"  switch_on_resistance_ohm   = {boundary.switch_on_resistance_ohm!r}")
    print(f"  flying_capacitances_f      = {boundary.flying_capacitances_f!r}")
    print(f"  switch_capacitance.high_total_f = "
          f"{boundary.switch_capacitance.high_total_f!r}")
    print(f"  switch_capacitance.low_total_f  = "
          f"{boundary.switch_capacitance.low_total_f!r}")
    print(f"  output_capacitance_f       = {boundary.output_capacitance_f!r}")
    print(f"  source_inductance_h        = {boundary.source_inductance_h!r}")
    print(f"  source_resistance_ohm      = {boundary.source_resistance_ohm!r}")
    print(f"  phase_inductance_h         = {boundary.phase_inductance_h!r}")
    print(f"  phase_inductor_resistance_ohm = "
          f"{boundary.phase_inductor_resistance_ohm!r}")
    print(f"  divider_enabled            = {boundary.divider_enabled!r}")
    print(f"  divider_capacitance_f      = {boundary.divider_capacitance_f!r}")
    print(f"  divider_leakage_ohm        = {boundary.divider_leakage_ohm!r}")
    print(f"  diode_off_resistance_ohm   = {boundary.diode_off_resistance_ohm!r}")
    print(f"  switch_off_resistance_ohm  = {boundary.switch_off_resistance_ohm!r}")
    print(f"  boundary.load_resistance_ohm (nominal 190 W) = "
          f"{boundary.load_resistance_ohm!r}")
    rload = B.rload_from_actual_power_ohm()
    print()
    print("RLOAD actually used by the netlist -- sized from Section 1's own")
    print("ACTUAL delivered power, NOT from the 190 W nominal target:")
    print(f"  Vout_avg = {B.AVERAGE_OUTPUT_V!r} V, P_avg = "
          f"{B.AVERAGE_LOAD_POWER_W!r} W")
    print(f"  RLOAD = Vout^2 / P = {B.AVERAGE_OUTPUT_V!r}^2 / "
          f"{B.AVERAGE_LOAD_POWER_W!r} = {rload!r} ohm")
    print(f"  (cross-check: boundary.load_resistance_ohm = "
          f"{boundary.load_resistance_ohm!r} ohm, relative difference "
          f"{abs(rload - boundary.load_resistance_ohm) / boundary.load_resistance_ohm:.3e})")
    print()
    print(f"Period start t0 (A51's own `period_start_s`, = "
          f"BASE_PERIOD_INDEX*T + d/2) = {t0!r} s")
    print()

    # ------------------------------------------------------------------
    # (a) bisection of `commanded_pwm_mode`
    # ------------------------------------------------------------------
    print("-" * 78)
    print("(a) Commanded segments, found by BISECTING `commanded_pwm_mode`")
    print("    (absolute solver time; no T/4 formula used anywhere here)")
    print("-" * 78)
    segments_by_phase = {}
    for phase0 in range(4):
        segments = B.phase_segments(boundary, t0, phase0, RUN_SPAN_S)
        segments_by_phase[phase0 + 1] = segments
        print(f"  phase {phase0 + 1}:")
        for segment in segments:
            print(
                f"    {segment.kind:<18} "
                f"[{segment.start_s!r}, {segment.end_s!r})"
                f"   len = {(segment.end_s - segment.start_s) * 1e9:.6f} ns"
            )
        print()

    # ------------------------------------------------------------------
    # (b) A51's own `period_intervals`
    # ------------------------------------------------------------------
    print("-" * 78)
    print("(b) A51's own already-committed `period_intervals(boundary, t0)`")
    print("-" * 78)
    a51_turn_on: dict[int, tuple[float, float]] = {}
    a51_turn_off: dict[int, tuple[float, float]] = {}
    for interval in B.A51.period_intervals(boundary, t0):
        label = interval.kind
        phase = None if interval.phase_index is None else interval.phase_index + 1
        print(
            f"    {label:<10} phase={phase}  "
            f"[{interval.start_s!r}, {interval.end_s!r})"
        )
        if interval.kind == "turn_on":
            a51_turn_on[phase] = (interval.start_s, interval.end_s)
        elif interval.kind == "turn_off":
            a51_turn_off[phase] = (interval.start_s, interval.end_s)
    print()

    # ------------------------------------------------------------------
    # cross-check (a) vs (b) vs BOUNDARY.md Section 4
    # ------------------------------------------------------------------
    print("-" * 78)
    print("Cross-check: (a) bisection vs (b) A51 `period_intervals` vs")
    print("             BOUNDARY.md Section 4's own quoted turn-on windows")
    print("-" * 78)
    checks = []
    all_exact = True
    for phase in (1, 2, 3, 4):
        # the turn-on window of this phase, as found by (a)
        turn_on_a = [
            segment
            for segment in segments_by_phase[phase]
            if segment.kind == "DEADTIME_TURN_ON"
        ]
        # `period_intervals` covers exactly ONE period, so it reports each
        # phase's turn-on window once; (a) covers 250 ns and may report the
        # same window plus a later repeat.  Compare the one inside the period.
        inside = [
            segment
            for segment in turn_on_a
            if t0 - 1e-18 <= segment.start_s < t0 + boundary.period_s - 1e-18
        ]
        assert len(inside) == 1, f"phase {phase}: {inside}"
        start_a, end_a = inside[0].start_s, inside[0].end_s
        start_b, end_b = a51_turn_on[phase]
        target = B.SECTION4_TARGETS[phase]
        start_c, end_c = target["window_start_s"], target["window_end_s"]

        bitwise_ab = (start_a == start_b) and (end_a == end_b)
        # (a) and (b) compute the same instant by different float paths
        # (bisection of the schedule vs `center +/- d/2`), so they may differ
        # by one unit in the last place.  One ULP at 2.3e-5 s is about
        # 3.4e-21 s -- 18 orders of magnitude below the 2.15 ns window and
        # 9 orders below the finest timestep LTspice will be asked for, so
        # agreement is asserted at 1 ULP, and the actual ULP gap is reported.
        ulp_a = np.spacing(max(abs(start_a), abs(end_a)))
        close_ab = (
            abs(start_a - start_b) <= ulp_a and abs(end_a - end_b) <= ulp_a
        )
        # Section 4 quotes the windows to 10 significant figures, so compare
        # at that printed precision.
        exact_ac = abs(start_a - start_c) <= ulp_a and abs(end_a - end_c) <= ulp_a
        all_exact = all_exact and close_ab and exact_ac
        print(f"  phase {phase}:")
        print(f"    (a) bisection        [{start_a!r}, {end_a!r})")
        print(f"    (b) period_intervals [{start_b!r}, {end_b!r})")
        print(f"    (c) BOUNDARY Sec. 4  [{start_c!r}, {end_c!r}]")
        print(f"    (a) vs (b): bit-for-bit {bitwise_ab}; |dstart| "
              f"{abs(start_a - start_b):.3e} s, |dend| "
              f"{abs(end_a - end_b):.3e} s (1 ULP = {ulp_a:.3e} s) "
              f"-> within 1 ULP: {close_ab}")
        print(f"    (a) vs (c) |dstart|  : {abs(start_a - start_c):.3e} s   "
              f"|dend| : {abs(end_a - end_c):.3e} s   -> match: {exact_ac}")
        checks.append(
            {
                "phase": phase,
                "bisection_window_s": [start_a, end_a],
                "a51_period_intervals_window_s": [start_b, end_b],
                "boundary_md_section4_window_s": [start_c, end_c],
                "bisection_equals_a51_bitwise": bool(bitwise_ab),
                "bisection_equals_a51_within_1_ulp": bool(close_ab),
                "ulp_s": float(ulp_a),
                "bisection_matches_boundary_md": bool(exact_ac),
                "delta_start_s": float(abs(start_a - start_c)),
                "delta_end_s": float(abs(end_a - end_c)),
            }
        )
    print()
    print(f"  ALL FOUR WINDOWS MATCH BOUNDARY.md SECTION 4 EXACTLY: {all_exact}")
    print()

    # ------------------------------------------------------------------
    # offset conversion to netlist time
    # ------------------------------------------------------------------
    print("-" * 78)
    print("Offset conversion to netlist time (explicit, per the task)")
    print("-" * 78)
    print(f"  common reference TOFFSET := t0 = {t0!r} s")
    print("  netlist time  tau := t_absolute - TOFFSET")
    print("  so the netlist's `.tran` starts at tau = 0, which is EXACTLY the")
    print("  instant A51's own period map starts from, i.e. the instant at")
    print("  which phase 1's turn-on dead-time window ends and phase 1 goes")
    print("  HIGH.  The seed state z* (BOUNDARY Section 1) is the state at")
    print("  tau = 0.")
    print()
    netlist_segments: dict[int, list[dict]] = {}
    for phase in (1, 2, 3, 4):
        print(f"  phase {phase} (netlist time, ns):")
        rows = []
        for segment in segments_by_phase[phase]:
            start_tau = segment.start_s - t0
            end_tau = segment.end_s - t0
            rows.append(
                {
                    "kind": segment.kind,
                    "start_s": start_tau,
                    "end_s": end_tau,
                }
            )
            print(
                f"    {segment.kind:<18} "
                f"[{start_tau * 1e9:>12.7f}, {end_tau * 1e9:>12.7f}) ns"
            )
        netlist_segments[phase] = rows
        print()

    print("  BOUNDARY.md Section 4's four turn-on windows, in netlist time:")
    section4_netlist = {}
    for phase in (1, 2, 3, 4):
        target = B.SECTION4_TARGETS[phase]
        start_tau = target["window_start_s"] - t0
        end_tau = target["window_end_s"] - t0
        section4_netlist[phase] = [start_tau, end_tau]
        print(
            f"    phase {phase}: [{start_tau * 1e9:>12.7f}, "
            f"{end_tau * 1e9:>12.7f}) ns    "
            f"(target crossing at +{target['crossing_time_ns']:.6f} ns "
            f"-> tau = {(start_tau + target['crossing_time_ns'] * 1e-9) * 1e9:.7f} ns)"
        )
    print()

    print("  Vds node pair per phase (from `solver_copy.HIGH_SIDE_BRANCHES`):")
    for phase0 in range(4):
        first, second = B.vds_expression(phase0)
        print(f"    phase {phase0 + 1}: V({first}) - "
              f"V({second if second is not None else '0'})")
    print()

    payload = {
        "t0_absolute_s": t0,
        "toffset_s": t0,
        "run_span_s": RUN_SPAN_S,
        "boundary": {
            "period_s": boundary.period_s,
            "duty": boundary.duty,
            "on_time_s": boundary.on_time_s,
            "dead_time_s": boundary.dead_time_s,
            "switch_on_resistance_ohm": boundary.switch_on_resistance_ohm,
            "switch_off_resistance_ohm": boundary.switch_off_resistance_ohm,
            "flying_capacitances_f": list(boundary.flying_capacitances_f),
            "ch_total_f": boundary.switch_capacitance.high_total_f,
            "cl_total_f": boundary.switch_capacitance.low_total_f,
            "output_capacitance_f": boundary.output_capacitance_f,
            "source_inductance_h": boundary.source_inductance_h,
            "source_resistance_ohm": boundary.source_resistance_ohm,
            "phase_inductance_h": boundary.phase_inductance_h,
            "phase_inductor_resistance_ohm": boundary.phase_inductor_resistance_ohm,
            "divider_capacitance_f": boundary.divider_capacitance_f,
            "divider_leakage_ohm": boundary.divider_leakage_ohm,
            "diode_off_resistance_ohm": boundary.diode_off_resistance_ohm,
            "vin_target_v": boundary.vin_target_v,
            "nominal_load_resistance_ohm": boundary.load_resistance_ohm,
            "rload_used_ohm": rload,
        },
        "cross_check": checks,
        "all_windows_match_boundary_md": bool(all_exact),
        "netlist_time_segments": netlist_segments,
        "section4_turn_on_windows_netlist_time_s": section4_netlist,
    }
    (HERE / "window_derivation.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    print(f"wrote {HERE / 'window_derivation.json'}")
    return 0 if all_exact else 1


if __name__ == "__main__":
    raise SystemExit(main())
