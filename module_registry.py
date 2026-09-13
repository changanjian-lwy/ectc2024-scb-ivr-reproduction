"""Replaceable module catalogue; registration never implies adoption."""

from __future__ import annotations

from collections import defaultdict

from evidence import Evidence
from ivr_framework import (
    critical_inductance,
    duty_cycle,
    high_side_on_time,
    inductor_peak_current,
    parallel_embedded_inductors,
    unit_embedded_inductance,
)
from model_contracts import Module, Slot
from p24_operating_sequence import P24_PHASE1_INTERVALS
from p25_operating_supplement import P25_PHASE1_TO_PHASE2_MODES


MODULES = (
    Module(
        "p24_fig3_four_phase_topology",
        Slot.TOPOLOGY,
        Evidence.P24_EXPLICIT,
        "P24",
        "Fig. 3 and Sec. II-B",
        frozenset({"four_phase_power_topology"}),
        note="Terminal ambiguity remains represented by the separate topology audit.",
    ),
    Module(
        "p24_equations_1_to_6",
        Slot.ANALYTICAL,
        Evidence.P24_EXPLICIT,
        "P24",
        "Eqs. (1)-(6)",
        frozenset(
            {
                "duty",
                "on_time",
                "phase_peak_current",
                "critical_inductance",
                "embedded_inductor_count",
                "unit_inductance",
            }
        ),
        payload={
            "duty": duty_cycle,
            "on_time": high_side_on_time,
            "phase_peak_current": inductor_peak_current,
            "critical_inductance": critical_inductance,
            "embedded_inductor_count": parallel_embedded_inductors,
            "unit_inductance": unit_embedded_inductance,
        },
    ),
    Module(
        "p24_three_interval_phase_local_sequence",
        Slot.SEQUENCE,
        Evidence.P24_EXPLICIT,
        "P24",
        "Sec. II-B, first/second/third intervals",
        frozenset({"phase_local_three_interval_sequence", "p24_negative_branch"}),
        conflicts_with=frozenset({"p25_cross_phase_handoff_sequence"}),
        payload=P24_PHASE1_INTERVALS,
    ),
    Module(
        "p24_derived_single_phase_stiff_boundary",
        Slot.BOUNDARY,
        Evidence.P24_DERIVED,
        "P24",
        "Eq. (1) four-phase periodic-state reduction",
        frozenset({"single_phase_stiff_rail_boundary"}),
        requires=frozenset({"duty", "on_time", "phase_peak_current"}),
        note=(
            "Uses Vin/nP and a stiff Vo only for a local analytical replay; "
            "not a full topology or startup model."
        ),
    ),
    Module(
        "ltspice_latched_event_memory",
        Slot.NUMERICAL_ENGINE,
        Evidence.PROJECT_DECISION,
        "LTspice",
        ".machine state memory",
        frozenset({"latched_event_memory"}),
        note="Numerical realization only; adds no detector delay or paper parameter.",
    ),
    Module(
        "ideal_switch_pair",
        Slot.DEVICE,
        Evidence.EXPLORATORY_ASSUMPTION,
        "project idealization",
        "R04A local boundary replay",
        frozenset({"ideal_switch_pair"}),
        note="May support waveform/transition checks but no loss or hardware claim.",
    ),
    Module(
        "p25_six_mode_cross_phase_supplement",
        Slot.SEQUENCE,
        Evidence.P25_SUPPLEMENT,
        "P25",
        "Figs. 2-3, Modes 1-6",
        frozenset({"p25_cross_phase_handoff_sequence", "commutation_submodes"}),
        requires=frozenset({"three_phase_power_topology"}),
        conflicts_with=frozenset({"phase_local_three_interval_sequence"}),
        payload=P25_PHASE1_TO_PHASE2_MODES,
    ),
    Module(
        "p25_symbolic_commutation_equations",
        Slot.COMMUTATION,
        Evidence.P25_SUPPLEMENT,
        "P25",
        "Eqs. (5)-(6), (13)-(14)",
        frozenset({"symbolic_coss_commutation"}),
        requires=frozenset({"commutation_capacitance", "dead_time"}),
        note="Equations are available; numeric CH/CL and dead time are not.",
    ),
    Module(
        "unknown_p24_p25_controller",
        Slot.CONTROLLER,
        Evidence.UNKNOWN_BLOCKING,
        "P24/P25",
        "implementation not published",
        frozenset(),
        note="ZCD, delay, blanking and variable-off-time implementation are missing.",
    ),
    Module(
        "unknown_p24_p25_startup",
        Slot.STARTUP,
        Evidence.UNKNOWN_BLOCKING,
        "P24/P25",
        "startup sequence not published",
        frozenset(),
    ),
)


def modules_by_slot() -> dict[Slot, tuple[Module, ...]]:
    grouped: dict[Slot, list[Module]] = defaultdict(list)
    for module in MODULES:
        grouped[module.slot].append(module)
    return {slot: tuple(items) for slot, items in grouped.items()}


def get_module(module_id: str) -> Module:
    for module in MODULES:
        if module.module_id == module_id:
            return module
    raise KeyError(module_id)
