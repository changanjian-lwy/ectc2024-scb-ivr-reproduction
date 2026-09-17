"""Event-driven startup rotation controller with separate P24/P25 branches.

No timing labels are used as transition conditions.  The P24-minimal branch
closes the same-phase t0-t3 cycle and deliberately blocks before an unsupported
phase handoff.  The P25-extension branch rotates a generic k -> k+1 handoff and
is never relabelled as P24 evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from scb_ivr.evidence import Evidence


class RotationBranch(str, Enum):
    P24_MINIMAL = "P24_MINIMAL"
    P25_TO_P24_FOUR_PHASE_EXTENSION = "P25_TO_P24_FOUR_PHASE_EXTENSION"


class StartupState(str, Enum):
    ACTIVE_ENERGY = "ACTIVE_ENERGY"
    ACTIVE_HS_COMMUTATION = "ACTIVE_HS_COMMUTATION"
    ACTIVE_LS_FREEWHEEL = "ACTIVE_LS_FREEWHEEL"
    ACTIVE_NEGATIVE_CURRENT = "ACTIVE_NEGATIVE_CURRENT"
    ACTIVE_HS_ZVS_COMMUTATION = "ACTIVE_HS_ZVS_COMMUTATION"
    NEXT_PHASE_ZERO_WAIT = "NEXT_PHASE_ZERO_WAIT"
    NEXT_PHASE_NEGATIVE_CURRENT = "NEXT_PHASE_NEGATIVE_CURRENT"
    NEXT_PHASE_HS_ZVS_COMMUTATION = "NEXT_PHASE_HS_ZVS_COMMUTATION"
    BLOCKED_P24_HANDOFF_UNPUBLISHED = "BLOCKED_P24_HANDOFF_UNPUBLISHED"


class StartupEvent(str, Enum):
    ACTIVE_CURRENT_LIMIT = "ACTIVE_CURRENT_LIMIT"
    ACTIVE_LOW_SIDE_VDS_ZERO = "ACTIVE_LOW_SIDE_VDS_ZERO"
    ACTIVE_CURRENT_ZERO = "ACTIVE_CURRENT_ZERO"
    ACTIVE_NEGATIVE_TARGET = "ACTIVE_NEGATIVE_TARGET"
    ACTIVE_HIGH_SIDE_VDS_ZERO = "ACTIVE_HIGH_SIDE_VDS_ZERO"
    NEXT_CURRENT_ZERO = "NEXT_CURRENT_ZERO"
    NEXT_NEGATIVE_TARGET = "NEXT_NEGATIVE_TARGET"
    NEXT_HIGH_SIDE_VDS_ZERO = "NEXT_HIGH_SIDE_VDS_ZERO"


@dataclass(frozen=True)
class RotationController:
    n_p: int
    branch: RotationBranch
    active_phase: int = 1
    state: StartupState = StartupState.ACTIVE_ENERGY
    cycles_completed: int = 0

    def __post_init__(self) -> None:
        if self.n_p < 2:
            raise ValueError("n_p must be explicit and at least 2")
        if not 1 <= self.active_phase <= self.n_p:
            raise ValueError("active phase outside n_p")

    @property
    def next_phase(self) -> int:
        return self.active_phase % self.n_p + 1

    @property
    def evidence(self) -> Evidence:
        return (
            Evidence.P24_EXPLICIT
            if self.branch is RotationBranch.P24_MINIMAL
            else Evidence.CROSS_PAPER_EXTENSION
        )

    def commanded_on(self) -> tuple[str, ...]:
        all_lows = tuple(f"S{k}b" for k in range(1, self.n_p + 1))
        if self.branch is RotationBranch.P24_MINIMAL:
            if self.state is StartupState.ACTIVE_ENERGY:
                return (f"S{self.active_phase}a", f"S{self.next_phase}b")
            if self.state is StartupState.ACTIVE_HS_COMMUTATION:
                return (f"S{self.next_phase}b",)
            if self.state in {
                StartupState.ACTIVE_LS_FREEWHEEL,
                StartupState.ACTIVE_NEGATIVE_CURRENT,
            }:
                return (f"S{self.active_phase}b", f"S{self.next_phase}b")
            if self.state is StartupState.ACTIVE_HS_ZVS_COMMUTATION:
                return (f"S{self.next_phase}b",)
            return ()
        if self.state is StartupState.ACTIVE_ENERGY:
            return (f"S{self.active_phase}a",) + tuple(
                switch for switch in all_lows if switch != f"S{self.active_phase}b"
            )
        if self.state in {
            StartupState.ACTIVE_HS_COMMUTATION,
            StartupState.NEXT_PHASE_HS_ZVS_COMMUTATION,
        }:
            return tuple(
                switch for switch in all_lows if switch != f"S{self.active_phase}b"
            )
        if self.state in {
            StartupState.ACTIVE_LS_FREEWHEEL,
            StartupState.ACTIVE_NEGATIVE_CURRENT,
            StartupState.ACTIVE_HS_ZVS_COMMUTATION,
            StartupState.NEXT_PHASE_ZERO_WAIT,
            StartupState.NEXT_PHASE_NEGATIVE_CURRENT,
        }:
            return all_lows
        return ()

    def transition(self, event: StartupEvent) -> "RotationController":
        if self.branch is RotationBranch.P24_MINIMAL:
            table = {
                (StartupState.ACTIVE_ENERGY, StartupEvent.ACTIVE_CURRENT_LIMIT): StartupState.ACTIVE_HS_COMMUTATION,
                (StartupState.ACTIVE_HS_COMMUTATION, StartupEvent.ACTIVE_LOW_SIDE_VDS_ZERO): StartupState.ACTIVE_LS_FREEWHEEL,
                (StartupState.ACTIVE_LS_FREEWHEEL, StartupEvent.ACTIVE_CURRENT_ZERO): StartupState.ACTIVE_NEGATIVE_CURRENT,
                (StartupState.ACTIVE_NEGATIVE_CURRENT, StartupEvent.ACTIVE_NEGATIVE_TARGET): StartupState.ACTIVE_HS_ZVS_COMMUTATION,
                (StartupState.ACTIVE_HS_ZVS_COMMUTATION, StartupEvent.ACTIVE_HIGH_SIDE_VDS_ZERO): StartupState.BLOCKED_P24_HANDOFF_UNPUBLISHED,
            }
        else:
            table = {
                (StartupState.ACTIVE_ENERGY, StartupEvent.ACTIVE_CURRENT_LIMIT): StartupState.ACTIVE_HS_COMMUTATION,
                (StartupState.ACTIVE_HS_COMMUTATION, StartupEvent.ACTIVE_LOW_SIDE_VDS_ZERO): StartupState.NEXT_PHASE_ZERO_WAIT,
                (StartupState.NEXT_PHASE_ZERO_WAIT, StartupEvent.NEXT_CURRENT_ZERO): StartupState.NEXT_PHASE_NEGATIVE_CURRENT,
                (StartupState.NEXT_PHASE_NEGATIVE_CURRENT, StartupEvent.NEXT_NEGATIVE_TARGET): StartupState.NEXT_PHASE_HS_ZVS_COMMUTATION,
            }
            if (
                self.state is StartupState.NEXT_PHASE_HS_ZVS_COMMUTATION
                and event is StartupEvent.NEXT_HIGH_SIDE_VDS_ZERO
            ):
                return replace(
                    self,
                    active_phase=self.next_phase,
                    state=StartupState.ACTIVE_ENERGY,
                    cycles_completed=self.cycles_completed + 1,
                )

        destination = table.get((self.state, event))
        if destination is None:
            raise ValueError(f"illegal event {event.value} while in {self.state.value}")
        return replace(self, state=destination)


def assert_gate_interlock(controller: RotationController) -> None:
    gates = set(controller.commanded_on())
    for phase in range(1, controller.n_p + 1):
        if {f"S{phase}a", f"S{phase}b"} <= gates:
            raise AssertionError(f"shoot-through command in phase {phase}")
