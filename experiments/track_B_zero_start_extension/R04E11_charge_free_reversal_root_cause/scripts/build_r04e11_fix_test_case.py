"""Build the ONE-CHANGE fix-hypothesis test case.

DIAGNOSIS (see RESULTS.md Sections 3-6 for the full evidence trail):
direct raw-trace inspection of the instrumented I_LIMIT=30A/T_CHARGE_MAX=
20ns diagnostic cell (r04e11_diag_i30_tchg20ns_instrumented.cir/.raw)
showed that during the CHARGE3/CHARGE4 -> FREE1 "reversal" episodes, the
two reset-gate booleans (V(reset_gate), V(reset_gate_chg)) NEVER
disagree -- they are perfect complements at every sampled instant
throughout the whole reversal window (checked directly, 151/151 rows, 0
conflicts). This REFUTES the originally-hypothesized "two reset gates
briefly disagree" race.

What IS observed: V(state_mon) itself sweeps DOWNWARD through several
half-integer bucket boundaries (3.5, 2.5, 1.5) in a few picoseconds,
during the exact same sub-picosecond-timestep solver-retry episodes that
also produce the ICS1-3 current-spike artifact. The reset switches
(SRESET/SRESET_CHG, model SWRESET) that gate `timer`/`timer_chg` are
driven by comparators with Vt=2.5, Vh=0 -- ZERO hysteresis -- sitting
EXACTLY on the same half-integer state-bucket boundaries the underlying
`.machine` uses for its own CHARGE_k/FREE_k partition. This creates a
delay-free algebraic loop: state_mon -> reset_gate/reset_gate_chg ->
SRESET/SRESET_CHG switch action -> timer/timer_chg voltage -> the very
`.rule` conditions that decide the next state -> state -> state_mon.
Under normal (non-retry) operation this loop is harmless because
reset_gate/reset_gate_chg are clean 0V/5V digital signals, comfortably
clear of any hysteresis band around Vt=2.5. But during a difficult,
sub-picosecond retry episode, a ZERO-hysteresis comparator sitting
exactly on the loop's own natural switching point can re-trigger on
every microscopic solver iteration, which is a textbook precondition for
this kind of chatter/instability.

ONE-CONCEPTUAL-CHANGE FIX TESTED HERE: give the SWRESET switch model
explicit hysteresis (Vh=1, i.e. turn-on/turn-off thresholds at 3.0V/2.0V
instead of a single 2.5V point) -- a classic debounce for exactly this
class of comparator-chatter problem. This is the ONLY change from the
already-committed r04e11_diag_i30_tchg20ns_instrumented.cir; every other
line (topology, parameters, the .machine/.rule table, the B-source gate
logic itself, .options, .tran, the diagnostic .save additions) is
unchanged. Because reset_gate/reset_gate_chg swing cleanly between 0V
and 5V under normal operation, Vh=1 (a 2.0-3.0V dead band) has NO effect
on any transition that isn't already sitting in the previously-diagnosed
difficult regime -- it cannot change any cell's steady-operation timing.
"""

from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
CASES = HERE / "cases"

SRC = CASES / "r04e11_diag_i30_tchg20ns_instrumented.cir"
DST = CASES / "r04e11_fixtest_i30_tchg20ns_hysteresis.cir"

OLD_MODEL = ".model SWRESET SW(Ron={TIMER_RESET_RON} Roff=1Meg Vt=2.5 Vh=0)"
NEW_MODEL = ".model SWRESET SW(Ron={TIMER_RESET_RON} Roff=1Meg Vt=2.5 Vh=1)"

HEADER = """\
* R04E11 FIX-HYPOTHESIS TEST: identical to r04e11_diag_i30_tchg20ns_
* instrumented.cir EXCEPT the SWRESET switch model below gains explicit
* hysteresis (Vh=1, thresholds 2.0V/3.0V instead of a single 2.5V point).
* See build_r04e11_fix_test_case.py module docstring and RESULTS.md
* Sections 3-6 for the diagnosis this fix targets and why Vh=1 cannot
* affect normal-operation switching (reset_gate/reset_gate_chg are clean
* 0V/5V digital signals outside the diagnosed difficult regime).
"""


def build() -> Path:
    text = SRC.read_text()
    if OLD_MODEL not in text:
        raise ValueError("expected SWRESET model line not found verbatim")
    text = text.replace(OLD_MODEL, NEW_MODEL)
    text = HEADER + text
    DST.write_text(text)
    return DST


if __name__ == "__main__":
    p = build()
    print(p)
