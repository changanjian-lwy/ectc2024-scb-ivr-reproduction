"""Generate R04E13's phase-2-precharge-stacked-on-phase-1 cells, parented on
R04E10's own committed I_LIMIT=60A/T_CHARGE_MAX=50ns cell
(../../R04E10_timeout_gated_multi_rotation_bootstrap/cases/
r04e10_ilimit_60a_tchg_50ns.cir), per BOUNDARY.md Section 2/4.

This generalizes R04E12's own `build_r04e12_cases.py` (phase-1-only
precharge gate) to TWO stacked gates: phase 1's own (N1_PRECHARGE, reused
UNCHANGED construct/values from R04E12) and a new, analogous phase-2 gate
(N2_PRECHARGE, this experiment's own addition). Same "every `.machine`
state has exactly one outgoing `.rule`" discipline as every prior
experiment in this lineage (R04E5-R04E12), reused for the identical reason
R04E12's own RESULTS.md Section 1 documented.

======================================================================
IMPORTANT DESIGN FINDING, discovered and corrected DURING this
experiment's own build (documented here in full, not silently patched
over, per this project's own honest-reporting convention):
======================================================================

A first implementation attempt tried to naively generalize R04E12's own
phase-1 pattern by hanging the phase-2 mirror chain directly off the
REAL, SHARED `FREE2` state's single outgoing rule (i.e. `.rule FREE2
PCHG2_1 ...` instead of `.rule FREE2 CHARGE3 ...`). Direct raw-trace
verification (`verify_precharge_gate2.py`) caught this immediately: the
phase-2 mirror chain re-triggered on EVERY subsequent round-robin
rotation, not just once, because `FREE2` is itself part of the closed
round-robin CYCLE (entered every rotation via `CHARGE2`, which is entered
via `FREE1`, which is entered via `CHARGE1`, which is entered every
rotation via `FREE4`). In a `.machine` where every state has EXACTLY ONE
outgoing rule (a deterministic function on states, i.e. every state's own
next-state is fixed and does not depend on how that state was reached),
ANY state reachable from a cyclic state is ALSO on that same cycle
forever -- there is no way for a state's single, static rule to behave
differently on its "first" visit vs. its "later" visits. This is exactly
why R04E12's OWN phase-1 gate worked without this problem: its mirror
chain is placed strictly BEFORE `CHARGE1` ever joins the cycle (reachable
only via the machine's own one-time initial condition, never via any
`.rule`), so nothing inside the closed loop ever points back into it. A
gate positioned entirely INSIDE the loop (as phase 2's naturally is,
since `CHARGE2`/`FREE2` are round-robin members) cannot reuse that exact
trick unmodified.

FIX: whenever `N2_PRECHARGE>1`, this generator builds a dedicated,
ONE-TIME-ONLY "admission" copy of `CHARGE1`/`FREE1`/`CHARGE2`/`FREE2`
(named `CHARGE1_ADMIT`/`FREE1_ADMIT`/`CHARGE2_ADMIT`/`FREE2_ADMIT` --
electrically IDENTICAL mirrors of the real `CHARGE1`/`FREE1`/`CHARGE2`/
`FREE2`, same current-limit-OR-timeout / zero-crossing-OR-timeout rules),
positioned strictly BEFORE the closed round-robin loop, exactly as
phase 1's own mirror chain already is. The one-time walk is:
  [phase-1 mirror chain, if N1_PRECHARGE>1]
  -> CHARGE1_ADMIT -> FREE1_ADMIT -> CHARGE2_ADMIT -> FREE2_ADMIT
  -> [phase-2 mirror chain: PCHG2_k/PFREE2_k, k=1..N2_PRECHARGE-1]
  -> CHARGE3 (merges into the closed loop here)
and the closed, PERMANENT round-robin loop (entered exactly once, from
the tail above, and repeating forever after) is the ordinary 8-state
cycle using PLAIN names:
  CHARGE3 -> FREE3 -> CHARGE4 -> FREE4 -> CHARGE1 -> FREE1 -> CHARGE2 ->
  FREE2 -> CHARGE3 (cycle closes; NEITHER mirror chain, nor the `_ADMIT`
  states, is ever reachable from inside this cycle).
`CHARGE1_ADMIT`/`FREE1_ADMIT`/`CHARGE2_ADMIT`/`FREE2_ADMIT` are visited
EXACTLY ONCE in the entire run (the one-time walk from program start to
the first arrival at the loop's own `CHARGE3`), electrically identical to
the loop's own `CHARGE1`/`FREE1`/`CHARGE2`/`FREE2` (same gate drive, same
exit conditions) -- the duplication is a pure `.machine`-state-graph
necessity (to give the phase-2 branch point a private, acyclic history to
branch on), not a second physical circuit. This is a strictly stronger
requirement than phase 1's own construct needed, discovered directly by
running the naive generalization first and catching its failure via
BOUNDARY.md Section 5's own required pilot verification -- exactly the
kind of "isolated/naive generalization does not guarantee correctness"
lesson R04E10's own Section 1 (T_CHARGE_MAX=5ns cells) and R04E12's
Section 1 (single-rule-per-state discipline) already established for
this project; this is a further instance of the same lesson, caught here
by the same discipline (pilot-verify before trusting the grid), not
avoided by it.

When `N2_PRECHARGE==1` (no phase-2 gate at all), NONE of this `_ADMIT`
duplication is emitted -- the construct collapses EXACTLY to R04E12's own
single-shared-loop pattern (BOUNDARY.md Section 2's required identity:
`N1_PRECHARGE=X, N2_PRECHARGE=1` must be definitionally identical to
R04E12's own `N_PRECHARGE=X` cell), verified directly in RESULTS.md.

Because the whole extended state numbering still strictly alternates
charge-role (even code) / free-role (odd code) -- true because every
group (phase-1 mirrors, the four `_ADMIT` states, phase-2 mirrors, the
four shared tail states, the four loop-only states) is emitted as
consecutive (charge,free) pairs in that exact order -- the existing
per-machine-wide `timer`/`timer_chg` reset-gate construct generalizes the
same bucket-boolean way R04E12's own did, just with more OR-terms.
Verified directly by script (not assumed) below and in
verify_precharge_gate2.py.

gh1_cmd/gl1_cmd (phase 1's own gate drive) covers `CHARGE1`/`FREE1` (loop)
PLUS `CHARGE1_ADMIT`/`FREE1_ADMIT` (if emitted) PLUS every `PCHG1_k`/
`PFREE1_k` mirror. gh2_cmd/gl2_cmd (phase 2's own gate drive) covers
`CHARGE2`/`FREE2` (loop) PLUS `CHARGE2_ADMIT`/`FREE2_ADMIT` (if emitted)
PLUS every `PCHG2_k`/`PFREE2_k` mirror -- all of these physically command
the exact same phase-2 gate signal.
"""

from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPDIR = HERE.parent
CASES = EXPDIR / "cases"
R04E10_TEMPLATE = (
    EXPDIR.parent
    / "R04E10_timeout_gated_multi_rotation_bootstrap"
    / "cases"
    / "r04e10_ilimit_60a_tchg_50ns.cir"
)

# (N1_PRECHARGE, N2_PRECHARGE) cells to generate.
# (1,1)  -- identity check 1 (must match R04E10's own committed cell).
# (3,1)  -- identity check 2 / the N2_PRECHARGE=1 baseline of the main grid
#           (must match R04E12's own committed N_PRECHARGE=3 cell).
# (3,3), (3,5), (3,10) -- the rest of the main 4-cell grid (BOUNDARY.md
#           Section 4: N1_PRECHARGE=3 fixed, N2_PRECHARGE in {1,3,5,10}).
CELLS = [(1, 1), (3, 1), (3, 3), (3, 5), (3, 10)]

I_LIMIT = 60
T_CHARGE_MAX = 5.000000e-08
T_FREEWHEEL_MAX = 5.000000e-08

CHARGE1_COND = "(I(XMOD:L1)>=I_LIMIT) | (V(timer_chg)>=T_CHARGE_MAX)"
FREE1_COND = "(I(XMOD:L1)<=0) | (V(timer)>=T_FREEWHEEL_MAX)"
CHARGE2_COND = "(I(XMOD:L2)>=I_LIMIT) | (V(timer_chg)>=T_CHARGE_MAX)"
FREE2_COND = "(I(XMOD:L2)<=0) | (V(timer)>=T_FREEWHEEL_MAX)"
CHARGE3_COND = "(I(XMOD:L3)>=I_LIMIT) | (V(timer_chg)>=T_CHARGE_MAX)"
FREE3_COND = "(I(XMOD:L3)<=0) | (V(timer)>=T_FREEWHEEL_MAX)"
CHARGE4_COND = "(I(XMOD:L4)>=I_LIMIT) | (V(timer_chg)>=T_CHARGE_MAX)"
FREE4_COND = "(I(XMOD:L4)<=0) | (V(timer)>=T_FREEWHEEL_MAX)"


def bucket(v: int) -> str:
    # Same byte-identical-at-v==0 special case R04E12 used, for the same
    # reason (removes even a hypothetical solver-level-divergence risk in
    # this already solver-stiff family, per R04E11's own finding).
    if v == 0:
        return "(V(state_mon)<0.5)"
    return f"(V(state_mon)>{v - 0.5})&(V(state_mon)<{v + 0.5})"


def build_state_plan(n1_precharge: int, n2_precharge: int):
    """Returns (order, charge_role, free_role, rules) for a given
    (N1_PRECHARGE, N2_PRECHARGE) pair. See module docstring for the exact
    combined state order and the ADMIT/LOOP duplication this experiment's
    own pilot verification found necessary whenever N2_PRECHARGE>1."""
    order = []  # list of (name, code)
    code = 0
    charge_role = []
    free_role = []
    rules = []  # list of (from, to, cond)

    def add(name, role):
        nonlocal code
        order.append((name, code))
        (charge_role if role == "charge" else free_role).append(name)
        code += 1

    # --- Phase-1 precharge chain: mirror-then-real, R04E12's own
    # construction, reused verbatim (BOUNDARY.md Section 3: "reused
    # unchanged, not re-verified from scratch").
    n1_extra = n1_precharge - 1
    prev_free1_name = None
    for k in range(1, n1_extra + 1):
        cname, fname = f"PCHG1_{k}", f"PFREE1_{k}"
        add(cname, "charge")
        add(fname, "free")
        rules.append((cname, fname, CHARGE1_COND))
        if prev_free1_name is not None:
            rules.append((prev_free1_name, cname, FREE1_COND))
        prev_free1_name = fname

    if n2_precharge == 1:
        # No phase-2 gate at all: EXACT R04E12 construct (single shared
        # closed loop, no ADMIT/LOOP duplication needed or emitted).
        add("CHARGE1", "charge")
        add("FREE1", "free")
        add("CHARGE2", "charge")
        add("FREE2", "free")
        add("CHARGE3", "charge")
        add("FREE3", "free")
        add("CHARGE4", "charge")
        add("FREE4", "free")
        if prev_free1_name is not None:
            rules.append((prev_free1_name, "CHARGE1", FREE1_COND))
        rules.append(("CHARGE1", "FREE1", CHARGE1_COND))
        rules.append(("FREE1", "CHARGE2", FREE1_COND))
        rules.append(("CHARGE2", "FREE2", CHARGE2_COND))
        rules.append(("FREE2", "CHARGE3", FREE2_COND))
        rules.append(("CHARGE3", "FREE3", CHARGE3_COND))
        rules.append(("FREE3", "CHARGE4", FREE3_COND))
        rules.append(("CHARGE4", "FREE4", CHARGE4_COND))
        rules.append(("FREE4", "CHARGE1", FREE4_COND))
        return order, charge_role, free_role, rules

    # --- N2_PRECHARGE > 1: the phase-2 gate needs a dedicated, one-time-
    # only ADMIT copy of CHARGE1/FREE1/CHARGE2/FREE2 (see module docstring
    # for why this is necessary, not merely a stylistic choice).
    add("CHARGE1_ADMIT", "charge")
    add("FREE1_ADMIT", "free")
    add("CHARGE2_ADMIT", "charge")
    add("FREE2_ADMIT", "free")
    if prev_free1_name is not None:
        rules.append((prev_free1_name, "CHARGE1_ADMIT", FREE1_COND))
    rules.append(("CHARGE1_ADMIT", "FREE1_ADMIT", CHARGE1_COND))
    rules.append(("FREE1_ADMIT", "CHARGE2_ADMIT", FREE1_COND))
    rules.append(("CHARGE2_ADMIT", "FREE2_ADMIT", CHARGE2_COND))

    # --- Phase-2 precharge mirror chain, hanging off FREE2_ADMIT's own
    # one-time-only exit (never revisited, since nothing inside the closed
    # loop below ever points back to FREE2_ADMIT or any PCHG2_k/PFREE2_k).
    n2_extra = n2_precharge - 1
    prev_free2_name = None
    for k in range(1, n2_extra + 1):
        cname, fname = f"PCHG2_{k}", f"PFREE2_{k}"
        add(cname, "charge")
        add(fname, "free")
        rules.append((cname, fname, CHARGE2_COND))
        src = "FREE2_ADMIT" if prev_free2_name is None else prev_free2_name
        rules.append((src, cname, FREE2_COND))
        prev_free2_name = fname

    # --- Merge point into the closed, permanent round-robin loop. The
    # tail's last link (last phase-2 mirror pair's free-role state, or
    # FREE2_ADMIT itself if n2_extra==0 -- not reachable here since that
    # case is handled by the n2_precharge==1 branch above, but kept
    # general) feeds into the loop's own CHARGE3.
    add("CHARGE3", "charge")
    add("FREE3", "free")
    add("CHARGE4", "charge")
    add("FREE4", "free")
    add("CHARGE1", "charge")
    add("FREE1", "free")
    add("CHARGE2", "charge")
    add("FREE2", "free")

    src_to_charge3 = "FREE2_ADMIT" if prev_free2_name is None else prev_free2_name
    rules.append((src_to_charge3, "CHARGE3", FREE2_COND))
    rules.append(("CHARGE3", "FREE3", CHARGE3_COND))
    rules.append(("FREE3", "CHARGE4", FREE3_COND))
    rules.append(("CHARGE4", "FREE4", CHARGE4_COND))
    rules.append(("FREE4", "CHARGE1", FREE4_COND))       # loop entry
    rules.append(("CHARGE1", "FREE1", CHARGE1_COND))     # loop
    rules.append(("FREE1", "CHARGE2", FREE1_COND))       # loop
    rules.append(("CHARGE2", "FREE2", CHARGE2_COND))     # loop
    rules.append(("FREE2", "CHARGE3", FREE2_COND))       # loop closes

    return order, charge_role, free_role, rules


def render_machine_block(n1_precharge: int, n2_precharge: int) -> tuple[str, str, dict]:
    order, charge_role, free_role, rules = build_state_plan(n1_precharge, n2_precharge)
    name_to_code = {nm: c for nm, c in order}

    lines = []
    lines.append(".machine 1p")
    for nm, c in order:
        lines.append(f".state {nm} {c}")
    for frm, to, cond in rules:
        lines.append(f".rule {frm} {to} {cond}")

    gh1_names = [nm for nm in charge_role
                 if nm in ("CHARGE1", "CHARGE1_ADMIT") or nm.startswith("PCHG1_")]
    gl1_names = [nm for nm in free_role
                 if nm in ("FREE1", "FREE1_ADMIT") or nm.startswith("PFREE1_")]
    gh2_names = [nm for nm in charge_role
                 if nm in ("CHARGE2", "CHARGE2_ADMIT") or nm.startswith("PCHG2_")]
    gl2_names = [nm for nm in free_role
                 if nm in ("FREE2", "FREE2_ADMIT") or nm.startswith("PFREE2_")]

    def expr_for(names: list[str]) -> str:
        if len(names) == 1:
            return f"state=={names[0]}"
        return " | ".join(f"(state=={nm})" for nm in names)

    lines.append(f".output (gh1_cmd) VGATE*({expr_for(gh1_names)})")
    lines.append(f".output (gl1_cmd) VGATE*({expr_for(gl1_names)})")
    lines.append(f".output (gh2_cmd) VGATE*({expr_for(gh2_names)})")
    lines.append(f".output (gl2_cmd) VGATE*({expr_for(gl2_names)})")
    lines.append(".output (gh3_cmd) VGATE*(state==CHARGE3)")
    lines.append(".output (gl3_cmd) VGATE*(state==FREE3)")
    lines.append(".output (gh4_cmd) VGATE*(state==CHARGE4)")
    lines.append(".output (gl4_cmd) VGATE*(state==FREE4)")
    lines.append(".output (state_mon) state")
    lines.append(".output (rot_flag) VGATE*(state==FREE4)")
    lines.append(".endmachine")

    charge_codes = sorted(name_to_code[nm] for nm in charge_role)
    free_codes = sorted(name_to_code[nm] for nm in free_role)
    charge_bucket_expr = "|".join(bucket(v) for v in charge_codes)
    free_bucket_expr = "|".join(bucket(v) for v in free_codes)

    timer_block = []
    timer_block.append("CTIMER timer 0 {TIMER_C} ic=0")
    timer_block.append(f"BTIMER_CHG timer 0 I=-1p*({free_bucket_expr})")
    timer_block.append(f"BRESET_GATE reset_gate 0 V=5*({charge_bucket_expr})")
    timer_block.append("SRESET timer 0 reset_gate 0 SWRESET")
    timer_block.append(
        ".model SWRESET SW(Ron={TIMER_RESET_RON} Roff=1Meg Vt=2.5 Vh=0)"
    )
    timer_block.append("CTIMER_CHG timer_chg 0 {TIMER_C} ic=0")
    timer_block.append(f"BTIMER_CHG2 timer_chg 0 I=-1p*({charge_bucket_expr})")
    timer_block.append(f"BRESET_GATE2 reset_gate_chg 0 V=5*({free_bucket_expr})")
    timer_block.append("SRESET_CHG timer_chg 0 reset_gate_chg 0 SWRESET")

    meta = {
        "name_to_code": name_to_code,
        "charge_role": charge_role,
        "free_role": free_role,
        "n1_extra_pairs": n1_precharge - 1,
        "n2_extra_pairs": n2_precharge - 1,
    }
    return "\n".join(lines), "\n".join(timer_block), meta


def build_case(n1_precharge: int, n2_precharge: int) -> str:
    template = R04E10_TEMPLATE.read_text()

    machine_block, timer_block, meta = render_machine_block(n1_precharge, n2_precharge)

    marker_timer_start = "* Per-state elapsed FREEWHEEL-time timer"
    marker_handoff_start = "* Handoff-condition observer"
    marker_machine_comment = "* Unified event-driven, latched four-phase rotation machine."
    marker_meas_start = ".meas tran STATE_FINAL"

    pre = template.split(marker_timer_start)[0]
    handoff_block = template.split(marker_handoff_start, 1)[1]
    handoff_block = handoff_block.split(marker_machine_comment, 1)[0]
    handoff_block = marker_handoff_start + handoff_block
    handoff_block = handoff_block.strip("\n")

    post = template.split(marker_meas_start, 1)[1]
    post = ".meas tran STATE_FINAL" + post

    post = post.replace("SCB4P_P24_R04E10", "SCB4P_P24_R04E13")
    pre = pre.replace(
        "XMOD vin out 0 gh1_cmd gl1_cmd gh2_cmd gl2_cmd gh3_cmd gl3_cmd gh4_cmd gl4_cmd SCB4P_P24_R04E10",
        "XMOD vin out 0 gh1_cmd gl1_cmd gh2_cmd gl2_cmd gh3_cmd gl3_cmd gh4_cmd gl4_cmd SCB4P_P24_R04E13",
    )

    n_states = len(meta["name_to_code"])
    initial_state = "PCHG1_1" if meta["n1_extra_pairs"] else (
        "CHARGE1_ADMIT" if n2_precharge > 1 else "CHARGE1"
    )
    admit_note = (
        "This cell also emits a dedicated, one-time-only ADMIT copy of "
        "CHARGE1/FREE1/CHARGE2/FREE2 (CHARGE1_ADMIT/FREE1_ADMIT/"
        "CHARGE2_ADMIT/FREE2_ADMIT), required because N2_PRECHARGE>1 -- "
        "see scripts/build_r04e13_cases.py module docstring's documented "
        "design-correction finding."
        if n2_precharge > 1 else
        "N2_PRECHARGE=1 -- no phase-2 gate, no ADMIT states emitted; this "
        "cell's machine block is state/rule-list IDENTICAL to R04E12's own "
        "construct for the given N1_PRECHARGE."
    )

    header = f"""* R04E13 - phase-2 precharge admission gate stacked on phase-1's own
* (r04e13_n1_{n1_precharge}_n2_{n2_precharge})
* SENSITIVITY CASE: N1_PRECHARGE={n1_precharge}, N2_PRECHARGE={n2_precharge}.
* Fixed for the whole grid (BOUNDARY.md Section 4, R04E10's own
* best-performing cell / R04E12's own clean best N_PRECHARGE=3 value):
* I_LIMIT={I_LIMIT} A, T_CHARGE_MAX={T_CHARGE_MAX:.6e} s, T_FREEWHEEL_MAX=
* {T_FREEWHEEL_MAX:.6e} s.
* PARENT: R04E12 (phase-1-only precharge admission gate), itself parented on
* R04E10/R04E9. SINGLE CONCEPTUAL CHANGE from R04E12: a SECOND, analogous
* precharge admission gate is stacked after phase 1's own (fixed here at
* N1_PRECHARGE={n1_precharge}): after the real CHARGE2/FREE2 is reached for
* the first time, the machine repeats phase 2 alone N2_PRECHARGE-1 extra
* times before ever advancing to the real CHARGE3, then joins the normal
* round-robin permanently. {admit_note}
* See scripts/build_r04e13_cases.py module docstring for the exact
* compile-time-unrolled construct used, including a documented design
* correction found and fixed during this experiment's own pilot
* verification (a naive generalization of R04E12's phase-1 pattern caused
* the phase-2 gate to re-trigger every rotation; caught directly by
* BOUNDARY.md Section 5's required pilot check, not assumed correct).
* N1_PRECHARGE=1, N2_PRECHARGE=1 emits ZERO extra state pairs/ADMIT states --
* this cell's machine block is state/rule-list IDENTICAL to R04E10's own
* committed I_LIMIT=60A/T_CHARGE_MAX=50ns cell (verified in RESULTS.md).
* N1_PRECHARGE=3, N2_PRECHARGE=1 emits ZERO phase-2 extra states/ADMIT
* states -- this cell's machine block is state/rule-list IDENTICAL to
* R04E12's own committed N_PRECHARGE=3 cell (verified in RESULTS.md).
* Everything else (node topology, CFLY=3uF, COUT=4.672mF, GS61008T device
* data, true-zero-energy initial conditions, current-limit/timeout exit
* rules, handoff-condition monitor) is unchanged from R04E10/R04E12.
* SCOPE: bootstrap-only. Does NOT build or test handoff into the existing
* strict steady-state controller; only measures whether/when the handoff
* CONDITION is reached.
* This machine has {n_states} states ({meta['n1_extra_pairs']} phase-1
* extra precharge pairs + {meta['n2_extra_pairs']} phase-2 extra precharge
* pairs + 8 original R04E10 states{' + 4 ADMIT states' if n2_precharge > 1 else ''});
* initial state is {initial_state} (code 0).
"""

    include_marker = ".include "
    pre_body = pre[pre.index(include_marker):]

    full = header + "\n" + pre_body + "\n" + timer_block + "\n\n" + \
        handoff_block + "\n\n" + \
        "* Unified event-driven, latched two-stage-precharge-then-round-robin machine.\n" + \
        "* See scripts/build_r04e13_cases.py for the exact construct.\n" + \
        machine_block + "\n\n" + \
        "RSTATE state_mon 0 1k\n" + \
        "RROT rot_flag 0 1k\n" + \
        "RGH1 gh1_cmd 0 1k\n" + \
        "RGL1 gl1_cmd 0 1k\n" + \
        "RGH2 gh2_cmd 0 1k\n" + \
        "RGL2 gl2_cmd 0 1k\n" + \
        "RGH3 gh3_cmd 0 1k\n" + \
        "RGL3 gl3_cmd 0 1k\n" + \
        "RGH4 gh4_cmd 0 1k\n" + \
        "RGL4 gl4_cmd 0 1k\n\n" + \
        post

    return full


def main():
    CASES.mkdir(parents=True, exist_ok=True)
    for n1, n2 in CELLS:
        text = build_case(n1, n2)
        out = CASES / f"r04e13_n1_{n1}_n2_{n2}.cir"
        out.write_text(text)
        print(f"wrote {out} ({len(text)} bytes)")


if __name__ == "__main__":
    main()
