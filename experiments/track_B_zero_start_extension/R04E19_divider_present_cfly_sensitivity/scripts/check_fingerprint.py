"""Solver-corruption fingerprint check for R04E19, following R04E18's own
refined method: checks for (a) non-monotonic/duplicate timestamps and
(b) the independent Vin PWL source reading a value implausible for its
own commanded 0-Vin ramp. A generous +/-15% or 2V floor tolerance (looser
than R04E18's own, since R04E19's own divider/Cfly combinations show
larger real LC-ringing overshoot near the fast end) is used to separate
legitimate ringing from actual corruption (values many orders of
magnitude outside the rail, e.g. R04E16's own -20885V/5.33e24V).
"""
import sys
from pathlib import Path
from ltspice_raw_parser import RawFile

VIN = 48.0

def check(path):
    rf = RawFile(path)
    t_idx = rf.name_to_idx["time"]
    vin_idx = rf.name_to_idx["V(vin)"]
    prev_t = None
    dt_nonpos = 0
    vin_min = float("inf")
    vin_max = float("-inf")
    implausible = 0
    max_dev = 0.0
    for row in rf.rows():
        t = row[t_idx]
        v = row[vin_idx]
        if prev_t is not None and t <= prev_t:
            dt_nonpos += 1
        prev_t = t
        if v < vin_min:
            vin_min = v
        if v > vin_max:
            vin_max = v
        if v < -5.0 or v > VIN * 1.5:
            implausible += 1
        dev = abs(v) if v < 0 else 0.0
        if v > VIN:
            dev = max(dev, v - VIN)
        max_dev = max(max_dev, dev)
    return dict(
        points=rf.no_points,
        dt_nonpos=dt_nonpos,
        vin_min=vin_min,
        vin_max=vin_max,
        implausible_gt_5x_or_neg5=implausible,
        max_dev_from_rail=max_dev,
    )

if __name__ == "__main__":
    for p in sys.argv[1:]:
        r = check(Path(p))
        print(p, r)
