# A70 - a valley-switching fallback for the high-side turn-on (RESULTS)

Track A, `CROSS_PAPER_EXTENSION`. Boundary: `BOUNDARY.md`, with its
Section 7 amendment, a stall-detection fix made before run 4 was rerun.
Records: `run_*.json`.

## 0. Verdict

**The published fallback removes A69's deadlock, and it does not disturb
the orbit.** The rule is Chiang and Chen's (TPEL 2009): when ZVS is not
reached, turn on at the resonant valley of Vds.
- **Deadlock start.** Started from the state that deadlocked in A69, the
  circuit fires the valley path once. It then settles on the periodic ZVS
  state that D42 found at 4.9 mOhm, matching D42's saved section `z*` to
  within 0.6 mA.
  - D42's own formal return check at 4.9 mOhm is a near-closure: the
    current residual is 2.8e-8 A against the 1e-8 A tolerance
    (`symbolic_derivations/02_P25_native/D42_DAMPING_CONTINUATION.md`).
  - A70 is independent circuit evidence that a periodic state exists
    there.
- **Near the orbit.** The valley path never fires, and the run is
  bit-identical to A69.

| run | start | outcome | valley firings |
|---|---|---|---:|
| 1 regression, 80 cycles | A69's perturbed D42 start | identical to A69 (max difference 0.0 in every section) | 0 |
| 2 deadlock case, 250 cycles | lossless D41 orbit (A69 deadlocked at 7.85 us) | **(a) settles on D42's 4.9 mOhm section**: last section within 0.6 mA / 10 uV of `z*`, period 2172.366 ns (D42 2172.346) | **1** (cycle 1) |
| 3 = run 2 with `dV_hys` 0.2 V | same | (a), same final state | 7 (cycles 1-10) |
| 4 unenergized inductors (exploratory) | D42 voltages, all currents 0 | (c) stalls at 6.0 us with phases (LOW, LOW, LOW): Vo = -0.52 V | 0 |

## 1. What the deadlock actually was

In run 2 the single valley firing is phase 2 in cycle 1:
- its `Vds` bottomed at **4 mV** and rose back;
- the fallback turned SH2 on at 54 mV.

A69's deadlock was therefore a near miss. The node came within 4 mV of
ZVS, fell back, and the strict `Vds <= 0` rule then had no second chance.
With the fallback the turn-on costs almost nothing.

The deviation from the orbit (max phase-current error) runs:

| cycle | 0 | 5 | 10 | 20 | 50 | 100 | 150-250 |
|---|---:|---:|---:|---:|---:|---:|---:|
| max phase-current error | 6.6 A | 6.8 A | 4.1 A | 0.58 A | 14 mA | 6 mA | ~1 mA (floor) |

With the larger hysteresis (run 3), the valley path fires seven times in
cycles 1-10, some at up to 2.4 V. The run still reaches the same orbit.

## 2. Run 4: the stall is the load model, not the high sides

At the stall:
- Vo = -0.52 V;
- the three low sides are on;
- i1 = +26.7 A and rising.

The mechanism:
1. The constant-current port draws 67.5 A from Co = 100 uF while the
   empty inductors ramp up, which pulls Vo negative.
2. With Vo < 0, phase 1's current rises during its low-side interval.
   Its -2.5 A turn-off target is therefore unreachable.
3. Nothing is wrong with the high-side rule; it never came into play.

A real converter is not started into a full constant-current load.
Stillwell and Pilawa-Podgurski (TPEL 2019, Sec. VI-C) start with the
output disconnected, ramp the input with the switching running, and
connect the load only afterwards. That sequence is the next test (Section
4). The current-target wait has a related weakness at a true zero start:
with Vo ~ 0 the current barely falls during the low-side interval.

## 3. What this means

- **For the P25-native control (mathematical and physical models).** The
  single-sensor fixed-shift rule of D41 needs the valley fallback on its
  high-side turn-on to be robust. The fallback is invisible on the orbit
  (run 1) and rescues the far start (run 2). It should become part of the
  control memory in the mathematical model (D06/D41), with the orbit and
  its stability re-checked there.
- **For Track B.** R04E21-R04E26 stalled in `COMMUTATE_HIGH_TO_ZVS`: the
  ring pulled the high side's Vds down only to 9.66 V (ZVS needs 0 V),
  and 4.8x more negative current would have been needed. That is the same missing path. At P24's 48 V, 5 MHz
  point, A67 shows ZVS is out of reach at the stated 1-2% negative current.
  - The valley path is then not a fallback but the steady-state turn-on.
    This matches Track A's tuned steady state, where the high side
    hard-switches the remaining ~10-12 V.
  - The precharge-to-controller handoff therefore does not need a
    special release sequence. It needs a turn-on rule that cannot wait
    forever.

## 4. Next (grounded in the three papers read on 2026-09-29)

The start-up test follows Stillwell and Pilawa-Podgurski's
hardware-validated sequence:
1. load disconnected;
2. switching running;
3. input or duty ramped;
4. then load connected.

Kim et al. (TPEL 2018) show the conventional SCB's soft start by duty ramp
and its start-up voltage stress. The switches see the full Vin while the
series capacitors are empty. This matters for P24: EPC2067 is rated 40 V
against a 48 V input, so the precharge step Track B built is a
requirement there. It does not matter for P25: GS61008T is rated 100 V
against 12 V.

## 5. Reproduction

```
python3 a70_transient.py regression_4p9_perturbed --cycles 80 --ref ref_D42_R4p9mohm.json --start start_D42_R4p9mohm_perturbed.json
python3 a70_transient.py deadlock_start_4p9 --cycles 250 --ref ref_D42_R4p9mohm.json --start ref_D41_lossless.json
python3 a70_transient.py deadlock_start_4p9_hys0p2 --cycles 250 --v-hys 0.2 --ref ref_D42_R4p9mohm.json --start ref_D41_lossless.json
python3 a70_transient.py zero_currents_4p9 --cycles 250 --zero-currents --ref ref_D42_R4p9mohm.json
```

Wall time is ~2 s per cycle.
