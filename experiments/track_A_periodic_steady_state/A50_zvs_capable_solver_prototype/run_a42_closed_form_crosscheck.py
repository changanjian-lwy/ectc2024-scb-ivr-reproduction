"""A50 supporting cross-check - closed form vs A42's own published SPICE rows.

Gate 2 compares an A50 backward-Euler number against A42's LTspice number.  A
disagreement of a few millivolts on an 11.98 V transition could be either
solver's time-discretization error, so this script supplies a third, exact,
solver-independent reference.

Phase 4's commutation cell (and A42's own cell) is an ISOLATED LC: `L` against
`CH + CL` resonating about the `Vout` rail with both switches off.  Its exact
lossless solution is closed form.  Comparing that closed form with EVERY row
A42 published -- not only the two threshold rows -- shows whether a residual
offset is a physics difference (it would scale with the row's current) or an
integration artifact (it scales with the swing and the elapsed time).

A42's own numbers are read from its committed result files; nothing in A42 is
modified or re-run.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import a42_local_validation as a42  # noqa: E402

A42_DIR = HERE.parent / "A42_zero_snubber_negative_current_threshold"


def analytic_release_time_s(negative_current_a: float) -> float:
    """Exact RL ramp `L di/dt = i*RLS - Vout` from `i = 0` to `i = -INEG`."""
    resistance = a42.A42_RLS_OHM
    return (
        a42.LPHASE_H
        / resistance
        * math.log(1.0 / (1.0 - negative_current_a * resistance / a42.VOUT_V))
    )


def load_rows() -> list[dict[str, object]]:
    rows: dict[float, dict[str, object]] = {}
    for name in ("coarse_results.json", "refinement_results.json"):
        for row in json.loads((A42_DIR / name).read_text()):
            rows[row["negative_fraction_pct"]] = row
    fine = A42_DIR / "fine_results.json"
    if fine.exists():
        for row in json.loads(fine.read_text()):
            rows[row["negative_fraction_pct"]] = row
    return [rows[key] for key in sorted(rows)]


def main() -> None:
    table = []
    header = (
        f"{'pct':>6} {'I (A)':>8} {'A42 minVds mV':>14} {'LC minVds mV':>13} "
        f"{'diff mV':>9} {'A42 trel ns':>12} {'LC trel ns':>11} {'diff ps':>8} "
        f"{'A42 tcomm ns':>13} {'LC tcomm ns':>12} {'diff %':>8}"
    )
    print(header)
    print("-" * len(header))
    for row in load_rows():
        current = row["negative_target_a"]
        drop = current * a42.A42_RLS_OHM
        closed = a42.analytic_lossless_commutation(
            negative_current_a=current, switch_node_v=drop
        )
        spice_min_mv = row["minimum_vds_high_after_release_v"] * 1e3
        closed_min_mv = closed["minimum_vds_v"] * 1e3
        spice_release_ns = row["release_time_ns"]
        closed_release_ns = analytic_release_time_s(current) * 1e9
        spice_comm_ns = row["commutation_duration_ns"]
        closed_comm_ns = closed["crossing_time_s"] * 1e9
        comm_diff = (
            None
            if spice_comm_ns is None or math.isnan(closed_comm_ns)
            else 100.0 * (closed_comm_ns - spice_comm_ns) / spice_comm_ns
        )
        # Once a row reaches ZVS, A42's state machine turns the high side ON,
        # which clamps V(vin,a1) near zero, so its reported minimum is no
        # longer the free resonant minimum and must not be compared.
        comparable = not row["natural_zvs_after_release"]
        entry = {
            "negative_fraction_pct": row["negative_fraction_pct"],
            "negative_target_a": current,
            "minimum_vds_comparable": comparable,
            "a42_minimum_vds_mv": spice_min_mv,
            "closed_form_minimum_vds_mv": closed_min_mv,
            "minimum_vds_difference_mv": spice_min_mv - closed_min_mv,
            "a42_release_time_ns": spice_release_ns,
            "closed_form_release_time_ns": closed_release_ns,
            "release_time_difference_ps": (spice_release_ns - closed_release_ns) * 1e3,
            "a42_commutation_ns": spice_comm_ns,
            "closed_form_commutation_ns": (
                None if math.isnan(closed_comm_ns) else closed_comm_ns
            ),
            "commutation_difference_pct": comm_diff,
        }
        table.append(entry)
        if comparable:
            minimum_columns = (
                f"{spice_min_mv:14.4f} {closed_min_mv:13.4f} "
                f"{entry['minimum_vds_difference_mv']:9.4f} "
            )
        else:
            minimum_columns = f"{'(clamped)':>14} {closed_min_mv:13.4f} {'-':>9} "
        release_columns = (
            f"{spice_release_ns:12.4f} {closed_release_ns:11.4f} "
            f"{entry['release_time_difference_ps']:8.2f} "
        )
        spice_comm_column = (
            f"{spice_comm_ns:13.4f}" if spice_comm_ns is not None else f"{'-':>13}"
        )
        closed_comm_column = (
            f" {closed_comm_ns:12.4f}"
            if not math.isnan(closed_comm_ns)
            else f" {'-':>12}"
        )
        comm_diff_column = (
            f" {comm_diff:8.2f}" if comm_diff is not None else f" {'-':>8}"
        )
        print(
            f"{entry['negative_fraction_pct']:6.2f} {current:8.4f} "
            + minimum_columns
            + release_columns
            + spice_comm_column
            + closed_comm_column
            + comm_diff_column
        )
    out = HERE / "a42_closed_form_crosscheck.json"
    out.write_text(json.dumps(table, indent=2) + "\n")
    print(f"\nwrote {out.name}")


if __name__ == "__main__":
    main()
