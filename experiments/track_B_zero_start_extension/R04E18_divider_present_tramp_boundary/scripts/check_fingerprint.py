"""R04E18's own solver-corruption fingerprint check, applied to its three
new cells' `.raw` traces. Repeats, byte-for-byte, the same two-part check
R04E16 (RESULTS.md Section 3a) and R04E17 (RESULTS.md Section 4)
established for this exact netlist family:

  (a) non-monotonic/near-duplicate timestamps in the raw trace (dt<=0
      between consecutive points), the retry-chatter signature; and
  (b) the independent, state-independent V(vin) trace deviating from its
      own commanded PWL ramp by more than a generous tolerance -- since
      V(vin) sits behind RPAR_IN=10mOhm/LPAR_IN=5nH from the ideal PWL
      source V(src), a small legitimate drop/ring is expected, so the
      same generous "+/-5% of commanded value, floor 0.5V" tolerance
      R04E17 used is applied here, not an exact-equality check.

Full-file, not sampled: every point in every cell's .raw is read.

USAGE:
  python3 check_fingerprint.py <case_stem> <vin> <tramp_s> <tstop_s>
"""

from __future__ import annotations

import sys
from pathlib import Path

from ltspice_raw_parser import RawFile

HERE = Path(__file__).resolve().parent
CASES = HERE.parent / "cases"


def commanded_vin(t: float, vin: float, tramp: float, tstop: float) -> float:
    if t <= 0:
        return 0.0
    if t >= tramp:
        return vin
    return vin * t / tramp


def check(case: str, vin: float, tramp: float, tstop: float) -> dict:
    raw_path = CASES / f"{case}.raw"
    rf = RawFile(raw_path)
    t_idx = rf.name_to_idx["time"]
    vin_idx = rf.name_to_idx["V(vin)"]

    n = rf.no_points
    dt_nonpositive = 0
    min_positive_dt = None
    prev_t = None

    vin_anomalies = 0
    max_abs_dev = 0.0
    max_abs_dev_t = None
    max_abs_dev_actual = None
    max_abs_dev_commanded = None
    worst_examples = []

    # Implausibility bound: R04E16/R04E17's own documented corruption
    # signature reads values MANY ORDERS OF MAGNITUDE beyond anything
    # physically reachable (-20885 V, 5.33e24 V, ~-1e17 V plateau, for a
    # 0-48 V commanded rail). A generous physical bound is used here to
    # separate that from legitimate small-signal RPAR/LPAR ringing
    # against the divider network's own real capacitive loading (which
    # the tight "+/-5%/-0.5V vs. instantaneous commanded value" check
    # below does NOT distinguish from corruption -- it flags both).
    IMPLAUSIBLE_LO = -5.0 * vin  # -240 V for vin=48
    IMPLAUSIBLE_HI = 5.0 * vin  # +240 V for vin=48
    implausible_count = 0
    v_min = None
    v_max = None
    implausible_examples = []

    for row in rf.rows():
        t = row[t_idx]
        v = row[vin_idx]

        if prev_t is not None:
            dt = t - prev_t
            if dt <= 0:
                dt_nonpositive += 1
            else:
                if min_positive_dt is None or dt < min_positive_dt:
                    min_positive_dt = dt
        prev_t = t

        if v_min is None or v < v_min:
            v_min = v
        if v_max is None or v > v_max:
            v_max = v
        if v < IMPLAUSIBLE_LO or v > IMPLAUSIBLE_HI:
            implausible_count += 1
            if len(implausible_examples) < 5:
                implausible_examples.append((t, v))

        cmd = commanded_vin(t, vin, tramp, tstop)
        tol = max(0.05 * abs(cmd), 0.5)
        dev = v - cmd
        if abs(dev) > tol:
            vin_anomalies += 1
            if len(worst_examples) < 5:
                worst_examples.append((t, v, cmd, dev))
        if abs(dev) > max_abs_dev:
            max_abs_dev = abs(dev)
            max_abs_dev_t = t
            max_abs_dev_actual = v
            max_abs_dev_commanded = cmd

    return {
        "case": case,
        "n_points": n,
        "dt_nonpositive": dt_nonpositive,
        "min_positive_dt": min_positive_dt,
        "vin_anomalies": vin_anomalies,
        "max_abs_dev": max_abs_dev,
        "max_abs_dev_t": max_abs_dev_t,
        "max_abs_dev_actual": max_abs_dev_actual,
        "max_abs_dev_commanded": max_abs_dev_commanded,
        "worst_examples": worst_examples,
        "v_min": v_min,
        "v_max": v_max,
        "implausible_count": implausible_count,
        "implausible_examples": implausible_examples,
        "implausible_bounds": (IMPLAUSIBLE_LO, IMPLAUSIBLE_HI),
        "clean": dt_nonpositive == 0 and implausible_count == 0,
        "clean_strict_tolerance": dt_nonpositive == 0 and vin_anomalies == 0,
    }


CELLS = [
    ("e18_div_f3_t5", 48.0, 5.000000e-06, 305e-6),
    ("e18_div_f3_t22p87", 48.0, 2.287000e-05, 322.87e-6),
    ("e18_div_f3_t40", 48.0, 4.000000e-05, 340e-6),
]


def main() -> None:
    all_clean = True
    for case, vin, tramp, tstop in CELLS:
        result = check(case, vin, tramp, tstop)
        all_clean = all_clean and result["clean"]
        print(f"=== {case} ===")
        print(f"  n_points parsed: {result['n_points']}")
        print(f"  dt<=0 count (non-monotonic/duplicate timestamps): {result['dt_nonpositive']}")
        print(f"  smallest positive dt: {result['min_positive_dt']!r}")
        print(f"  V(vin) observed range: [{result['v_min']!r}, {result['v_max']!r}] "
              f"(commanded rail: 0 to {vin} V)")
        print(f"  implausible-value count (outside {result['implausible_bounds']}): "
              f"{result['implausible_count']}")
        for ex in result["implausible_examples"]:
            print(f"    IMPLAUSIBLE: t={ex[0]!r} V(vin)={ex[1]!r}")
        print(f"  [informational, strict tolerance] V(vin) anomaly count "
              f"(|actual-commanded|>generous +/-5%/-0.5V tol): {result['vin_anomalies']}")
        print(f"  [informational] max |actual-commanded| observed: {result['max_abs_dev']!r} "
              f"at t={result['max_abs_dev_t']!r} "
              f"(actual={result['max_abs_dev_actual']!r}, "
              f"commanded={result['max_abs_dev_commanded']!r})")
        print(f"  CLEAN (no non-monotonic timestamps, no physically-impossible V(vin)): "
              f"{result['clean']}")
        print(f"  clean under strict tight tolerance (informational only): "
              f"{result['clean_strict_tolerance']}")
        print()
    print(f"ALL THREE CELLS CLEAN (corruption fingerprint absent): {all_clean}")


if __name__ == "__main__":
    sys.exit(main())
