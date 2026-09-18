"""A52 steps 3-5 -- judge the SPICE run against BOUNDARY.md Section 4.

Three independent readings of the same run are produced and compared, so a
single parsing or measurement mistake cannot silently set the verdict:

  (1) LTspice's own `.meas` output (`meas_log`), which is the project's
      established A37/A48 convention;
  (2) an independent scan of the `.raw` binary (this project's own
      `ltspice_raw_parser.py`, copied verbatim into `scripts/`), which
      re-finds every zero crossing by linear interpolation without using
      any `.meas` result;
  (3) the same run repeated at a 4x finer maximum timestep, so the
      crossing times are shown to be step-size converged -- A50/A51's own
      standing discipline before any crossing claim is trusted.

Safety and solver-fingerprint checks are done on the `.raw` directly.

Writes `results.json`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "scripts"))

import a52_boundary as B  # noqa: E402
import meas_log  # noqa: E402
from ltspice_raw_parser import RawFile  # noqa: E402

MAIN = "A52_spice_crosscheck_reduced_load_zvs"
FINE = "A52_spice_crosscheck_reduced_load_zvs_step250f"


def load_metadata() -> dict:
    return json.loads((HERE / "netlist_metadata.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# independent `.raw` readings
# ---------------------------------------------------------------------------
def raw_columns(raw: RawFile, names: list[str]) -> dict[str, list[float]]:
    indices = {name: raw.name_to_idx[name] for name in names}
    out: dict[str, list[float]] = {name: [] for name in names}
    for row in raw.rows():
        for name, index in indices.items():
            out[name].append(row[index])
    return out


def interpolate_at(times: list[float], values: list[float], target: float) -> float:
    """Linear interpolation of `values` at `target` on the `times` grid."""
    low, high = 0, len(times) - 1
    while low < high:
        middle = (low + high) // 2
        if times[middle] < target:
            low = middle + 1
        else:
            high = middle
    if low == 0:
        return values[0]
    t0, t1 = times[low - 1], times[low]
    v0, v1 = values[low - 1], values[low]
    if t1 == t0:
        return v1
    return v0 + (v1 - v0) * (target - t0) / (t1 - t0)


def first_downward_zero(
    times: list[float], values: list[float], start_s: float, end_s: float
) -> float | None:
    """First instant in `(start_s, end_s]` at which `values` crosses 0 downward."""
    previous_time = None
    previous_value = None
    for time_s, value in zip(times, values):
        if time_s < start_s:
            previous_time, previous_value = time_s, value
            continue
        if time_s > end_s:
            break
        if (
            previous_value is not None
            and previous_value > 0.0
            and value <= 0.0
            and previous_time is not None
            and previous_time >= start_s
        ):
            span = value - previous_value
            if span == 0.0:
                return previous_time
            return previous_time + (-previous_value) * (time_s - previous_time) / span
        previous_time, previous_value = time_s, value
    return None


def analyse_run(tag: str, metadata: dict) -> dict:
    stem = MAIN if tag == "main" else FINE
    log = HERE / f"{stem}.log"
    raw_path = HERE / f"{stem}.raw"
    meas = meas_log.parse(log)
    raw = RawFile(raw_path)

    probes = {int(k): v for k, v in metadata["vds_probe"].items()}
    windows = {int(k): v for k, v in metadata["turn_on_windows_netlist_time"].items()}

    wanted = ["time", "V(src)"] + [f"I(LIND{k})" for k in range(1, 5)]
    # `V(vin,a1)` is not a stored trace; the differences are reconstructed
    # from the two stored node voltages, exactly as the descriptor defines
    # `Vds` (`HIGH_SIDE_BRANCHES`).
    node_names = set()
    for phase0 in range(4):
        first, second = B.vds_expression(phase0)
        node_names.add(f"V({first})")
        if second is not None:
            node_names.add(f"V({second})")
    wanted += sorted(node_names)
    columns = raw_columns(raw, wanted)
    times = columns["time"]

    # ---- fingerprint ----------------------------------------------------
    non_monotonic = sum(
        1 for a, b in zip(times, times[1:]) if b < a
    )
    duplicates = sum(1 for a, b in zip(times, times[1:]) if b == a)
    src = columns["V(src)"]
    # t=0 is LTspice's own pre-source UIC row under `.tran ... UIC`; the
    # rail is checked from the first real timepoint onward.
    src_after_zero = src[1:]
    src_min = min(src_after_zero)
    src_max = max(src_after_zero)
    fingerprint = {
        "points": raw.no_points,
        "non_monotonic_timestamps": non_monotonic,
        "duplicate_timestamps": duplicates,
        "t_first_s": times[0],
        "t_second_s": times[1],
        "t_last_s": times[-1],
        "v_src_at_t0_v": src[0],
        "v_src_min_after_t0_v": src_min,
        "v_src_max_after_t0_v": src_max,
        "v_src_constant_48v_after_t0": bool(src_min == 48.0 and src_max == 48.0),
        "v_src_t0_row_is_uic_artifact": bool(src[0] == 0.0 and src[1] == 48.0),
    }

    # ---- safety ---------------------------------------------------------
    safety = {}
    worst = 0.0
    for phase in range(1, 5):
        series = columns[f"I(LIND{phase})"]
        maximum = max(abs(value) for value in series)
        worst = max(worst, maximum)
        safety[f"phase_{phase}_max_abs_current_a"] = maximum
        # Independent cross-check against LTspice's own `.meas MAX ABS(...)`.
        safety[f"phase_{phase}_max_abs_current_meas_a"] = meas.get(f"imax_p{phase}")
    safety["max_abs_phase_current_a"] = worst
    safety["limit_a"] = B.PHASE_CURRENT_LIMIT_A
    safety["within_limit"] = bool(worst <= B.PHASE_CURRENT_LIMIT_A)

    # ---- per-phase ZVS verdict -----------------------------------------
    phases = []
    for phase in (1, 2, 3, 4):
        phase0 = phase - 1
        window_start, window_end = windows[phase]
        first, second = B.vds_expression(phase0)
        vds = [
            value - other
            for value, other in zip(columns[f"V({first})"], columns[f"V({second})"])
        ]
        raw_cross = first_downward_zero(times, vds, window_start, window_end)
        meas_cross = meas.get(f"txp{phase}")
        meas_state_on = meas.get(f"ton_p{phase}")
        vds_entry = meas.get(f"vdsent_p{phase}")
        il_entry = meas.get(f"ilent_p{phase}")
        vds_before_end = meas.get(f"vdsend_p{phase}")
        vds_min = meas.get(f"vdsmin_p{phase}")
        vds_at_on = meas.get(f"vdson_p{phase}")

        target = B.SECTION4_TARGETS[phase]
        target_cross_ns = target["crossing_time_ns"]

        # A crossing counts as NATURAL only if it happened strictly inside
        # the window, i.e. the commanded timeout did not fire first.
        natural = bool(
            raw_cross is not None
            and raw_cross < window_end
            and vds_before_end is not None
            and vds_before_end <= 0.0
        )
        spice_cross_ns = None if raw_cross is None else (raw_cross - window_start) * 1e9
        meas_cross_ns = (
            None if meas_cross is None else (meas_cross - window_start) * 1e9
        )
        relative_error = (
            None
            if spice_cross_ns is None
            else (spice_cross_ns - target_cross_ns) / target_cross_ns
        )
        phases.append(
            {
                "phase": phase,
                "vds_probe": probes[phase],
                "window_start_netlist_s": window_start,
                "window_end_netlist_s": window_end,
                "window_start_absolute_s": target["window_start_s"],
                "python_target": {
                    "natural_zvs": target["natural_zvs"],
                    "crossing_time_ns": target_cross_ns,
                    "il_at_entry_a": target["il_at_entry_a"],
                    "initial_vds_v": target["initial_vds_v"],
                    "min_abs_vds_v": target["min_abs_vds_v"],
                },
                "spice": {
                    "natural_zvs": natural,
                    "crossing_time_ns_from_raw": spice_cross_ns,
                    "crossing_time_ns_from_meas": meas_cross_ns,
                    "state_transition_time_ns": (
                        None
                        if meas_state_on is None
                        else (meas_state_on - window_start) * 1e9
                    ),
                    "il_at_entry_a": il_entry,
                    "initial_vds_v": vds_entry,
                    "vds_just_before_window_end_v": vds_before_end,
                    "min_signed_vds_in_window_v": vds_min,
                    "vds_at_switch_on_v": vds_at_on,
                },
                "comparison": {
                    "crossing_time_relative_error": relative_error,
                    "crossing_time_error_ns": (
                        None
                        if spice_cross_ns is None
                        else spice_cross_ns - target_cross_ns
                    ),
                    "within_20pct_tolerance": (
                        None
                        if relative_error is None
                        else bool(
                            abs(relative_error) <= B.CROSSING_TIME_TOLERANCE_FRACTION
                        )
                    ),
                    "raw_vs_meas_crossing_difference_ns": (
                        None
                        if (spice_cross_ns is None or meas_cross_ns is None)
                        else spice_cross_ns - meas_cross_ns
                    ),
                    "il_at_entry_error_a": (
                        None
                        if il_entry is None
                        else il_entry - target["il_at_entry_a"]
                    ),
                    "initial_vds_error_v": (
                        None
                        if vds_entry is None
                        else vds_entry - target["initial_vds_v"]
                    ),
                    "natural_zvs_agrees": bool(natural == target["natural_zvs"]),
                },
            }
        )

    # ---- periodicity: SPICE state one period on, versus the seed z* -----
    boundary = B.build_boundary()
    names = B.A51.variable_names(boundary)
    seed = dict(zip(names, B.Z_STAR.tolist()))
    period = metadata["period_s"]
    node_to_trace = {
        name: f"V({name})"
        for name in names
        if name not in ("LPAR_IN", "L1", "L2", "L3", "L4", "I_VSTEP")
    }
    inductor_to_trace = {
        "LPAR_IN": "I(L_PAR_IN)",
        "L1": "I(LIND1)",
        "L2": "I(LIND2)",
        "L3": "I(LIND3)",
        "L4": "I(LIND4)",
    }
    needed = sorted(set(node_to_trace.values()) | set(inductor_to_trace.values()))
    extra = raw_columns(raw, [name for name in needed if name not in columns] + ["time"])
    for key, value in extra.items():
        columns.setdefault(key, value)

    periodicity = []
    worst_abs = 0.0
    for variable in names:
        if variable == "I_VSTEP":
            continue
        trace = node_to_trace.get(variable) or inductor_to_trace[variable]
        # Sampled at 2 ps, not 0: under `.tran ... UIC` LTspice emits one
        # pre-source row at t=0 (V(src)=0 there), and all four machines ramp
        # their gate outputs over ~1.13 ps starting at t=0, so t=0 is not a
        # physically meaningful sample.  2 ps is A37's own convention.
        start_value = interpolate_at(times, columns[trace], 2e-12)
        end_value = interpolate_at(times, columns[trace], period)
        drift = end_value - seed[variable]
        worst_abs = max(worst_abs, abs(drift))
        periodicity.append(
            {
                "variable": variable,
                "trace": trace,
                "seed_value": seed[variable],
                "spice_at_2ps": start_value,
                "spice_after_one_period": end_value,
                "drift_vs_seed": drift,
                "drift_over_period": end_value - start_value,
            }
        )
    seed_norm = max(abs(value) for value in seed.values())
    periodicity_summary = {
        "period_s": period,
        "max_abs_drift_vs_seed": worst_abs,
        "seed_inf_norm": seed_norm,
        "relative_residual": worst_abs / max(seed_norm, 1.0),
        "rows": periodicity,
    }

    return {
        "tag": tag,
        "netlist": f"{stem}.cir",
        "max_step_s": metadata["max_step_s"],
        "netlist_error": meas.netlist_error,
        "fingerprint": fingerprint,
        "safety": safety,
        "phases": phases,
        "periodicity": periodicity_summary,
        "vout_avg_v": meas.get("vout_avg"),
        "pload_avg_w": meas.get("pload_avg"),
    }


def main() -> int:
    metadata = load_metadata()
    runs = {}
    for tag in ("main", "_step250f"):
        stem = MAIN if tag == "main" else FINE
        if not (HERE / f"{stem}.raw").exists():
            print(f"skipping {tag}: {stem}.raw not present")
            continue
        runs[tag] = analyse_run(tag, metadata[tag])

    main_run = runs["main"]

    print("=" * 78)
    print("A52 -- SPICE vs A51 per-phase ZVS comparison")
    print("=" * 78)
    print(
        f"{'Ph':<3}{'Python tcross':>15}{'SPICE tcross':>15}{'err':>12}"
        f"{'rel':>10}{'<=20%':>8}{'natural':>10}"
    )
    for row in main_run["phases"]:
        spice = row["spice"]["crossing_time_ns_from_raw"]
        comparison = row["comparison"]
        target_ns = row["python_target"]["crossing_time_ns"]
        spice_text = "n/a" if spice is None else f"{spice:.6f}"
        error = comparison["crossing_time_error_ns"]
        error_text = "n/a" if error is None else f"{error:+.6f}"
        relative = comparison["crossing_time_relative_error"]
        relative_text = "n/a" if relative is None else f"{relative * 100:.3f}%"
        print(
            f"{row['phase']:<3}{target_ns:>15.6f}{spice_text:>15}"
            f"{error_text:>12}{relative_text:>10}"
            f"{str(comparison['within_20pct_tolerance']):>8}"
            f"{str(row['spice']['natural_zvs']):>10}"
        )
    print()
    print("Entry-condition agreement (SPICE .meas vs A51 Section 4):")
    for row in main_run["phases"]:
        print(
            f"  phase {row['phase']}: "
            f"Vds_entry {row['spice']['initial_vds_v']:.6f} V vs "
            f"{row['python_target']['initial_vds_v']:.6f} V "
            f"(d={row['comparison']['initial_vds_error_v']:+.3e}); "
            f"iL_entry {row['spice']['il_at_entry_a']:.6f} A vs "
            f"{row['python_target']['il_at_entry_a']:.6f} A "
            f"(d={row['comparison']['il_at_entry_error_a']:+.3e})"
        )
    print()
    print("Cross-check, `.raw` scan vs LTspice `.meas` crossing instants:")
    for row in main_run["phases"]:
        print(
            f"  phase {row['phase']}: raw {row['spice']['crossing_time_ns_from_raw']:.9f} ns, "
            f"meas {row['spice']['crossing_time_ns_from_meas']:.9f} ns, "
            f"difference {row['comparison']['raw_vs_meas_crossing_difference_ns'] * 1e3:+.4f} ps"
        )
    print()
    if "_step250f" in runs:
        print("Step-size convergence (1 ps vs 0.25 ps maximum timestep):")
        fine = {row["phase"]: row for row in runs["_step250f"]["phases"]}
        for row in main_run["phases"]:
            coarse_value = row["spice"]["crossing_time_ns_from_raw"]
            fine_value = fine[row["phase"]]["spice"]["crossing_time_ns_from_raw"]
            print(
                f"  phase {row['phase']}: 1 ps -> {coarse_value:.9f} ns, "
                f"0.25 ps -> {fine_value:.9f} ns, "
                f"difference {(fine_value - coarse_value) * 1e3:+.4f} ps"
            )
        print()
    print("Safety:")
    safety = main_run["safety"]
    for phase in range(1, 5):
        print(f"  phase {phase} max |iL| = {safety[f'phase_{phase}_max_abs_current_a']:.4f} A")
    print(
        f"  worst = {safety['max_abs_phase_current_a']:.4f} A, limit "
        f"{safety['limit_a']} A -> within: {safety['within_limit']}"
    )
    print()
    print("Solver fingerprint:")
    for key, value in main_run["fingerprint"].items():
        print(f"  {key} = {value!r}")
    print()
    print("Periodicity (SPICE at t=T versus the seed z*):")
    summary = main_run["periodicity"]
    print(
        f"  max |drift| = {summary['max_abs_drift_vs_seed']:.6e}, "
        f"relative residual = {summary['relative_residual']:.6e}"
    )
    for row in summary["rows"]:
        print(
            f"    {row['variable']:<8} seed {row['seed_value']:>22.12f}  "
            f"t=T {row['spice_after_one_period']:>22.12f}  "
            f"drift {row['drift_vs_seed']:>+13.6e}"
        )
    print()
    print(
        f"Average output {main_run['vout_avg_v']!r} V (A51: {B.AVERAGE_OUTPUT_V} V); "
        f"average load power {main_run['pload_avg_w']!r} W "
        f"(A51: {B.AVERAGE_LOAD_POWER_W} W)"
    )

    payload = {
        "experiment": "A52_spice_crosscheck_reduced_load_zvs",
        "tolerance_fraction": B.CROSSING_TIME_TOLERANCE_FRACTION,
        "phase_current_limit_a": B.PHASE_CURRENT_LIMIT_A,
        "seed_state_variable_order": list(B.A51.variable_names(B.build_boundary())),
        "seed_state": B.Z_STAR.tolist(),
        "ic_mapping": metadata["main"]["ic_mapping"],
        "window_derivation": json.loads(
            (HERE / "window_derivation.json").read_text(encoding="utf-8")
        ),
        "pilot": json.loads((HERE / "pilot_results.json").read_text(encoding="utf-8")),
        "runs": runs,
    }
    all_natural = all(row["spice"]["natural_zvs"] for row in main_run["phases"])
    all_within = all(
        row["comparison"]["within_20pct_tolerance"] for row in main_run["phases"]
    )
    payload["verdict"] = {
        "all_four_phases_natural_zvs_in_spice": all_natural,
        "all_four_crossing_times_within_20pct": all_within,
        "safety_within_limit": main_run["safety"]["within_limit"],
        "fingerprint_clean": bool(
            main_run["fingerprint"]["non_monotonic_timestamps"] == 0
            and main_run["fingerprint"]["duplicate_timestamps"] == 0
            and main_run["fingerprint"]["v_src_constant_48v_after_t0"]
        ),
    }
    (HERE / "results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print()
    print(f"verdict: {payload['verdict']}")
    print(f"wrote {HERE / 'results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
