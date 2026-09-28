# A62 - load sweep at fixed 250 W-tuned dead times (RESULTS)

Track A, `SENSITIVITY_ONLY`. Boundary: `BOUNDARY.md`, unmodified, plus one
added load (225 W) to locate the crossover. Records: `runs/*.json`,
`results.json` (`build_a62_results.py`).

## 0. Verdict

**The large-ripple design wins only near full load. Below about 211 W
(84% of rated) the baseline has lower loss. At light load the gap is
large, because the large-ripple design's ~22 W loss floor does not fall
with load.**

A59 reference model (Tj ~ 60 C). Each design keeps its 250 W-tuned
`(d_rise, d_fall)`, and `Vout` is regulated to 1 V at each load.

| P out | large-ripple P_B | baseline P_B | difference | efficiency proxy, large-ripple / baseline |
|---:|---:|---:|---:|---|
| 250 W | 28.67 W | 33.26 W | -4.58 W | 89.7% / 88.3% |
| 225 W (added) | 26.55 W | 28.24 W | -1.69 W | 89.4% / 88.8% |
| 200 W | 25.13 W | 23.77 W | **+1.36 W** | 88.8% / 89.4% |
| 150 W | 23.11 W | 16.64 W | +6.47 W | 86.7% / 90.0% |
| 100 W | 22.07 W | 11.76 W | +10.31 W | 81.9% / 89.5% |
| 50 W | 22.04 W | 9.14 W | +12.90 W | 69.4% / 84.5% |
| 25 W | 22.40 W | 8.69 W | +13.71 W | 52.7% / 74.2% |

Linear interpolation puts the crossover at **211 W**. The efficiency proxy
is `P/(P + P_B)`. It excludes gate drive (~8.6 W), inductor loss and
magnetics, so it is not comparable with P24's measured efficiency.

All 14 points regulated. Peak currents fall with load: from 217 A to
156 A (large-ripple) and from 128 A to 70 A (baseline).

## 1. Mechanism

| P out | large-ripple channel / capacitive / reverse | baseline channel / capacitive / reverse |
|---:|---|---|
| 250 W | 28.17 / 0.19 / 0.32 | 18.94 / 14.14 / 0.19 |
| 200 W | 24.03 / 0.30 / 0.81 | 13.50 / 10.26 / 0.01 |
| 100 W | 18.29 / 0.97 / 2.91 | 6.29 / 5.47 / 0.00 |
| 25 W | 16.22 / 1.76 / 4.59 | 4.03 / 4.66 / 0.00 |

- **Large-ripple.** The ~300 A p-p ripple is set by `L`, `Vin` and timing,
  not by load. Its ~87 A AC rms keeps the channel loss at 16 W even at
  25 W out. Below 200 W the high side is all natural ZVS, and it finishes
  its transition earlier. The fixed `d_rise` therefore leaves longer
  reverse conduction (0.3 -> 4.6 W). The low side becomes partially hard,
  at 2.6-4.3 V residual.
- **Baseline.** Its conduction loss falls roughly with the square of the
  DC current (18.9 -> 4.0 W). As load falls the valley current goes more
  negative, so the high-side hard-switch residual drops (12.0 -> 3.7 V) and
  its capacitive loss falls too. At light load the low side becomes
  partially hard (1-6 V residual), because the slower low-side transition
  outlasts the fixed 1.15 ns window.
- The crossover is not an artifact of fixed dead times. With ideal adaptive
  turn-on (`P_A`), the large-ripple design is already worse at 200 W
  (24.34 vs 23.76 W) and better at 225 W (26.18 vs 28.15 W).

## 2. What this means

The A56-A59 ranking is a rated-load statement. Any realistic mission
profile weights part load heavily, and that favors the baseline by a wide
margin. The large-ripple design pays for its full-load ZVS with a
load-independent circulating-current floor. Recovering light-load
efficiency would need load-adaptive measures outside this boundary: phase
shedding, variable frequency or burst modes, or adaptive dead time.

## 3. Limits

- Fixed dead times across load (the declared realistic case).
- Tj ~ 60 C at every load (in reality Tj falls at light load, which helps
  the large-ripple design less than the baseline because its loss does
  not fall).
- No inductor, gate-drive or magnetic loss.
- Not a paper reproduction.

## 4. Reproduction

```
python3 run_load_sweep.py --design zvs --seed-json ../A59_nonlinear_coss_epc2067/runs/zvs_r1.950_f0.650.json --rise 1.95 --fall 0.65 --powers 250,200,150,100,50,25
python3 run_load_sweep.py --design baseline --seed-json ../A59_nonlinear_coss_epc2067/runs/baseline_r2.150_f1.150.json --rise 2.15 --fall 1.15 --powers 250,200,150,100,50,25
python3 run_load_sweep.py --design zvs --seed-json runs/zvs_r1.950_f0.650_P250W.json --rise 1.95 --fall 0.65 --powers 225   # baseline likewise
python3 build_a62_results.py
```
