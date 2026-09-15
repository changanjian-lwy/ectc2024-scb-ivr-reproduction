"""Generate R04E11's instrumented diagnostic netlists.

PARENT CONSTRUCT: R04E10's timeout-gated multi-rotation bootstrap
(experiments/track_B_zero_start_extension/
R04E10_timeout_gated_multi_rotation_bootstrap/, built by
build_b06_r04e10_timeout_gated_multi_rotation_bootstrap.py). R04E10 found
(but did not root-cause) a CHARGE3/CHARGE4 -> FREE1 reversal/retry dynamic
and a coincident ICS1-3 numerical artifact.

WHAT THIS SCRIPT DOES: takes R04E10's own already-generated, already-run
case netlists (r04e10_ilimit_*_tchg_*.cir, committed under R04E10's own
cases/ directory) and produces BYTE-IDENTICAL copies except for ONE
addition to the `.save` line: the four internal construct nodes R04E10
never recorded --

  V(reset_gate)      -- BRESET_GATE output (5*IS_CHARGE boolean, resets the
                         FREEWHEEL timer `timer`)
  V(reset_gate_chg)  -- BRESET_GATE2 output (5*IS_FREE boolean, resets the
                         CHARGE timer `timer_chg`)
  V(timer)           -- FREEWHEEL elapsed-time timer node (CTIMER)
  V(timer_chg)       -- CHARGE elapsed-time timer node (CTIMER_CHG)

`.save` only controls which nodes LTspice WRITES to the .raw file; it does
not add or remove any circuit element, does not change any parameter, and
does not alter the solver's internal timestep choices. This is therefore
pure additional instrumentation, not a circuit or mechanism change -- the
"what must not change" list in this experiment's own BOUNDARY.md Section 4
is untouched. Every other line (topology, parameters, .machine/.rule
table, .options, .tran) is copied verbatim from the R04E10 source file.

CASES GENERATED:
  1. r04e11_diag_i30_tchg20ns_instrumented.cir -- copy of R04E10's own
     I_LIMIT=30A/T_CHARGE_MAX=20ns cell, BOUNDARY.md Section 3's primary
     diagnostic target (known reversal near t=19.275us, ~143ns retry
     period during the first rotation).
  2. r04e11_diag_i30_tchg5ns_instrumented.cir -- copy of R04E10's own
     I_LIMIT=30A/T_CHARGE_MAX=5ns cell, the secondary target: one of the
     three T_CHARGE_MAX=5ns total-stall cells (0 rotations in the full
     20us window), representing the reversal dynamic in its most extreme
     (never-escaping) form.
"""

from __future__ import annotations

from pathlib import Path

TRACK = Path(__file__).resolve().parent.parent.parent
R04E10_CASES = (
    TRACK / "R04E10_timeout_gated_multi_rotation_bootstrap" / "cases"
)
HERE = TRACK / "R04E11_charge_free_reversal_root_cause"
CASES = HERE / "cases"

OLD_SAVE = (
    ".save V(vc1_mon) V(vc2_mon) V(vc3_mon) V(state_mon) V(rot_flag) "
    "V(handoff_flag) V(out) I(XMOD:L1) I(XMOD:L2) I(XMOD:L3) I(XMOD:L4) "
    "I(XMOD:CS1) I(XMOD:CS2) I(XMOD:CS3)"
)
NEW_SAVE = (
    ".save V(vc1_mon) V(vc2_mon) V(vc3_mon) V(state_mon) V(rot_flag) "
    "V(handoff_flag) V(out) I(XMOD:L1) I(XMOD:L2) I(XMOD:L3) I(XMOD:L4) "
    "I(XMOD:CS1) I(XMOD:CS2) I(XMOD:CS3) "
    "V(reset_gate) V(reset_gate_chg) V(timer) V(timer_chg)"
)

INSTRUMENT_HEADER = """\
* R04E11 DIAGNOSTIC INSTRUMENTATION of R04E10's own {src_case} case.
* ONLY CHANGE from the R04E10 source netlist: the .save line below adds
* V(reset_gate), V(reset_gate_chg), V(timer), V(timer_chg) -- the four
* internal reset-gate/timer nodes R04E10 never recorded. .save only
* controls which nodes are WRITTEN to the .raw file; it adds no circuit
* element, changes no parameter, and does not alter solver timestep
* choices. Every other line below (topology, parameters, .machine/.rule
* table, .options, .tran) is byte-identical to R04E10's own
* {src_case}.cir. See
* R04E11_charge_free_reversal_root_cause/scripts/
* build_r04e11_diagnostic_cases.py and this experiment's own BOUNDARY.md
* Section 3-4.
"""

CASES_TO_BUILD = [
    ("r04e10_ilimit_30a_tchg_20ns", "r04e11_diag_i30_tchg20ns_instrumented"),
    ("r04e10_ilimit_30a_tchg_5ns", "r04e11_diag_i30_tchg5ns_instrumented"),
]


def build() -> list[Path]:
    CASES.mkdir(parents=True, exist_ok=True)
    generated = []
    for src_stem, dst_stem in CASES_TO_BUILD:
        src_path = R04E10_CASES / f"{src_stem}.cir"
        text = src_path.read_text()
        if OLD_SAVE not in text:
            raise ValueError(
                f"expected .save line not found verbatim in {src_path}"
            )
        text = text.replace(OLD_SAVE, NEW_SAVE)
        header = INSTRUMENT_HEADER.format(src_case=src_stem)
        text = header + text
        dst_path = CASES / f"{dst_stem}.cir"
        dst_path.write_text(text)
        generated.append(dst_path)
    return generated


if __name__ == "__main__":
    paths = build()
    print(f"# generated {len(paths)} instrumented diagnostic cases")
    for p in paths:
        print(p)
