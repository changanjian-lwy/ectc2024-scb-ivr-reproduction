"""Solver-corruption fingerprint check for R04E24, copied unchanged (same
core logic: non-monotonic/duplicate timestamps + implausible-value scan)
from R04E23's own scripts/check_fingerprint.py (itself adapted from
R04E21/R04E22, R04E19/R04E20's own scripts/check_fingerprint.py). This
experiment's own VRAIL source is a near-instant step (PWL(0 0 {TRAIL}
{VIN} 20u {VIN}), TRAIL=10p), not a slow ramp, so the Vin plausibility
band is widened to account for the fast step's own legitimate LC
turn-on ringing; the phase-1 current I(XMOD:L1) is additionally checked
directly against this project's own documented +/-250 A engineering
bound, per BOUNDARY.md Section 6's explicit requirement to report this
regardless of outcome.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ltspice_raw_parser import RawFile

VIN = 48.0
I_BOUND = 250.0


def check(path):
    rf = RawFile(path)
    t_idx = rf.name_to_idx["time"]
    vin_idx = rf.name_to_idx["V(vin)"]
    il1_idx = rf.name_to_idx["I(xmod:L1)"]

    prev_t = None
    dt_nonpos = 0
    dt_nonpos_examples = []
    vin_min = float("inf")
    vin_max = float("-inf")
    implausible_vin = 0
    il1_min = float("inf")
    il1_max = float("-inf")
    il1_over_bound = 0
    il1_over_bound_examples = []
    n = 0
    for row in rf.rows():
        t = row[t_idx]
        v = row[vin_idx]
        il1 = row[il1_idx]
        n += 1
        if prev_t is not None and t <= prev_t:
            dt_nonpos += 1
            if len(dt_nonpos_examples) < 5:
                dt_nonpos_examples.append((prev_t, t))
        prev_t = t
        if v < vin_min:
            vin_min = v
        if v > vin_max:
            vin_max = v
        if v < -5.0 or v > VIN * 3.0:
            implausible_vin += 1
        if il1 < il1_min:
            il1_min = il1
        if il1 > il1_max:
            il1_max = il1
        if abs(il1) > I_BOUND:
            il1_over_bound += 1
            if len(il1_over_bound_examples) < 5:
                il1_over_bound_examples.append((t, il1))

    return dict(
        points=rf.no_points,
        rows_scanned=n,
        dt_nonpos_count=dt_nonpos,
        dt_nonpos_examples=dt_nonpos_examples,
        vin_min=vin_min,
        vin_max=vin_max,
        implausible_vin_count=implausible_vin,
        il1_min=il1_min,
        il1_max=il1_max,
        il1_max_abs=max(abs(il1_min), abs(il1_max)),
        il1_over_250a_count=il1_over_bound,
        il1_over_250a_examples=il1_over_bound_examples,
    )


if __name__ == "__main__":
    for p in sys.argv[1:]:
        r = check(Path(p))
        print(p)
        for k, v in r.items():
            print(f"  {k}: {v}")
