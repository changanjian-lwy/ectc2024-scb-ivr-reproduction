# A57 - pricing A56's dead-time conduction with the EPC2067 datasheet reverse characteristic (RESULTS)

Track A, `SENSITIVITY_ONLY` post-processing of A56 plus one
`EXTERNAL_DEVICE_DATA` input. Boundary: `BOUNDARY.md`, unmodified. No orbit
was re-solved and no SPICE was run. Machine-readable record: `results.json`;
digitized curve: `epc2067_fig8_reverse_characteristics.csv` with provenance
in `epc2067_fig8_digitization.json`.

## 0. Verdict

**A56's 3.18 W ZVS advantage holds only if every gate turns on within about
0.4 ns of its natural zero crossing. Under the fixed symmetric dead time of
the A51/A56 scheduler, the datasheet reverse drop reverses the ranking by
about 7 W.**

All values are partial electrical-loss proxies at 250 W:

| point | Scenario A: ideal adaptive turn-on (A56 as computed) | Scenario B: fixed dead time, Fig. 8 25 C | Fig. 8 125 C | constant 1.2 V floor |
|---|---:|---:|---:|---:|
| baseline: 1.4667 nH, 2.15 ns | 31.382 W | **37.411 W** | 37.361 W | 34.372 W |
| best ZVS: 0.627406 nH, 2.15 ns | 28.206 W | **44.472 W** | 44.894 W | 35.605 W |
| ZVS minus baseline | **-3.18 W** | **+7.06 W** | +7.53 W | +1.23 W |

- Even the ZVS-most-favorable reading, the datasheet table's
  `VSD = 1.2 V` at 0.5 A, leaves the ZVS point 1.23 W worse under fixed dead
  time. At the actual per-device currents, the curve gives 2.27-2.52 V, far
  above A56's break-even drops of 0.90 V (2.15 ns) and 0.32 V (4.3 ns).
- At 4.3 ns the ZVS points are 33-35 W worse (Fig. 8). A longer fixed dead
  time only adds reverse-conduction time.
- Under fixed dead time, the lowest of all nine A56 candidates is the nominal
  L with the shortest dead time (1.075 ns): 31.89 W. This is the usual GaN
  lesson: keep reverse conduction short.
- Step independence: Scenario B is 37.411/37.409/37.408 W for the baseline and
  44.472/44.462/44.458 W for the ZVS point at 62.5/31.25/15.625 ps.

**What survives.** The ZVS advantage is real only in the adaptive limit.
With equal residual reverse time `t_r` on every admitted edge of both
designs, the ZVS point keeps a lower proxy only while `t_r` is below
**0.44 ns** (Fig. 8 25 C). The limit is 0.43 ns at 125 C, 0.37-0.49 ns across
the four ZVS candidates, and ~1.0 ns even at the 1.2 V floor. This is a
per-edge timing-accuracy requirement on the gate drive, not a result about
the power stage.

## 1. Did the math-model session supply the number?

No. Its new D05 (`symbolic_derivations/02_P25_native/D05_REVERSE_COMPLEMENTARITY.md`,
uncommitted at the time of this run) defines an explicit
`constant_drop_surrogate` with dissipation `Vf*r`. That is the same form as
A56's break-even and this experiment's Scenario B. D05 explicitly supplies no
real reverse drop, is P25 three-phase, is instantaneous only, and is not
wired to a periodic solver. It is consistent with this pricing, but it was
not imported.

## 2. The datasheet data

- Source: EPC2067 datasheet, "Revised October 21, 2021" (the revision
  `device_library.py` cites). SHA-256 of the file read:
  `8271d9eb71a3f78285c4c024ccfd06c33af129583c1bdef484d7dde01ae2324f`.
- Figure 8 (`VGS = 0 V`, typical, per device) was digitized from the PDF's
  vector Bezier paths, not from a raster image. The axis-map residual is at
  most 0.009 V. Zero current is anchored to the curves' flat `ISD=0` run. The
  tick-label-center alternative differs by 1.76 A, which only matters below
  a few amperes.
- Values at 25 C: 5 A 2.03 V, 25 A 2.24 V, 42 A 2.35 V, 50 A 2.40 V, 72 A
  2.53 V, 100 A 2.68 V, 200 A 3.18 V, 400 A 4.09 V. The 125 C curve crosses
  the 25 C curve near 50 A, so temperature barely matters in the operating
  range (22-72 A per device).
- **Datasheet internal inconsistency:** the table gives `VSD = 1.2 V typ` at
  0.5 A ("defined by design, not production tested"), while Fig. 8 reads
  ~1.8 V at 0.5 A. At 0.5 A the figure is only 0.2 pt tall, so it cannot
  resolve that point. The figure governs at operating current. 1.2 V is used
  only as the ZVS-favorable floor.
- The datasheet notes that a negative OFF gate bias raises the reverse drop.
  A 0 V OFF gate (EPC's recommendation) is assumed. A negative bias would
  make Scenario B worse for any candidate with reverse exposure.

## 3. Why the ZVS point is penalized

At the ZVS point, the large ripple that creates the high-side negative current
also puts +215 A on the low-side edge (72 A per device across `NLS=3`). That
node swing finishes about 0.7 ns into the 2.15 ns window. The remaining
~1.45 ns is spent at 2.52 V x 215 A (~540 W instantaneous): about 3.9-4.4 W per
phase and 16.2 W for four phases. The baseline's low-side edge carries 125 A
(42 A per device, 2.35 V) for ~1 ns, totaling 6.2 W. The ZVS point's high-side
edges add only 0.75 W at 2.15 ns, because the crossing lands 0.10 ns before
the window end.

| orbit | Ron loss replaced | reverse loss (Fig. 8 25 C) | residual-time slope |
|---|---:|---:|---:|
| baseline 2.15 ns | 0.172 W | 6.201 W | 5.76 W/ns |
| best ZVS 2.15 ns | 0.729 W | 16.995 W | 12.91 W/ns |
| best ZVS 4.3 ns | 1.790 W | 43.998 W | 12.21 W/ns |

Break-even residual time = Scenario A margin / slope difference =
3.18 W / (12.91 - 5.76) W/ns = 0.44 ns.

## 4. Method checks (`test_a57.py`, 8 tests, all pass)

- The digitized curves are monotone, match coarse visual reads of the figure,
  cross near 50 A, and lie above the 1.2 V floor at operating current.
- The Ron loss replaced inside the intervals reproduces A56's stored
  `channel_loss_metered_inside_surrogate_intervals_w` to 1e-9 W for all nine
  candidates.
- **Contract identity with A56:** substituting A56's own break-even constant
  drop for each ZVS candidate gives exactly zero Scenario B difference, to
  1e-9 W. This experiment uses A56's accounting unchanged; only the drop
  value is new.
- The population and dynamics Ron agree: `NHS=2`, `NLS=3`, and Ron equals
  1.55 mOhm / n.
- Mean-current versus rms-current evaluation of `VSD` changes every
  difference by at most 0.022 W (per-event rms/mean <= 1.05).

## 5. Stated approximations

- **First-order.** Orbits are not re-solved with a `-VSD` clamp. Holding the
  node at about -2.5 V instead of about 0 for 1-4 ns slightly perturbs the
  regulated operating point (`Ton_cmd` would shift), and this is neglected.
- **Equal current sharing** among parallel devices. The curve is typical,
  with no device spread.
- **Turn-on recharge** from `-VSD`: estimated at `0.5*C_node*VSD^2*f_sw` per
  event, with `C_node = 13.0 nF` (A56's measured high-side node, used for
  every event). It adds 0.72 W to the baseline and 1.50 W to the ZVS point,
  widening the Scenario B gap to +7.84 W. It is listed separately and is not
  in the headline.
- The residual-time analysis assumes the same `t_r` on every admitted edge
  and the event-mean current. It is illustrative and is not a gate-driver
  specification.

## 6. What this does and does not change

- A56's Scenario A numbers are unchanged. They are now explicitly the
  **ideal adaptive dead-time** result.
- "Rated-load ZVS pays for itself" is now conditional on sub-0.5 ns per-edge
  turn-on accuracy, in addition to A56's other open terms (Co(er)/Co(tr),
  magnetic loss, and negative current at ~39% of peak versus P24's 1-2%).
- Under the A51 fixed symmetric dead-time scheduler, the answer is "not
  worth it" by ~7 W. This agrees in sign with A53/A54's conclusion, but for a
  different reason: A53/A54 never priced reverse conduction, and their
  original arguments (unequal power, biased meter) remain invalid.
- Not decided: whether P24's hardware used adaptive dead time; gate-drive,
  magnetic, thermal and package loss; hardware efficiency; paper
  reproduction.

## 7. Reproduction

From this directory; both scripts refuse to overwrite their outputs:

```
python3 digitize_epc2067_fig8.py <path/to/epc2067_datasheet.pdf>   # checks revision; records SHA-256
python3 price_reverse_conduction.py
python3 test_a57.py -v
```

Requires `pymupdf` for digitization only. No A37-A56 file, `src/scb_ivr/`,
`results/` or `paper_locked/` file was modified.
