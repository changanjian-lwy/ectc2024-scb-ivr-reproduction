"""Cross-source candidates that cannot silently satisfy P24 primary slots."""

from evidence import Evidence
from model_contracts import Module, Slot


CANDIDATE_ADAPTERS = (
    Module(
        "isscc2019_self_trimmed_zcd_candidate",
        Slot.CONTROLLER,
        Evidence.CROSS_PAPER_EXTENSION,
        "ISSCC 2019 8.5-A FIVR",
        "Fig. 8.5.2 and ZCD discussion",
        frozenset({"candidate_negative_current_detector"}),
        requires=frozenset({"controller_scaling_validation"}),
        note=(
            "Provides comparator auto-zero/trim and residual-current ideas at a "
            "very different voltage/current/integration scale; not a P24 controller."
        ),
    ),
    Module(
        "epe2019_auxiliary_startup_candidate",
        Slot.STARTUP,
        Evidence.CROSS_PAPER_EXTENSION,
        "EPE 2019 four-phase CSC buck",
        "Startup Operation, Figs. 4-5",
        frozenset({"candidate_startup_initialization"}),
        requires=frozenset({"p24_startup_topology_compatibility"}),
        note=(
            "Four-phase and 48-V evidence is relevant, but the CSC switch "
            "reconfiguration and capacitor targets differ from P24 Fig. 3."
        ),
    ),
    Module(
        "three_level_active_precharge_candidate",
        Slot.STARTUP,
        Evidence.CROSS_PAPER_EXTENSION,
        "three-level buck soft-start paper",
        "Sec. III-C and Fig. 8",
        frozenset({"candidate_startup_initialization"}),
        requires=frozenset({"p24_startup_topology_compatibility"}),
        note="One flying capacitor and different topology; adaptation required.",
    ),
    Module(
        "thesis_coss_energy_candidate",
        Slot.COMMUTATION,
        Evidence.CROSS_PAPER_EXTENSION,
        "Hybrid switched-capacitor converter thesis",
        "Chapter 6, Eqs. (6.1)-(6.5)",
        frozenset({"commutation_energy_inequality"}),
        requires=frozenset({"p24_commutation_topology_compatibility"}),
        note=(
            "Reusable energy-screening physics only; does not supply the P24 "
            "numeric capacitance or dead time."
        ),
    ),
)
