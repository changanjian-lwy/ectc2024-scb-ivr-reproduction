"""A55-only asymmetric high-/low-side Ron extension.

The A50/A51 solver owns one uniform ``switch_on_resistance_ohm`` field. This
module leaves those historical files untouched. It builds their descriptor
first, then applies an exact conductance-matrix correction to each *enabled*
switch branch so the high and low sides can use different effective
resistances. A scoped context redirects A51's imported descriptor hooks only
while an A55 solve is running and restores them afterward.

The context is intentionally single-thread-only because it temporarily swaps
module globals. A55 optimization must run serially, which also matches the
project's LTspice/continuation discipline.
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterator

import numpy as np

HERE = Path(__file__).resolve().parent
A51_DIR = HERE.parent / "A51_four_phase_joint_zvs_solve"
A54_DIR = HERE.parent / "A54_epc2067_lphase_joint_tradeoff"
if str(A51_DIR) not in sys.path:
    sys.path.insert(0, str(A51_DIR))
if str(A54_DIR) not in sys.path:
    sys.path.insert(0, str(A54_DIR))

import a51_period_map as M  # noqa: E402
import a54_boundary as B  # noqa: E402
import solver_copy.zero_start_descriptor as D  # noqa: E402
import solver_copy.zero_start_hybrid_solver as H  # noqa: E402


ORIGINAL_ASSEMBLE_DESCRIPTOR = D.assemble_descriptor


@dataclass(frozen=True)
class AsymmetricRonBoundary(D.ZeroStartBoundary):
    """A50 boundary plus population-corrected channel resistances."""

    # Use the high-side value as the base assembly resistance; the matrix
    # correction is then exactly zero for enabled high-side branches.
    switch_on_resistance_ohm: float = 0.775e-3
    high_side_on_resistance_ohm: float = 0.775e-3
    low_side_on_resistance_ohm: float = 1.55e-3 / 3.0

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.high_side_on_resistance_ohm <= 0:
            raise ValueError("high-side on-resistance must be positive")
        if self.low_side_on_resistance_ohm <= 0:
            raise ValueError("low-side on-resistance must be positive")


def build_epc2067_boundary(
    *,
    phase_inductance_h: float = B.NOMINAL_LPHASE_H,
    dead_time_s: float = B.DEAD_TIME_S,
    cfly_f: float = B.CFLY_F,
    module_power_w: float = 250.0,
) -> AsymmetricRonBoundary:
    """Build the A55 EPC2067 boundary without modifying A54's builder."""

    return AsymmetricRonBoundary(
        phase_inductance_h=phase_inductance_h,
        flying_capacitances_f=(cfly_f, cfly_f, cfly_f),
        module_power_w=module_power_w,
        dead_time_s=dead_time_s,
        switch_capacitance=B.SWITCH_CAPACITANCE,
        evidence=B.Evidence.CROSS_PAPER_EXTENSION,
    )


def _branch_vector(
    node_names: tuple[str, ...], pair: tuple[str, str | None]
) -> np.ndarray:
    index = {name: position for position, name in enumerate(node_names)}
    vector = np.zeros(len(node_names), dtype=float)
    first, second = pair
    vector[index[first]] += 1.0
    if second is not None:
        vector[index[second]] -= 1.0
    return vector


def assemble_descriptor(boundary, mode, time_s):
    """Return A50's descriptor with enabled-switch conductances corrected."""

    system = ORIGINAL_ASSEMBLE_DESCRIPTOR(boundary, mode, time_s)
    if not isinstance(boundary, AsymmetricRonBoundary):
        return system
    a = system.a.copy()
    n_nodes = len(system.node_names)
    reference_g = 1.0 / boundary.switch_on_resistance_ohm
    for enabled, pair in zip(mode.high_side_on, D.HIGH_SIDE_BRANCHES):
        if enabled:
            branch = _branch_vector(system.node_names, pair)
            delta_g = 1.0 / boundary.high_side_on_resistance_ohm - reference_g
            a[:n_nodes, :n_nodes] += delta_g * np.outer(branch, branch)
    for enabled, pair in zip(mode.low_side_on, D.LOW_SIDE_BRANCHES):
        if enabled:
            branch = _branch_vector(system.node_names, pair)
            delta_g = 1.0 / boundary.low_side_on_resistance_ohm - reference_g
            a[:n_nodes, :n_nodes] += delta_g * np.outer(branch, branch)
    return replace(system, a=a)


@contextmanager
def asymmetric_ron_context() -> Iterator[None]:
    """Route one serial A55 solve through the asymmetric descriptor."""

    old_m = M.assemble_descriptor
    old_h = H.assemble_descriptor
    M.assemble_descriptor = assemble_descriptor
    H.assemble_descriptor = assemble_descriptor
    try:
        yield
    finally:
        M.assemble_descriptor = old_m
        H.assemble_descriptor = old_h
