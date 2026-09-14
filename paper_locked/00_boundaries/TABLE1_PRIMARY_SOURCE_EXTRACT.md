# Table 1 primary-source extraction and independent ratio re-check (2026-09-14)

## Purpose

`PAPER_LOCKED_REPRODUCTION_BASELINE.md` and the Mihai progress report both
state that Table 1's `nP=4` row (this project's mainline) sits at a
non-clean `~1.83x` ratio against Eq. (4), while the `nP=6`, `nP=8` and
`nP=16` rows sit at clean `2x`, `~2x` and `~1x` ratios respectively. That
claim had previously been recorded only as a recalculated ratio table,
without the raw printed Table 1 text archived alongside it. This closes that
gap: the project's own Q&A prep (`QA_PREP_CN_2026-09-14.md`, Q1) had flagged
"re-check the `nP=4` row's raw inputs against the paper by hand" as a fast,
not-yet-done item. This document performs and archives that check.

## Extraction method

Text extracted directly from the source PDF (`Package_Power_Delivery_
Architecture_for_High_Performance_Computing_Systems_With_a_1_kW_IVR_
Operated_in_CCM-DCM_Boundary_Mode_Condition (1).pdf`, Table 1, page 4) using
`pymupdf`, not re-typed by hand and not taken from any prior secondary
summary.

## Raw printed Table 1 (`nM=4` sub-row of each `nP` group, 5 MHz column only)

| `nP` | `nM` | Power/module (W) | Duty | `Ton` @5MHz | `Lcrit` @5MHz (table) | `IL,pk` (A) |
|---:|---:|---:|---:|---:|---:|---:|
| 4 | 4 | 250 | 8.4% | 16.7 ns | 2.68 nH | 125 |
| 6 | 4 | 250 | 12.5% | 25 ns | 4.2 nH | 83.4 |
| 8 | 4 | 250 | 16.7% | 33.5 ns → (per-column 5 MHz cell) 5.32 nH | 5.32 nH | 62.5 |
| 16 | 4 | 250 | 33.3% | 67 ns | 4.27 nH | 31.25 |

(The `nM=4` sub-row is used for all four groups because it is the row this
project's mainline (`nP=4`) actually uses — one 250 W module — and holding
`nM` fixed while varying `nP` is the only way to compare groups without
introducing a second changed variable.)

## Eq. (4) recalculation, same rows

`Lcrit = nP*nM*Vo*(1-nP*Vo/Vin)/(2*Io*fsw)`, `Vin=48 V`, `Vo=1 V`,
`Io=1000 A`, `fsw=5 MHz`:

| `nP` | `D=nP*Vo/Vin` | Eq.(4) `Lcrit` @5MHz | Table `Lcrit` @5MHz | table/Eq.(4) |
|---:|---:|---:|---:|---:|
| 4 | 0.08333 | 1.4667 nH | 2.68 nH | 1.8276 |
| 6 | 0.12500 | 2.1000 nH | 4.2 nH | 2.0000 |
| 8 | 0.16667 | 2.6667 nH | 5.32 nH | 1.9950 |
| 16 | 0.33333 | 4.2667 nH | 4.27 nH | 1.0008 |

## Result

This independently reproduces, from freshly extracted primary-source text
rather than from any prior recalculation, the exact pattern already recorded
in `PAPER_LOCKED_REPRODUCTION_BASELINE.md`: three of four `nP` groups
(`6`, `8`, `16`) sit at a clean `2x`, `~2x` and `~1x` multiple of the Eq. (4)
prediction, while `nP=4` — the row this project's mainline depends on — sits
at a non-clean, intermediate `~1.83x` that resolves to neither.

This also directly closes the raw-input transcription check: `Vin=48 V`,
`Vo=1 V`, `nP=4`, `nM=4`, `fsw=5 MHz`, `Ton=16.7 ns`, `IL,pk=125 A` and
`Lcrit(table)=2.68 nH` all match the printed Table 1 cell exactly as already
used throughout this project's `paper_locked` documents and netlists. No
transcription error was found on this project's side.

## Prohibited claims

This is a primary-source verification exercise only. It does not run any
new SPICE experiment, does not change the adopted `1.4667 nH` value, does
not promote `2.68 nH` to a candidate, and does not by itself prove the
`nP=4` row is a paper error rather than a project-side error — it only rules
out the specific project-side error (mistyped raw input) that was flagged as
unchecked. The standing conclusion (paper table row) remains a documented
open question for Mihai, not a resolved fact.
