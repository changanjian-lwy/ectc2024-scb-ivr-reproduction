"""A54 - a local, read-only-importing wrapper that exposes `phase_inductance_h`
as an explicit, overridable parameter on the boundary construction, with
EPC2067's own device parameters plugged in instead of GS61008T's.

`BOUNDARY.md` Section 2. This module does not modify, and is not imported by,
any A50/A51/A53 file. It imports `a51_period_map.py` (and, through it, A50's
own `solver_copy/`) READ-ONLY via `sys.path`, exactly the way A51 and A53
already do. It is a sibling of `A53`'s own `a53_boundary.py` (same structure,
same reasoning), not an edit to it -- A53's own file is untouched.

Device-parameter swap, `BOUNDARY.md` Section 2:
- `switch_on_resistance_ohm` stays at the near-ideal `1e-6` default for the
  SOLVER itself (identical reasoning to A53's own file: the conduction-loss
  `Ron` is a separate, post-hoc estimate applied to the solved RMS currents,
  not a change to the dynamics being solved). The POST-HOC conduction-loss
  `Ron` used by `run_three_point_analysis.py` is EPC2067's own raw
  single-device `1.55 mOhm` (uniform, NOT population-divided -- `BOUNDARY.md`
  Section 2's explicit instruction to mirror A51/A53's own simplification).
- `switch_capacitance` uses EPC2067's own `Co(tr)_(0-20V) = 1860 pF` per
  device (`paper_locked/04_component_models/EPC2067_typical_params.lib`),
  P24 Table 3's own `NHS=2`/`NLS=3` population for this `nP=4`/`nM=4` row
  (`paper_locked/04_component_models/EPC2067_commutation_capacitance.lib`):
  `CH_TOTAL = 2*1860pF = 3720 pF`, `CL_TOTAL = 3*1860pF = 5580 pF`.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
A51_DIR = HERE.parent / "A51_four_phase_joint_zvs_solve"
if str(A51_DIR) not in sys.path:
    sys.path.insert(0, str(A51_DIR))

import a51_period_map as M  # noqa: E402
from solver_copy.commutation_capacitance import CommutationCapacitance  # noqa: E402
from solver_copy.evidence import Evidence  # noqa: E402
from solver_copy.zero_start_descriptor import ZeroStartBoundary  # noqa: E402

#: Re-exported for callers that only want this module (avoids a second
#: `sys.path` dance at every call site).
DEAD_TIME_S = M.DEAD_TIME_S
CFLY_F = M.CFLY_F
PHASE_CURRENT_LIMIT_A = M.PHASE_CURRENT_LIMIT_A
NOMINAL_LPHASE_H = 1.4666667e-9  # P24 Eq.(4)-derived, same value A24-A53 use.

#: EPC2067 datasheet, revised 2021-10-21 (`EXTERNAL_DEVICE_DATA`), per
#: `paper_locked/04_component_models/EPC2067_typical_params.lib`.
EPC2067_RDS_TYP_25C_OHM = 1.55e-3
EPC2067_COTR_0_20V_F = 1860e-12
#: P24's own printed Table 3, nP=4/nM=4 row (2 parallel high-side, 3 parallel
#: low-side), per `EPC2067_commutation_capacitance.lib`'s own header.
NHS = 2
NLS = 3
#: A42/A51/A53's own GS61008T device, for the direct side-by-side comparison
#: this experiment reports against (unchanged, read-only, for reference only
#: -- never used to build a boundary in this file).
GS61008T_RON_OHM = 7e-3

#: EPC2067's own commutation capacitance for this Table-3 population,
#: `CH_TOTAL=3720 pF`, `CL_TOTAL=5580 pF` -- replaces GS61008T's `385/770 pF`.
SWITCH_CAPACITANCE = CommutationCapacitance(
    high_device_f=NHS * EPC2067_COTR_0_20V_F,
    low_device_f=NLS * EPC2067_COTR_0_20V_F,
    device_evidence=Evidence.EXTERNAL_DEVICE_DATA,
)


def build_boundary(
    *,
    phase_inductance_h: float = NOMINAL_LPHASE_H,
    dead_time_s: float = DEAD_TIME_S,
    cfly_f: float = CFLY_F,
    switch_on_resistance_ohm: float = 1e-6,
    module_power_w: float = 250.0,
) -> ZeroStartBoundary:
    """A51/A53's own `build_boundary`, with `phase_inductance_h` exposed and
    EPC2067's own `switch_capacitance` plugged in (Section 2).

    Every field not named here keeps `ZeroStartBoundary`'s own dataclass
    default, identical to A51/A53's own construction. `switch_on_resistance_
    ohm` stays at the near-ideal `1e-6` default for the SOLVE itself --
    `BOUNDARY.md` Section 2's `Ron=1.55 mOhm` is a separate, post-hoc
    conduction-loss ESTIMATE applied to the solved RMS currents downstream,
    not a change to the dynamics being solved (same reasoning A51/A53 use).
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
