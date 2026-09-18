"""A52 pilot -- BOUNDARY.md Section 2's mandatory "pilot-first" check.

Isolates ONE mechanism question and nothing else: can LTspice express, and
fire at the correct instant, the transition

    DEADTIME -> next state, at whichever comes FIRST of
        (i)  a natural `V <= 0` crossing of the switching node, or
        (ii) the commanded dead-time window's own end.

The pilot circuit is a single 1 nF node discharged by a constant current
that switches on exactly when the commanded window opens, so the natural
crossing instant is known in CLOSED FORM and the two branches are selected
purely by choosing the current:

    dV/dt = -I/C  =>  t_cross = t_window_start + V0*C/I

    I = 10 A  ->  t_cross = window_start + 1.000 ns, INSIDE the 2.15 ns
                  window  => branch (i), the natural crossing must win
    I =  2 A  ->  V(window_end) = 10 - 2*2.15 = 5.7 V > 0, never crosses
                  => branch (ii), the commanded timeout must win, exactly
                  at the window end, with 5.7 V still standing on the node

Mechanism, as established by this pilot's own earlier iterations (all of
which are reported in RESULTS.md rather than quietly discarded):

* `.machine` is a TOP-LEVEL directive here and its argument is a TIME, not
  a name.  The first iteration wrote `.machine pilot` and was rejected
  outright; `.machine 1p` parses.  (A37's own netlist writes `.machine 1p`
  inside a `.subckt`; both placements work once the argument is a time.)
* Several `.machine` blocks may coexist in one netlist, so the four phases
  get four INDEPENDENT machines and no global-ordering argument is needed.
* Commanded instants are expressed as `time>=<constant>` rules, exactly as
  A37 already does, so a commanded edge carries NO waveform-shaping error
  at all (no PULSE/PWL ramp, no threshold interpolation).
* The OR is written `(V(node)<=0) | (time>=<end>)`.  A variant using two
  separate rules with the same source and target states was tested and
  gives bit-identical results; the `|` form is used for legibility.

Two candidate encodings of the OR and two maximum timesteps are still
generated and run, so the record contains the evidence rather than the
claim.
"""

from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
PILOT_DIR = HERE / "pilot"

#: Window placed early so the pilot is short; only its LENGTH must equal the
#: real `dead_time_s`, which it does.
WINDOW_START_S = 1.0e-9
DEAD_TIME_S = 2.15e-9
WINDOW_END_S = WINDOW_START_S + DEAD_TIME_S
INITIAL_V = 10.0
NODE_CAPACITANCE_F = 1e-9
#: Centered on WINDOW_START_S, so the charge the ramp removes is
#: first-order identical to an ideal current step at WINDOW_START_S.
EDGE_S = 1e-13
GATE_V = 5.0
THRESHOLD_V = 2.5
RON_OHM = 7e-3
#: `.machine` output ramp, measured in this pilot's own sweep to be
#: independent of this argument (see RESULTS.md).
MACHINE_RAMP = "1p"

CASES = {
    #: name -> (pull current A, expected branch, expected transition time s)
    "natural": (
        10.0,
        "natural_crossing",
        WINDOW_START_S + INITIAL_V * NODE_CAPACITANCE_F / 10.0,
    ),
    "timeout": (2.0, "commanded_timeout", WINDOW_END_S),
}
MECHANISMS = ("or", "dual")
MAX_STEPS_S = {"1p": 1e-12, "10p": 10e-12}


def expected_residual_v(current_a: float) -> float:
    """`Vds` still standing at the window end if no crossing happens."""
    return INITIAL_V - current_a * DEAD_TIME_S / NODE_CAPACITANCE_F


def rules_block(mechanism: str) -> str:
    if mechanism == "or":
        return f".rule S_DT S_ON (V(vds)<=0) | (time>={WINDOW_END_S:.12e})\n"
    if mechanism == "dual":
        return (
            ".rule S_DT S_ON V(vds)<=0\n"
            f".rule S_DT S_ON time>={WINDOW_END_S:.12e}\n"
        )
    raise ValueError(mechanism)


def build(case: str, mechanism: str, max_step_name: str) -> Path:
    current_a, branch, expected_s = CASES[case]
    max_step_s = MAX_STEPS_S[max_step_name]
    analytic_cross_s = WINDOW_START_S + INITIAL_V * NODE_CAPACITANCE_F / current_a
    name = f"A52_pilot_{case}_{mechanism}_{max_step_name}"
    text = f"""* {name}
* A52 pilot for BOUNDARY.md Section 2's event-gated dead-time transition.
* Case        : {case}  (expected branch: {branch})
* Mechanism   : {mechanism}
* Max timestep: {max_step_name}
* Commanded window : [{WINDOW_START_S:.12e}, {WINDOW_END_S:.12e}] s
*                    (length {DEAD_TIME_S:.12e} s = the real dead_time_s)
* Analytic natural crossing instant          : {analytic_cross_s:.12e} s
* Analytic Vds at window end if never crossing: {expected_residual_v(current_a):.9f} V
* EXPECTED transition instant                 : {expected_s:.12e} s
.param VG={GATE_V} VTH={THRESHOLD_V} RON={RON_OHM}
.param TWSTART={WINDOW_START_S:.12e} TWEND={WINDOW_END_S:.12e}

* The commutating node: held at V0 until the commanded window opens, then
* discharged by a constant current.  The current ramp is centered on
* TWSTART, so the charge removed is first-order identical to an ideal step.
C_NODE vds 0 {NODE_CAPACITANCE_F:.12e}
I_PULL vds 0 PWL(0 0 {{TWSTART-{EDGE_S / 2:.12e}}} 0
+ {{TWSTART+{EDGE_S / 2:.12e}}} {current_a})
S_HIGH vds 0 gh 0 SWU
R_NUM vds 0 1G

* Commanded instants are `time>=` rules: no waveform, no threshold, no ramp.
.machine {MACHINE_RAMP}
.state S_WAIT 0
.state S_DT 1
.state S_ON 2
.rule S_WAIT S_DT time>={WINDOW_START_S:.12e}
{rules_block(mechanism)}.output (gh) VG*(state==S_ON)
.output (pstate) state
.endmachine
R_GH gh 0 1k
R_PSTATE pstate 0 1k

.model SWU SW(Ron={{RON}} Roff=1T Vt={{VTH}} Vh=0)

* Branch (i)/(ii) discriminators.
*  - T_VDS_CROSS is the DIRECT physical crossing instant and carries no
*    gate-ramp latency at all; FALL=1 is used so the t=0 sample cannot be
*    mistaken for a crossing.
*  - T_GH_ON is the instant the switch actually closes, which lags the
*    state change by the `.machine` output ramp (measured, see RESULTS.md).
.meas tran T_DT_ENTER WHEN V(pstate)=0.5 RISE=1
.meas tran T_GH_ON WHEN V(gh)={{VTH}} RISE=1
.meas tran VDS_AT_ON FIND V(vds) WHEN V(gh)={{VTH}} RISE=1
.meas tran T_VDS_CROSS WHEN V(vds)=0 FALL=1
.meas tran VDS_BEFORE_WEND FIND V(vds) AT {{TWEND-1f}}
.meas tran VDS_AT_WSTART FIND V(vds) AT {{TWSTART}}

.options plotwinsize=0 reltol=1e-6 abstol=1e-12 vntol=1e-9 chgtol=1e-16
+ cshunt=1e-15
.save V(vds) V(gh) V(pstate)
.ic V(vds)={INITIAL_V}
.tran 0 4n 0 {max_step_s:.12e} UIC
.end
"""
    PILOT_DIR.mkdir(parents=True, exist_ok=True)
    path = PILOT_DIR / f"{name}.cir"
    path.write_text(text, encoding="ascii")
    return path


def main() -> int:
    built = []
    for case in CASES:
        for mechanism in MECHANISMS:
            for max_step_name in MAX_STEPS_S:
                built.append(build(case, mechanism, max_step_name))
    for path in built:
        print(path)
    print()
    print("Expected, per case (closed form, see module docstring):")
    for case, (current_a, branch, expected_s) in CASES.items():
        print(
            f"  {case:<8} I={current_a:>5} A  branch={branch:<18} "
            f"transition at {expected_s * 1e9:.9f} ns   "
            f"Vds at window end if never crossing = "
            f"{expected_residual_v(current_a):.6f} V"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
