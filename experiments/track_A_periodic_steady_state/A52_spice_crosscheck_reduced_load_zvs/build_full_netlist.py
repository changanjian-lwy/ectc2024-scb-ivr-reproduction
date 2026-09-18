"""A52 step 2 -- generate the full four-phase LTspice netlist.

Every timing constant in the emitted netlist is produced by
`a52_boundary.phase_segments`, i.e. by bisecting `solver_copy`'s own
`commanded_pwm_mode`.  No `T/4` offset arithmetic is written here
(BOUNDARY.md Section 2's explicit instruction), and no window instant is
typed by hand.

Topology
--------
Node-for-node the descriptor `solver_copy.zero_start_descriptor.
assemble_descriptor` builds, with the SAME node names, so the initial
conditions can be transcribed coordinate-by-coordinate without any
re-interpretation:

    V_SRC     src -> 0        constant 48 V (post-ramp; no ramp is modeled,
                              this is a periodicity/ZVS test seeded from an
                              already-converged state, not a startup test)
    R_SRC     src -> src_r    source_resistance_ohm
    L_PAR_IN  src_r -> vin    source_inductance_h
    divider   vin-tap3-tap2-tap1-0, 4 x divider_capacitance_f, each with a
              parallel divider_leakage_ohm
    diodes    tap3-a1, tap2-a2, tap1-a3, each at diode_OFF_resistance_ohm,
              because A51's `evaluate_period_map` is called throughout with
              `diode_state=(False, False, False)`
    SH1..SH4  vin-a1, a1-a2, a2-a3, a3-x4   (= `HIGH_SIDE_BRANCHES`)
    SL1..SL4  x1-0, x2-0, x3-0, x4-0        (= `LOW_SIDE_BRANCHES`)
    CH1..CH4  CH_TOTAL across each high branch, always present
    CL1..CL4  CL_TOTAL across each low branch, always present
    C1..C3    a1-x1, a2-x2, a3-x3, flying_capacitances_f
    LIND1..4  x1-out .. x4-out, phase_inductance_h with Rser =
              phase_inductor_resistance_ohm
    COUT      out -> 0, output_capacitance_f
    RLOAD     out -> 0, sized from Section 1's ACTUAL delivered power

Deliberate faithfulness choices, stated rather than assumed
-----------------------------------------------------------
* `Ron = 7 mOhm` UNIFORM on every switch, high and low, all four phases --
  BOUNDARY.md Section 2's explicit requirement.  A37/A42/A49's asymmetric
  `RHS`/`RLS` is NOT used here, because Section 1's seed state was solved
  under the uniform assumption.
* NO reverse-conduction diodes (A37's own `DH*_REVERSE`/`DL*_REVERSE`
  `DGAN_IDEAL` devices) are instantiated.  A51's descriptor model has no
  diode across any switch at all: it reaches zero-voltage turn-on purely by
  the event-gated switch admission this netlist reproduces.  Adding an
  ideal clamp would give the SPICE circuit a conduction path the model
  being checked does not have, which would make the comparison test a
  different physical model -- the exact failure Section 2 warns against.
* Switch capacitance stays asymmetric (`CH=385 pF`, `CL=770 pF`), as
  Section 2 requires, and is present in both the on and the off state,
  exactly as `assemble_descriptor` places it.
"""

from __future__ import annotations

import json
from pathlib import Path

import a52_boundary as B

HERE = Path(__file__).resolve().parent
RUN_SPAN_S = 250e-9
GATE_V = 5.0
GATE_THRESHOLD_V = 2.5
#: Validated in the pilot; the result is independent of this value.
MACHINE_RAMP = "1p"
#: The low-side admission node of phase `p` (0-based), matching
#: `a51_period_map._resolve_turn_off`'s own `node = f"x{phase_index + 1}"`.
def low_side_node(phase0: int) -> str:
    return f"x{phase0 + 1}"


def vds_probe(phase0: int) -> str:
    first, second = B.vds_expression(phase0)
    if second is None:
        return f"V({first})"
    return f"V({first},{second})"


def ic_mapping(boundary) -> list[dict]:
    """Coordinate-by-coordinate map from the 20-variable `z*` to the netlist.

    Every row carries how that coordinate reaches SPICE, so the mapping is
    auditable rather than implied -- the same discipline A51 used for its
    own `a37_seed_state` conversion table.
    """
    names = B.A51.variable_names(boundary)
    values = dict(zip(names, B.Z_STAR.tolist()))
    rows = [
        {
            "variable": "src",
            "value": values["src"],
            "target": "V(src)",
            "how": "NOT an initial condition: V_SRC pins V(src) to exactly "
            "48 V for the whole run.  z*'s 48.00000000687211 is the "
            "solver's own residual on an algebraically-pinned variable "
            "(6.9e-9 V); SPICE enforces the same equation exactly.",
        },
        {
            "variable": "src_r",
            "value": values["src_r"],
            "target": ".ic V(src_r)",
            "how": "node between R_SRC and L_PAR_IN",
        },
        {
            "variable": "vin",
            "value": values["vin"],
            "target": ".ic V(vin)",
            "how": "node after the input inductor; NOT the 48 V rail (that "
            "is `src`).  This is the descriptor's own naming.",
        },
        {
            "variable": "tap3",
            "value": values["tap3"],
            "target": ".ic V(tap3)",
            "how": "precharge divider tap",
        },
        {
            "variable": "tap2",
            "value": values["tap2"],
            "target": ".ic V(tap2)",
            "how": "precharge divider tap",
        },
        {
            "variable": "tap1",
            "value": values["tap1"],
            "target": ".ic V(tap1)",
            "how": "precharge divider tap",
        },
        {
            "variable": "a1",
            "value": values["a1"],
            "target": ".ic V(a1)",
            "how": "ladder node; with V(x1) it carries VC1 = a1-x1",
        },
        {
            "variable": "a2",
            "value": values["a2"],
            "target": ".ic V(a2)",
            "how": "ladder node; with V(x2) it carries VC2 = a2-x2",
        },
        {
            "variable": "a3",
            "value": values["a3"],
            "target": ".ic V(a3)",
            "how": "ladder node; with V(x3) it carries VC3 = a3-x3",
        },
        {
            "variable": "x1",
            "value": values["x1"],
            "target": ".ic V(x1)",
            "how": "phase 1 switching node",
        },
        {
            "variable": "x2",
            "value": values["x2"],
            "target": ".ic V(x2)",
            "how": "phase 2 switching node",
        },
        {
            "variable": "x3",
            "value": values["x3"],
            "target": ".ic V(x3)",
            "how": "phase 3 switching node",
        },
        {
            "variable": "x4",
            "value": values["x4"],
            "target": ".ic V(x4)",
            "how": "phase 4 switching node",
        },
        {
            "variable": "out",
            "value": values["out"],
            "target": ".ic V(out)",
            "how": "output node across COUT and RLOAD",
        },
        {
            "variable": "LPAR_IN",
            "value": values["LPAR_IN"],
            "target": "L_PAR_IN ic=",
            "how": "descriptor branch ('src_r','vin'): current positive from "
            "src_r to vin.  LTspice's `L_PAR_IN src_r vin` uses the same "
            "first-node-to-second-node convention, so the sign transfers "
            "unchanged.",
        },
        {
            "variable": "L1",
            "value": values["L1"],
            "target": "LIND1 ic=",
            "how": "descriptor branch ('x1','out'), same sign convention",
        },
        {
            "variable": "L2",
            "value": values["L2"],
            "target": "LIND2 ic=",
            "how": "descriptor branch ('x2','out'), same sign convention",
        },
        {
            "variable": "L3",
            "value": values["L3"],
            "target": "LIND3 ic=",
            "how": "descriptor branch ('x3','out'), same sign convention",
        },
        {
            "variable": "L4",
            "value": values["L4"],
            "target": "LIND4 ic=",
            "how": "descriptor branch ('x4','out'), same sign convention",
        },
        {
            "variable": "I_VSTEP",
            "value": values["I_VSTEP"],
            "target": "(none)",
            "how": "the MNA source-branch current.  Purely algebraic (its "
            "column of E is exactly zero, per A51's own seed table), so it "
            "is not an initial condition anywhere; SPICE determines V_SRC's "
            "current from the circuit.",
        },
    ]
    if [row["variable"] for row in rows] != list(names):
        raise RuntimeError("IC table ordering does not match variable_names")
    return rows


def build(max_step_s: float, tag: str) -> tuple[Path, dict]:
    boundary = B.build_boundary()
    t0 = B.A51.period_start_s(boundary)
    rload = B.rload_from_actual_power_ohm()
    rows = ic_mapping(boundary)
    values = {row["variable"]: row["value"] for row in rows}

    # ---- machines, emitted straight from the bisected schedule -----------
    machines: list[str] = []
    schedule: dict[int, list[dict]] = {}
    turn_on_windows: dict[int, tuple[float, float]] = {}
    state_codes: dict[int, dict[str, int]] = {}
    for phase0 in range(4):
        phase = phase0 + 1
        segments = B.phase_segments(boundary, t0, phase0, RUN_SPAN_S)
        local = [
            {
                "kind": segment.kind,
                "start_s": segment.start_s - t0,
                "end_s": segment.end_s - t0,
            }
            for segment in segments
        ]
        schedule[phase] = local
        lines = [f".machine {MACHINE_RAMP}"]
        codes: dict[str, int] = {}
        for index, segment in enumerate(local):
            state = f"P{phase}_S{index}"
            codes[state] = index
            lines.append(f".state {state} {index}")
        for index, segment in enumerate(local[:-1]):
            source = f"P{phase}_S{index}"
            target = f"P{phase}_S{index + 1}"
            end = segment["end_s"]
            if segment["kind"] == "DEADTIME_TURN_ON":
                condition = f"({vds_probe(phase0)}<=0) | (time>={end:.12e})"
                turn_on_windows.setdefault(
                    phase, (segment["start_s"], segment["end_s"])
                )
            elif segment["kind"] == "DEADTIME_TURN_OFF":
                condition = f"(V({low_side_node(phase0)})<=0) | (time>={end:.12e})"
            else:
                condition = f"time>={end:.12e}"
            lines.append(f".rule {source} {target} {condition}")
        high_states = [
            f"(state==P{phase}_S{index})"
            for index, segment in enumerate(local)
            if segment["kind"] == "HIGH"
        ]
        low_states = [
            f"(state==P{phase}_S{index})"
            for index, segment in enumerate(local)
            if segment["kind"] == "LOW"
        ]
        lines.append(
            f".output (gh{phase}) VG*({'+'.join(high_states) if high_states else '0'})"
        )
        lines.append(
            f".output (gl{phase}) VG*({'+'.join(low_states) if low_states else '0'})"
        )
        lines.append(f".output (p{phase}state) state")
        lines.append(".endmachine")
        machines.append("\n".join(lines))
        state_codes[phase] = codes

    # ---- per-phase measurements ----------------------------------------
    meas: list[str] = []
    turn_on_state_index: dict[int, int] = {}
    for phase0 in range(4):
        phase = phase0 + 1
        local = schedule[phase]
        index = next(
            position
            for position, segment in enumerate(local)
            if segment["kind"] == "DEADTIME_TURN_ON"
        )
        turn_on_state_index[phase] = index
        window_start, window_end = local[index]["start_s"], local[index]["end_s"]
        probe = vds_probe(phase0)
        threshold = index + 0.5
        meas.append(
            f"* ---- phase {phase} turn-on window "
            f"[{window_start:.12e}, {window_end:.12e}] s (netlist time)"
        )
        # The state signal is monotone over the run, so `=index+0.5 RISE=1`
        # identifies this one transition unambiguously -- no TD guard and no
        # RISE-count bookkeeping, and it is not affected by the gate ramp.
        meas.append(
            f".meas tran TON_P{phase} WHEN V(p{phase}state)={threshold} RISE=1"
        )
        meas.append(
            f".meas tran VDSON_P{phase} FIND {probe} "
            f"WHEN V(p{phase}state)={threshold} RISE=1"
        )
        meas.append(
            f".meas tran ILON_P{phase} FIND I(LIND{phase}) "
            f"WHEN V(p{phase}state)={threshold} RISE=1"
        )
        # The DIRECT physical crossing, independent of the machine entirely.
        # TD is required: while the high side conducts, `Vds = I*Ron` sits
        # near zero and changes sign, which would otherwise be picked up.
        meas.append(
            f".meas tran TXP{phase} WHEN {probe}=0 TD={window_start:.12e} FALL=1"
        )
        meas.append(
            f".meas tran VDSENT_P{phase} FIND {probe} AT {window_start:.12e}"
        )
        meas.append(
            f".meas tran ILENT_P{phase} FIND I(LIND{phase}) AT {window_start:.12e}"
        )
        # Natural-vs-forced discriminator: what is still standing on the node
        # immediately BEFORE the commanded window would end.
        meas.append(
            f".meas tran VDSEND_P{phase} FIND {probe} AT {window_end - 1e-15:.12e}"
        )
        meas.append(
            f".meas tran VDSMIN_P{phase} MIN {probe} "
            f"FROM {window_start:.12e} TO {window_end:.12e}"
        )
        meas.append(
            f".meas tran IMAX_P{phase} MAX ABS(I(LIND{phase})) FROM 0 TO {RUN_SPAN_S:.12e}"
        )

    # ---- periodicity (one full period apart) ----------------------------
    period = boundary.period_s
    meas.append("* ---- periodicity: same commanded configuration, one period apart")
    periodic_probes = {
        "VC1": "V(a1,x1)",
        "VC2": "V(a2,x2)",
        "VC3": "V(a3,x3)",
        "VOUT": "V(out)",
        "VA1": "V(a1)",
        "VA2": "V(a2)",
        "VA3": "V(a3)",
        "VX1": "V(x1)",
        "VX2": "V(x2)",
        "VX3": "V(x3)",
        "VX4": "V(x4)",
        "VVIN": "V(vin)",
        "VSRCR": "V(src_r)",
        "VTAP1": "V(tap1)",
        "VTAP2": "V(tap2)",
        "VTAP3": "V(tap3)",
        "IL1": "I(LIND1)",
        "IL2": "I(LIND2)",
        "IL3": "I(LIND3)",
        "IL4": "I(LIND4)",
        "ILPAR": "I(L_PAR_IN)",
    }
    for key, probe in periodic_probes.items():
        meas.append(f".meas tran {key}_I FIND {probe} AT 2p")
        meas.append(f".meas tran {key}_F FIND {probe} AT {period + 2e-12:.12e}")
        meas.append(f".meas tran D{key} PARAM {key}_F-{key}_I")
    meas.append("* ---- fingerprint: the commanded rail must not move")
    meas.append(".meas tran VSRC_MIN MIN V(src)")
    meas.append(".meas tran VSRC_MAX MAX V(src)")
    meas.append(f".meas tran VOUT_AVG AVG V(out) FROM 0 TO {period:.12e}")
    meas.append(
        f".meas tran PLOAD_AVG AVG V(out)*V(out)/{rload:.12e} FROM 0 TO {period:.12e}"
    )

    # ---- initial conditions ---------------------------------------------
    ic_nodes = [
        row for row in rows if row["target"].startswith(".ic ")
    ]
    ic_line = ".ic " + " ".join(
        f"{row['target'][4:]}={row['value']!r}" for row in ic_nodes
    )

    saves = (
        ["V(src)", "V(src_r)", "V(vin)", "V(tap1)", "V(tap2)", "V(tap3)"]
        + ["V(a1)", "V(a2)", "V(a3)", "V(x1)", "V(x2)", "V(x3)", "V(x4)", "V(out)"]
        + [f"V(gh{k})" for k in range(1, 5)]
        + [f"V(gl{k})" for k in range(1, 5)]
        + [f"V(p{k}state)" for k in range(1, 5)]
        + [f"I(LIND{k})" for k in range(1, 5)]
        + ["I(L_PAR_IN)"]
    )

    name = f"A52_spice_crosscheck_reduced_load_zvs{tag}"
    header = f"""* {name}
* A52 -- SPICE cross-check of A51's four-phase joint ZVS state.
* Seed state, topology values and EVERY commanded switching instant are
* generated by `build_full_netlist.py` from `solver_copy`'s own
* `commanded_pwm_mode` / `ZeroStartBoundary`; nothing below is hand-typed.
*
* Absolute solver time of this period's start (A51's own `period_start_s`,
* = BASE_PERIOD_INDEX*T + d/2)     : {t0!r} s
* Netlist time offset TOFFSET       : {t0!r} s
*   netlist time tau = t_absolute - TOFFSET, so `.tran` starts at tau=0,
*   which is the instant A51's period map starts from (phase 1 goes HIGH).
* Period T                          : {period!r} s
* Ton                               : {boundary.on_time_s!r} s
* Dead time d                       : {boundary.dead_time_s!r} s
* Ron (UNIFORM, both sides, all four phases, BOUNDARY Section 2)
*                                   : {boundary.switch_on_resistance_ohm!r} ohm
* CH_TOTAL / CL_TOTAL               : {boundary.switch_capacitance.high_total_f!r} /
*                                     {boundary.switch_capacitance.low_total_f!r} F
* CFLY                              : {boundary.flying_capacitances_f[0]!r} F
* RLOAD = Vout^2/P at Section 1's ACTUAL delivered power
*   {B.AVERAGE_OUTPUT_V!r}^2 / {B.AVERAGE_LOAD_POWER_W!r} = {rload!r} ohm
* Maximum timestep                  : {max_step_s!r} s
.param VG={GATE_V} VTH={GATE_THRESHOLD_V}
.param RON={boundary.switch_on_resistance_ohm!r}
.param CH_TOTAL={boundary.switch_capacitance.high_total_f!r}
.param CL_TOTAL={boundary.switch_capacitance.low_total_f!r}
.param CFLY={boundary.flying_capacitances_f[0]!r}
.param COUT={boundary.output_capacitance_f!r}
.param RLOAD={rload!r}
.param LPHASE={boundary.phase_inductance_h!r} RLSER={boundary.phase_inductor_resistance_ohm!r}
.param LSRC={boundary.source_inductance_h!r} RSRC={boundary.source_resistance_ohm!r}
.param CDIV={boundary.divider_capacitance_f!r} RDIVLEAK={boundary.divider_leakage_ohm!r}
.param RDIODE_OFF={boundary.diode_off_resistance_ohm!r}
.param VIN={boundary.vin_target_v!r}

* ---------------- source path (constant 48 V, no ramp) ----------------
V_SRC src 0 {{VIN}}
R_SRC src src_r {{RSRC}}
L_PAR_IN src_r vin {{LSRC}} Rser=0 ic={values['LPAR_IN']!r}

* ---------------- precharge divider (divider_enabled=True) -------------
C_DIV4 vin tap3 {{CDIV}}
R_DIV4 vin tap3 {{RDIVLEAK}}
C_DIV3 tap3 tap2 {{CDIV}}
R_DIV3 tap3 tap2 {{RDIVLEAK}}
C_DIV2 tap2 tap1 {{CDIV}}
R_DIV2 tap2 tap1 {{RDIVLEAK}}
C_DIV1 tap1 0 {{CDIV}}
R_DIV1 tap1 0 {{RDIVLEAK}}
* Precharge diodes, held OFF for the whole run: A51's `evaluate_period_map`
* is called throughout with diode_state=(False, False, False), which the
* descriptor renders as `diode_off_resistance_ohm`.
R_PD3 tap3 a1 {{RDIODE_OFF}}
R_PD2 tap2 a2 {{RDIODE_OFF}}
R_PD1 tap1 a3 {{RDIODE_OFF}}

* ---------------- four-phase series-capacitor ladder --------------------
* No reverse-conduction diode is instantiated anywhere: see this builder's
* own module docstring.  A51's model has none.
SH1 vin a1 gh1 0 SWU
CH1_TOTAL vin a1 {{CH_TOTAL}}
C1 a1 x1 {{CFLY}}
CL1_TOTAL x1 0 {{CL_TOTAL}}
SL1 x1 0 gl1 0 SWU
LIND1 x1 out {{LPHASE}} Rser={{RLSER}} ic={values['L1']!r}

SH2 a1 a2 gh2 0 SWU
CH2_TOTAL a1 a2 {{CH_TOTAL}}
C2 a2 x2 {{CFLY}}
CL2_TOTAL x2 0 {{CL_TOTAL}}
SL2 x2 0 gl2 0 SWU
LIND2 x2 out {{LPHASE}} Rser={{RLSER}} ic={values['L2']!r}

SH3 a2 a3 gh3 0 SWU
CH3_TOTAL a2 a3 {{CH_TOTAL}}
C3 a3 x3 {{CFLY}}
CL3_TOTAL x3 0 {{CL_TOTAL}}
SL3 x3 0 gl3 0 SWU
LIND3 x3 out {{LPHASE}} Rser={{RLSER}} ic={values['L3']!r}

SH4 a3 x4 gh4 0 SWU
CH4_TOTAL a3 x4 {{CH_TOTAL}}
CL4_TOTAL x4 0 {{CL_TOTAL}}
SL4 x4 0 gl4 0 SWU
LIND4 x4 out {{LPHASE}} Rser={{RLSER}} ic={values['L4']!r}

C_OUT out 0 {{COUT}}
R_LOAD out 0 {{RLOAD}}

* Ron is UNIFORM for high and low side alike (BOUNDARY Section 2); A51's
* ZeroStartBoundary has a single scalar switch_on_resistance_ohm.
.model SWU SW(Ron={{RON}} Roff={boundary.switch_off_resistance_ohm!r} Vt={{VTH}} Vh=0)

* ---------------- commanded schedule, one machine per phase -------------
* Each machine is the SAME HIGH -> DEADTIME -> LOW -> DEADTIME schedule
* `commanded_pwm_mode` emits, UNROLLED over this run so that every
* commanded instant is an exact `time>=` constant with no waveform,
* threshold or modular arithmetic anywhere.  Each dead-time window exits on
* `(natural V<=0 crossing) | (commanded window end)` -- whichever comes
* first -- which is `resolve_deadtime_window`'s own rule and the mechanism
* validated by this experiment's own pilot.
"""

    body = "\n\n".join(machines)
    gate_loads = "\n".join(
        [f"R_GH{k} gh{k} 0 1k" for k in range(1, 5)]
        + [f"R_GL{k} gl{k} 0 1k" for k in range(1, 5)]
        + [f"R_PS{k} p{k}state 0 1k" for k in range(1, 5)]
    )

    footer = f"""
{gate_loads}

* ---------------- measurements -----------------------------------------
{chr(10).join(meas)}

.options plotwinsize=0 reltol=1e-6 abstol=1e-9 vntol=1e-9 chgtol=1e-16
+ solver=alt cshunt=1e-15
.save {' '.join(saves)}
{ic_line}
.tran 0 {RUN_SPAN_S:.12e} 0 {max_step_s:.12e} UIC
.end
"""
    text = header + "\n" + body + "\n" + footer
    path = HERE / f"{name}.cir"
    path.write_text(text, encoding="ascii")

    metadata = {
        "netlist": path.name,
        "tag": tag,
        "max_step_s": max_step_s,
        "t0_absolute_s": t0,
        "toffset_s": t0,
        "run_span_s": RUN_SPAN_S,
        "period_s": period,
        "rload_ohm": rload,
        "ic_mapping": rows,
        "schedule_netlist_time": schedule,
        "turn_on_windows_netlist_time": turn_on_windows,
        "turn_on_state_index": turn_on_state_index,
        "vds_probe": {
            phase0 + 1: vds_probe(phase0) for phase0 in range(4)
        },
        "low_side_node": {
            phase0 + 1: low_side_node(phase0) for phase0 in range(4)
        },
    }
    return path, metadata


def main() -> int:
    paths = {}
    metadata = {}
    for tag, step in (("", 1e-12), ("_step250f", 0.25e-12)):
        path, meta = build(step, tag)
        paths[tag or "main"] = str(path)
        metadata[tag or "main"] = meta
        print(f"wrote {path}  (max step {step:.3e} s)")
    (HERE / "netlist_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    print(f"wrote {HERE / 'netlist_metadata.json'}")

    print()
    print("Initial-condition mapping (z* -> netlist):")
    for row in metadata["main"]["ic_mapping"]:
        print(f"  {row['variable']:<8} {row['value']!r:<24} -> {row['target']}")
    print()
    print("Turn-on windows in netlist time (s):")
    for phase, window in metadata["main"]["turn_on_windows_netlist_time"].items():
        print(f"  phase {phase}: [{window[0]:.12e}, {window[1]:.12e}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
