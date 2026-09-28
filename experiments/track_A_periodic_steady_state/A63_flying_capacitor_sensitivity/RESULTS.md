# A63 - flying-capacitor sensitivity of the tuned comparison (RESULTS)

Track A, `SENSITIVITY_ONLY`. Boundary: `BOUNDARY.md`, unmodified. Records:
`runs/*.json` (1, 2 and 6 uF; the 3 uF points are A59's), `results.json`
(`build_a63_results.py`, which also replays each orbit for the
flying-capacitor voltages), `logs/`.

## 0. Verdict

**The A59 conclusion is robust across 1-6 uF. The exact flying-capacitor
value is not needed for this question.** The large-ripple design barely
moves. The baseline gets worse as `Cfly` shrinks, so the advantage grows.

| Cfly (all three) | large-ripple P_B | baseline P_B | large-ripple minus baseline |
|---:|---:|---:|---:|
| 1 uF | 28.738 W | 34.865 W | -6.13 W |
| 2 uF | 28.683 W | 33.649 W | -4.97 W |
| 3 uF (A59) | 28.671 W | 33.255 W | -4.58 W |
| 6 uF | 28.699 W | 32.872 W | -4.17 W |

All points regulated to 250 W at the A59-tuned dead times, with no
retuning. The ZVS/hard verdicts are unchanged across `Cfly`: large-ripple
`FFFT/FFFT`, baseline `FFFF/FFFT`.

## 1. Mechanism

| Cfly | VC ripple p-p, large-ripple | VC ripple p-p, baseline | baseline high-side residual at turn-on | baseline capacitive loss |
|---:|---:|---:|---:|---:|
| 1 uF | 1.51-1.53 V | 1.18 V | 12.5-12.8 V | 15.31 W |
| 2 uF | 0.77 V | 0.59 V | 12.1-12.5 V | 14.42 W |
| 3 uF | 0.51-0.52 V | 0.39 V | 12.0-12.3 V | 14.14 W |
| 6 uF | 0.26 V | 0.20 V | 11.9-12.2 V | 13.86 W |

A smaller `Cfly` lets the flying-capacitor voltages swing more. Some
baseline switches then hard-switch from a higher residual voltage, and the
capacitive loss grows roughly with its square. The large-ripple design
turns on near zero voltage, where that swing hardly matters: its
residuals are 0.8-1.5 V and its capacitive loss stays 0.18-0.20 W. Mean
flying-capacitor voltages stay at ~35.9 / 23.9 / 11.9 V (3/4, 1/2, 1/4 of
48 V) in all cases.

## 2. Consequence for the advisor request

Item 7 of `results/MINIMUM_INFORMATION_REQUEST.md` (C1..C3 values, ESR,
ESL, DC-bias derating) is not blocking for the loss comparison over this
range. It remains relevant to startup (Track B) and to paper-level
reproduction.

## 3. Limits

- Equal `C1 = C2 = C3`; no ESR or ESL.
- Dead times not retuned per `Cfly`, since the fixed-timing design is the
  one tested.
- Everything else is A59's reference model (Tj ~ 60 C).

## 4. Reproduction

```
python3 run_cfly.py --design zvs --seed-json ../A59_nonlinear_coss_epc2067/runs/zvs_r1.950_f0.650.json --rise 1.95 --fall 0.65 --cfly-uf 2,1
python3 run_cfly.py --design zvs --seed-json ../A59_nonlinear_coss_epc2067/runs/zvs_r1.950_f0.650.json --rise 1.95 --fall 0.65 --cfly-uf 6
python3 run_cfly.py --design baseline --seed-json ../A59_nonlinear_coss_epc2067/runs/baseline_r2.150_f1.150.json --rise 2.15 --fall 1.15 --cfly-uf 2,1
python3 run_cfly.py --design baseline --seed-json ../A59_nonlinear_coss_epc2067/runs/baseline_r2.150_f1.150.json --rise 2.15 --fall 1.15 --cfly-uf 6
python3 build_a63_results.py
```
