# A60 - junction-temperature sensitivity: typical RDS(on)(Tj) from the EPC2067 datasheet (BOUNDARY)

Track: A. Classification: `SENSITIVITY_ONLY` device-model extension of
A59, with one new `EXTERNAL_DEVICE_DATA` input. Not a P24/P25
reproduction. Part of the user's 2026-09-28 direction to finish all
self-doable work before asking the advisor.

## 0. Why this experiment exists

The two designs lose power differently. The large-ripple design's loss is
mostly channel conduction (~28 W). The baseline's is ~18 W conduction plus
~13-14 W hard-switch capacitive loss. On-resistance rises with junction
temperature, so a hotter device penalizes the large-ripple design more.

Reading the datasheet table also showed that every A55-A59 run uses
`RDS(on) = 1.55 mOhm` per device, labelled typical in
`src/scb_ivr/device_library.py`. It is the **maximum at 25 C**; the typical
value is 1.3 mOhm. By Fig. 9, 1.55 mOhm equals the typical device at
Tj ~ 60 C. The A55-A59 conclusions therefore hold at one implicit
temperature. This experiment makes temperature an explicit variable.

## 1. Device data (`EXTERNAL_DEVICE_DATA`)

- EPC2067 datasheet (2021-10-21), table: `RDS(on)` typ 1.3 mOhm, max
  1.55 mOhm at 25 C, `VGS = 5 V`, `ID = 37 A`.
- Fig. 9, typical normalized `RDS(on)` vs `Tj`, digitized from the PDF
  vector path by `digitize_epc2067_fig9.py`. Self-check: k(25 C) = 1.0003.
  Values: k = 1.138 (50 C), 1.280 (75 C), 1.429 (100 C), 1.586 (125 C).
- The reverse drop comes from Fig. 8's 25 C and 125 C curves (A57). At an
  intermediate `Tj`, `VSD(I)` is linearly interpolated in temperature
  between them (`NUMERICAL_IDEALIZATION`; the datasheet gives only two
  temperatures).
- `Coss(V)` is A59's Fig. 5a model, held temperature-independent: the
  datasheet gives no `Coss(T)`. This is stated, not claimed.

## 2. Method

Per device `R(Tj) = 1.3 mOhm * k(Tj)`. High-side branch `R/2`, low-side
`R/3` (`NHS=2`, `NLS=3`), as A55's asymmetric-Ron boundary fields. The
dynamics, regulation to 250 W, accounting and nonlinear Coss are A59's.
The Ron used by A57's pricing credit is scoped to the boundary's actual
Ron for each point.

Temperatures: `Tj` in {25, 60, 100, 125} C. Plus one reproduction anchor:
`R = 1.55 mOhm` exactly must reproduce A59's tuned points to solver
tolerance.

At each `Tj`, both designs are regulated at A59's tuned `(d_rise, d_fall)`.
At 25 C and 125 C, `d_fall` is also moved one A59 grid step (0.1 ns) either
side, to confirm the optimum does not move. If it does move, the moved
optimum is used and reported.

Seeds: A59's tuned points, continued in temperature order (25 -> 60 ->
100 -> 125 C), each from the previous temperature.

## 3. Outputs

`P_A`, `P_B` (Fig. 8, temperature-interpolated), the ZVS verdicts,
`Ton_cmd` and peak current for both designs at each `Tj`. Also the
large-ripple-minus-baseline difference vs `Tj`, and the break-even `Tj`
(interpolated) if the sign changes.

## 4. Provenance

| Value | Source | Category |
|---|---|---|
| `RDS(on)` 1.3 mOhm typ (25 C); k(Tj) | EPC2067 table, Fig. 9 | `EXTERNAL_DEVICE_DATA` |
| Same Tj for all devices, VSD interpolation in T, Coss independent of T | This document | `PROJECT_DECISION` / `NUMERICAL_IDEALIZATION` |
| Everything else | A59 | inherited |

## 5. What the result can and cannot decide

Decides: whether the tuned large-ripple advantage (A59) survives realistic
junction temperatures, and at which `Tj` it vanishes, if it does.

Cannot decide: the actual junction temperature. That needs a thermal
model (`R_thJC` = 0.4 C/W and `R_thJB` = 1.4 C/W are published, but the
board and cooling are not). Also out of scope: unequal temperatures
between devices or designs, device spread, magnetic loss.

## 6. Constraints

Do not modify `src/scb_ivr/`, `results/`, `paper_locked/`, or any A37-A59
file. Never overwrite a result JSON. Retain failed points.
