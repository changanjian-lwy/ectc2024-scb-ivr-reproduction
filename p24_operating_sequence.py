"""Only the three operating intervals explicitly described by P24 Sec. II-B."""

from __future__ import annotations

from dataclasses import dataclass

from evidence import Evidence


@dataclass(frozen=True)
class P24Interval:
    name: str
    time_span: str
    explicitly_on: tuple[str, ...]
    explicitly_off: tuple[str, ...]
    current_statement: str
    commutation_statement: str
    end_condition: str
    unspecified_commands: tuple[str, ...]
    evidence: Evidence = Evidence.P24_EXPLICIT


P24_PHASE1_INTERVALS = (
    P24Interval(
        name="P24_I1_PHASE1_ENERGY",
        time_span="t0-t1",
        explicitly_on=("QH1", "QS2"),
        explicitly_off=(),
        current_statement="iL1 rises to twice its phase-average current",
        commutation_statement="L1 charges through Vin, QH1, C1 and Co/output",
        end_condition="t1: end of the high-side conduction interval",
        unspecified_commands=("QH2-QH4", "remaining low-side switches"),
    ),
    P24Interval(
        name="P24_I2_PHASE1_HS_OFF_LS_ZVS",
        time_span="t1-t2",
        explicitly_on=(),
        explicitly_off=("QH1",),
        current_statement=(
            "positive iL1 charges QH1 Coss and discharges QL1 Coss; "
            "iL1 reaches zero at the end of interval two"
        ),
        commutation_statement="QL1 may be turned on after its output capacitance is discharged",
        end_condition="t2: iL1 reaches zero",
        unspecified_commands=(
            "exact QL1 gate instant",
            "remaining phase gates",
            "dead time",
        ),
    ),
    P24Interval(
        name="P24_I3_PHASE1_NEGATIVE_AND_HS_ZVS",
        time_span="t2-t3",
        explicitly_on=("QL1 until its negative-current turn-off event",),
        explicitly_off=(),
        current_statement=(
            "iL1 becomes negative; QL1 turns off at 1%-2% of phase peak"
        ),
        commutation_statement=(
            "reverse iL1 discharges QH1 output capacitance toward the input; "
            "QH1 turns on when its drain-source voltage reaches zero"
        ),
        end_condition="t3: QH1 zero-voltage turn-on",
        unspecified_commands=(
            "complete four-phase gate vector",
            "negative-current detector realization",
            "Coss/snubber value",
            "dead time",
        ),
    ),
)
