"""Topology specification and quarantined legacy cross-paper candidate.

The authoritative sequences now live in `p24_operating_sequence.py` and
`p25_operating_supplement.py`; merging policy lives in
`sequence_resolution.py`. The old six-interval/20-state construction is kept
only as a candidate for audit and cannot authorize a publication-locked run.
"""

from __future__ import annotations

from dataclasses import dataclass
from scb_ivr.evidence import Evidence


@dataclass(frozen=True)
class Connection:
    component: str
    terminal_1: str
    terminal_2: str
    evidence: Evidence
    note: str


@dataclass(frozen=True)
class OperatingInterval:
    name: str
    start_event: str
    commanded_on: tuple[str, ...]
    state_description: str
    end_event: str
    evidence: Evidence
    unresolved: tuple[str, ...] = ()


@dataclass(frozen=True)
class BlockingUncertainty:
    identifier: str
    question: str
    impact: str


@dataclass(frozen=True)
class GateState:
    """One commanded state in the P24-first four-phase rotating sequence."""

    name: str
    active_phase: int
    next_phase: int
    commanded_on: tuple[str, ...]
    end_event: str
    evidence: Evidence
    claim_boundary: str


# Rail nodes R0..R3 form the high-side series ladder. X1..X4 are switching
# nodes; OUT is the common output rail; 0 is the module reference.
CONNECTIONS = (
    Connection("VIN", "R0", "0", Evidence.P24_EXPLICIT, "48 V input port"),
    Connection("S1a", "R0", "R1", Evidence.P24_EXPLICIT, "top ladder switch"),
    Connection("C1", "R1", "X1", Evidence.P24_EXPLICIT, "series capacitor"),
    Connection("L1", "X1", "OUT", Evidence.P24_EXPLICIT, "phase-1 inductor"),
    Connection("S2a", "R1", "R2", Evidence.P24_EXPLICIT, "ladder switch"),
    Connection("C2", "R2", "X2", Evidence.P24_EXPLICIT, "series capacitor"),
    Connection("L2", "X2", "OUT", Evidence.P24_EXPLICIT, "phase-2 inductor"),
    Connection("S3a", "R2", "R3", Evidence.P24_EXPLICIT, "ladder switch"),
    Connection("C3", "R3", "X3", Evidence.P24_EXPLICIT, "series capacitor"),
    Connection("L3", "X3", "OUT", Evidence.P24_EXPLICIT, "phase-3 inductor"),
    Connection(
        "S4a",
        "R3",
        "X4",
        Evidence.CROSS_PAPER_EXTENSION,
        "read from P24 Fig. 3; terminal dots/labels are not printed",
    ),
    Connection("L4", "X4", "OUT", Evidence.P24_EXPLICIT, "phase-4 inductor"),
    Connection(
        "S1b",
        "X1",
        "0",
        Evidence.P25_SUPPLEMENT,
        "P25 Fig. 1 explicitly grounds SL1 source; accepted for the project",
    ),
    Connection(
        "S2b",
        "X2",
        "0",
        Evidence.P25_SUPPLEMENT,
        "P25 Fig. 1 explicitly grounds SL2 source; accepted for the project",
    ),
    Connection(
        "S3b",
        "X3",
        "0",
        Evidence.P25_SUPPLEMENT,
        "P25 Fig. 1 explicitly grounds SL3 source; accepted for the project",
    ),
    Connection(
        "S4b",
        "X4",
        "0",
        Evidence.PROJECT_DECISION,
        "accepted fourth-phase extension of the scalable P25 grounded-low-side implementation",
    ),
    Connection("Co", "OUT", "0", Evidence.P24_EXPLICIT, "shared output capacitor"),
)


# Six intervals describe the hand-off from phase 1 to phase 2.  The same
# pattern then rotates 2->3, 3->4 and 4->1.  P24 groups each phase into three
# main intervals; P25 resolves the commutations and negative-current interval.
LEGACY_CROSS_PAPER_PHASE1_TO_PHASE2_CANDIDATE = (
    OperatingInterval(
        "M1_energy_transfer",
        "t0: S1a commanded on after its ZVS condition",
        ("S1a", "S2b", "S3b", "S4b"),
        "iL1 rises; the other phase currents freewheel and fall",
        "t1: commanded S1a turn-off after its on-time",
        Evidence.CROSS_PAPER_EXTENSION,
        (
            "P24 names S1a and phase-2 low-side only; S3b/S4b conduction is "
            "the four-phase extension of P25 Mode 1",
        ),
    ),
    OperatingInterval(
        "M2_S1a_turnoff_commutation",
        "t1: S1a gate removed",
        ("S2b", "S3b", "S4b"),
        "iL1 commutates switch capacitances: high-side capacitance charges "
        "and low-side capacitance discharges; iL1 is approximately constant",
        "t2: Vds(S1b) reaches zero; S1b may then be gated on",
        Evidence.P25_SUPPLEMENT,
        (
            "P24 does not give Coss/snubber values or an exact dead time",
            "P25 equations require CH1/CL1 values that are not reported exactly",
        ),
    ),
    OperatingInterval(
        "M3_S1b_freewheel",
        "t2: S1b turns on at zero Vds",
        ("S1b", "S2b", "S3b", "S4b"),
        "iL1, iL2, iL3 and iL4 fall under their applicable output/freewheel voltages",
        "t3: iL2 crosses zero",
        Evidence.CROSS_PAPER_EXTENSION,
        ("P25 explicitly covers three phases; the iL4 state is an extension",),
    ),
    OperatingInterval(
        "M4_phase2_negative_current",
        "t3: iL2 crosses zero while S2b remains on",
        ("S1b", "S2b", "S3b", "S4b"),
        "iL2 becomes slightly negative to store commutation energy for S2a ZVS",
        "t4: controller turns S2b off at the negative-current target",
        Evidence.P25_SUPPLEMENT,
        (
            "the project adopts P25's 5%-10% range; no fitted point inside the "
            "range is yet selected",
            "the exact zero-current detector and turn-off implementation are not reported",
        ),
    ),
    OperatingInterval(
        "M5_S2b_turnoff_commutation",
        "t4: S2b gate removed near zero current",
        ("S1b", "S3b", "S4b"),
        "negative iL2 commutates S2a/S2b capacitances toward zero Vds on S2a",
        "t5: Vds(S2a) reaches zero; S2a may then be gated on",
        Evidence.P25_SUPPLEMENT,
        (
            "exact capacitances, nonlinear Coss curves and available dead time "
            "are not reported for the 2024 design",
        ),
    ),
    OperatingInterval(
        "M6_phase2_energy_transfer",
        "t5: S2a turns on at zero Vds",
        ("S1b", "S2a", "S3b", "S4b"),
        "C1/R1-side network acts as the phase-2 source; iL2 rises toward its peak",
        "t6: commanded S2a turn-off after its on-time",
        Evidence.CROSS_PAPER_EXTENSION,
        (
            "P25 explicitly uses CS1 as the phase-2 source in the three-phase circuit; "
            "the four-phase voltage/state equations are not printed in P24",
        ),
    ),
)


BLOCKING_UNCERTAINTIES = (
    BlockingUncertainty(
        "U03_CAPACITANCE_AND_DEADTIME",
        "What CH/CL (including nonlinear device Coss) and dead-time values belong to "
        "the intended 2024 case?",
        "Without them, t1-t2 and t4-t5 cannot be calculated or validated.",
    ),
    BlockingUncertainty(
        "U04_CONTROL_REALIZATION",
        "What zero-cross detector, delay/blanking and variable-off-time logic is intended?",
        "Prevents an event-driven boundary controller from being reproduced.",
    ),
    BlockingUncertainty(
        "U05_STARTUP_INITIAL_STATE",
        "How are C1-C3 charged and current-limited during startup?",
        "The papers analyze near-steady operation but do not define zero-state startup.",
    ),
)


PROJECT_DECISIONS = {
    "U01_LOW_SIDE_REFERENCE": {
        "status": "RESOLVED",
        "value": "S1b-S4b sources tied to module reference 0",
        "basis": "P25 Fig. 1 plus user-approved extension to the fourth phase",
    },
    "U02_NEGATIVE_CURRENT_TARGET": {
        "status": "USER_SELECTED_BRINGUP_BRANCH",
        "p24_value": (0.01, 0.02),
        "p25_mode_text": (0.05, 0.10),
        "p25_design_limit": (0.0, 0.05),
        "selected_bringup_value": 0.10,
        "selection_scope": "initial commutation/state-machine bring-up only; later margin tests must return to 5% and 2%",
        "basis": "P24 Sec. II-B and P25 Interval 4/Eq. (20) provide different ranges; neither silently overrides the other",
    },
    "U06_INDUCTANCE_CONFLICT": {
        "status": "USER_SELECTED_RECALCULATED_VALUE",
        "selected_lcrit_h": 1.4666666666666667e-9,
        "printed_table1_h": 2.68e-9,
        "selection_scope": "main 48-V/1-V, four-phase, four-module, 5-MHz analytical model",
        "basis": "use the value recalculated from the printed equation and locked inputs; retain Table-I value only as an audit discrepancy",
    },
}


def build_p24_first_four_phase_command_table() -> tuple[GateState, ...]:
    """Rotate the P24/P25-supported handoff without using complementary PWM.

    P24 explicitly establishes the active-high/adjacent-low mechanism and the
    three physical intervals. P25 explicitly shows, for three phases, that all
    non-active low sides freewheel and subdivides capacitance commutation. The
    fourth low-side entry is therefore labelled a cross-paper extension.
    """

    states: list[GateState] = []
    phases = range(1, 5)
    all_lows = tuple(f"S{phase}b" for phase in phases)
    for active in phases:
        nxt = active % 4 + 1
        inactive_lows = tuple(low for low in all_lows if low != f"S{active}b")
        next_off_lows = tuple(low for low in all_lows if low != f"S{nxt}b")
        states.extend(
            (
                GateState(
                    f"P{active}_ENERGY",
                    active,
                    nxt,
                    (f"S{active}a",) + inactive_lows,
                    f"S{active}a on-time reaches P24 Ton",
                    Evidence.CROSS_PAPER_EXTENSION,
                    "P24 interval 1; other-low freewheel set is the P25-to-four-phase extension",
                ),
                GateState(
                    f"P{active}_HS_COMMUTATION",
                    active,
                    nxt,
                    inactive_lows,
                    f"Vds(S{active}b)=0",
                    Evidence.P25_SUPPLEMENT,
                    "Timing remains symbolic until CH/CL/Coss and dead time are sourced",
                ),
                GateState(
                    f"P{active}_ALL_LOW_FREEWHEEL",
                    active,
                    nxt,
                    all_lows,
                    f"iL{nxt}=0",
                    Evidence.CROSS_PAPER_EXTENSION,
                    "P25 mode rotation extended from three to four phases",
                ),
                GateState(
                    f"P{active}_NEXT_NEGATIVE",
                    active,
                    nxt,
                    all_lows,
                    f"iL{nxt} reaches -10% of peak for the selected bring-up branch",
                    Evidence.PROJECT_DECISION,
                    "10% is the user-selected upper end of P25 mode text; later tests must check 5% and P24 2%",
                ),
                GateState(
                    f"P{active}_NEXT_HS_COMMUTATION",
                    active,
                    nxt,
                    next_off_lows,
                    f"Vds(S{nxt}a)=0",
                    Evidence.P25_SUPPLEMENT,
                    "Timing remains symbolic until CH/CL/Coss and dead time are sourced",
                ),
            )
        )
    return tuple(states)


def validate_p24_first_command_table(states: tuple[GateState, ...]) -> None:
    """Reject ordinary-complement or shoot-through command construction."""

    assert len(states) == 20, "four phases require five commanded states per handoff"
    for state in states:
        commanded = set(state.commanded_on)
        for phase in range(1, 5):
            assert not ({f"S{phase}a", f"S{phase}b"} <= commanded), (
                f"same-leg shoot-through in {state.name}"
            )
        if state.name.endswith("_ENERGY"):
            assert f"S{state.active_phase}a" in commanded
            assert f"S{state.active_phase}b" not in commanded
        if state.name.endswith("_NEXT_HS_COMMUTATION"):
            assert f"S{state.next_phase}b" not in commanded


CROSS_PAPER_CANDIDATE_COMMAND_TABLE = build_p24_first_four_phase_command_table()
validate_p24_first_command_table(CROSS_PAPER_CANDIDATE_COMMAND_TABLE)


def publication_locked_spice_ready() -> bool:
    """False until source resolution and numeric uncertainties are both clear."""
    from scb_ivr.sequence_resolution import publication_sequence_ready

    return not BLOCKING_UNCERTAINTIES and publication_sequence_ready()
