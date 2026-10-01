# A92 - error-based correctors that tolerate the gate driver (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION` + `LITERATURE_METHOD`. Written before any
code or run.

## 1. Question

A91 found that the adopted correctors cannot absorb a gate-driver delay
mismatch m.
- Each corrector **sets** its delay to a time measured from an actual edge
  (the crossing after the actual high-side turn-off; the valley after the
  actual low-side turn-off).
- The RTL adds that delay to a **command** time.

So:
- the faster side's actual dead time is its natural transition time - |m|,
  with no floor;
- LMG1210's typical 1 ns already reaches phase 4's 0.98 ns crossing;
- jitter is amplified by the reset-plus-step rule (dither 0.91 to 2.75 A at
  30 ps).

**Can an error-based update, as in the adaptive dead-time literature, keep
the module soft and free of cross-conduction for m = ±1 and ±3.4 ns and
σ = 30 and 100 ps, without breaking anything that works now?**

## 2. What others do (read for this step)

**Thuc and Chen, APEC 2023**, DOI 10.1109/APEC43580.2023.10131397, a GaN
gate-driver IC with a double-sided adaptive dead time:
- It states the problem A91 found. The command dead time "is heavily
  influenced by the delay time of" the level shifter and the gate drivers.
- **It senses the actual edges.** A phase error detector compares the real
  switch node with the real low-side gate, after comparators.
- **The output is a signed error.** UP pulses mean reverse conduction, DN
  pulses mean a hard turn-on, and the pulse width is proportional to the
  error.
- **The update is incremental:** coarse steps plus a fine charge-pump term
  proportional to the pulse width. The delay is never set to an absolute
  value.
- **It starts from a large dead time** to avoid shoot-through. A hard
  turn-on ("switching loss" dead time) is "harmful": the controller has
  to leave that condition at once.
- Result: 28-548 ps dead times.

**Lange et al., ECCE Europe 2025**, DOI
10.1109/ECCE-Europe62795.2025.11238584:
- body-diode (reverse) conduction detection;
- a fixed initial dead time "greater than optimal", then small iterative
  steps;
- a noticeable spread of the dead time within one operating point;
- adaptive step size left as future work.

**Zhang et al., TPEL 2023** (already used in A87): the dead time is a
trade-off between reverse-conduction loss and turn-on loss.

## 3. The change (RTL, opt-in)

A copy of A89's RTL in `rtl/`. A89's files are not modified. Two new
configuration bits, each off by default.

**cfg_err_low.** The low-side report carries a new field:
- ml_err = actual low-side turn-on - zero crossing, in LSB, ≥ 0 when the
  node had crossed.
- Update:
  - early (the node had not crossed): dtl += cfg_dtl_step, as before;
  - otherwise: dtl -= (ml_err - cfg_el_tgt) >>> cfg_err_shift, clamped to
    [0, cfg_dtl_max].

**cfg_err_high.** The high-side report carries:
- m_err = actual high-side turn-on - valley, in LSB, ≥ 0 when the node was
  no longer falling.
- Update:
  - early: dt_pred += cfg_dt_step, as before;
  - flat: hold, as before;
  - otherwise: dt_pred = base - ((m_err - cfg_eh_tgt) >>> cfg_err_shift),
    clamped to [0, cfg_dt_max].
- The base is the delay that phase actually used: dt_pred after a
  predictive turn-on, cfg_rs_high after a restart (learning at restarts,
  A83).

**Configuration (`PROJECT_DECISION`):**

| parameter | value | why |
|---|---|---|
| cfg_el_tgt | 3 LSB = 94 ps | inside the low side's free window after the crossing (0.16-0.23 ns, D48), away from both edges |
| cfg_eh_tgt | 3 LSB = 94 ps | after the valley, which is flat for about ±0.3 ns |
| cfg_err_shift | 1 (gain 1/2) | jitter filtering against tracking speed (Section 6) |
| dtl_init | 4.5 ns | a large initial dead time above the maximum mismatch (both papers) |
| mode-S dead time | 4.5 ns | above the maximum mismatch plus margin (A91 Section 2) |
| cfg_dt_step, cfg_dtl_step | unchanged (0.2 ns, 2 LSB) | |

**The floors are 0** on the command delays. Command order is therefore
kept: the low side is never commanded on before the high side is
commanded off, and the high side is never commanded on before the low
side is commanded off. Negative command dead times would remove the cost
named in Section 5 for m = +3.4 ns, but they are a separate step.

## 4. Sensors (bridge)

A copy of A91's bridge with the driver model. It also reports ml_err and
m_err, as A89's reports do for the old rules.
- **ml_err:** the actual low-side turn-on minus the interpolated zero
  crossing. In hardware: a low-side gate comparator (ground-referenced)
  and a switch-node comparator, as in APEC 2023's detector.
- **m_err:** the actual high-side turn-on minus the valley (the minimum
  V_DS). In hardware: the node's collapse at turn-on, and the valley
  comparator.
- Both are rounded to the 31.25 ps LSB. The comparators are ideal: no
  delay or offset. That is a stated idealisation.
- The reports go out in every run, and the RTL uses them only when its
  bit is set.

## 5. Predictions (written before the runs)

**Fixed point (Section 6).** When no floor binds:
- the actual low-side turn-on sits at crossing + 94 ps;
- the actual high-side turn-on sits at valley + 94 ps;
- **whatever m is.**

The command delays absorb m: dtl = crossing - m + 94 ps, and
dt_pred = valley + m + 94 ps.

| run | m | σ | prediction |
|---|---:|---:|---|
| g0 | flags off, no driver model | - | bit-identical to A89 r2 |
| n0 | 0 | 0 | soft, P_rev about 0, no early low-side edges. Dither ≤ 0.91 A: the targets remove A89's two-cycle early/late alternation. |
| m1p | +1 ns | 0 | as n0: dtl about 0.05-0.26 ns, so the floor does not bind |
| m1n | -1 ns | 0 | as n0, no cross-conduction: dtl about 2.0-2.3 ns |
| m3n | -3.4 ns | 0 | runs to the end, no cross-conduction. Steady state as n0 (dtl about 4.4-4.6 ns). In transients the high-side floor may bind: late turn-ons, not overlaps. |
| m3p | +3.4 ns | 0 | runs to the end, no cross-conduction. **The low-side floor binds** (dtl = 0), so the low side lands 3.4 ns after the turn-off: about 2.0-2.3 ns of reverse conduction per edge, **P_rev about 11-13 W** (D50 to compute). The high side as n0. |
| j30 | 0 | 30 ps | soft, P_rev about 0, early low-side edges ≤ 1%, **dither ≤ 1.2 A** |
| j100 | 0 | 100 ps | no cross-conduction. About 20% early and 25% beyond-window low-side edges, so small losses (< 0.3 W). Dither above n0 but **below A91's 4.73 A**. |

**No run may stop on a cross-conduction.**

## 6. Mathematical model (D50)

`symbolic_derivations/03_P24_native/D50_P24_ERROR_BASED_CORRECTORS.md`
covers:
1. the fixed point, and when the floor binds;
2. why no cross-conduction occurs when the start values and floors are as
   in Section 3;
3. the scalar jitter loop: e(k+1) - e* = (1 - g)(e(k) - e*) plus jitter
   terms, so Var(e) = 2σ²/(2 - g) = 1.33σ² at g = 1/2;
4. D47-map orbits:
   - offsets of 94 ps from the crossing and from the valley (compared with
     n0, m1p, m1n, m3n);
   - the low side fixed at 3.4 ns after the turn-off (compared with m3p).

The script is new; D47 and D49 are not changed.

## 7. Runs

All runs:
- 5%, from a zero start to 388.61 us;
- A89 r2 otherwise: realistic plant, 20 ns blanking, asynchronous phase-1
  path, learning at restarts, ki 0.25 ns/V;
- stop on the first cross-conduction.

Every run except g0 uses Section 3's configuration with both bits on.

| run | flags | m | σ | mode-S dead time | dtl_init |
|---|---|---:|---:|---:|---:|
| g0 | off | - | - | 2.15 ns | 2.15 ns |
| n0 | on | 0 | 0 | 4.5 ns | 4.5 ns |
| m1p / m1n | on | ±1 ns | 0 | 4.5 ns | 4.5 ns |
| m3p / m3n | on | ±3.4 ns | 0 | 4.5 ns | 4.5 ns |
| j30 / j100 | on | 0 | 30 / 100 ps | 4.5 ns | 4.5 ns |

**Unit tests:**
- A89's 26 tests, unchanged, with the new inputs at 0;
- new tests for each update rule, the clamps, the restart base, and both
  bits off.

**Synthesis:** yosys statistics.

## 8. Decides / does not decide

Decides:
- whether the error-based correctors tolerate LMG1210's mismatch range and
  the two jitter levels at 5%, with the gate intact.

Does not decide:
- negative command dead times, the cost at m = +3.4 ns;
- comparator delay and offset;
- driver rise and fall times;
- other loads, and line and load steps;
- the target and gain values: they are fixed here, and their optimisation
  belongs to the system-level checkpoint.

## 9. Amendment (after the runs were launched, before any result was read)

**A correction to Section 5's jitter numbers.** Each corrector's error is
the difference of two edges, and each edge carries its own independent
jitter:
- the low side: the low-side turn-on and the high-side turn-off, which
  sets the crossing;
- the high side: the high-side turn-on and the low-side turn-off.

So the jitter in the error has standard deviation √2σ, not σ. With
Section 6's loop, σ_e = √2σ · (2/(2 - g))^½ = 1.63σ at g = 1/2.

Section 5's predictions for the jitter runs become:

| run | σ_e | low side early (e < 0) | beyond 0.16 ns (reverse conduction possible) | losses |
|---|---:|---:|---:|---|
| j30 | 49 ps | about 3% | about 9% | P_rev about 0.01 W |
| j100 | 163 ps | about 28% | about 34% | P_rev about 0.2 W, small hard turn-ons; total < 0.3 W |

These are linear Gaussian estimates. They ignore the early branch, which
takes a fixed step instead of a proportional one.

The dither predictions (j30 ≤ 1.2 A; j100 above n0 and below 4.73 A) are
unchanged.
