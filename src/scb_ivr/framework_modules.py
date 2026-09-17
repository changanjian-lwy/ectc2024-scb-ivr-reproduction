"""Fixed framework slots and provenance-tagged candidate implementations.

The slot interfaces do not change when a candidate is added.  A candidate is
never promoted to the 2024 reproduction merely because it can be represented
by the interface; compatibility and provenance remain attached to it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import pi, sqrt


class Compatibility(str, Enum):
    DIRECT_FAMILY_INCOMPLETE = "DIRECT_FAMILY_INCOMPLETE"
    ADAPTATION_REQUIRED = "ADAPTATION_REQUIRED"
    GENERAL_PHYSICS_ONLY = "GENERAL_PHYSICS_ONLY"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class Provenance:
    source_file: str
    location: str
    source_topology: str
    note: str


@dataclass(frozen=True)
class CommutationParametersModule:
    name: str
    compatibility: Compatibility
    provenance: Provenance
    c_high_f: float | None
    c_low_f: float | None
    nonlinear_coss_model: str | None
    dead_time_s: float | None
    equations: tuple[str, ...]


@dataclass(frozen=True)
class BoundaryControllerModule:
    name: str
    compatibility: Compatibility
    provenance: Provenance
    sensed_quantity: str | None
    zero_cross_threshold_a: float | None
    negative_current_fraction_range: tuple[float, float] | None
    blanking_time_s: float | None
    propagation_delay_s: float | None
    timing_policy: str | None


@dataclass(frozen=True)
class StartupStrategyModule:
    name: str
    compatibility: Compatibility
    provenance: Provenance
    target_rule: str | None
    current_limit_method: str | None
    completion_event: str | None
    extra_components: tuple[str, ...]
    unresolved_adaptation: tuple[str, ...]


@dataclass(frozen=True)
class FrameworkSlots:
    commutation_parameters: CommutationParametersModule
    boundary_controller: BoundaryControllerModule
    startup_strategy: StartupStrategyModule


P24_FILE = (
    "Package_Power_Delivery_Architecture_for_High_Performance_Computing_"
    "Systems_With_a_1_kW_IVR_Operated_in_CCM-DCM_Boundary_Mode_Condition (1).pdf"
)
P25_FILE = (
    "Design_and_Implementation_of_a_GaN-Based_Soft-Switched_Series-"
    "Capacitor_Buck_Converter_Operating_at_the_CCM-DCM_Boundary_for_"
    "High-Performance_Computing_Systems.pdf"
)
THESIS_FILE = (
    "HybridSwitched capcaitor power conversters fundamental limits and "
    "design techniques - phdthesis.pdf"
)
STARTUP_FILE = "Three_level_buck_converter_with_control_and_soft_startup.pdf"


PRIMARY_EMPTY_SLOTS = FrameworkSlots(
    commutation_parameters=CommutationParametersModule(
        name="P24/P25 SCB commutation - unresolved numeric implementation",
        compatibility=Compatibility.UNRESOLVED,
        provenance=Provenance(
            P25_FILE,
            "Fig. 1; Intervals 2 and 5; Eqs. (5)-(6), (13)-(14)",
            "three-phase SCB follow-up to the 2024 concept",
            "Mechanism and equations exist; CH/CL values and numeric dead time do not.",
        ),
        c_high_f=None,
        c_low_f=None,
        nonlinear_coss_model=None,
        dead_time_s=None,
        equations=(
            "P25 Eq. (5)-(6): phase-1 capacitance commutation and duration",
            "P25 Eq. (13)-(14): phase-2 capacitance commutation and duration",
        ),
    ),
    boundary_controller=BoundaryControllerModule(
        name="P24/P25 boundary controller - interface only",
        compatibility=Compatibility.UNRESOLVED,
        provenance=Provenance(
            P25_FILE,
            "Section III; Table IV; reference [22]",
            "SCB at CCM-DCM boundary",
            "One phase-current sensor per module is stated sufficient, but the cited "
            "high-frequency ZCD implementation is not present in the folder.",
        ),
        sensed_quantity="one inductor current per module",
        zero_cross_threshold_a=None,
        negative_current_fraction_range=(0.05, 0.10),
        blanking_time_s=None,
        propagation_delay_s=None,
        timing_policy="adjustable on-time and off-time / constant off-time",
    ),
    startup_strategy=StartupStrategyModule(
        name="P24/P25 SCB zero-state startup - absent",
        compatibility=Compatibility.UNRESOLVED,
        provenance=Provenance(
            P24_FILE,
            "No startup section; P25 also has no startup section",
            "four-phase SCB",
            "No precharge, startup balancing or current-limit sequence is specified.",
        ),
        target_rule=None,
        current_limit_method=None,
        completion_event=None,
        extra_components=(),
        unresolved_adaptation=(),
    ),
)


THESIS_ZVS_COMMUTATION_CANDIDATE = CommutationParametersModule(
    name="charge-equivalent Coss energy/dead-time model",
    compatibility=Compatibility.GENERAL_PHYSICS_ONLY,
    provenance=Provenance(
        THESIS_FILE,
        "Chapter 6, Eqs. (6.1)-(6.5), PDF pp. 141-142 (printed pp. 123-124)",
        "cascaded resonant switched-capacitor converter",
        "Physics is reusable; example values and quarter-cycle timing are not "
        "automatically valid for the SCB state network.",
    ),
    c_high_f=None,
    c_low_f=None,
    nonlinear_coss_model=(
        "Coss_Qeq(Vds) = Qoss(Vds)/Vds = integral_0^Vds(Coss(v)dv)/Vds"
    ),
    dead_time_s=None,
    equations=(
        "L*Ioff^2 > Coss_total*Vswitch^2",
        "L*Ineg^2 > Coss_total*Vswitch^2",
        "Imin = sqrt(Coss_total*Vswitch^2/L)",
        "tdead_min = (pi/2)*sqrt(L*Coss_total), under the source paper assumptions",
    ),
)


THREE_LEVEL_PRECHARGE_CANDIDATE = StartupStrategyModule(
    name="two-series-MOSFET flying-capacitor precharge",
    compatibility=Compatibility.ADAPTATION_REQUIRED,
    provenance=Provenance(
        STARTUP_FILE,
        "Section III-C and Fig. 8, PDF pp. 4-5 (printed pp. 34-35)",
        "three-level buck with one flying capacitor",
        "The paper demonstrates the method in Saber and reports a 7 A peak for "
        "its example; 7 A is not an SCB design value.",
    ),
    target_rule="resistive divider sets flying-capacitor target to 0.5*Vin",
    current_limit_method=(
        "slowly ramp the gates of two small series MOSFETs so they act as "
        "voltage-controlled current sources in saturation"
    ),
    completion_event=(
        "comparator changes state at target voltage and turns off precharge MOSFETs"
    ),
    extra_components=(
        "two small external MOSFETs",
        "resistive divider",
        "comparator",
        "gate-ramp generator",
    ),
    unresolved_adaptation=(
        "derive targets for all three SCB series capacitors rather than one 0.5*Vin capacitor",
        "define safe sequential or simultaneous charging paths for C1-C3",
        "select device ratings and current ramp for 48 V/1 kW hardware",
        "prove that the added paths do not disturb normal SCB switching states",
    ),
)


CANDIDATE_MODULES = {
    "commutation_parameters": (THESIS_ZVS_COMMUTATION_CANDIDATE,),
    "boundary_controller": (),
    "startup_strategy": (THREE_LEVEL_PRECHARGE_CANDIDATE,),
}


def quarter_cycle_dead_time_s(inductance_h: float, coss_total_f: float) -> float:
    """Thesis Eq. (6.5); caller must validate topology compatibility."""
    if inductance_h <= 0 or coss_total_f <= 0:
        raise ValueError("inductance_h and coss_total_f must be positive")
    return (pi / 2.0) * sqrt(inductance_h * coss_total_f)


def minimum_commutation_current_a(
    inductance_h: float, coss_total_f: float, switching_voltage_v: float
) -> float:
    """Thesis Eq. (6.4); caller must validate topology compatibility."""
    if inductance_h <= 0 or coss_total_f <= 0 or switching_voltage_v <= 0:
        raise ValueError("all arguments must be positive")
    return sqrt(coss_total_f * switching_voltage_v**2 / inductance_h)


def primary_slots_complete() -> bool:
    """The primary P24/P25 slots remain unchanged until direct data exist."""
    return all(
        module.compatibility is not Compatibility.UNRESOLVED
        for module in (
            PRIMARY_EMPTY_SLOTS.commutation_parameters,
            PRIMARY_EMPTY_SLOTS.boundary_controller,
            PRIMARY_EMPTY_SLOTS.startup_strategy,
        )
    )

