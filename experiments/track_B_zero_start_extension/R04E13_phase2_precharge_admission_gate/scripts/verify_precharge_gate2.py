"""Pilot verification required by BOUNDARY.md Section 5: directly inspect
V(state_mon)'s settled dwell sequence (reusing R04E12/R04E11's own
`ltspice_raw_parser.py` unchanged) for a given (N1_PRECHARGE, N2_PRECHARGE)
cell's .raw file, and confirm the phase-2 precharge gate stacked on top of
phase 1's own (BOUNDARY.md Section 2/5) does exactly what is specified:

  1. The machine visits every phase-2 precharge pair (PCHG2_k/PFREE2_k,
     k=1..N2_PRECHARGE-1) exactly once, in strictly increasing k order,
     STRICTLY AFTER phase 1's own precharge chain completes and the real
     CHARGE2 is first reached, and STRICTLY BEFORE the real CHARGE3.
  2. The phase-2 precharge chain is never re-entered after the machine's
     first arrival at the real CHARGE3 (one-time admission gate, same as
     phase 1's own).
  3. The exact count of phase-2-precharge-role dwells equals
     2*(N2_PRECHARGE-1).

Also generalizes R04E12's own verify_precharge_gate.py phase-1 checks
(admission order/one-time-gating/dwell count) so a single script confirms
BOTH stacked gates in one pass, generalized to this experiment's combined
(N1,N2) state-numbering (see build_r04e13_cases.py's own state_plan,
mirrored here by hand -- deliberately NOT importing the generator, same
independent-double-check reasoning R04E12's own verify script used).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ltspice_raw_parser import RawFile


def state_names_for(n1_precharge: int, n2_precharge: int) -> dict[int, str]:
    """Mirrors build_r04e13_cases.py's own build_state_plan exactly,
    INCLUDING the ADMIT/LOOP duplication its own module docstring documents
    as a necessary design correction whenever N2_PRECHARGE>1 (a naive
    single-shared-loop generalization of R04E12's phase-1 pattern was tried
    first and FAILED this very verification script's own check 2, which is
    exactly why the ADMIT states exist -- kept in sync by hand deliberately,
    same independent-double-check reasoning R04E12's own verify script
    used, so a bug in the generator cannot also silently corrupt this
    checker)."""
    names = {}
    code = 0
    for k in range(1, n1_precharge):
        names[code] = f"PCHG1_{k}"; code += 1
        names[code] = f"PFREE1_{k}"; code += 1
    if n2_precharge == 1:
        for nm in ["CHARGE1", "FREE1", "CHARGE2", "FREE2",
                   "CHARGE3", "FREE3", "CHARGE4", "FREE4"]:
            names[code] = nm; code += 1
        return names
    names[code] = "CHARGE1_ADMIT"; code += 1
    names[code] = "FREE1_ADMIT"; code += 1
    names[code] = "CHARGE2_ADMIT"; code += 1
    names[code] = "FREE2_ADMIT"; code += 1
    for k in range(1, n2_precharge):
        names[code] = f"PCHG2_{k}"; code += 1
        names[code] = f"PFREE2_{k}"; code += 1
    for nm in ["CHARGE3", "FREE3", "CHARGE4", "FREE4",
               "CHARGE1", "FREE1", "CHARGE2", "FREE2"]:
        names[code] = nm; code += 1
    return names


def dwell_sequence(raw_file: Path, names: dict[int, str], tol: float):
    rf = RawFile(raw_file)
    tidx = rf.name_to_idx["time"]
    sidx = rf.name_to_idx["V(state_mon)"]

    last_settled = None
    dwell_seq = []
    for row in rf.rows():
        t = row[tidx]
        s = row[sidx]
        near = round(s)
        if abs(s - near) < tol and 0 <= near < len(names):
            if last_settled is None or near != last_settled:
                dwell_seq.append((t, near, names[near]))
                last_settled = near
    return dwell_seq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw_file", type=Path)
    ap.add_argument("n1_precharge", type=int)
    ap.add_argument("n2_precharge", type=int)
    ap.add_argument("--tol", type=float, default=0.01)
    args = ap.parse_args()

    names = state_names_for(args.n1_precharge, args.n2_precharge)
    dwell_seq = dwell_sequence(args.raw_file, names, args.tol)

    print(f"# N1_PRECHARGE={args.n1_precharge}, N2_PRECHARGE={args.n2_precharge}, "
          f"n_states={len(names)}, total settled dwell transitions={len(dwell_seq)}")
    print("# state code -> name map:", names)
    print("\n# full settled-dwell sequence:")
    for t, code, nm in dwell_seq:
        print(f"t={t!r}\tcode={code}\tname={nm}")

    all_names_seq = [nm for _, _, nm in dwell_seq]

    # --- PHASE-1 CHECKS (generalized from R04E12's own verify script) ---
    # The state the phase-1 mirror chain feeds into is "CHARGE1" when
    # N2_PRECHARGE==1 (R04E12's own construct, unmodified), or
    # "CHARGE1_ADMIT" when N2_PRECHARGE>1 (this experiment's own ADMIT
    # duplication, see build_r04e13_cases.py module docstring).
    p1_target = "CHARGE1" if args.n2_precharge == 1 else "CHARGE1_ADMIT"
    expected_p1_prefix = []
    for k in range(1, args.n1_precharge):
        expected_p1_prefix.append(f"PCHG1_{k}")
        expected_p1_prefix.append(f"PFREE1_{k}")
    expected_p1_prefix.append(p1_target)
    actual_p1_prefix = all_names_seq[: len(expected_p1_prefix)]
    p1_prefix_ok = actual_p1_prefix == expected_p1_prefix
    print(f"\n# PHASE-1 CHECK 1 (precharge admission order, before {p1_target}): "
          f"{'PASS' if p1_prefix_ok else 'FAIL'}")
    print(f"#   expected: {expected_p1_prefix}")
    print(f"#   actual:   {actual_p1_prefix}")

    # No PCHG1_k/PFREE1_k dwell should EVER occur outside that exact
    # leading prefix (they must never recur, anywhere, at any later index).
    rest_after_p1_prefix = all_names_seq[len(expected_p1_prefix):]
    p1_reentries = [nm for nm in rest_after_p1_prefix
                    if nm.startswith("PCHG1_") or nm.startswith("PFREE1_")]
    p1_never_retriggers = len(p1_reentries) == 0
    print(f"\n# PHASE-1 CHECK 2 (phase-1 mirror chain never re-triggers after "
          f"the leading prefix): {'PASS' if p1_never_retriggers else 'FAIL'}")
    if p1_reentries:
        print(f"#   re-entries found: {p1_reentries[:20]}")

    n_p1_dwells = sum(1 for nm in all_names_seq if nm.startswith("PCHG1_") or nm.startswith("PFREE1_"))
    expected_n_p1_dwells = 2 * (args.n1_precharge - 1)
    p1_count_ok = n_p1_dwells == expected_n_p1_dwells
    print(f"\n# PHASE-1 CHECK 3 (precharge dwell count): "
          f"{'PASS' if p1_count_ok else 'FAIL'} "
          f"(expected {expected_n_p1_dwells}, got {n_p1_dwells})")

    # --- PHASE-2 CHECKS (this experiment's own new construct) ---
    if args.n2_precharge == 1:
        # No phase-2 gate at all -- trivially satisfied (R04E12-equivalent
        # construct, nothing further to verify here).
        p2_order_ok = True
        expected_p2_segment: list[str] = []
        actual_p2_segment: list[str] = []
        p2_never_retriggers = True
        print("\n# PHASE-2 CHECK 1/2/3: N/A (N2_PRECHARGE=1, no phase-2 gate) -- PASS (trivial)")
    else:
        # Verification 1: every phase-2 precharge pair visited exactly
        # once, in strictly increasing k order, strictly AFTER the "real"
        # (ADMIT-copy) CHARGE2/FREE2 is first reached, and strictly BEFORE
        # the real (loop) CHARGE3.
        first_charge2_admit_idx = next((i for i, nm in enumerate(all_names_seq) if nm == "CHARGE2_ADMIT"), None)
        first_charge3_idx = next((i for i, nm in enumerate(all_names_seq) if nm == "CHARGE3"), None)

        p2_order_ok = False
        actual_p2_segment = None
        expected_p2_segment = []
        for k in range(1, args.n2_precharge):
            expected_p2_segment.append(f"PCHG2_{k}")
            expected_p2_segment.append(f"PFREE2_{k}")
        if first_charge2_admit_idx is not None and first_charge3_idx is not None:
            segment = all_names_seq[first_charge2_admit_idx: first_charge3_idx]
            # segment should be ["CHARGE2_ADMIT", "FREE2_ADMIT", <mirror pairs...>]
            if len(segment) >= 2 and segment[0] == "CHARGE2_ADMIT" and segment[1] == "FREE2_ADMIT":
                actual_p2_segment = segment[2:]
                p2_order_ok = actual_p2_segment == expected_p2_segment
        print(f"\n# PHASE-2 CHECK 1 (precharge admission order, after real "
              f"CHARGE2_ADMIT/FREE2_ADMIT, before real CHARGE3): "
              f"{'PASS' if p2_order_ok else 'FAIL'}")
        print(f"#   expected segment after CHARGE2_ADMIT/FREE2_ADMIT: {expected_p2_segment}")
        print(f"#   actual segment after CHARGE2_ADMIT/FREE2_ADMIT:   {actual_p2_segment}")

        # Verification 2: the phase-2 mirror chain never re-triggers after
        # the machine's first arrival at the real (loop) CHARGE3 -- in
        # fact, per the ADMIT-copy construction, PCHG2_k/PFREE2_k/
        # CHARGE2_ADMIT/FREE2_ADMIT/CHARGE1_ADMIT/FREE1_ADMIT should NEVER
        # appear again anywhere after that first CHARGE3 arrival.
        p2_reentries = []
        if first_charge3_idx is not None:
            for t, code, nm in dwell_seq[first_charge3_idx + 1:]:
                if (nm.startswith("PCHG2_") or nm.startswith("PFREE2_")
                        or nm in ("CHARGE1_ADMIT", "FREE1_ADMIT", "CHARGE2_ADMIT", "FREE2_ADMIT")):
                    p2_reentries.append((t, code, nm))
        p2_never_retriggers = len(p2_reentries) == 0
        print(f"\n# PHASE-2 CHECK 2 (gate/ADMIT states never re-triggers after "
              f"first CHARGE3): {'PASS' if p2_never_retriggers else 'FAIL'}")
        if p2_reentries:
            print(f"#   re-entries found: {p2_reentries[:20]}")

    # Verification 3: exact count of phase-2-precharge-role dwells equals
    # 2*(N2_PRECHARGE-1).
    n_p2_dwells = sum(1 for nm in all_names_seq if nm.startswith("PCHG2_") or nm.startswith("PFREE2_"))
    expected_n_p2_dwells = 2 * (args.n2_precharge - 1)
    p2_count_ok = n_p2_dwells == expected_n_p2_dwells
    print(f"\n# PHASE-2 CHECK 3 (precharge dwell count): "
          f"{'PASS' if p2_count_ok else 'FAIL'} "
          f"(expected {expected_n_p2_dwells}, got {n_p2_dwells})")

    overall = (p1_prefix_ok and p1_never_retriggers and p1_count_ok and
               p2_order_ok and p2_never_retriggers and p2_count_ok)
    print(f"\n# OVERALL: {'PASS' if overall else 'FAIL'}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
