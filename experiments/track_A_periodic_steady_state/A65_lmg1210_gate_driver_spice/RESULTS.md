# A65 - A64 with a real gate driver: TI LMG1210's output stage (RESULTS)

Track A, `SENSITIVITY_ONLY`. Boundary: `BOUNDARY.md` (commit `1399585`), with
its amendment 4 made before any record and a wording-only scope correction
(2026-09-29). LTspice 26.0.2 (macOS, Wine). Records:
- `runs/*.json`, one per solved point, never overwritten;
- `results.json`, built by `build_a65_results.py`;
- `logs/*.txt`.

The EPC library is fetched into the git-ignored `vendor/` and is not in
this repository. Neither is the LMG1210 datasheet: only the digitized
curves (`lmg1210_output_iv.csv`) and the PDF's hash are.

## 0. Verdict

**With a real commercial driver, one LMG1210 output per device, the tuned
large-ripple design still loses to the tuned baseline at 250 W, by
11.7 W.** The real driver lands between A64's two resistor cases, closer to
the 1 Ohm end.

| 250 W, Tj 60 C, each design at its own tuned timing | LMG1210 per device (A65) | A64 R_drv 0.3 Ohm | A64 R_drv 1.0 Ohm |
|---|---:|---:|---:|
| large-ripple 0.627 nH: P_loss = P_in - P_out | **52.23 W** | 36.95 W | 61.09 W |
| baseline 1.467 nH: P_loss | **40.55 W** | 35.75 W | 43.74 W |
| **large-ripple minus baseline** | **+11.68 W** | +1.20 W | +17.35 W |
| same, device loss only (passive R removed) | +11.63 W | +1.18 W | +17.27 W |
| same, including gate-drive energy | +11.65 W | +1.15 W | +17.32 W |
| change vs A59 (-4.58 W, ideal switch) | +16.21 W | +5.76 W | +21.86 W |

- **The mechanism is A64's, with one addition that belongs to this driver**
  (Section 2).
  - The baseline pays ~20 W of hard turn-on, whatever the driver.
  - The large-ripple design avoids that, but pays:
    - +11 W of conduction from its circulating current;
    - +11.3 W of extra turn-off overlap: its high side is commanded off
      at ~162 A against the baseline's ~101 A;
    - +5.7 W of under-driven channel.
  - **New with LMG1210: +3.3 W of reverse conduction.** Its pull-up is
    weak (1.68 A) and its pull-down strong (3.64 A). The incoming channel
    therefore turns on ~1 ns after the outgoing one turns off, even at zero
    command dead time. At the fall edge that is ~1.1 ns of third-quadrant
    conduction at ~160 A. Command overlap to close the gap costs more
    (Section 1).
- **Gate energy is a wash.** It is 8.41 W vs 8.44 W; the per-device drive
  energy is the same in both designs.
- **One LMG1210 per 2-device switch is infeasible for the high side**
  (BOUNDARY Section 2). The gate reaches only 3.2 V within the on-time.
  The per-device arrangement reported here is the strongest arrangement
  commercial output stages allow, so the result is optimistic for the
  large-ripple design.

## 1. Loss grids (P_loss = P_in - P_out - dE_stored/T, W, 50 ps max step)

`c` = channel-matched centre. Bold = optimum. `NC` = not converged under
A64's stop criteria (value of the last chunk shown). Every other point is
`REGULATED_TO_250W`.

**Large-ripple.**

The centre search did not converge to the channel targets (A59's
1.95 / 0.65 ns). The slow pull-up keeps the fall channel dead time at
≥ ~1 ns even at zero command dead time (BOUNDARY amendment 4). The search
stopped at (0.49, -0.25) ns, and the centre point was solved at
(0.5, -0.25).

d_fall line at d_rise 0.5 ns:

| d_fall (ns) | -0.55 | -0.45 | -0.35 | -0.25c | -0.15 | -0.05 | 0.05 | 0.15 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| P_loss | 65.65 | 62.49 | 59.93 | 57.99 | 56.71 | 55.95 | 55.69 | 55.73 |

d_rise line at d_fall 0.05 ns (declared +0.1 ns edge extensions):

| d_rise (ns) | 0.2 | 0.3 | 0.4 | 0.5 | 0.6 | 0.7 | 0.8 | 0.9 | 1.0 | 1.1 | 1.2 | 1.3 | 1.4 | 1.5 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| P_loss | 60.10 | 58.34 | 56.89 | 55.69 | 54.73 | 53.94 | 53.37 | 52.89 | 52.56 | 52.40 | 52.37 | 52.23 | **52.23** | 52.23 |

- **Bracket completion at d_rise 1.4.** d_fall -0.05 gives 52.43, 0.05
  gives **52.232**, and 0.15 gives 52.31.
- **d_rise is flat from 1.3 to 1.5 ns.** The spread is 2 mW, below the
  run-to-run noise.
- **Why so much rise dead time?** Rise-edge ZVS (4 of 4 phases) needs a
  channel rise dead time of ≥ ~2.2 ns, reached from d_rise 0.7 ns. Below
  that, the high side turns on before the node has risen.

**Baseline** (centre search `CHANNEL_MATCHED` at (2.23, 0.05)).

d_fall line at d_rise 2.25 ns:

| d_fall (ns) | -0.25 | -0.15 | -0.05 | 0.05c | 0.15 | 0.25 | 0.35 | 0.45 | 0.55 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| P_loss | 50.72 | 47.87 | 45.52 | 43.70 | 42.36 | 41.67 NC | 40.87 | 40.56 | 40.57 |

d_rise line at d_fall 0.45 ns:

| d_rise (ns) | 1.95 | 2.05 | 2.15 | 2.25 | 2.35 | 2.45 | 2.55 |
|---|---:|---:|---:|---:|---:|---:|---:|
| P_loss | NC (40.0-41.5) | **40.55** | 40.57 | 40.56 | 40.67 | 40.71 | 40.67 |

**The baseline optimum sits next to a non-converged point.** The declared
edge extension to d_rise 1.95 ns was attempted four times
(`_v2`-`_v4`) with identical results; LTspice is deterministic. There the
Ton regulator alternates between 249.6 and 250.4 W, and P_loss between 40.0
and 41.5 W (last ten chunks: mean 40.5 W). It does not diverge.

The baseline surface is flat to ±0.02 W over d_rise 2.05-2.25 ns. Its true
optimum can therefore be at most a few tenths of a watt below 40.55 W. That
moves the headline by less than 5%.

## 2. Loss decomposition at the optima (vendor model, Coss-corrected, W)

Method: A64's `decompose_states` (A64 RESULTS Section 3), unchanged. The
vendor-model Coss table was re-measured into this directory (`coss` stage):
- C(0) = 2440 pF, C(12 V) = 1808 pF, Q(12 V) = 26.44 nC;
- 25 C vs 60 C differ by < 2e-4.

These are fresh 3-period re-runs from the accepted states. Their P_loss
agrees with the accepted records to within 0.006 W.

| state | large-ripple | baseline | difference | A64 0.3 Ohm diff | A64 1.0 Ohm diff |
|---|---:|---:|---:|---:|---:|
| conduction (Vgs >= 4.5 V) | 22.50 | 11.47 | +11.03 | +12.65 | +11.17 |
| turn-on overlap | 0.29 | 20.16 | **-19.87** | -19.63 | -19.52 |
| turn-off overlap | 14.42 | 3.10 | **+11.32** | +4.81 | +19.16 |
| under-driven (turn-on + turn-off) | 9.56 | 3.83 | +5.73 | +2.87 | +5.66 |
| third quadrant (reverse conduction) | 4.63 | 1.32 | **+3.31** | +0.43 | +0.75 |
| off state | 0.33 | 0.27 | +0.06 | +0.01 | +0.02 |
| **sum (dissipative)** | 51.71 | 40.15 | +11.56 | +1.15 | +17.21 |

Findings:

- **Turn-off overlap.**
  - LMG1210's 3.64 A sink falls between the two resistors. Command-to-
    channel turn-off of the high side (fall edge) takes 4.09 ns, against
    2.3 ns (0.3 Ohm) and 4.9 ns (1.0 Ohm) in A64.
  - The large-ripple high side is commanded off at ~162 A (the phase
    current peaks at 219 A); the baseline's at ~101 A.
  - The turn-off overlap penalty (+11.3 W) sits between A64's +4.8 and
    +19.2 W.
- **Reverse conduction.**
  - LMG1210's 1.68 A source makes channel turn-on slow. The low side turns
    on 5.1 ns after its command at the fall edge, against 1.3 ns
    (0.3 Ohm) and 2.8 ns (1.0 Ohm) in A64.
  - At the large-ripple fall edge, the low side reverse-conducts for
    1.10-1.22 ns before its channel turns on, against 0.12-0.20 ns
    (0.3 Ohm) and 0.39-0.50 ns (1.0 Ohm) in A64. The current there is
    ~160 A; 4.3 W of the 4.6 W is on the low side.
  - Closing the gap with command overlap costs more: d_fall -0.05 gives
    +0.19 W.
  - A resistor driver has no such asymmetry.
- **Where the two A64 cases agree, A65 agrees too.**
  - The baseline's hard turn-on costs 19.7-20.2 W in all three cases.
  - Conduction (baseline / large-ripple) is 11.5 / 22.5 W, against A64's
    11.5-12.6 / 22.7-25.2 W.
  - The full-gate on-resistance is 1.52-1.61 mOhm per device.

## 3. What this settles

- **A64's open question is closed.** A64's gate driver was a free
  resistor. The best commercial arrangement puts the answer at +11.7 W,
  not at the +1.2 W corner.
  - Consequence for the consolidation: the "cold device + 0.3 Ohm drive"
    corner could have flipped the sign, because A60 found 2.6 W more
    advantage at 25 C.
  - With a real driver it cannot: 2.6 W is well short of 11.7 W.
- **Amendment 4 was necessary, but did not bind at the optimum.**
  - Negative command dead times were explored (-0.55 to -0.05 ns). They
    are worse.
  - The large-ripple optimum's d_fall is +0.05 ns: channel 1.09 ns,
    above the 0.65 ns target.
  - Without the amendment, the centre search and the d_fall line could not
    have shown this.
- **The optima need timing accuracy that the part does not have.**
  LMG1210's minimum dead time spreads -0.55 / 0.8 / 3.1 ns part to part,
  and its high/low matching is up to 3.4 ns (BOUNDARY Section 4). On the
  grids above, 0.6-0.7 ns of fall-edge error costs about 10 W in either
  design: large-ripple d_fall 0.05 → -0.55 (at d_rise 0.5); baseline
  0.45 → -0.25. Fixed timing is not viable for either design. Only
  closed-loop adaptive timing reaches these optima.

## 4. Limits

- Everything in A64's limits: the 4-module row, one operating point
  (250 W, 60 C), no gate-loop inductance, and the vendor model as
  distributed.
- The driver is its *typical* output I-V: the curves, which are stronger
  than the table's typical values. There is no temperature or supply
  variation, and no propagation-delay spread.
- Each device has an ideal floating 5 V supply. In the SCB, the sources of
  high sides 1-3 sit on flying-capacitor nodes, so real supplies are
  isolated or cascaded-bootstrap (BOUNDARY Section 2).

## 5. Reproduction

```
A65_WORKDIR=<scratch> python3 run_a65.py --design zvs      --stages center,sweep --case LMG1210_DEV:60
A65_WORKDIR=<scratch> python3 run_a65.py --design baseline --stages center,sweep --case LMG1210_DEV:60
# declared bracket completion: d_rise 1.5 at d_fall 0.05; d_fall -0.05 / 0.15 at d_rise 1.4
A65_WORKDIR=<scratch> python3 run_a65.py --design zvs      --stages coss,decomp --case LMG1210_DEV:60
A65_WORKDIR=<scratch> python3 run_a65.py --design baseline --stages decomp      --case LMG1210_DEV:60
python3 build_a65_results.py
```

`python3 fetch_epc2067_model.py` first, to fetch and hash-check the vendor
library.
