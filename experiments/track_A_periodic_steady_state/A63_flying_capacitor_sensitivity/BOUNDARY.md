# A63 - flying-capacitor sensitivity of the tuned comparison (BOUNDARY)

Track: A. Classification: `SENSITIVITY_ONLY`. Not a P24/P25
reproduction. Part of the user's 2026-09-28 direction to finish all
self-doable work before asking the advisor. The flying-capacitor value is
item 7 of `results/MINIMUM_INFORMATION_REQUEST.md`.

## 0. Why this experiment exists

Since A51 every four-phase solve has used `C1 = C2 = C3 = 3 uF`, a
`SENSITIVITY_ONLY` choice. The independent first-principles estimate
(`paper_locked/00_boundaries/CFLY_FIRST_PRINCIPLES_ESTIMATE.md`) spans
~0.6-8.7 uF. The advisor named a part (Murata GRM32EC72A106KE05L: 10 uF,
100 V, X7S, 1210) whose DC-bias-derated value at 12-36 V and whose count
per position are unknown. Murata's DC-bias data could not be retrieved
non-interactively. Before chasing those data, this experiment asks the
cheaper question: does the tuned comparison depend on `Cfly` at all?

## 1. Declared boundary

- Model: A59's reference model at each design's A59-tuned
  `(d_rise, d_fall)`, regulated to 250 W, unchanged except
  `C1 = C2 = C3 = Cfly`.
- `Cfly in {1, 2, 3, 6} uF`, where 3 uF reproduces A59. The runs continue
  3 -> 2 -> 1 and 3 -> 6, each seeded by its neighbour.
- Dead times are not retuned. If a verdict changes (ZVS lost or gained),
  that is reported as the finding.

## 2. Outputs

`P_A`, `P_B`, the large-ripple-minus-baseline difference, ZVS verdicts,
residual voltages and flying-capacitor voltage ripple for each `Cfly`.

## 3. What the result can and cannot decide

Decides: whether the A59 conclusion is robust across the plausible `Cfly`
range. If it is, the exact `Cfly` is not needed for this question. If not,
the derated value becomes a blocking item.

Cannot decide: the actual `Cfly`, ESR/ESL, unequal `C1..C3`, startup
behaviour, or paper reproduction.

## 4. Provenance

| Value | Source | Category |
|---|---|---|
| `Cfly` range | first-principles estimate, advisor-named part (value unknown) | `SENSITIVITY_ONLY` |
| Everything else | A59 | inherited |

## 5. Constraints

Do not modify `src/scb_ivr/`, `results/`, `paper_locked/`, or any A37-A62
file. Never overwrite a result JSON. Retain failed points.
