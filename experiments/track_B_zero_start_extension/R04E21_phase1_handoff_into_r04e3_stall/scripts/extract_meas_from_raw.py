"""Extract .meas-equivalent values directly from the .raw binary trace,
because the Step-1 re-run's own .log file (e17_div_f3_t68p61_plus_il1_at_
tstop.log) did not print .meas results (LTspice's own post-processing
step hit an "unable to open database file" condition, apparently after
the .raw trace was already fully flushed to disk -- the .raw file's own
point count, 8,208,737, matches R04E17's own already-published point
count for this exact cell exactly, confirming the underlying transient
data itself is intact and trustworthy).

Reproduces LTspice's own FIND ... AT <t> semantics (linear interpolation
between the two straddling stored time points) and MAX/MIN FROM 0 TO T
semantics, reading directly off the .raw trace via ltspice_raw_parser.py's
RawFile class (copied unchanged from R04E20's own reference script).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ltspice_raw_parser import RawFile  # noqa: E402


def find_at(rf: RawFile, colname: str, t_target: float, other_col: str | None = None):
    """Interpolated value of colname (optionally colname - other_col) at
    time t_target, matching LTspice's FIND ... AT semantics (linear
    interpolation in time between the two stored points straddling
    t_target)."""
    tidx = rf.name_to_idx["time"]
    cidx = rf.name_to_idx[colname]
    oidx = rf.name_to_idx[other_col] if other_col else None

    prev_row = None
    for row in rf.rows():
        t = row[tidx]
        if t >= t_target:
            if prev_row is None:
                v = row[cidx] - (row[oidx] if oidx is not None else 0.0)
                return v, t
            t0, t1 = prev_row[tidx], t
            v0 = prev_row[cidx] - (prev_row[oidx] if oidx is not None else 0.0)
            v1 = row[cidx] - (row[oidx] if oidx is not None else 0.0)
            if t1 == t0:
                return v1, t1
            frac = (t_target - t0) / (t1 - t0)
            return v0 + frac * (v1 - v0), t_target
        prev_row = row
    # target beyond last point
    t = prev_row[tidx]
    v = prev_row[cidx] - (prev_row[oidx] if oidx is not None else 0.0)
    return v, t


def max_min_from_to(rf: RawFile, colname: str, t_from: float, t_to: float):
    tidx = rf.name_to_idx["time"]
    cidx = rf.name_to_idx[colname]
    vmax = None
    vmin = None
    for row in rf.rows():
        t = row[tidx]
        if t < t_from:
            continue
        if t > t_to:
            break
        v = row[cidx]
        if vmax is None or v > vmax:
            vmax = v
        if vmin is None or v < vmin:
            vmin = v
    return vmax, vmin


def main():
    raw_path = Path(sys.argv[1])
    rf = RawFile(raw_path)

    TRAMP = 6.861000e-05
    TSTOP = TRAMP + 300e-6
    TSTOP_M1N = TSTOP - 1e-9

    print(f"no_points={rf.no_points}")
    print(f"TRAMP={TRAMP!r} TSTOP={TSTOP!r} TSTOP-1n={TSTOP_M1N!r}")

    vc1_final, t1 = find_at(rf, "V(a1)", TSTOP_M1N, other_col="V(x1)")
    vc2_final, t2 = find_at(rf, "V(a2)", TSTOP_M1N, other_col="V(x2)")
    vc3_final, t3 = find_at(rf, "V(a3)", TSTOP_M1N, other_col="V(x3)")
    vout_final, t4 = find_at(rf, "V(out)", TSTOP_M1N)
    print(f"VC1_FINAL={vc1_final!r} (at t={t1!r})")
    print(f"VC2_FINAL={vc2_final!r} (at t={t2!r})")
    print(f"VC3_FINAL={vc3_final!r} (at t={t3!r})")
    print(f"VOUT_FINAL={vout_final!r} (at t={t4!r})")

    vc1_tramp, _ = find_at(rf, "V(a1)", TRAMP, other_col="V(x1)")
    vc2_tramp, _ = find_at(rf, "V(a2)", TRAMP, other_col="V(x2)")
    vc3_tramp, _ = find_at(rf, "V(a3)", TRAMP, other_col="V(x3)")
    vout_tramp, _ = find_at(rf, "V(out)", TRAMP)
    print(f"VC1_AT_TRAMP={vc1_tramp!r}")
    print(f"VC2_AT_TRAMP={vc2_tramp!r}")
    print(f"VC3_AT_TRAMP={vc3_tramp!r}")
    print(f"VOUT_AT_TRAMP={vout_tramp!r}")

    il1_max, il1_min = max_min_from_to(rf, "I(L1)", 0.0, TSTOP)
    il2_max, il2_min = max_min_from_to(rf, "I(L2)", 0.0, TSTOP)
    il3_max, il3_min = max_min_from_to(rf, "I(L3)", 0.0, TSTOP)
    il4_max, il4_min = max_min_from_to(rf, "I(L4)", 0.0, TSTOP)
    print(f"IL1_MAX={il1_max!r} IL1_MIN={il1_min!r}")
    print(f"IL2_MAX={il2_max!r} IL2_MIN={il2_min!r}")
    print(f"IL3_MAX={il3_max!r} IL3_MIN={il3_min!r}")
    print(f"IL4_MAX={il4_max!r} IL4_MIN={il4_min!r}")

    vout_pk, vout_min = max_min_from_to(rf, "V(out)", 0.0, TSTOP)
    print(f"VOUT_PK={vout_pk!r} VOUT_MIN={vout_min!r}")

    il1_at_tstop, tprobe = find_at(rf, "I(L1)", TSTOP)
    print(f"IL1_AT_TSTOP={il1_at_tstop!r} (at t={tprobe!r}, target=368.61u)")


if __name__ == "__main__":
    main()
