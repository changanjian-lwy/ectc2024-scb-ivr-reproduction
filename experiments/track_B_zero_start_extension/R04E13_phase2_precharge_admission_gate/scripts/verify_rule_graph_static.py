"""Independent, run-INDEPENDENT structural verification of
build_r04e13_cases.py's own generated `.rule` graph, for all 5 grid cells,
done BEFORE trusting any LTspice run's raw-trace pilot check.

Checks, purely from the `(order, charge_role, free_role, rules)` the
generator produces (no LTspice, no .raw file):
  1. State codes are contiguous 0..N-1, no gaps/duplicates.
  2. Every declared state has EXACTLY ONE outgoing `.rule` (this project's
     own single-rule-per-state discipline, R04E12 RESULTS.md Section 1).
  3. Every rule's target is itself a declared state.
  4. charge-role codes are all even, free-role codes are all odd, and the
     two sets partition all codes exactly (the parity property the shared
     `timer`/`timer_chg` bucket-boolean generalization depends on).
  5. Simulating the DETERMINISTIC walk from state 0 (following rule
     targets only, ignoring the electrical trigger conditions -- valid
     because out-degree is exactly 1 everywhere, so the walk is uniquely
     determined) for many steps confirms: every PCHG1_k/PFREE1_k,
     PCHG2_k/PFREE2_k, and (when N2_PRECHARGE>1) CHARGE1_ADMIT/
     FREE1_ADMIT/CHARGE2_ADMIT/FREE2_ADMIT state is visited AT MOST ONCE
     ever, and the walk converges to the intended closed 8-state loop
     (CHARGE1/FREE1/CHARGE2/FREE2/CHARGE3/FREE3/CHARGE4/FREE4) forever
     after.

This is what lets RESULTS.md attribute the N2_PRECHARGE=5/10 raw-trace
pilot-check anomaly (verify_precharge_gate2.py) to the ALREADY-DIAGNOSED
R04E10/R04E11 solver retry/chatter artifact rather than a genuine
`.rule`-graph defect: this script proves the graph itself is correct,
independent of any specific LTspice run's solver behavior.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_r04e13_cases import CELLS, build_state_plan


def check_cell(n1: int, n2: int, walk_steps: int = 200) -> bool:
    order, charge_role, free_role, rules = build_state_plan(n1, n2)
    codes = [c for _, c in order]
    names = [nm for nm, _ in order]
    ok = True

    if codes != list(range(len(codes))):
        print(f"  FAIL: non-contiguous codes: {codes}")
        ok = False
    if len(set(names)) != len(names):
        print(f"  FAIL: duplicate state name in {names}")
        ok = False

    froms = [f for f, _, _ in rules]
    if len(set(froms)) != len(froms):
        dupes = [n for n, c in Counter(froms).items() if c > 1]
        print(f"  FAIL: state(s) with more than one outgoing rule: {dupes}")
        ok = False
    if set(froms) != set(names):
        missing = set(names) - set(froms)
        extra = set(froms) - set(names)
        if missing:
            print(f"  FAIL: state(s) with NO outgoing rule: {missing}")
            ok = False
        if extra:
            print(f"  FAIL: rule(s) FROM an undeclared state: {extra}")
            ok = False

    targets = [t for _, t, _ in rules]
    bad_targets = [t for t in targets if t not in names]
    if bad_targets:
        print(f"  FAIL: rule target(s) not a declared state: {bad_targets}")
        ok = False

    name_to_code = {nm: c for nm, c in order}
    charge_codes = sorted(name_to_code[nm] for nm in charge_role)
    free_codes = sorted(name_to_code[nm] for nm in free_role)
    if not all(c % 2 == 0 for c in charge_codes):
        print(f"  FAIL: charge-role code(s) not even: {charge_codes}")
        ok = False
    if not all(c % 2 == 1 for c in free_codes):
        print(f"  FAIL: free-role code(s) not odd: {free_codes}")
        ok = False
    if set(charge_codes) | set(free_codes) != set(codes):
        print("  FAIL: charge/free role codes do not partition all codes")
        ok = False

    if not ok:
        return False

    # Deterministic walk simulation.
    target_of = {f: t for f, t, _ in rules}
    seq = []
    cur = names[0]
    for _ in range(walk_steps):
        seq.append(cur)
        cur = target_of[cur]
    cnt = Counter(seq)
    recurring = {nm for nm, c in cnt.items() if c > 1}
    once_only = {nm for nm, c in cnt.items() if c == 1}

    bad_recurring = [nm for nm in recurring
                     if nm.startswith("PCHG") or nm.startswith("PFREE")
                     or nm.endswith("_ADMIT")]
    if bad_recurring:
        print(f"  FAIL: precharge/ADMIT state(s) recur in the walk: {bad_recurring}")
        ok = False

    expected_loop = {"CHARGE1", "FREE1", "CHARGE2", "FREE2",
                      "CHARGE3", "FREE3", "CHARGE4", "FREE4"}
    if recurring != expected_loop:
        print(f"  FAIL: walk's recurring set is not the expected 8-state loop: {recurring}")
        ok = False

    print(f"  once-only states: {sorted(once_only)}")
    print(f"  recurring (loop) states: {sorted(recurring)}")
    return ok


def main():
    overall = True
    for n1, n2 in CELLS:
        print(f"cell (N1_PRECHARGE={n1}, N2_PRECHARGE={n2}):")
        cell_ok = check_cell(n1, n2)
        print(f"  -> {'PASS' if cell_ok else 'FAIL'}")
        overall = overall and cell_ok
    print(f"\nOVERALL (all {len(CELLS)} cells): {'PASS' if overall else 'FAIL'}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
