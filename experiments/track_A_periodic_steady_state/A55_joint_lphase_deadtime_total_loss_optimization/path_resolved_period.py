"""A55 phase-current path proxy evaluator; no optimizer or total-loss claims.

This adapter reuses A51's event sequence and A53's monitor structure
read-only. It adds only the high-side/low-side/dead-time ``i^2 dt`` accounting
required by A55's initial path gate. Asymmetric dynamics are supplied by the
separate scoped descriptor extension. The 2026-09-26 audit identified that
phase current is not generally the enabled switch channel current in this
flying-capacitor network. The loss returned here is a historical proxy;
audit_accepted_orbit.py meters actual resistive branch voltages for power.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

HERE = Path(__file__).resolve().parent
A53_DIR = HERE.parent / "A53_lphase_zvs_load_tradeoff"
A51_DIR = HERE.parent / "A51_four_phase_joint_zvs_solve"
if str(A51_DIR) not in sys.path:
    sys.path.insert(0, str(A51_DIR))
if str(A53_DIR) not in sys.path:
    sys.path.insert(0, str(A53_DIR))

import a51_period_map as M  # noqa: E402
import a53_solve as S  # noqa: E402
from scb_ivr.conduction_loss import (  # noqa: E402
    ConductionLossResult,
    PathI2Accumulator,
    PathI2Integrals,
    path_resolved_conduction_loss,
)
from scb_ivr.device_library import (  # noqa: E402
    EPC2067,
    P24_EPC2067_POPULATION,
)


@dataclass
class PathResolvedMonitor(S.RmsMonitor):
    # A51's turn-on resolver first probes the whole dead-time window and then
    # backtracks to a refined natural crossing. Keep a rollback-capable sample
    # list so provisional post-crossing samples are not integrated twice.
    path_samples: list[
        tuple[float, tuple[float, ...], tuple[bool, ...], tuple[bool, ...]]
    ] = field(default_factory=list)

    def observe(self, step: M.HybridStep) -> None:
        super().observe(step)
        currents = tuple(float(step.state[self.index[f"L{phase}"]]) for phase in range(1, 5))
        tolerance = 1e-21
        while self.path_samples and self.path_samples[-1][0] > step.time_s + tolerance:
            self.path_samples.pop()
        self.path_samples.append(
            (
                step.time_s,
                currents,
                step.mode.high_side_on,
                step.mode.low_side_on,
            )
        )

    def path_integrals(self, *, period_s: float) -> PathI2Integrals:
        accumulator = PathI2Accumulator(phase_count=4)
        for time_s, currents, high, low in self.path_samples:
            accumulator.observe(
                time_s=time_s,
                phase_currents_a=currents,
                high_side_on=high,
                low_side_on=low,
            )
        return accumulator.integrals(period_s=period_s)


def evaluate_period_map_with_paths(
    boundary,
    z: NDArray[np.float64],
    *,
    coarse_step_s: float = 62.5e-12,
    sub_step_s: float = 2e-12,
    diode_state: tuple[bool, bool, bool] = (False, False, False),
    t0: float | None = None,
) -> tuple[M.PeriodResult, PathI2Integrals, ConductionLossResult]:
    """Evaluate one period and expose the three mutually exclusive paths."""

    start_s = M.period_start_s(boundary) if t0 is None else t0
    names = M.variable_names(boundary)
    index = {name: position for position, name in enumerate(names)}
    if np.asarray(z).shape != (len(names),):
        raise ValueError(f"state must have {len(names)} entries")
    monitor = PathResolvedMonitor(index=index)
    current = M._initial_step(boundary, z, start_s, diode_state)
    monitor.observe(current)
    result = M.PeriodResult(z_next=np.empty(0))
    for interval in M.period_intervals(boundary, start_s):
        if interval.kind == "normal":
            current = M._march(
                current, interval.end_s, coarse_step_s, boundary, diode_state, monitor
            )
        elif interval.kind == "turn_on":
            result.turn_on_entry[interval.phase_index] = current  # type: ignore[index]
            current, verdict = M._resolve_turn_on(
                boundary,
                current,
                interval.phase_index,  # type: ignore[arg-type]
                interval.end_s,
                sub_step_s,
                diode_state,
                monitor,
            )
            result.turn_on.append(verdict)
        else:
            current, verdict = M._resolve_turn_off(
                boundary,
                current,
                interval.phase_index,  # type: ignore[arg-type]
                interval.end_s,
                sub_step_s,
                diode_state,
                monitor,
            )
            result.turn_off.append(verdict)
    result.z_next = current.state.copy()
    result.monitor = monitor
    result.final_step = current
    result.turn_on.sort(key=lambda verdict: verdict.phase_index)
    result.turn_off.sort(key=lambda verdict: verdict.phase_index)

    integrals = monitor.path_integrals(period_s=boundary.period_s)
    loss = path_resolved_conduction_loss(
        EPC2067,
        P24_EPC2067_POPULATION,
        integrals,
    )
    return result, integrals, loss
