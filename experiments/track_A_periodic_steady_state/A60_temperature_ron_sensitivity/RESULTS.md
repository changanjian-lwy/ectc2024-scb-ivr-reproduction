# A60 - junction-temperature sensitivity: typical RDS(on)(Tj) from the EPC2067 datasheet (RESULTS)

Track A, `SENSITIVITY_ONLY`. Boundary: `BOUNDARY.md`, unmodified. Records:
`runs/*.json`, `results.json` (`build_a60_results.py`), the digitized
curve `epc2067_fig9_ron_vs_tj.csv` and `epc2067_fig9_digitization.json`.

## 0. Verdict

**The tuned large-ripple advantage shrinks steeply with junction
temperature and reverses at about Tj = 114 C.** All four devices of a
design are assumed at the same Tj, and each design is at its A59-tuned
fixed dead times, regulated to 250 W.

| Tj (typical device) | RDS(on) per device | large-ripple P_B | baseline P_B | large-ripple minus baseline |
|---:|---:|---:|---:|---:|
| 25 C | 1.300 mOhm | 23.938 W | 31.132 W | **-7.19 W** |
| 60 C | 1.552 mOhm | 28.705 W | 33.270 W | -4.56 W |
| 100 C | 1.857 mOhm | 34.641 W | 35.903 W | -1.26 W |
| 125 C | 2.062 mOhm | 38.658 W | 37.675 W | **+0.98 W** |

Linear interpolation between 100 and 125 C gives the break-even at
**114.1 C**. `P_B` uses Fig. 8's VSD, linearly interpolated in temperature
between its 25 C and 125 C curves.

- Reproduction anchor: RDS(on) = 1.55 mOhm exactly reproduces A59's tuned
  points bit-for-bit (28.671 / 33.255 W). The 60 C point (1.552 mOhm) is
  essentially the same, which confirms that A55-A59's 1.55 mOhm (the 25 C
  datasheet maximum) is the typical device at ~60 C.
- The optimum does not move with temperature. At 25 C and 125 C, moving
  `d_fall` by +/-0.1 ns is worse for both designs:

| | d_fall -0.1 | A59 d_fall | +0.1 |
|---|---:|---:|---:|
| large-ripple 25 C | 24.491 | **23.938** | 24.178 |
| large-ripple 125 C | 39.038 | **38.658** | 39.067 |
| baseline 25 C | 31.236 | **31.132** | 31.218 |
| baseline 125 C | 37.740 | **37.675** | 37.853 |

- The verdicts are unchanged at every Tj: large-ripple `FFFT/FFFT`,
  baseline `FFFF/FFFT`.

## 1. Mechanism

| | channel loss 25 -> 125 C | capacitive loss 25 -> 125 C |
|---|---|---|
| large-ripple | 23.42 -> 38.18 W (+14.8) | 0.22 -> 0.14 W |
| baseline | 16.08 -> 24.66 W (+8.6) | 14.87 -> 12.82 W |

The large-ripple design's loss is almost entirely channel conduction of a
~107 A rms phase current, so it scales with RDS(on). The baseline carries
only ~73 A rms. Its other large term is hard-switch capacitive loss,
which does not depend on RDS(on) directly. It falls slightly as `Tj` rises,
while the regulated `Ton_cmd` rises (18.24 -> 18.59 ns); that mechanism was
not analysed further.

## 2. What this means

- The A56-A59 advantage is a warm-device result: 4.6 W at ~60 C. At a
  realistic full-load junction temperature of 100-125 C it is 1.3 W to
  -1.0 W, before any inductor loss (A61: at 100 C, ~50 uOhm of inductor
  resistance erases the remaining 1.26 W).
- The actual Tj needs a thermal model. The datasheet gives
  `R_thJC = 0.4 C/W` and `R_thJB = 1.4 C/W` per device, but the board and
  cooling are unknown. Each device dissipates on the order of 1-2 W here
  (~30-38 W over 20 devices), so Tj depends strongly on the board, and the
  project cannot pin it down.

## 3. Limits

- Same Tj for every device of both designs, although the designs
  dissipate differently.
- Coss treated as temperature-independent (the datasheet gives no Coss(T)).
- VSD interpolated linearly between the two published temperatures.
- Rated load only; see A62 for other loads.

## 4. Reproduction

```
python3 digitize_epc2067_fig9.py <epc2067_datasheet.pdf>
python3 run_a60.py --design zvs --seed-json ../A59_nonlinear_coss_epc2067/runs/zvs_r1.950_f0.650.json --rise 1.95 --fall 0.65 --points 1.55mohm,60,100,125
python3 run_a60.py --design zvs --seed-json ../A59_nonlinear_coss_epc2067/runs/zvs_r1.950_f0.650.json --rise 1.95 --fall 0.65 --points 25
python3 run_a60.py --design zvs --seed-json runs/zvs_r1.950_f0.650_T25C.json --rise 1.95 --fall 0.55 --points 25,125   # and --fall 0.75; baseline likewise at 1.05 / 1.25
python3 build_a60_results.py
```
