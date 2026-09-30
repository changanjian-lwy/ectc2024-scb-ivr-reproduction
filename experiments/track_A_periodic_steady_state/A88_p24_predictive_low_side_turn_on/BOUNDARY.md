# A88 - a predicted low-side turn-on (dead time) in the P24 module (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION`. Written before any run.

## 1. Question

A87 added EPC2067's reverse-conduction drop. Every phase stays soft, but
the low side conducts in reverse for 9.8 ns per edge, at about 2.4 V: 56 W
at 250 W out.
- The cause is the adopted mode-P rule (A75): the low side turns on only
  after its comparator sees V_DS = 0, plus the 10 ns comparator-to-gate
  latency.
- With a 2 ns latency the loss was 10 W (A87 r5).

**Does a predicted low-side turn-on remove this loss while keeping every
phase soft?**

This is one controller change, at the single-module circuit level. The
device model stays A87's: datasheet Coss(V) and reverse drop.

## 2. What others do (sources)

1. **P25 itself** (Sec. II, Modes 2' and 5'). For GaN, "minimizing Mode 2'
   is essential to prevent dead-time losses", and the bottom switch turns
   on when the node has returned to zero. The dead time comes from the
   node's charge and the peak current (Eqs. 5-6): it is timed, not sensed
   and then delayed.
2. **Zhang et al., TPEL 2023**, DOI 10.1109/TPEL.2022.3217456 (A87
   Section 4a). Dead time is a trade-off:
   - too short gives turn-on loss;
   - too long gives reverse conduction.

   They predict a reference dead time from a model of the turn-off
   transient.
3. **TI LMG1210** (GaN half-bridge driver, datasheet SNOSD12D, 2019).
   - Typical propagation delay 10 ns (21 ns max), but only 3.4 ns
     high/low mismatch.
   - In PWM mode the dead time is inserted between the two complementary
     edges, adjustable from 0.8 ns (typ) to 20 ns.
   - So the propagation latency is common to both edges and does not add
     to the dead time.
4. **This project's high-side rule** (A75/A82): a timed edge whose delay a
   per-phase corrector learns from the measured valley (early: +step;
   late: set to the measured time).

## 3. The rule (mode P; mode S keeps its fixed 2.15 ns)

**Timing.** Phase k's low side turns on at t_off,k + dtl_k, where t_off,k
is its high-side turn-off. It is a timed edge, like the high side's
predictive edge, so the comparator latency does not apply to it.

**The comparator** at V_DS(SL_k) = 0 stays, as a timestamp t_cross,k
only.

**Correction**, once per edge, at the turn-on:
- **Late:** the node crossed zero before the edge (t_cross exists), so the
  low side was reverse conducting. Set dtl_k = t_cross,k - t_off,k.
- **Early:** no crossing yet (V_DS > 0), so this is a hard turn-on at
  V_DS. Set dtl_k = dtl_k + 0.05 ns.
- Otherwise leave dtl_k unchanged.

**Settings.**
- Initial dtl = 2.15 ns (P24's dead time, as mode S).
- Cap 10 ns.
- The 20 ns restart timer stays as a guard.

**`PROJECT_DECISION`s:**
- the 0.05 ns early step (the node falls about 12 V/ns, so 0.05 ns is
  about 0.6 V);
- no extra margin after the crossing;
- the cap.

**What the rule does not change:**
- the high side;
- the phase-1 current comparator (it keeps the 10 ns latency, which the
  trim compensates);
- the loop.

## 4. Model and code

**The physical model:** `a88_transient.py`, a copy of A87's.
- `--low-mode predictive` switches the rule on.
- The default (`reactive`) is A87's path. Gate r0 must replay A87 run r1
  bit-identically.

**New records:**
- per low-side edge: V_DS at the turn-on, and whether it was early or
  late;
- a low-side turn-on proxy, 1/2 C_node V_DS^2 f, over the early edges;
- the final dtl.

## 5. Runs

A87's module and controller otherwise:
- datasheet Coss(V) and reverse drop;
- predictive valley high side, with learning at restarts;
- trim 0.5, no reactive ZVS;
- restart 20 / 400 ns;
- ki 0.25 ns/V;
- t_d 10 ns;
- zero start, 388.61 us.

| run | target | low side | purpose |
|---|---:|---|---|
| r0 | 3% | reactive (A87) | gate (= A87 r1) |
| r1 | 3% | predictive | main |
| r2 | 2% | predictive | P24's stated value |
| r3 | 5% | predictive | |
| r4 | 7.5% | predictive | |

## 6. Predictions (written before the runs)

- **P_rev** falls from about 56 W to **below 2 W**. Only the late-side
  dither of the corrector conducts in reverse.
- **The low-side turn-on proxy** stays **below 1 W**: early edges are at
  most 0.05 ns early, about 0.6 V.
- **Ton** returns close to A86's (about 17.5 ns at 3%), since the extra
  current decay disappears.
- **Phase 4's current and turn-on voltage** return close to A86's (-3.19 A
  and 9.90 V at 3%).
- **Criterion 2** passes at 2-7.5%.
- **dtl converges** near the node's fall time after the high-side turn-off,
  about 1 ns (about 13 nF x 12 V / 150 A).

## 7. Decides / does not decide

Decides:
- whether a timed low side, learnt from the zero crossing, removes the
  reverse-conduction loss without losing soft switching.

Does not decide:
- the Verilog implementation (the next step, after the mathematical
  cross-check D47);
- gate-driver dynamics (finite gate ramp, Miller plateau);
- the dynamic threshold;
- temperature;
- package and PCB parasitics (next level).
