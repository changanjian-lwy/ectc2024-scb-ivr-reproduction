"""A53 - a local, read-only-importing wrapper that exposes `phase_inductance_h`
as an explicit, overridable parameter to the boundary construction.

`BOUNDARY.md` Section 2 step 1.  This module does not modify, and is not
imported by, any A50/A51 file.  It imports `a51_period_map.py` (and, through
it, A50's own `solver_copy/`) READ-ONLY via `sys.path`, exactly the way A51
itself imports A50.

A51's own `build_boundary` (`a51_period_map.py`) hardcodes every
`ZeroStartBoundary` field it names and leaves every other field at the
dataclass's own default -- which already includes `phase_inductance_h`
(default `1.4666667e-9`, the paper's own nominal value). A51 simply never
plumbed it through as a keyword. This file is the same function with that one
additional keyword added, nothing else changed.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
A51_DIR = HERE.parent / "A51_four_phase_joint_zvs_solve"
if str(A51_DIR) not in sys.path:
    sys.path.insert(0, str(A51_DIR))

import a51_period_map as M  # noqa: E402
from solver_copy.evidence import Evidence  # noqa: E402
from solver_copy.zero_start_descriptor import ZeroStartBoundary  # noqa: E402

#: Re-exported for callers that only want this module (avoids a second
#: `sys.path` dance at every call site).
DEAD_TIME_S = M.DEAD_TIME_S
CFLY_F = M.CFLY_F
SWITCH_CAPACITANCE = M.SWITCH_CAPACITANCE
PHASE_CURRENT_LIMIT_A = M.PHASE_CURRENT_LIMIT_A
NOMINAL_LPHASE_H = 1.4666667e-9  # P24 Eq.(4)-derived, same value A24-A52 use.


def build_boundary(
    *,
    phase_inductance_h: float = NOMINAL_LPHASE_H,
    dead_time_s: float = DEAD_TIME_S,
    cfly_f: float = CFLY_F,
    switch_on_resistance_ohm: float = 1e-6,
    module_power_w: float = 250.0,
) -> ZeroStartBoundary:
    """A51's own `build_boundary`, with `phase_inductance_h` exposed.

    Every field not named here keeps `ZeroStartBoundary`'s own dataclass
    default, identical to A51's own construction. `switch_on_resistance_ohm`
    stays at A51's own `1e-6` (near-ideal) default for the SOLVE itself --
    `BOUNDARY.md` Section 2.4's `Ron=7 mOhm` is a separate, post-hoc
    conduction-loss ESTIMATE applied to the solved RMS currents, not a change
    to the dynamics being solved (the same reason A51/A52 kept the solver's
    own resistance idealized while reasoning about `RHS`/`RLS` separately).
    """
    return ZeroStartBoundary(
        phase_inductance_h=phase_inductance_h,
        flying_capacitances_f=(cfly_f, cfly_f, cfly_f),
        switch_on_resistance_ohm=switch_on_resistance_ohm,
        module_power_w=module_power_w,
        dead_time_s=dead_time_s,
        switch_capacitance=SWITCH_CAPACITANCE,
        evidence=Evidence.CROSS_PAPER_EXTENSION,
    )
