# A83 - the corrector fix in the Verilog co-simulation (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION`. Written before any run.

## 1. Question

A82 confirmed D43's finding: the phase-4 restart state is a lock-up of a
corrector that samples only after predictive turn-ons. The Verilog runs
share that flaw:
- the RTL (A81) updates `dt_pred` on every measurement pulse;
- but the bridge's front end measures only after predictive turn-ons, and
  A80 case f1 (5%) locked in the restart state.

**Question.** With the front end also measuring after restart turn-ons,
does the Verilog controller settle soft at 5% and at 3%, as the Python model
does (A82)?

## 2. Model used, and why

**The physical model** (A79's plant, identical copy), with the Verilog
controller of A81, used **unchanged** (`run_cosim.py` builds A81's `rtl/`).
Only the behavioural front end changes, so the RTL's claims are tested
without editing it.

## 3. Cases

A80 f1's setup:
- zero start, 30x ramp, load and handover at 88.61 us, 388.61 us;
- ki 0.25 ns/V;
- 250 MHz, 125 ps edges, 10 ns driver.

| case | target | async path | measure after restarts | expectation |
|---|---:|---|---|---|
| h0 | 5% | off | off | gate: equals A80 f1 bit for bit (restart state) |
| h1 | 5% | on (1 ns) | on | every phase soft (A82 run 1) |
| h2 | 3% | on (1 ns) | on | every phase soft (A82 run 3) |

## 4. Decides / does not decide

Decides:
- whether the corrector fix carries over to the implementation-level
  controller.

Does not decide:
- the Ton-LSB dither (Roberts' minimum-duty-increment method, a later
  step);
- the measurement circuit itself (behavioural TDC and slope detector).
