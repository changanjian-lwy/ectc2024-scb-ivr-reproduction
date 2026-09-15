"""Count settled-state dwell reversals in an R04E12 cell's .raw file,
generalizing R04E11's own `state_sequence.py` reversal count to this
experiment's per-cell-shifted state numbering (R04E11's own script
hardcodes the "settled state 7 -> 0" wraparound test, which is only
correct for R04E10's original 0..7 numbering; here the real round-robin's
wraparound is FREE4 -> CHARGE1, at codes (S0+7) -> S0, where S0 =
2*(N_PRECHARGE-1) depends on the cell). Used to check for a recurrence of
R04E10/R04E11's own diagnosed retry/chatter dynamic (BOUNDARY.md Section
1), reported honestly per BOUNDARY.md Section 9, not silently worked
around.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ltspice_raw_parser import RawFile
from verify_precharge_gate import state_names_for


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw_file", type=Path)
    ap.add_argument("n_precharge", type=int)
    ap.add_argument("--tol", type=float, default=0.01)
    args = ap.parse_args()

    names = state_names_for(args.n_precharge)
    code_of = {v: k for k, v in names.items()}
    s0 = code_of["CHARGE1"]
    free4_code = code_of["FREE4"]

    rf = RawFile(args.raw_file)
    tidx = rf.name_to_idx["time"]
    sidx = rf.name_to_idx["V(state_mon)"]

    last_settled = None
    dwell_seq = []
    for row in rf.rows():
        t = row[tidx]
        s = row[sidx]
        near = round(s)
        if abs(s - near) < args.tol and 0 <= near < len(names):
            if last_settled is None or near != last_settled:
                dwell_seq.append((t, near))
                last_settled = near

    reversals = 0
    reversal_events = []
    for (t_prev, prev), (t_next, nxt) in zip(dwell_seq, dwell_seq[1:]):
        is_wraparound = (prev == free4_code and nxt == s0)
        if nxt < prev and not is_wraparound:
            reversals += 1
            reversal_events.append((t_next, names[prev], names[nxt]))

    print(f"# N_PRECHARGE={args.n_precharge}: total settled dwell "
          f"transitions={len(dwell_seq)}, reversals={reversals} "
          f"({100.0*reversals/max(1,len(dwell_seq)-1):.1f}% of transitions)")
    if reversal_events:
        print("# first 10 reversal events:")
        for t, a, b in reversal_events[:10]:
            print(f"#   t={t!r}  {a} -> {b}")


if __name__ == "__main__":
    main()
