# A83 - the corrector fix in the Verilog co-simulation (RESULTS)

Track A, `CROSS_PAPER_EXTENSION`. Boundary: `BOUNDARY.md`. Records:
- `cosim/run_h*.json`;
- `a83_summary.json`.

**Model: the physical model** (A79's plant, identical copy) with the Verilog
controller of A81, **unchanged**. Only the behavioural front end changes: it
now also measures after restart turn-ons.

## 0. Verdict

**The corrector fix carries over to the implementation-level controller.**
With the front end measuring after restart turn-ons too, the Verilog
controller settles soft at 5%, which had locked in the restart state in
A80 f1, and at 3%. It matches the Python model with the same fix (A82):

| case | target | async / learn | phase 4 | phases 1-3 Vds at turn-on | phase-4 Vds (Verilog / Python A82) | Vo | dither | peak Vds / i |
|---|---:|---|---|---|---:|---:|---:|---|
| h0 (gate) | 5% | off / off | **restart** (= A80 f1, bit for bit) | 9.05 V | 11.90 V (A80 f1: 11.90) | 1.0013 V | 1.47 A | 25.20 V / 173.7 A |
| h1 | 5% | on / on | **predictive, soft** | 8.81-8.83 V | 9.19 / 9.24 V | 1.0003 V | 1.66 A | 25.48 V / 170.4 A |
| h2 | 3% | on / on | **predictive, soft** | 9.58-9.60 V | 10.24 / 10.16 V | 0.9997 V | 1.60 A | 25.18 V / 173.4 A |

**Other results:**
- Every phase turns on once per cycle, with no restart in h1 and h2.
- The handover is at 88.80 us in every case, and Vo is inside 1% within
  65-67 us.
- The asynchronous path keeps phase 1's turn-off current within ±0.13 A of
  its mean.

**Still open:** the dither, 1.6-1.7 A against the 1 A threshold. The
suspected source is the Ton command toggling between 125 ps LSBs (A81
Section 0).

## 1. Checks

The gate h0 equals A80 f1 bit for bit: 1740 sections, difference 0.0.

## 2. Limits

- **Behavioural analog blocks.** The front end (TDC, slope detector,
  latch, delay line) is behavioural.
- **Idealised plant.** The same as A79.
- **One run per case.**

## 5a. Reproduction

```
export PATH="$HOME/tools/oss-cad-suite/bin:$PATH"
cd cosim && zsh run_a83_cosim.sh h0_gate_a80f1 h1_5pct_async_learn h2_3pct_async_learn && cd ..
python3 a83_analyze.py
```
