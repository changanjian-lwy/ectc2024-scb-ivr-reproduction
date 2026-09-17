"""Source values and model-calibrated control targets without provenance loss."""

from __future__ import annotations

from dataclasses import dataclass

from scb_ivr.evidence import Evidence


@dataclass(frozen=True)
class NegativeCurrentTarget:
    target_id: str
    fraction_of_phase_peak: float
    evidence: Evidence
    source_location: str
    applicability: str
    default_for_current_model: bool = False

    def current_a(self, phase_peak_a: float) -> float:
        if phase_peak_a <= 0:
            raise ValueError("phase_peak_a must be positive")
        return -self.fraction_of_phase_peak * phase_peak_a


P24_ONE_PERCENT = NegativeCurrentTarget(
    "p24_lower_bound_1pct", 0.01, Evidence.P24_EXPLICIT,
    "P24 Sec. II-B, third interval", "P24 source lower boundary"
)
P24_TWO_PERCENT = NegativeCurrentTarget(
    "p24_upper_bound_2pct", 0.02, Evidence.P24_EXPLICIT,
    "P24 Sec. II-B, third interval", "P24 source upper boundary"
)
P25_FIVE_PERCENT = NegativeCurrentTarget(
    "p25_design_5pct", 0.05, Evidence.P25_SUPPLEMENT,
    "P25 Sec. III and Eq. (20)", "P25 source design target"
)
P25_TEN_PERCENT = NegativeCurrentTarget(
    "p25_mode4_upper_10pct", 0.10, Evidence.P25_SUPPLEMENT,
    "P25 Sec. II, Mode 4", "P25 source textual upper boundary"
)

# This is deliberately scoped to the exact R04D3 local model. It must be
# recalibrated if L, Coss view/population, voltage, topology or initial state changes.
R04D3_GS61008T_SCALAR_MIN_ZVS = NegativeCurrentTarget(
    "r04d3_gs61008t_scalar_min_zvs_7p77pct",
    0.0777,
    Evidence.MODEL_CALIBRATION,
    "R04D3D refined sweep: 7.76% fails, 7.77% first reaches Vds(QH1)=0",
    (
        "P24 local phase-1 commutation; Vin=48 V, Vo=1 V, L=1.4666667 nH, "
        "Ipk=125 A, GS61008T CO(TR)=385 pF, one HS and two parallel LS devices, "
        "Cfly=53.8 uF, R04D2A-chained t2 state"
    ),
    default_for_current_model=False,
)

R04D3_IDEAL_OPERATING_EIGHT_PERCENT = NegativeCurrentTarget(
    "r04d3_ideal_operating_8pct",
    0.08,
    Evidence.MODEL_CALIBRATION,
    "R04D3D margin sweep: 8% leaves -2.37994 A at the high-side zero-Vds event",
    (
        "Same exact applicability as the R04D3 7.77% threshold; selected as the "
        "smallest whole-percent value above the numerical threshold for ideal-stage continuation"
    ),
    default_for_current_model=True,
)

NEGATIVE_CURRENT_TARGETS = (
    P24_ONE_PERCENT,
    P24_TWO_PERCENT,
    P25_FIVE_PERCENT,
    P25_TEN_PERCENT,
    R04D3_GS61008T_SCALAR_MIN_ZVS,
    R04D3_IDEAL_OPERATING_EIGHT_PERCENT,
)


def current_model_default() -> NegativeCurrentTarget:
    defaults = tuple(t for t in NEGATIVE_CURRENT_TARGETS if t.default_for_current_model)
    if len(defaults) != 1:
        raise RuntimeError("exactly one current-model default is required")
    return defaults[0]
