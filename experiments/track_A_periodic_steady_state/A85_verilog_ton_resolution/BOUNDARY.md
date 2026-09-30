# A85 - is the Verilog dither the Ton resolution? (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION`. Written before the run.

## 1. Question

**What remains.** With the asynchronous path and the corrector fix (A83),
the Verilog controller's cycle-to-cycle dither is still 1.6-1.7 A. The
Python model shows 0.6-0.9 A at the same settings (A82).

**The suspected cause.** The Ton command is quantised to the 125 ps delay-
line LSB. Under the integral voltage loop it alternates between
neighbouring LSBs (about 6.7 mV of Vo each).

**Cheapest discriminating test.** Change nothing in the RTL. Only widen the
delay line from 5 to 7 bits: the parameter FB, giving an LSB of 31.25 ps.
- If the dither falls clearly, the Ton resolution is the cause. The design
  fixes are then a finer delay line or Roberts' minimum-duty-increment
  method.
- If it does not fall, the cause lies elsewhere.

## 2. Model used, and why

**The physical model** (A79's plant) with A81's RTL, unchanged, at FB = 7,
through A83's bridge. Resolution is an implementation property.

## 3. Run

A83 case h1 (5% target, async path, corrector fix, ki 0.25, zero start,
388.61 us) with FB = 7. The same times in ns map to 4x more LSB. The
predictive step becomes 6 LSB (0.1875 ns, against 0.25 ns at FB = 5). The
reference is A83 h1 at FB = 5.

## 4. Decides / does not decide

Decides:
- whether the Ton / edge resolution is the dominant source of the Verilog
  dither.

Does not decide:
- the minimum-duty-increment implementation;
- delay-line circuit feasibility at 31 ps.
