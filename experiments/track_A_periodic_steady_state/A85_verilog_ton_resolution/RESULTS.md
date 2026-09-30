# A85 - is the Verilog dither the Ton resolution? (RESULTS)

Track A, `CROSS_PAPER_EXTENSION`. Boundary: `BOUNDARY.md`. Records:
- `cosim/run_r7_5pct_fb7.json`;
- `a85_summary.json`.

**Model: the physical model** (A79's plant) with A81's RTL, **unchanged**
except for the parameter FB = 7, through A83's bridge.

## 0. Verdict

**Yes. The remaining Verilog dither came from the edge / Ton resolution.**
With a 7-bit delay line (31.25 ps LSB) instead of 5 bits (125 ps), all at
5%:
- the dither falls from 1.66 to 0.90 A;
- the Vo ripple at the section samples falls from 0.60 to 0.09 mV;
- the period spread falls from 1.6 to 0.3 ns;
- the maximum turn-on voltage of phases 2-4 falls from 9.21-9.63 to
  8.93-9.32 V.

**The implementation-level controller now meets single-module criterion 2
in full at 5%:**
- every phase soft once per cycle;
- no restart;
- peak Vds 25.5 V;
- dither 0.90 A < 1 A.

It also regulates Vo to 1.0002 V, with Ton 17.719 ns against Python's
17.693 ns (A82 run 1).

**Two ways to get the resolution.**
- **A finer delay line**, as here.
- **Roberts' minimum-duty-increment method.** It gives per-phase Ton codes
  that differ by one LSB, which raises the effective output-voltage
  resolution N-fold (Roberts' thesis Chapter 2, already read). It is not
  implemented here. The quantisation limit-cycle theory behind both is:
  - Peterchev and Sanders, TPEL 2003, DOI 10.1109/TPEL.2002.807092;
  - Peng et al., TPEL 2007, DOI 10.1109/TPEL.2006.886602.

  Both DOIs are verified on Crossref; neither paper has been read.

| | A83 h1 (FB = 5, 125 ps) | A85 (FB = 7, 31.25 ps) |
|---|---:|---:|
| dither (last 20 sections) | 1.66 A | **0.90 A** |
| Vo, ripple | 1.0003 V, 0.60 mV | 1.0002 V, 0.09 mV |
| period (spread) | 230.87 (1.6) ns | 230.54 (0.3) ns |
| Ton | 17.750 ns | 17.719 ns |
| phases 1-4 Vds at turn-on, mean (max) | 8.83 (8.87) / 8.81 (9.21) / 8.82 (9.23) / 9.19 (9.63) V | 8.83 (8.87) / 8.80 (8.94) / 8.80 (8.93) / 9.17 (9.32) V |
| phase-1 turn-off current | -6.37 [-6.50, -6.24] A | -6.37 [-6.50, -6.24] A |
| peak Vds / i | 25.48 V / 170.4 A | 25.50 V / 169.5 A |

**Phase 1's turn-off current** is unchanged. The asynchronous path already
made it resolution-independent (A81).

## 1. Limits

- **Feasibility of 31 ps.** Delay-line DPWMs in integrated controllers
  reach tens of ps. A C2000-class high-resolution PWM is coarser (about
  150 ps), so this is an IC-controller assumption (`PROJECT_DECISION`).
- **One run.** The RTL's 32-bit time words cover 388 us at 31.25 ps
  (12.4 million LSB), well inside 2^32.
- **The same plant and front-end idealisations as A83.**

## 5a. Reproduction

```
export PATH="$HOME/tools/oss-cad-suite/bin:$PATH"
cd cosim && zsh run_a85_cosim.sh r7_5pct_fb7 && cd ..
python3 a85_analyze.py
```
