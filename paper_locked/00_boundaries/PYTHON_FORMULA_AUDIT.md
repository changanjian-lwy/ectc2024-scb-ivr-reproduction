# Python formula audit

## Locked hierarchy

1. `ivr_framework.py` contains only the P24 analytical core.
2. `apec2025_supplements.py` may import P24 results and supplement a missing
   implementation detail; P24 never imports P25.
3. Cross-paper generalizations return a value together with provenance. They
   are not bare numbers that can silently enter a P24 report.
4. Table values remain independent comparison data and are never fitted back
   into an equation.

## P24 formula map

| Python function | Source | Status | Boundary |
|---|---|---|---|
| `SystemSpec.iout_a` | `Io=Po/Vo` | `P24_DERIVED` | DC output target |
| `duty_cycle` | P24 Eq. (1) | `P24_EXPLICIT` | step-down condition `nP*Vo/Vin<1` |
| `inductor_peak_current` | P24 Eq. (2) | `P24_EXPLICIT` | zero-to-peak triangular boundary waveform |
| `high_side_on_time` | P24 Eq. (3) | `P24_EXPLICIT` | positive frequency and valid architecture |
| `critical_inductance` | P24 Eq. (4) | `P24_EXPLICIT` | preserved literally; Table-I conflict retained |
| `parallel_embedded_inductors` | P24 Eq. (5) | explicit real-valued result | integer ceiling is a separate `PROJECT_DECISION` |
| `unit_embedded_inductance` | P24 Eq. (6) | `P24_EXPLICIT` | peak rating is an external design input |

## Corrections made in this audit

- Removed the P25 Eq. (20) generalization from the P24 formula-core module.
- Created `apec2025_supplements.py`; its generalized result is tagged
  `CROSS_PAPER_EXTENSION`.
- Added missing validation of `SystemSpec` and phase count to P24 Eq. (3).
- Renamed the UI's `(1-margin)*Lcrit` output from a “recommended inductance” to
  an `EXPLORATORY_ASSUMPTION`. P24 states a negative-current range, but the UI's
  arbitrary linear scaling must not masquerade as a printed P24 formula.
- Kept the P24 Eq. (4)/Table-I mismatch visible; no fitting was introduced.

## Remaining formula-level caution

The Python equations reproduce what is printed. That does not resolve the
internal Eq. (4)/Table-I inconsistency. The recalculated branch and printed
table branch must remain separate until the source of that discrepancy is
identified.
