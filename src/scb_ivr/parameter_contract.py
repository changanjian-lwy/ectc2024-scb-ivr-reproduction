"""Minimum information contract for progressively stronger reproduction claims."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum, IntEnum


class ClaimLevel(IntEnum):
    EQUATION_AUDIT = 1
    LOCAL_ZVS = 2
    PERIODIC_MULTIPHASE = 3
    HARDWARE_PERFORMANCE = 4


class ResolutionRoute(str, Enum):
    AUTHOR_CONFIRMATION = "author_confirmation"
    DATASHEET_OR_VENDOR_MODEL = "datasheet_or_vendor_model"
    MEASURED_WAVEFORM = "measured_waveform"
    PARAMETRIC_SWEEP = "parametric_sweep"


@dataclass(frozen=True)
class ParameterRequirement:
    key: str
    category: str
    unit_or_format: str
    first_required_for: ClaimLevel
    preferred_route: str
    reason: str
    already_known: bool = False
    current_source: str | None = None

    def as_dict(self) -> dict:
        row = asdict(self)
        row["first_required_for"] = self.first_required_for.name
        return row


REQUIREMENTS = (
    ParameterRequirement(
        "operating_point",
        "system",
        "Vin, Vo, Pout, fsw, nP, nM",
        ClaimLevel.EQUATION_AUDIT,
        ResolutionRoute.AUTHOR_CONFIRMATION.value,
        "defines the paper row being reproduced",
        True,
        "P24 Table I / P25 Table II",
    ),
    ParameterRequirement(
        "inductor_large_signal_model",
        "power_stage",
        "L(I,f,T), DCR and tolerance",
        ClaimLevel.LOCAL_ZVS,
        ResolutionRoute.DATASHEET_OR_VENDOR_MODEL.value,
        "sets current slope and commutation energy; nominal L alone is insufficient",
    ),
    ParameterRequirement(
        "switch_identity_and_population",
        "device",
        "part number and HS/LS parallel count",
        ClaimLevel.LOCAL_ZVS,
        ResolutionRoute.AUTHOR_CONFIRMATION.value,
        "selects the applicable nonlinear device charge and resistance model",
    ),
    ParameterRequirement(
        "nonlinear_qoss_model",
        "device",
        "Qoss(V) or validated nonlinear SPICE model",
        ClaimLevel.LOCAL_ZVS,
        ResolutionRoute.DATASHEET_OR_VENDOR_MODEL.value,
        "determines commutation charge and energy instead of a fitted scalar Coss",
    ),
    ParameterRequirement(
        "added_snubber_values",
        "device",
        "CH/CL and connection for every switch position",
        ClaimLevel.LOCAL_ZVS,
        ResolutionRoute.AUTHOR_CONFIRMATION.value,
        "P24/P25 mention added capacitance but do not publish a complete value set",
    ),
    ParameterRequirement(
        "dead_time_and_driver_delay",
        "control",
        "commanded dead time plus propagation mismatch",
        ClaimLevel.LOCAL_ZVS,
        ResolutionRoute.AUTHOR_CONFIRMATION.value,
        "defines the available commutation time and reverse-conduction interval",
    ),
    ParameterRequirement(
        "negative_current_definition",
        "control",
        "threshold, reference peak definition and detector location",
        ClaimLevel.LOCAL_ZVS,
        ResolutionRoute.AUTHOR_CONFIRMATION.value,
        "1-2% and 5-10% are unusable quantitatively until the referenced peak is defined",
    ),
    ParameterRequirement(
        "flying_capacitor_network",
        "power_stage",
        "C1..C(nP-1), ESR, ESL and bias derating",
        ClaimLevel.PERIODIC_MULTIPHASE,
        ResolutionRoute.AUTHOR_CONFIRMATION.value,
        "controls ladder ripple, charge return and phase-to-phase coupling",
    ),
    ParameterRequirement(
        "complete_gate_timing_policy",
        "control",
        "event order plus common/per-phase Ton corrections",
        ClaimLevel.PERIODIC_MULTIPHASE,
        ResolutionRoute.AUTHOR_CONFIRMATION.value,
        "a local ZVS event does not determine the full interleaved periodic scheduler",
    ),
    ParameterRequirement(
        "periodic_state_or_waveforms",
        "state",
        "flying-node voltages and phase currents at one timestamp",
        ClaimLevel.PERIODIC_MULTIPHASE,
        ResolutionRoute.MEASURED_WAVEFORM.value,
        "provides a reproducible shooting seed and an independent state-return check",
    ),
    ParameterRequirement(
        "layout_parasitics",
        "hardware",
        "loop L/R, capacitor ESL and interconnect resistance",
        ClaimLevel.HARDWARE_PERFORMANCE,
        ResolutionRoute.AUTHOR_CONFIRMATION.value,
        "required for switching loss, overshoot and EMI claims",
    ),
    ParameterRequirement(
        "thermal_operating_conditions",
        "hardware",
        "junction/ambient temperature and cooling boundary",
        ClaimLevel.HARDWARE_PERFORMANCE,
        ResolutionRoute.MEASURED_WAVEFORM.value,
        "device resistance and loss cannot be validated without temperature",
    ),
)


@dataclass(frozen=True)
class SweepVariable:
    key: str
    range_or_rule: str
    purpose: str
    limitation: str

    def as_dict(self) -> dict:
        return asdict(self)


SWEEP_VARIABLES = (
    SweepVariable(
        "negative_current_fraction",
        "P24 native 1-2%; P25 supplement 5-10%; never merge the labels",
        "map local charge/energy admission and sensitivity",
        "cannot establish which branch the P24 hardware actually used",
    ),
    SweepVariable(
        "inductance",
        "reported value, equation-derived value, then a labelled tolerance sweep",
        "test current-ramp and fixed-frequency closure",
        "cannot replace a large-signal L(I,f,T) model",
    ),
    SweepVariable(
        "commutation_energy_and_charge",
        "symbolic or bounded Ecomm/Qcomm until nonlinear Qoss is sourced",
        "solve the maximum admissible unknown device burden",
        "a fitted scalar capacitance is not a device identification",
    ),
    SweepVariable(
        "available_commutation_time",
        "symbolic, then sensitivity around sourced dead time and delay",
        "separate energy sufficiency from timing sufficiency",
        "cannot validate a controller without measured or author-confirmed delay",
    ),
    SweepVariable(
        "periodic_state_seed",
        "shooting/continuation variable only",
        "find and test a periodic state-return candidate",
        "is not evidence of zero-start or precharge behavior",
    ),
)


def requirements_for(claim_level: ClaimLevel) -> tuple[ParameterRequirement, ...]:
    return tuple(
        requirement
        for requirement in REQUIREMENTS
        if requirement.first_required_for <= claim_level
    )


def missing_requirements(
    claim_level: ClaimLevel, supplied_keys: set[str] | frozenset[str] = frozenset()
) -> tuple[ParameterRequirement, ...]:
    return tuple(
        requirement
        for requirement in requirements_for(claim_level)
        if not requirement.already_known and requirement.key not in supplied_keys
    )


def request_payload(claim_level: ClaimLevel) -> dict:
    return {
        "target_claim": claim_level.name,
        "rule": (
            "Only missing items required at or below the selected claim level are "
            "requested; sweepable numerical variables do not replace author-defined topology or control semantics."
        ),
        "missing": [
            requirement.as_dict()
            for requirement in missing_requirements(claim_level)
        ],
        "safe_sweeps_while_waiting": [
            variable.as_dict() for variable in SWEEP_VARIABLES
        ],
    }
