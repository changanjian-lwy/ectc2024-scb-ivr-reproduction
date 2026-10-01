# A91 - gate-driver timing non-idealities in the P24 module (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION` + `EXTERNAL_DEVICE_DATA`. Written before
any run.

## 1. Question

A89 (Verilog co-simulation with A88's realistic plant) applies every gate
edge exactly t_drv = 10 ns after its command. A real half-bridge GaN driver
has two non-idealities:
- a high/low **delay mismatch**;
- cycle-to-cycle **delay jitter**.

Meanwhile:
- the timed low side has a free timing window of only 0.15-0.23 ns after
  the zero crossing (D47, D48);
- the high side turns on at a valley that is flat for only about ±0.3 ns.

**How do the adopted controller and its correctors behave with a realistic
driver?**

This is one factor, the gate driver's timing. Its two aspects, mismatch
and jitter, are run separately. Rise and fall times stay zero: the
switches remain ideal.

## 2. Data and what others do

**TI LMG1210** (GaN half-bridge driver, datasheet SNOSD12D, 2019; public),
independent input mode:

| parameter | typ | max |
|---|---:|---:|
| turn-on / turn-off delay | 10 ns | 18 ns |
| high-off to low-on and low-off to high-on delay mismatch tMTCH (over temperature, TjHI = TjLO) | 1 ns | 3.4 ns |

**Jitter: no datasheet value.** The runs sweep it as a sensitivity
(`PROJECT_DECISION`).

**Adaptive dead time in the literature.** Since 2019 it closes the loop on
the actual switching, judging from titles; none of these papers has been
read:
- switch-node or body-diode-conduction detection;
- gate-signal feedback.

Examples:
- MDPI Electronics 2023, DOI 10.3390/electronics12010211;
- APEC 2023, DOI 10.1109/APEC43580.2023.10131397;
- ECCE Europe 2025, DOI 10.1109/ECCE-Europe62795.2025.11238584.

An error-based update of this kind cancels fixed driver delays.

## 3. A prediction from the RTL rules (written before the runs)

Both A89 correctors **set** their delay to a measured time.
- **Low side.** dtl = t_cross - t_off, measured from the **actual**
  high-side turn-off.
- **High side.** dt_pred = t_valley - t_lo, measured from the **actual**
  low-side turn-off.

The RTL adds these to its **command** times. With the low-side channel m
slower than the high side (all else equal):
- actual low-side turn-on = actual crossing + m;
- actual high-side turn-on = actual valley - m.

So **a static mismatch is not learned. It reappears as a timing error of m
on both sides.**

This contradicts the hypothesis in A89 RESULTS Section 5, which said a
static mismatch "is learned into dtl". That hypothesis is tested here.

**Expected consequences:**
- **m = +1 ns** (low side slower):
  - the low side conducts in reverse for about 1 - 0.2 = 0.8 ns per edge,
    so P_rev is about 4-6 W;
  - the high side turns on about 1 ns before its valley, so the turn-on
    Vds is somewhat higher;
  - soft switching is otherwise kept.
- **m = +3.4 ns:** P_rev about 18-22 W.
- **m = -1 and -3.4 ns** (low side faster): the low side turns on m before
  the crossing, a hard turn-on at several volts.
  - The early rule then adds one 62.5 ps step per cycle until the edge
    passes the crossing.
  - The next late measurement resets dtl to the crossing time, m too early
    again.
  - So the result is a limit cycle of mostly hard turn-ons, not a fixed
    point.
- **Jitter σ:** edges scatter by σ around the learned points.
  - **σ = 30 ps** should stay within the 0.15-0.23 ns window and the flat
    valley: little effect.
  - **σ = 100 ps** puts some low-side edges more than 0.15 ns late (a little
    reverse conduction), and some early (small hard turn-ons). The dither
    rises.

## 4. Model

**The physical model at implementation level:**
- the A89 RTL, unchanged (`cfg_low_pred = 1`, `cfg_blank = 20 ns`, FB 7);
- a copy of A89's bridge, with a driver model (opt-in, `"driver"` in the
  configuration);
- A88's plant: datasheet Coss(V) and reverse drop.

**The driver model.** Every gate edge is applied at t_cmd + t_drv + δ:
- δ = m for low-side edges and 0 for high-side edges. Then both mismatch
  pairs of the LMG1210 definition (high-off to low-on, low-off to high-on)
  are |m|.
- Plus, per edge, an independent Gaussian jitter of σ (seeded RNG).
- This includes the edges scheduled by A81's asynchronous phase-1 front
  end.

**Gate g0.** Driver model off. It must replay A89 run r2 bit-identically.

## 5. Runs

All at 5%, as A89 r2:
- realistic plant;
- timed low side, 20 ns blanking;
- asynchronous phase-1 path, learning at restarts;
- ki 0.25 ns/V;
- zero start to 388.61 us.

| run | m (low minus high delay) | jitter σ | purpose |
|---|---:|---:|---|
| g0 | off | off | gate (= A89 r2) |
| m1p | +1.0 ns | 0 | typical mismatch, low side slower |
| m1n | -1.0 ns | 0 | typical mismatch, low side faster |
| m3p | +3.4 ns | 0 | maximum mismatch |
| m3n | -3.4 ns | 0 | maximum mismatch |
| j30 | 0 | 30 ps | jitter |
| j100 | 0 | 100 ps | jitter |

**Records** (A89's, plus):
- the actual low-side edge time relative to the zero crossing, per edge;
- the high-side turn-on Vds.

## 6. Mathematical-model cross-check (fixed offsets)

For m > 0 the predicted fixed point is: low-side edge at crossing + m,
high-side edge at valley - m.
- D47's event map at the m1p and m3p conditions computes the regulated
  orbit with these offsets: d_low = crossing + m, d_high = valley - m,
  self-consistent otherwise.
- The script is new; D47 is unchanged.
- The co-simulation's P_rev, Ton and turn-on voltages are compared with
  it.

For m < 0 there is no fixed point to compare: the corrector limit-cycles.

## 7. Decides / does not decide

Decides:
- whether the adopted correctors tolerate a datasheet driver mismatch;
- what jitter the timed scheme tolerates.

Does not decide:
- a corrected rule. The next step (A92) uses the error-based update the
  literature suggests, if this run confirms the prediction.
- driver rise and fall times and gate-loop dynamics;
- temperature drift of the mismatch;
- package and PCB parasitics.

## 8. Amendment (written after the runs were launched, before any result was read)

**A refinement of Section 3's high-side prediction.**
- The high-side corrector has an early rule, +0.2 ns while the node is
  still falling at the edge.
- With m > 0 its "late" reset puts the actual turn-on m before the valley.
  The node is then still falling, so the early rule moves it later by
  0.2 ns per cycle until it passes the valley, and the next late
  measurement resets it.
- So the high side does not settle at valley - m. It runs a **sawtooth
  between about valley - m and valley**: mean offset about -m/2, and a
  larger dither.
- The low side for m > 0 has no early correction (it is never early), so
  its offset +m is a fixed point, as stated.

**Consequence for Section 6.** The mathematical cross-check fixes the low
side at crossing + m and the high side at its natural valley. That
brackets the high-side effect from one end. It is compared on P_rev, which
the low-side offset dominates.

## 9. Amendment (after m3p and m3n stopped; before m3p_s45 and m3n_s45)

**What happened.** Both maximum-mismatch runs stopped on a cross-
conduction during the mode-S start-up, before the handover:
- m3n (-3.4 ns): SL1 turned on while SH1 conducted, at 25.4 ns.
- m3p (+3.4 ns): an overlap at 76 ns.

**Why.** Mode S uses P24's fixed dead time of 2.15 ns at both
transitions. LMG1210's mismatch tMTCH applies to both pairs: high-off to
low-on, and low-off to high-on.
- With |m| = 3.4 ns > 2.15 ns, one of the two transitions overlaps by
  1.25 ns.
- m = -3.4 overlaps at high-off to low-on; m = +3.4 at low-off to
  high-on.

**A finding in itself.** With a driver of this class, a fixed dead time
must exceed the maximum mismatch plus margin. P24's 2.15 ns does not.

**Added runs.** These reach mode P at the maximum mismatch. Mode S's dead
time is raised to 4.5 ns (3.4 ns plus 1.1 ns margin, `PROJECT_DECISION`);
nothing else changes. dtl still starts at 2.15 ns.

| run | m | mode-S dead time | prediction |
|---|---:|---:|---|
| m3p_s45 | +3.4 ns | 4.5 ns | runs to the end. The low side lands about 3.4 ns after the crossing (P_rev about 18-22 W); the high side runs a sawtooth. |
| m3n_s45 | -3.4 ns | 4.5 ns | start-up passes. In mode P, dtl (2.15 ns, then about 1.2 ns) < 3.4 ns, so cross-conduction at the first high-off to low-on: the run stops at the handover. |
