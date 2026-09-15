"""Pilot verification required by BOUNDARY.md Section 5: directly inspect
V(state_mon)'s settled dwell sequence (reusing R04E11's own
`ltspice_raw_parser.py`/the dwell-extraction technique from its
`state_sequence.py`) for a given N_PRECHARGE cell's .raw file, and confirm
that the machine visits each precharge-mirror state pair (PCHG1_k/PFREE1_k,
k=1..N_PRECHARGE-1) EXACTLY ONCE, in strictly increasing k order, before
ever reaching the real CHARGE1/FREE1 states -- i.e. FREE1 (via its
PFREE1_k mirrors) returns to a CHARGE1-role state exactly N_PRECHARGE-1
times before the N_PRECHARGE-th completion routes to CHARGE2 and the
machine joins the permanent round-robin, per BOUNDARY.md Section 2/5's
exact requirement. Also reports whether the precharge chain is ever
RE-ENTERED after the machine first reaches CHARGE2 or later (it must not
be -- the gate is a one-time admission condition).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ltspice_raw_parser import RawFile

# Mirrors build_r04e12_cases.py's own state_plan exactly (kept in sync by
# hand since this is a small, independently-checkable verification script,
# deliberately NOT importing build_r04e12_cases.py's generator so that a
# bug in the generator cannot silently also corrupt the verifier).


def state_names_for(n_precharge: int) -> dict[int, str]:
    names = {}
    code = 0
    for k in range(1, n_precharge):  # n_precharge-1 extra pairs
        names[code] = f"PCHG1_{k}"; code += 1
        names[code] = f"PFREE1_{k}"; code += 1
    for nm in ["CHARGE1", "FREE1", "CHARGE2", "FREE2",
               "CHARGE3", "FREE3", "CHARGE4", "FREE4"]:
        names[code] = nm
        code += 1
    return names


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw_file", type=Path)
    ap.add_argument("n_precharge", type=int)
    ap.add_argument("--tol", type=float, default=0.01)
    args = ap.parse_args()

    names = state_names_for(args.n_precharge)
    rf = RawFile(args.raw_file)
    tidx = rf.name_to_idx["time"]
    sidx = rf.name_to_idx["V(state_mon)"]

    last_settled = None
    dwell_seq = []  # (time, code, name)
    for i, row in enumerate(rf.rows()):
        t = row[tidx]
        s = row[sidx]
        near = round(s)
        if abs(s - near) < args.tol and 0 <= near < len(names):
            if last_settled is None or near != last_settled:
                dwell_seq.append((t, near, names[near]))
                last_settled = near

    print(f"# N_PRECHARGE={args.n_precharge}, n_states={len(names)}, "
          f"total settled dwell transitions={len(dwell_seq)}")
    print("# state code -> name map:", names)
    print("\n# full settled-dwell sequence:")
    for t, code, nm in dwell_seq:
        print(f"t={t!r}\tcode={code}\tname={nm}")

    # --- Verification 1: the FIRST admission pass visits every precharge
    # pair exactly once, in strictly increasing k order, before the real
    # CHARGE1.
    expected_prefix = []
    for k in range(1, args.n_precharge):
        expected_prefix.append(f"PCHG1_{k}")
        expected_prefix.append(f"PFREE1_{k}")
    expected_prefix.append("CHARGE1")

    actual_prefix = [nm for _, _, nm in dwell_seq[: len(expected_prefix)]]
    prefix_ok = actual_prefix == expected_prefix
    print(f"\n# VERIFICATION 1 (precharge admission order): "
          f"{'PASS' if prefix_ok else 'FAIL'}")
    print(f"#   expected: {expected_prefix}")
    print(f"#   actual:   {actual_prefix}")

    # --- Verification 2: the precharge chain (any PCHG1_*/PFREE1_* name)
    # is never visited again after the first real CHARGE2 dwell (one-time
    # admission gate, never re-triggers).
    first_charge2_idx = None
    for idx, (_, _, nm) in enumerate(dwell_seq):
        if nm == "CHARGE2":
            first_charge2_idx = idx
            break
    reentries = []
    if first_charge2_idx is not None:
        for t, code, nm in dwell_seq[first_charge2_idx + 1:]:
            if nm.startswith("PCHG1_") or nm.startswith("PFREE1_"):
                reentries.append((t, code, nm))
    gate_never_retriggers = len(reentries) == 0
    print(f"\n# VERIFICATION 2 (gate never re-triggers after first CHARGE2): "
          f"{'PASS' if gate_never_retriggers else 'FAIL'}")
    if reentries:
        print(f"#   re-entries found: {reentries[:20]}")

    # --- Verification 3: exact count of precharge-role dwells matches
    # N_PRECHARGE-1 pairs (2*(N-1) dwells) before the real CHARGE1.
    n_precharge_dwells = sum(
        1 for _, _, nm in dwell_seq if nm.startswith("PCHG1_") or nm.startswith("PFREE1_")
    )
    expected_n_precharge_dwells = 2 * (args.n_precharge - 1)
    count_ok = n_precharge_dwells == expected_n_precharge_dwells
    print(f"\n# VERIFICATION 3 (precharge dwell count): "
          f"{'PASS' if count_ok else 'FAIL'} "
          f"(expected {expected_n_precharge_dwells}, got {n_precharge_dwells})")

    overall = prefix_ok and gate_never_retriggers and count_ok
    print(f"\n# OVERALL: {'PASS' if overall else 'FAIL'}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
