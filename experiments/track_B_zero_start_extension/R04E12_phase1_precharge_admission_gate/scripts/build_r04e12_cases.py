"""Generate R04E12's phase-1 precharge admission-gate grid (5 cells,
N_PRECHARGE in {1,3,5,10,20}), parented on R04E10's own committed
I_LIMIT=60A/T_CHARGE_MAX=50ns cell
(../../R04E10_timeout_gated_multi_rotation_bootstrap/cases/
r04e10_ilimit_60a_tchg_50ns.cir), per BOUNDARY.md Section 2/4.

IMPLEMENTATION DESIGN DECISION (documented explicitly, since BOUNDARY.md
Section 2/5 leaves the exact construct to this experiment's own design):
BOUNDARY.md's own suggested approach describes a runtime counter/node
that gates FREE1's single `.rule` transition target between CHARGE1 and
CHARGE2. Direct inspection of every existing `.machine` construct in this
project's own R04E5-R04E11 lineage (grepped directly, not assumed) shows
every single state, in every committed case file, has EXACTLY ONE
`.rule <from> <to> <cond>` line -- never two rules sharing the same
`<from>` state with different `<to>` targets. Rather than rely on
unverified multi-rule-per-state branching semantics for a from-state's
target selection (a genuinely new, never-before-used feature of this
project's own `.machine` usage), this generator instead implements the
IDENTICAL admission-gate behavior BOUNDARY.md Section 2 describes using a
compile-time-UNROLLED static chain of N_PRECHARGE-1 extra state pairs
(`PCHG1_k`/`PFREE1_k`, k=1..N_PRECHARGE-1), each an EXACT electrical
mirror of CHARGE1/FREE1 (same current-limit-OR-timeout / zero-crossing-
OR-timeout rule, same phase-1-only gate drive), chained
PCHG1_1->PFREE1_1->PCHG1_2->PFREE1_2->...->PCHG1_{N-1}->PFREE1_{N-1}->
CHARGE1(real)->FREE1(real)->CHARGE2->...->FREE4->CHARGE1(real, permanent
round robin, precharge chain never re-entered). Since each build-time
N_PRECHARGE value gets its OWN generated netlist anyway (this project's
established one-case-per-grid-cell convention), the "counter" BOUNDARY.md
describes is realized as this per-cell topology choice rather than a
runtime SPICE node -- functionally identical (each precharge pass is a
bona fide, independently-timed-out repeat visit to phase 1's own
current-limit-OR-timeout charge state and zero-crossing-OR-timeout free
state, using the SAME shared `timer`/`timer_chg` nodes and I_LIMIT/
T_CHARGE_MAX/T_FREEWHEEL_MAX parameters CHARGE1/FREE1 already use), while
avoiding introducing an additional, unvalidated counter/comparator
construct into an already solver-stiff machine (R04E11's own finding).
For N_PRECHARGE=1 this generator emits ZERO extra state pairs -- CHARGE1
is state 0, exactly R04E10's own numbering -- making the N_PRECHARGE=1
baseline cell BYTE-FOR-BYTE identical (mechanism-wise) to R04E10's own
committed I_LIMIT=60A/T_CHARGE_MAX=50ns cell, not merely numerically
close (Section 2 of BOUNDARY.md requires this exact equivalence, verified
directly in RESULTS.md).

Because the whole extended state numbering (0 .. 2*(N-1)+7) strictly
alternates charge-role (even code) / free-role (odd code) exactly as
R04E10's own original 0..7 numbering did (a direct consequence of every
precharge pair and every real CHARGE_k/FREE_k state consuming exactly one
even and one odd code in sequence), the existing per-machine-wide
(not per-phase) `timer`/`timer_chg` reset-gate construct generalizes
cleanly: it is extended to treat ALL charge-role states (not just
CHARGE1/2/3/4) as "timer_chg counts, timer held at 0" and ALL free-role
states as the opposite, using the same bucket-boolean pattern R04E9/R04E10
already validated, just with more OR-terms.
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

N_PRECHARGE_GRID = [1, 3, 5, 10, 20]

I_LIMIT = 60
T_CHARGE_MAX = 5.000000e-08
T_FREEWHEEL_MAX = 5.000000e-08


def bucket(v: int) -> str:
    # Special-case v==0 to emit the exact same text R04E10's own template
    # uses ("V(state_mon)<0.5", not the symmetric "-0.5<x<0.5" form) so
    # that the N_PRECHARGE=1 cell's generated timer-boolean lines are
    # BYTE-IDENTICAL to R04E10's own committed cell, not merely
    # mathematically equivalent (state_mon is bounded to [0,7] by the
    # .machine's own declared state range, so the two forms are equivalent
    # for v==0, but byte-identical text removes even a hypothetical risk
    # of a solver-level divergence in this already solver-stiff family,
    # per R04E11's own finding).
    if v == 0:
        return "(V(state_mon)<0.5)"
    return f"(V(state_mon)>{v - 0.5})&(V(state_mon)<{v + 0.5})"


def build_state_plan(n_precharge: int):
    """Returns (state_code_list_in_order, charge_role_names, free_role_names,
    rules, state_lines) for a given N_PRECHARGE."""
    order = []  # list of (name, code)
    code = 0
    charge_role = []
    free_role = []
    rules = []  # list of "from to cond" strings (cond filled below)

    n_extra = n_precharge - 1
    prev_free_name = None
    for k in range(1, n_extra + 1):
        cname = f"PCHG1_{k}"
        fname = f"PFREE1_{k}"
        order.append((cname, code)); code += 1
        order.append((fname, code)); code += 1
        charge_role.append(cname)
        free_role.append(fname)
        rules.append((cname, fname,
                       "(I(XMOD:L1)>=I_LIMIT) | (V(timer_chg)>=T_CHARGE_MAX)"))
        # Wire the PREVIOUS pair's free-mirror state forward to THIS pair's
        # charge-mirror state (the intermediate precharge-repeat link). The
        # very first pair (k==1) has no predecessor to wire here; the very
        # last pair's free-mirror state is wired to the real CHARGE1 below,
        # after the loop, once every pair has been declared.
        if prev_free_name is not None:
            rules.append((prev_free_name, cname,
                           "(I(XMOD:L1)<=0) | (V(timer)>=T_FREEWHEEL_MAX)"))
        prev_free_name = fname

    # Real round-robin states, unchanged from R04E10, but CHARGE1's code
    # depends on how many precharge pairs precede it.
    real_names = ["CHARGE1", "FREE1", "CHARGE2", "FREE2",
                  "CHARGE3", "FREE3", "CHARGE4", "FREE4"]
    real_codes = {}
    for nm in real_names:
        order.append((nm, code))
        real_codes[nm] = code
        code += 1
        if nm.startswith("CHARGE"):
            charge_role.append(nm)
        else:
            free_role.append(nm)

    # Wire the last precharge pair's FREE1-mirror to the real CHARGE1
    # (the admission gate closing permanently); if n_extra==0, nothing to
    # wire (machine starts directly at the real CHARGE1, R04E10-identical).
    if prev_free_name is not None:
        rules.append((prev_free_name, "CHARGE1",
                       "(I(XMOD:L1)<=0) | (V(timer)>=T_FREEWHEEL_MAX)"))

    # Real round-robin rules, unchanged in form from R04E10.
    rules.append(("CHARGE1", "FREE1",
                   "(I(XMOD:L1)>=I_LIMIT) | (V(timer_chg)>=T_CHARGE_MAX)"))
    rules.append(("FREE1", "CHARGE2",
                   "(I(XMOD:L1)<=0) | (V(timer)>=T_FREEWHEEL_MAX)"))
    rules.append(("CHARGE2", "FREE2",
                   "(I(XMOD:L2)>=I_LIMIT) | (V(timer_chg)>=T_CHARGE_MAX)"))
    rules.append(("FREE2", "CHARGE3",
                   "(I(XMOD:L2)<=0) | (V(timer)>=T_FREEWHEEL_MAX)"))
    rules.append(("CHARGE3", "FREE3",
                   "(I(XMOD:L3)>=I_LIMIT) | (V(timer_chg)>=T_CHARGE_MAX)"))
    rules.append(("FREE3", "CHARGE4",
                   "(I(XMOD:L3)<=0) | (V(timer)>=T_FREEWHEEL_MAX)"))
    rules.append(("CHARGE4", "FREE4",
                   "(I(XMOD:L4)>=I_LIMIT) | (V(timer_chg)>=T_CHARGE_MAX)"))
    rules.append(("FREE4", "CHARGE1",
                   "(I(XMOD:L4)<=0) | (V(timer)>=T_FREEWHEEL_MAX)"))

    return order, charge_role, free_role, rules


def render_machine_block(n_precharge: int) -> tuple[str, dict]:
    order, charge_role, free_role, rules = build_state_plan(n_precharge)
    name_to_code = {nm: c for nm, c in order}

    lines = []
    lines.append(".machine 1p")
    for nm, c in order:
        lines.append(f".state {nm} {c}")
    for frm, to, cond in rules:
        lines.append(f".rule {frm} {to} {cond}")

    # gh1_cmd/gl1_cmd cover the real CHARGE1/FREE1 PLUS every precharge
    # mirror state (all of which physically command the same phase-1-only
    # gate drive).
    gh1_names = [nm for nm in charge_role if nm == "CHARGE1" or nm.startswith("PCHG1_")]
    gl1_names = [nm for nm in free_role if nm == "FREE1" or nm.startswith("PFREE1_")]
    if len(gh1_names) == 1:
        # Byte-identical to R04E10's own template when N_PRECHARGE=1 (no
        # extra OR terms, no extra grouping parens).
        gh1_expr = f"state=={gh1_names[0]}"
    else:
        gh1_expr = " | ".join(f"(state=={nm})" for nm in gh1_names)
    if len(gl1_names) == 1:
        gl1_expr = f"state=={gl1_names[0]}"
    else:
        gl1_expr = " | ".join(f"(state=={nm})" for nm in gl1_names)
    lines.append(f".output (gh1_cmd) VGATE*({gh1_expr})")
    lines.append(f".output (gl1_cmd) VGATE*({gl1_expr})")
    lines.append(".output (gh2_cmd) VGATE*(state==CHARGE2)")
    lines.append(".output (gl2_cmd) VGATE*(state==FREE2)")
    lines.append(".output (gh3_cmd) VGATE*(state==CHARGE3)")
    lines.append(".output (gl3_cmd) VGATE*(state==FREE3)")
    lines.append(".output (gh4_cmd) VGATE*(state==CHARGE4)")
    lines.append(".output (gl4_cmd) VGATE*(state==FREE4)")
    lines.append(".output (state_mon) state")
    lines.append(".output (rot_flag) VGATE*(state==FREE4)")
    lines.append(".endmachine")

    # Timer bucket booleans, generalized over the full charge-role/free-role
    # state sets (order-independent; OR is commutative).
    charge_codes = sorted(name_to_code[nm] for nm in charge_role)
    free_codes = sorted(name_to_code[nm] for nm in free_role)
    charge_bucket_expr = "|".join(bucket(v) for v in charge_codes)
    free_bucket_expr = "|".join(bucket(v) for v in free_codes)

    timer_block = []
    timer_block.append(
        "CTIMER timer 0 {TIMER_C} ic=0"
    )
    timer_block.append(
        f"BTIMER_CHG timer 0 I=-1p*({free_bucket_expr})"
    )
    timer_block.append(
        f"BRESET_GATE reset_gate 0 V=5*({charge_bucket_expr})"
    )
    timer_block.append("SRESET timer 0 reset_gate 0 SWRESET")
    timer_block.append(
        ".model SWRESET SW(Ron={TIMER_RESET_RON} Roff=1Meg Vt=2.5 Vh=0)"
    )
    timer_block.append("CTIMER_CHG timer_chg 0 {TIMER_C} ic=0")
    timer_block.append(
        f"BTIMER_CHG2 timer_chg 0 I=-1p*({charge_bucket_expr})"
    )
    timer_block.append(
        f"BRESET_GATE2 reset_gate_chg 0 V=5*({free_bucket_expr})"
    )
    timer_block.append("SRESET_CHG timer_chg 0 reset_gate_chg 0 SWRESET")

    meta = {
        "name_to_code": name_to_code,
        "charge_role": charge_role,
        "free_role": free_role,
        "n_extra_pairs": n_precharge - 1,
    }
    return "\n".join(lines), "\n".join(timer_block), meta


def build_case(n_precharge: int) -> str:
    template = R04E10_TEMPLATE.read_text()

    machine_block, timer_block, meta = render_machine_block(n_precharge)

    # Split template into: header/params/monitors (before the old timer
    # block), and everything from the .meas section onward (after the old
    # .machine/.endmachine + RSTATE/RROT/RGHx/RGLx passive block), which is
    # reused completely unchanged (measurement definitions, .options,
    # .tran, and the SCB4P subcircuit).
    marker_timer_start = "* Per-state elapsed FREEWHEEL-time timer"
    marker_handoff_start = "* Handoff-condition observer"
    marker_machine_comment = "* Unified event-driven, latched four-phase rotation machine."
    marker_meas_start = ".meas tran STATE_FINAL"

    pre = template.split(marker_timer_start)[0]
    # The handoff-condition observer (BHANDOFF/RHANDOFF) sits between the
    # two original timer blocks' end and the old ".machine" comment, and is
    # unchanged by this experiment (BOUNDARY.md Section 3: "handoff-
    # condition monitor definition ... identical to R04E9/R04E10's").
    # Extract it verbatim so it is not silently dropped by the split above.
    handoff_block = template.split(marker_handoff_start, 1)[1]
    handoff_block = handoff_block.split(marker_machine_comment, 1)[0]
    handoff_block = marker_handoff_start + handoff_block
    handoff_block = handoff_block.strip("\n")

    post = template.split(marker_meas_start, 1)[1]
    post = ".meas tran STATE_FINAL" + post

    # Rename the subcircuit to avoid a same-name collision with R04E10's
    # own netlist (BOUNDARY.md Section 2), electrically identical otherwise.
    post = post.replace("SCB4P_P24_R04E10", "SCB4P_P24_R04E12")
    pre = pre.replace(
        "XMOD vin out 0 gh1_cmd gl1_cmd gh2_cmd gl2_cmd gh3_cmd gl3_cmd gh4_cmd gl4_cmd SCB4P_P24_R04E10",
        "XMOD vin out 0 gh1_cmd gl1_cmd gh2_cmd gl2_cmd gh3_cmd gl3_cmd gh4_cmd gl4_cmd SCB4P_P24_R04E12",
    )

    header = f"""* R04E12 - phase-1 precharge admission gate (r04e12_npre_{n_precharge})
* SENSITIVITY CASE: N_PRECHARGE={n_precharge}. Fixed for the whole grid
* (BOUNDARY.md Section 4, R04E10's own best-performing cell):
* I_LIMIT={I_LIMIT} A, T_CHARGE_MAX={T_CHARGE_MAX:.6e} s, T_FREEWHEEL_MAX=
* {T_FREEWHEEL_MAX:.6e} s.
* PARENT: R04E10 (r04e10_ilimit_60a_tchg_50ns.cir), itself parented on
* R04E9. SINGLE CONCEPTUAL CHANGE from R04E10: a precharge admission gate
* is inserted before the machine's normal round-robin rotation. See
* scripts/build_r04e12_cases.py module docstring for the exact
* compile-time-unrolled construct used (N_PRECHARGE-1 extra state pairs
* electrically mirroring CHARGE1/FREE1, chained before the real CHARGE1)
* and its equivalence to BOUNDARY.md Section 2's counter-gate description.
* N_PRECHARGE=1 emits ZERO extra state pairs -- this cell's machine block
* is mechanism-identical to R04E10's own committed
* I_LIMIT=60A/T_CHARGE_MAX=50ns cell (verified in RESULTS.md).
* Everything else (node topology, CFLY=3uF, COUT=4.672mF, GS61008T device
* data, true-zero-energy initial conditions, current-limit/timeout exit
* rules, handoff-condition monitor) is unchanged from R04E10.
* SCOPE: bootstrap-only. Does NOT build or test handoff into the existing
* strict steady-state controller; only measures whether/when the handoff
* CONDITION is reached.
* This machine has {len(meta['name_to_code'])} states ({meta['n_extra_pairs']}
* extra precharge pairs + 8 original R04E10 states); initial state is
* {"PCHG1_1" if meta['n_extra_pairs'] else "CHARGE1"} (code 0).
"""

    # Drop the old header comment block from the template (everything up to
    # the first blank .param block) and replace with ours; keep everything
    # from ".include" onward unchanged (device model, VIN/topology params,
    # handoff-band params, power-stage instantiation, VC monitors).
    include_marker = ".include "
    pre_body = pre[pre.index(include_marker):]

    full = header + "\n" + pre_body + "\n" + timer_block + "\n\n" + \
        handoff_block + "\n\n" + \
        "* Unified event-driven, latched precharge-then-round-robin machine.\n" + \
        "* See scripts/build_r04e12_cases.py for the exact construct.\n" + \
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
    for n in N_PRECHARGE_GRID:
        text = build_case(n)
        out = CASES / f"r04e12_npre_{n}.cir"
        out.write_text(text)
        print(f"wrote {out} ({len(text)} bytes)")


if __name__ == "__main__":
    main()
